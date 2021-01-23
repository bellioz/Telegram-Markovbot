import os
import re
import nltk
import random
import logging
import markovify
import configparser

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ChatType

# Токен бота
API_TOKEN = 'ТОКЕН БОТА'
BOT_ID = int(API_TOKEN.split(':')[0])

# Настройка логгера
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Инициализация конфига
config = configparser.ConfigParser()

# Список символов после которых не ставится точка в конце предложения
symbol = ('!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-',
          '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^',
          '_', '`', '{', '|', '}', '~')

# Список того что не будет обрабатываться в сообщениях
entities_block = ['mention', 'url', 'bot_command']


# Класс markovify для использования nltk в генерации сообщений
class POSifiedText(markovify.NewlineText):
    def word_split(self, sentence):
        words = re.split(self.word_split_pattern, sentence)
        words = ["::".join(tag) for tag in nltk.pos_tag(words)]
        return words

    def word_join(self, words):
        sentence = " ".join(word.split("::")[0] for word in words)
        return sentence


# Сообщение для тех кто захочет написать в личку боту
@dp.message_handler(chat_type=ChatType.PRIVATE)
async def private(message: types.Message):
    await types.ChatActions.typing()
    await message.reply('Beep-beep, motherfucker!')


# Настройка уровня пиздливости
@dp.message_handler(commands=['set_level'])
async def level(message: types.Message):

    # Получаем id чата
    chat_id = str(message.chat.id)

    # Читаем конфиг
    config.read('configs/' + chat_id + '.cfg')
    level = int(config['SETTINGS']['level'])

    percent = message.text.replace('/set_level ', '')
    if percent.isdigit():
        percent = int(percent)
        if percent < 0 or percent > 100:
            level_text = 'Попробуй еще раз и укажи число от 0 до 100'
        elif percent > level:
            level_text = 'Уровень пиздливости повышен до ' + str(percent)
            config['SETTINGS']['level'] = str(percent)
        elif percent < level:
            level_text = 'Уровень пиздливости понижен до ' + str(percent)
            config['SETTINGS']['level'] = str(percent)
        else:
            level_text = 'Текущий уровень пиздливости: ' + str(percent)
            config['SETTINGS']['level'] = str(percent)

        with open('configs/' + chat_id + '.cfg', 'w') as configfile:
            config.write(configfile)

        await types.ChatActions.typing()
        await message.reply(level_text)
    else:
        level_text = 'Текущий уровень пиздливости: ' + str(level)
        await types.ChatActions.typing()
        await message.reply(level_text)


# Сброс базы данных и настроек чата
@dp.message_handler(commands=['reset'], is_chat_admin=True)
async def reset(message: types.Message):

    # Получаем id чата
    chat_id = str(message.chat.id)

    # Сбрасываем конфиг чата и прописываем в него настройки по умолчанию
    if os.path.exists('configs/' + chat_id + '.cfg') is True:
        os.remove('configs/' + chat_id + '.cfg')
        config['SETTINGS'] = {'level': '10'}
        with open('configs/' + chat_id + '.cfg', 'w') as configfile:
            config.write(configfile)
    else:
        if os.path.isdir('configs/') is False:
            os.makedirs('configs/')
        config['SETTINGS'] = {'level': '10'}
        with open('configs/' + chat_id + '.cfg', 'w') as configfile:
            config.write(configfile)

    # Сбрасываем файл для записи логов чата
    if os.path.exists('logs/' + chat_id + '.log') is True:
        os.remove('logs/' + chat_id + '.log')
        log = open('logs/' + chat_id + '.log', 'w', encoding='utf-8')
        log.close()
    else:
        if os.path.isdir('logs/') is False:
            os.makedirs('logs/')
        log = open('logs/' + chat_id + '.log', 'w', encoding='utf-8')
        log.close()

    await types.ChatActions.typing()
    await message.reply('База данных и настройки чата сброшены.')


# Если бот добавлен в чат, создаем файл логов и конфиг для этого чата
@dp.message_handler(content_types=types.ContentTypes.NEW_CHAT_MEMBERS)
async def new_chat_member(message: types.Message):
    for member_id in message.new_chat_members:
        if member_id['id'] == BOT_ID:

            # Получаем id чата
            chat_id = str(message.chat.id)

            # Создаем конфиг чата и прописываем в него настройки по умолчанию
            if os.path.exists('configs/' + chat_id + '.cfg') is False:
                if os.path.isdir('configs/') is False:
                    os.makedirs('configs/')
                config['SETTINGS'] = {'level': '10'}
                with open('configs/' + chat_id + '.cfg',
                          'w', encoding='utf-8') as configfile:
                    config.write(configfile)

            # Создаем файл для записи логов чата
            if os.path.exists('logs/' + chat_id + '.log') is False:
                if os.path.isdir('logs/') is False:
                    os.makedirs('logs/')
                log = open('logs/' + chat_id + '.log', 'w', encoding='utf-8')
                log.close()


@dp.message_handler()
async def message(message: types.Message):

    # Получаем id чата
    chat_id = str(message.chat.id)

    # Проверка сообщения на ссылки, команды и упоминания
    if message.entities:
        for entitie in message.entities:
            if entitie['type'] in entities_block:
                bad_entitie = True
                break
            else:
                bad_entitie = False
    else:
        bad_entitie = False

    # Записываем сообщение в лог
    with open('logs/' + chat_id + '.log', 'a', encoding='utf-8') as log:
        # Если в сообщении есть ссылка, команда или упоминание, то пропускаем,
        # иначе записываем в лог
        if bad_entitie is False:
            if message.text.endswith(symbol):
                log.write(message.text + '\n')
            else:
                log.write(message.text + '.' + '\n')

    # Производим ротацию лога если строк в логе больше 10000
    with open('logs/' + chat_id + '.log', 'r', encoding='utf-8') as log:
        lines = log.readlines()
        quantity = len(lines)
    if quantity > 10000:
        del_quantity = quantity - 10000
        with open('logs/' + chat_id + '.log', 'w', encoding='utf-8') as log:
            log.writelines(lines[del_quantity:])

    # Функция генерации сообщения
    def gen_phrase():
        # Разбиваем сообщение на слова
        words = message.text.split()

        # Читаем файл стоп-слов
        with open('stopwords.txt', 'r', encoding='utf-8') as log:
            stopwords = eval(log.read())

        # Составляем список слов из сообщения за исключением стоп-слов
        good_words = []
        for word in words:
            if len(word) > 1 and word.lower().strip(''.join(symbol)) \
                    not in stopwords:
                good_words.append(word.lower().strip(''.join(symbol)))

        # Выбираем случайное слово из списка
        if good_words:
            word = random.choice(good_words)

            # Читаем лог чата, если слово есть в какой-либо строке,
            # то добавляем эту строку в список
            with open('logs/' + chat_id + '.log', 'r',
                      encoding='utf-8') as log:
                lines = log.readlines()
                phrase_list = []
                for line in lines:
                    if re.findall(r'\b' + word + r'\b', line) or \
                            re.findall(r'\b' + word.title() + r'\b', line):
                        phrase_list.append(line)

            # Генерируем сообщение при помощи цепей Маркова
            if phrase_list:
                text_model = markovify.NewlineText(
                    phrase_list, well_formed=False)
                phrase = text_model.make_short_sentence(280)
                return phrase

    # Читаем настройки конфига
    config.read('configs/' + chat_id + '.cfg')
    level = int(config['SETTINGS']['level'])

    # Случайное число
    number = random.randint(1, 100)

    # Если в сообщении нет ссылок, команд или упоминании,
    # то генерироуем сообщение
    if bad_entitie is False:
        # Если сообщение это ответ на сообщение бота, то отвечаем на ответ
        if message.reply_to_message:
            if message.reply_to_message['from']['id'] == BOT_ID:
                phrase = gen_phrase()
                if phrase is not None:
                    await types.ChatActions.typing()
                    await message.reply(phrase)

        # Если случайное число меньше числа level из конфига
        # то генерируем сообщение
        elif number <= level:
            phrase = gen_phrase()
            if phrase is not None:
                await types.ChatActions.typing()
                await message.answer(phrase)

# Зацикливаем бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

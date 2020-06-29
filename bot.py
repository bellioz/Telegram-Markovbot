import re
import json
import random
import telebot
import markovify
# from telebot import apihelper

'''
# Прокси
apihelper.proxy = {'https': 'socks5h://127.0.0.1:9050',
                   'http': 'socks5h://127.0.0.1:9050'}
'''

# Читаем конфиг
with open('config.json', 'r', encoding='utf-8') as file:
    config = json.load(file)

botname = config['botname']  # Username бота
token = config['token']  # Токен бота
chat_id = config['chat_id']  # ID чата

bot = telebot.TeleBot(token)

# Список символов после которых не ставится точка в конце предложения
symbol = ('!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-',
          '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^',
          '_', '`', '{', '|', '}', '~')


# Функция логирования сообщений с символом в конце строки
def log(message):
    with open('phrases.txt', 'a', encoding="utf-8") as file:
        file.write(message.text + '\n')


# Функция логирования сообщений без символа в конце строки
def log_dot(message):
    with open('phrases.txt', 'a', encoding="utf-8") as file:
        file.write(message.text + '.' + '\n')


# Функция проверки кол-ва уникальных слов
@bot.message_handler(commands=['stat'])
def stat(message):
    try:
        with open('phrases.txt', 'r', encoding="utf-8") as file:
            txt = len(set(file.read().split()))
        bot.send_message(
            chat_id, 'Количество уникальных слов в базе:' + ' ' + str(txt))
    except Exception:
        pass


# Задать уровень пиздливости
@bot.message_handler(commands=['set_level'])
def set_level(message):
    try:
        percent = int(message.text.replace('/set_level ', ''))
        with open('config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)

        if percent < 0 or percent > 100:
            text_level = 'Попробуй еще раз и укажи число от 0 до 100'
        elif percent > config['random_percent']:
            text_level = 'Уровень пиздливости повышен до ' + str(percent)
            config['random_percent'] = percent
        elif percent < config['random_percent']:
            text_level = 'Уровень пиздливости понижен до ' + str(percent)
            config['random_percent'] = percent
        else:
            text_level = 'Уровень пиздливости равен ' + str(percent)
            config['random_percent'] = percent

        with open('config.json', 'w', encoding='utf-8') as file:
            json.dump(config, file)
        bot.reply_to(message, text_level)
    except Exception:
        with open('config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        percent = config['random_percent']
        set_level_text = 'Текущий уровень пиздливости: ' + str(percent)
        bot.reply_to(message, set_level_text)


# Функция рандомного сообщения
@bot.message_handler(func=lambda message: True, content_types=['text'])
def message(message):
    if '/' in message.text or '@' in message.text:
        pass
    elif message.text.endswith(symbol):
        log(message)
    else:
        log_dot(message)

    # Генерация чистой фразы
    def gen_clear_phrase():
        try:
            with open('stopwords.txt', 'r', encoding='utf-8') as file:
                stopwords = eval(file.read())

            words = message.text.split()

            good_words = []
            for word in words:
                if len(word) > 1 and word.lower().strip(''.join(symbol)) \
                        not in stopwords:
                    good_words.append(word)

            word = random.choice(good_words)

            with open('phrases.txt', 'r', encoding='utf-8') as file:
                lines = file.readlines()
                phrase_list = []
                for line in lines:
                    if re.findall(r'\b' + word + r'\b', line):
                        phrase_list.append(line)

            text_model = markovify.NewlineText(phrase_list, well_formed=False)
            phrase = text_model.make_short_sentence(280)
            return phrase
        except Exception:
            pass

    # Генерация грязной фразы
    def gen_dirty_phrase():
        try:
            with open('stopwords.txt', 'r', encoding='utf-8') as file:
                stopwords = eval(file.read())

            words = message.text.split()

            good_words = []
            for word in words:
                if len(word) > 1 and word.lower().strip(''.join(symbol)) \
                        not in stopwords:
                    good_words.append(word)

            if good_words:
                word = random.choice(good_words)
            else:
                word = random.choice(words)

            with open('phrases.txt', 'r', encoding='utf-8') as file:
                lines = file.readlines()
                phrase_list = []
                for line in lines:
                    if re.findall(r'\b' + word + r'\b', line):
                        phrase_list.append(line)

            text_model = markovify.NewlineText(phrase_list, well_formed=False)
            phrase = text_model.make_short_sentence(280)
            return phrase
        except Exception:
            pass

    # Читаем конфиг и берем от туда значение random_percent
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)

    percent = config['random_percent']

    number = random.randint(1, 100)

    try:
        if message.reply_to_message is not None:
            if message.reply_to_message.from_user.username == botname:
                bot.reply_to(message, gen_dirty_phrase())
        elif botname in message.text:
            bot.reply_to(message, gen_dirty_phrase())
        elif number <= percent:
            bot.send_message(chat_id, gen_clear_phrase())
        else:
            pass
    except Exception:
        pass


bot.infinity_polling(True)

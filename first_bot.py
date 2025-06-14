import telebot
import random
import uuid
import base64
from painter import Painter
import redis
from telebot.apihelper import download_file
from config import TOKEN
from gpt import gpt_request
import time
from voice import get_audio
import os
from pathlib import Path


bot = telebot.TeleBot(TOKEN)
# Увеличиваем таймауты для всех запросов к Telegram API
telebot.apihelper.RETRY_ON_HTTP_ERROR = True # Пытаться повторить запрос при ошибках HTTP
telebot.apihelper.READ_TIMEOUT = 90         # Увеличить таймаут чтения до 90 секунд (по умолчанию 25)
telebot.apihelper.CONNECT_TIMEOUT = 90      # Увеличить таймаут соединения до 90 секунд (по умолчанию 25)

fact_database = [
    'Первый в мире ИИ-программа, написанная в 1951 году, называлась "Нейронная сеть" и была создана для игры в шашки.',
    'В 2018 году картина, созданная ИИ, была продана на аукционе за 432 500 долларов, что вызвало большой интерес к роли ИИ в творчестве.',
    'По прогнозам, к 2025 году более 80% взаимодействий с клиентами будут осуществляться с помощью чат-ботов и ИИ-систем'
]
# --- Обработчики команд ---
@bot.message_handler(commands=['fact'])
def fact(message):
    text = random.choice(fact_database)
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['start'])
def start(message):
    text = 'Я могу рассказывать <b>интересные факты</b>. Пришлите мне /fact для этого'
    bot.send_message(message.chat.id, text, parse_mode='html')

@bot.message_handler(commands=['help'])
def help(message):
    text = 'У бота одна рабочая команда /fact, с помощью нее вы можете получить интересный фатк'
    bot.reply_to(message, text)

# --- Функция say_hi ДОЛЖНА БЫТЬ ЗДЕСЬ (перед /hi)! ---
def say_hi(message):
    name = message.text
    bot.send_message(message.chat.id, f'Привет {name}!')

@bot.message_handler(commands=['hi'])
def hi(message):
    name = bot.send_message(message.chat.id, 'Как тебя зовут?')
    bot.register_next_step_handler(name, say_hi)

def save_docunent(message):
    file_name = message.document.file_name
    file_info = bot.get_file(message.document.file_id)
    download_file = bot.download_file(file_info.file_path)
    with open(file_name, 'wb') as new_file:
        new_file.write(download_file)
    return file_name

def read_file(message):
    doc_path = save_docunent(message)
    with open(doc_path, 'r', encoding='utf-8') as text_file:
        text = text_file.read()
    result = gpt_request(f'кратко перескажи этот текст: {text}')
    bot.send_message(message.chat.id, result)


@bot.message_handler(commands=['read'])
def get_file(message):
    to_read = bot.send_message(message.chat.id, 'Пришли файл, я его прочитаю и перескажу!')
    bot.register_next_step_handler(to_read, read_file)

@bot.message_handler(commands=['image'])
def image(message):
    chat_id = message.chat.id

    r = redis.Redis(host='localhost', port=6379)
    try:
        print(r.ping())  # Должно вывести True
    except redis.ConnectionError:
        print("Ошибка подключения к Redis")

    start_time = round(time.time())
    if r.get('gen_sec') == None:
        r.set('gen_sec', 50)

    prev_time = int(r.get('gen_sec').decode('UTF-8'))
    prev_time = random.randint(prev_time - 10, prev_time + 10)

    bot.send_message(chat_id, f"Работаю над вашей иллюстрацией, это может занять ~{prev_time} сек")
    bot.send_chat_action(chat_id, action='upload_photo')

    text_list = message.text.split()
    del text_list[0]
    text = ''.join(text_list)
    api = Painter()
    model_id = api.get_model()
    u = api.generate(text, model_id)
    images = api.check_generation(u)

    if images == 'CENSORED':
        bot.send_message(chat_id, 'Изображение содержало в себе то, что может оскорбить других или нарушает законы РФ')
    else:
        uniq_id = str(uuid.uuid4())
        image_path = f'images/{uniq_id}.png'

        end_time = round(time.time())
        gen_sec = end_time - start_time
        r.set('gen_sec', gen_sec)

        with open(image_path, 'wb') as fpng:
            fpng.write(base64.b64decode(images[0]))
        with open(image_path, 'rb') as fim:
            bot.send_photo(chat_id, fim, caption=f"Изображение было создано за ~{gen_sec} сек")


@bot.message_handler(content_types=['text'])
def reaction(message):
    chat_id = message.chat.id
    text = gpt_request(message.text)
    bot.send_message(chat_id, text)



@bot.message_handler(content_types=['photo'])
def photo_reaction(message):
    chat_id = message.chat.id
    data = ["Классная фотка!",
        "Хммм, прикольно..",
        "Вау! Это фантастика!"]
    random_msg = random.choice(data)
    bot.send_message(chat_id, random_msg)

@bot.message_handler(content_types=['voice'])
def gpt_voice_question(message):
    try:
        file_info = bot.get_file(message.voice.file_id) # 1. Запрос к Telegram API для информации о файле
        down_file = bot.download_file(file_info.file_path) # 2. Запрос к Telegram API для скачивания файла
        path = f'audio/{uuid.uuid4()}.oga'
        with open(path, 'wb') as file:
            file.write(down_file)

        # Обрабатываем и получаем ответ
        reply_audio_path = get_audio(path) # Здесь начинается основная обработка

        with open(reply_audio_path, 'rb') as audio_file:
            bot.send_voice(message.chat.id, audio_file) # 3. Запрос к Telegram API для отправки файла
    except Exception as e:
        bot.reply_to(message, f"Ошибка обработки: {str(e)}")


print('Бот заработал!')

# Увеличить таймауты для pollong, если они не заданы или меньше
bot.polling(non_stop=True, interval=0, timeout=90, long_polling_timeout=90)
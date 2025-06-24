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
from telebot import types


bot = telebot.TeleBot(TOKEN)
# Увеличиваем таймауты для всех запросов к Telegram API
telebot.apihelper.RETRY_ON_HTTP_ERROR = True # Пытаться повторить запрос при ошибках HTTP
telebot.apihelper.READ_TIMEOUT = 90         # Увеличить таймаут чтения до 90 секунд (по умолчанию 25)
telebot.apihelper.CONNECT_TIMEOUT = 90      # Увеличить таймаут соединения до 90 секунд (по умолчанию 25)

user_mode = {}


@bot.message_handler(commands=['start'])
def start(message):
    # Создаём кнопки
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("🎨 Создать изображение")
    btn2 = types.KeyboardButton("📄 Пересказать файл")
    btn3 = types.KeyboardButton("🎙 Спросить голосом")
    btn4 = types.KeyboardButton("🤖 Просто поговорить")

    # Добавляем кнопки в меню
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)


    # Отправляем приветствие с меню
    bot.send_message(
        message.chat.id,
        text=(
            "👋 Привет! Я твой умный бот 🤖\n\n"
            "Вот что я умею:\n"
            "🎨 Генерировать изображения\n"
            "📄 Пересказывать файлы\n"
            "🎙 Понимать голос\n"
            "🤖 Отвечать на вопросы\n\n"
            "Выбери нужную функцию кнопкой ниже:"
        ),
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == "🎨 Создать изображение")
def image_button(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Отправьте описание изображения для генерации:')
    bot.register_next_step_handler(message, handle_image)

def handle_image(message):
    chat_id = message.chat.id

    estimated_time = random.randint(30, 60)  # имитация времени генерации

    bot.send_message(chat_id, f"Работаю над вашей иллюстрацией, это может занять ~{estimated_time} сек")
    bot.send_chat_action(chat_id, action='upload_photo')
    start_time = time.time()

    api = Painter()
    try:
        model_id = api.get_model()
    except:
        bot.send_message(chat_id, "Извините, бот временно недоступен.")
    try:
        u = api.generate(message.text, model_id)
    except:
        bot.send_message(chat_id, "Извините, бот временно недоступен.")
    try:
        images = api.check_generation(u)
    except:
        bot.send_message(chat_id, "Извините, бот временно недоступен.")

    end_time = time.time()
    gen_sec = int(end_time - start_time)

    if images == 'CENSORED':
        bot.send_message(chat_id, 'Изображение содержало в себе то, что может оскорбить других или нарушает законы РФ')
    else:
        uniq_id = str(uuid.uuid4())
        image_path = f'images/{uniq_id}.png'

        with open(image_path, 'wb') as fpng:
            fpng.write(base64.b64decode(images[0]))
        with open(image_path, 'rb') as fim:
            bot.send_photo(chat_id, fim, caption=f"Изображение было создано за ~{gen_sec} сек")


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


@bot.message_handler(func=lambda message: message.text == "📄 Пересказать файл")
def get_file_button(message):
    to_read = bot.send_message(message.chat.id, "Пожалуйста, отправьте файл (TXT):")
    bot.register_next_step_handler(to_read, read_file)


@bot.message_handler(func=lambda message: message.text == "🎙 Спросить голосом")
def voice_button(message):
    chat_id = message.chat.id
    bot.send_message(message.chat.id, "Отправьте голосовое сообщение:🎙\n\nЧтобы выйти, напишите /stop")
    user_mode[chat_id] = 'voice'


@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    chat_id = message.chat.id
    if user_mode.get(chat_id) == 'voice':
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
    else:
        bot.send_message(message.chat.id, 'Нажмите /start, чтобы выбрать действие.')


@bot.message_handler(func=lambda message: message.text == "🤖 Просто поговорить")
def chat_button(message):
    chat_id = message.chat.id
    user_mode[chat_id] = 'chat'
    bot.send_message(chat_id, "Просто напишите мне, и я отвечу 🤖\n\nЧтобы выйти, напишите /stop")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    if user_mode.get(chat_id) == 'chat':
        # Пользователь в режиме чата
        response = gpt_request(message.text)
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, 'Нажмите /start, чтобы выбрать действие.')


@bot.message_handler(commands=['stop'])
def stop_chat(message):
    chat_id = message.chat.id
    user_mode.pop(chat_id, None)
    bot.send_message(chat_id, "Нажмите /start, чтобы выбрать действие.")

print('Бот заработал!')

# Увеличить таймауты для pollong, если они не заданы или меньше
bot.polling(non_stop=True, interval=0, timeout=90, long_polling_timeout=90)
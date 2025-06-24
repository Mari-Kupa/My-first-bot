import speech_recognition as sr
from gpt import gpt_request
import subprocess
from omegaconf import OmegaConf
import os
# Указываем новую папку для кэша torch.hub (например, в корне вашего проекта)
os.environ['TORCH_HOME'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.torch_cache')
import torch


torch.hub.download_url_to_file('https://raw.githubusercontent.com/snakers4/silero-models/master/models.yml',
                               'latest_silero_models.yml',
                               progress=False)
models = OmegaConf.load('latest_silero_models.yml')

def convert_audio(input_path, output_path):
    try:
        subprocess.run(['ffmpeg', '-i', input_path, '-ar', '16000', '-ac', '1', output_path],
                       check=True,
                       stderr=subprocess.PIPE
                       )
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode()}")
        return False

def get_audio(path):
    # Конвертируем в WAV
    wav_path = path.replace('.oga', '.wav')

    if not convert_audio(path, wav_path):
        raise Exception("Ошибка конвертации аудио")

    # Распознаем текст
    voice = sr.Recognizer()
    try:
        with sr.AudioFile(wav_path) as source:
            audio = voice.record(source)
            text = voice.recognize_google(audio, language='ru-RU')
            print('тут пока всё ок')
    except Exception as e:
        raise Exception(f"Ошибка распознавания: {str(e)}")

    # Получаем ответ от GPT
    reply = gpt_request(text)
    print('ответ от GPT')
    MAX_LEN = 1000
    if len(reply) > MAX_LEN:
        reply = reply[:MAX_LEN]

    # Синтезируем речь
    model_id = 'v4_ru'
    device = torch.device('cpu')

    model, example_text = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                     model='silero_tts',
                                     language='ru',
                                     speaker=model_id, # Используем правильную модель
                                     trust_repo=True, # Добавляем для обхода предупреждения
    )

    print("Доступные спикеры:", model.speakers)
    model.to(device)

    output_path = "audio/reply.wav"
    model.save_wav(text=f'{reply}', speaker='baya', sample_rate=48000, audio_path=output_path) # Или 'aidar', 'baya' и т.д

    # Удаляем временные файлы
    # os.remove(path)
    # os.remove(wav_path)

    return output_path
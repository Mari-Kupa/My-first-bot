import requests
import time
import json
from config import *


class Painter:
    def __init__(self):
        self.KEY_API_BASE_URL = KEY_API_BASE_URL
        self.AUTH_HEADERS = {
            'X-Key': f'Key {PAINTER_API_KEY}',
            'X-Secret': f'Secret {PAINTER_SECRET_KEY}',
        }

    def get_model(self):
        try:
            response = requests.get(self.KEY_API_BASE_URL + 'key/api/v1/pipelines', headers=self.AUTH_HEADERS)
            data = response.json()
            return data[0]['id']
        except Exception as e:
            raise Exception(f"Ошибка получения модели: {str(e)}")

    def generate(self, prompt, model, images=1, width=1024, height=1024):
        try:
            params = {
                "type": "GENERATE",
                "numImages": images,
                "width": width,
                "height": height,
                "generateParams": {
                    "query": f"{prompt}"
                }
            }

            data = {
                'pipeline_id': (None, model),
                'params': (None, json.dumps(params), 'application/json')
            }
            generate_url = f"{self.KEY_API_BASE_URL}key/api/v1/pipeline/run"
            response = requests.post(generate_url, headers=self.AUTH_HEADERS, files=data)
            data = response.json()
            return data['uuid']
        except Exception as e:
            raise Exception(f"Ошибка при генерации: {str(e)}")

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            try:
                response = requests.get(self.KEY_API_BASE_URL + 'key/api/v1/pipeline/status/' + request_id, headers=self.AUTH_HEADERS)
                data = response.json()
            except Exception as e:
                raise Exception(f'Невозможно получить статус: {str(e)}')
            if data['status'] == 'DONE':
                return data['result']['files']
            attempts -= 1
            time.sleep(delay)
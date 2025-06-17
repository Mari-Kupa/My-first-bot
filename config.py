from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv('TOKEN')

GPT_TOKEN = os.getenv('GPT_TOKEN')

KEY_API_BASE_URL = os.getenv('KEY_API_BASE_URL')
PAINTER_API_KEY = os.getenv('PAINTER_API_KEY')
PAINTER_SECRET_KEY = os.getenv('PAINTER_SECRET_KEY')


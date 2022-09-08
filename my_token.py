import os

from dotenv import load_dotenv

load_dotenv()

telegram_token = os.getenv('TELEGRAM_TOKEN')
practicum_token = os.getenv('PRACTICUM_TOKEN')
chat_id = os.getenv('CHAT_ID')
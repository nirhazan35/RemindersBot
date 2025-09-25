import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
CALENDAR_URL = 'https://caldav.icloud.com'
CALENDAR_USERNAME = os.getenv('CALENDAR_USERNAME')
CALENDAR_PASSWORD = os.getenv('CALENDAR_PASSWORD')
MY_PHONE_NUMBER = os.getenv('MY_PHONE_NUMBER')
REMINDER_BODY = os.getenv('REMINDER_BODY', '').replace('\\n', '\n')
TIMEZONE = 'Asia/Jerusalem'
WA_ADAPTER_URL = os.getenv("WA_ADAPTER_URL")
WA_SHARED_SECRET = os.getenv("WA_SHARED_SECRET")
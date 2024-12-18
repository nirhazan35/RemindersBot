import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    CALENDAR_URL = 'https://caldav.icloud.com'
    CALENDAR_USERNAME = os.getenv('CALENDAR_USERNAME')
    CALENDAR_PASSWORD = os.getenv('CALENDAR_PASSWORD')
    ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
    PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')
    MY_PHONE_NUMBER = os.getenv('MY_PHONE_NUMBER')
    API_VERSION = os.getenv('VERSION')
    REMINDER_BODY = os.getenv('REMINDER_BODY')
    VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
    TIMEZONE = 'Asia/Jerusalem'
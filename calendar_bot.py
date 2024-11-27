import pytz
import datetime
import caldav
from twilio.rest import Client
import schedule
import time
from dotenv import load_dotenv
import os
import re

class CalendarReminderBot:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Calendar Credentials
        self.calendar_url = 'https://caldav.icloud.com'
        self.username = os.getenv('CALENDAR_USERNAME')
        self.password = os.getenv('CALENDAR_PASSWORD')

        # Twilio Credentials
        self.twilio_client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'), 
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        self.twilio_number = os.getenv('TWILIO_PHONE_NUMBER')

        # Timezone (Israel Time Zone)
        self.timezone = pytz.timezone('Asia/Jerusalem')  # Use Israel's timezone

    def get_tomorrow_appointments(self):
        """Retrieve appointments for tomorrow"""
        try:
            # Connect to CalDAV
            print("Connecting to calendar...")
            client = caldav.DAVClient(
                url=self.calendar_url, 
                username=self.username, 
                password=self.password
            )
            principal = client.principal()
            calendars = principal.calendars()

            print(f"Successfully connected to CalDAV. Found {len(calendars)} calendar(s).")

            # Get tomorrow's date in Israel's timezone
            tomorrow = datetime.date.today() + datetime.timedelta(days=1)
            tomorrow_start = datetime.datetime.combine(tomorrow, datetime.time.min)
            tomorrow_end = datetime.datetime.combine(tomorrow, datetime.time.max)

            # Localize the times to Israel's timezone
            tomorrow_start = self.timezone.localize(tomorrow_start)
            tomorrow_end = self.timezone.localize(tomorrow_end)

            # Search for events
            appointments = []
            for calendar in calendars:
                events = calendar.date_search(start=tomorrow_start, end=tomorrow_end)
                print(f"Found {len(events)} event(s) in {calendar}.")
                appointments.extend(events)

            return appointments

        except Exception as e:
            print(f"Error retrieving appointments: {e}")
            return []

    def send_whatsapp_reminder(self, phone_number):
        """Send WhatsApp reminder for an appointment"""
        try:
            # Extract relevant appointment details and send message
            message = self.twilio_client.messages.create(
                from_=f'whatsapp:{self.twilio_number}',
                body=f"Reminder body",
                to=f'whatsapp:+{phone_number}'
            )
            
            print(f"Reminder sent for {phone_number}")
        except Exception as e:
            print(f"Error sending reminder: {e}")

    def extract_phone_number(self, description):
        """Extract phone number from event description and format it"""
        phone_number_match = re.search(r"(?:\+9725|05)\d{8}", description)
        if phone_number_match:
            phone_number = phone_number_match.group(0)
            # converting 05 to 9725
            if phone_number.startswith('05'):
                return '9725' + phone_number[2:]
            return phone_number
        return None

    def run_daily_check(self):
        """Daily routine to check appointments and send reminders"""
        print("Checking appointments...")
        appointments = self.get_tomorrow_appointments()
        
        for appointment in appointments:
            if hasattr(appointment, 'instance'):
                event_data = appointment.instance.vevent
                summary = event_data.summary.value if hasattr(event_data, 'summary') else 'No Summary'
                description = event_data.description.value if hasattr(event_data, 'description') else 'No Description'
            else:
                summary = getattr(appointment, 'summary', 'No Summary')
                description = getattr(appointment, 'description', 'No Description')

            print(f"Event Summary: {summary}")
            print(f"Event Description: {description}")

            if re.match(r"^tipul", summary.lower()):
                print(f"Matching event found: {summary}")
                phone_number = self.extract_phone_number(description)
                if phone_number:
                    self.send_whatsapp_reminder(phone_number)

def main():
    bot = CalendarReminderBot()
    
    # Schedule daily check at 8 PM Israel time
    #schedule.every().day.at("20:00").do(bot.run_daily_check)
    print("bot is running")
    bot.run_daily_check()




import pytz
import datetime
import caldav
import requests
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

        # WhatsApp API Credentials
        self.access_token = os.getenv('ACCESS_TOKEN')
        self.phone_number_id = os.getenv('PHONE_NUMBER_ID')
        self.my_phone_number = os.getenv('MY_PHONE_NUMBER')
        self.api_version = os.getenv('VERSION')

        # Reminder Template
        self.reminder_body = os.getenv('REMINDER_BODY')

        # Timezone (Israel Time Zone)
        self.timezone = pytz.timezone('Asia/Jerusalem')

    def get_tomorrow_tipul_appointments(self):
        """Retrieve tomorrow's appointments that start with 'tipul'"""
        try:
            print("Connecting to calendar...")
            client = caldav.DAVClient(
                url=self.calendar_url, 
                username=self.username, 
                password=self.password
            )
            principal = client.principal()
            calendars = principal.calendars()
            
            # Get tomorrow's start and end times
            tomorrow_start, tomorrow_end = self.get_tommorrows_time()

            tipul_appointments = []

            # Loop through all calendars
            for calendar in calendars:
                events = calendar.date_search(start=tomorrow_start, end=tomorrow_end)

                for event in events:
                    if hasattr(event, 'instance'):
                        event_data = event.instance.vevent
                        summary = event_data.summary.value if hasattr(event_data, 'summary') else ''
                        description = event_data.description.value if hasattr(event_data, 'description') else ''
                        
                        start_time = f"{event_data.dtstart.value.astimezone(self.timezone).hour}:{event_data.dtstart.value.astimezone(self.timezone).minute:02d}"
                        print(f"Found event: {summary} ({description}) at {start_time}")
                    else:
                        summary = getattr(event, 'summary', '')
                        description = getattr(event, 'description', '')

                    # Filtering only events that start with "tipul"
                    if re.match(r"^(tipul|טיפול)" , summary.lower()):
                        print(f"Matching event found: {summary}")
                        tipul_appointments.append((summary, description, start_time))

            return tipul_appointments

        except Exception as e:
            print(f"Error retrieving appointments: {e}")
            return []
        
    def get_tommorrows_time(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        tomorrow_start = datetime.datetime.combine(tomorrow, datetime.time.min)
        tomorrow_end = datetime.datetime.combine(tomorrow, datetime.time.max)
        tomorrow_start = self.timezone.localize(tomorrow_start)
        tomorrow_end = self.timezone.localize(tomorrow_end)
        return tomorrow_start, tomorrow_end

    def send_whatsapp_reminder(self, phone_number, start_time):
        """Send WhatsApp reminder for an appointment"""
        try:
            # Load the reminder body template from .env file
            reminder_template = self.reminder_body
            # Format the template with the start time
            formatted_body = reminder_template.format(start_time=start_time)

            url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {"body": formatted_body}
            }

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                print(f"Reminder sent successfully to {phone_number}")
            else:
                print(f"Failed to send reminder. Status: {response.status_code}, Response: {response.text}")

        except Exception as e:
            print(f"Error sending reminder: {e}")

    def send_confirmation_request(self, appointment_time):
        """Send a confirmation request to yourself before sending reminders"""
        try:
            url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": self.my_phone_number,
                "type": "text",
                "text": {
                    "body": f"Do you want to send the reminder for the appointment at {appointment_time}? Reply 'yes' to confirm."
                }
            }

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                print("Confirmation request sent to you successfully.")
            else:
                print(f"Failed to send confirmation. Status: {response.status_code}, Response: {response.text}")

        except Exception as e:
            print(f"Error sending confirmation request: {e}")



    def extract_phone_number(self, description):
        """Extract phone number from event description and format it"""
        phone_number_match = re.search(r"(?:\+9725|05)\d{8}", description)
        if phone_number_match:
            phone_number = phone_number_match.group(0)
            if phone_number.startswith('05'):
                return '9725' + phone_number[2:]
            return phone_number
        return None

    def run_daily_check(self):
        """Daily routine to check appointments and send reminders"""
        print("Checking appointments...")
        tipul_appointments = self.get_tomorrow_tipul_appointments()

        for summary, description, start_time in tipul_appointments:
            print(f"Event Summary: {summary}")
            print(f"Event Description: {description}")
            print(f"Event Start Time: {start_time}")

            phone_number = self.extract_phone_number(description)
            if phone_number:
                self.send_whatsapp_reminder(phone_number, start_time)
            else:
                print("Phone number not found in description.")


def main():
    bot = CalendarReminderBot()
    
    print("Bot is running")
    bot.run_daily_check()

if __name__ == "__main__":
    main()

import pytz
import datetime
import caldav
import requests
import re
from dotenv import load_dotenv
import os
import time


class CalendarReminderBot:
    def __init__(self, pending_confirmations):
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

        # Shared pending confirmation storage
        self.pending_confirmations = pending_confirmations

    def get_tomorrow_tipul_appointments(self):
        """Retrieve tomorrow's appointments that start with 'tipul'."""
        print("Connecting to calendar...")
        try:
            client = caldav.DAVClient(url=self.calendar_url, username=self.username, password=self.password)
            principal = client.principal()
            calendars = principal.calendars()

            tomorrow_start, tomorrow_end = self.get_tomorrow_time()

            tipul_appointments = []
            print("Retrieving appointments...")
            for calendar in calendars:
                events = calendar.date_search(start=tomorrow_start, end=tomorrow_end)
                print(f"Retrieved {len(events)} events from {calendar.name}")
                for event in events:
                    if hasattr(event, 'instance'):
                        event_data = event.instance.vevent
                        summary = event_data.summary.value if hasattr(event_data, 'summary') else ''
                        description = event_data.description.value if hasattr(event_data, 'description') else ''
                        start_time = f"{event_data.dtstart.value.astimezone(self.timezone).hour}:{event_data.dtstart.value.astimezone(self.timezone).minute:02d}"
                    else:
                        summary = getattr(event, 'summary', '')
                        description = getattr(event, 'description', '')
                    if re.match(r"^(tipul|טיפול)", summary.lower()):
                        tipul_appointments.append((summary, description, start_time))

            return tipul_appointments

        except Exception as e:
            print(f"Error retrieving appointments: {e}")
            return []

    def get_tomorrow_time(self):
        """Calculate tomorrow's start and end times."""
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        tomorrow_start = self.timezone.localize(datetime.datetime.combine(tomorrow, datetime.time.min))
        tomorrow_end = self.timezone.localize(datetime.datetime.combine(tomorrow, datetime.time.max))
        return tomorrow_start, tomorrow_end

    def send_confirmation_request(self, appointment_time, customer_number):
        """Send a button confirmation request to yourself before sending reminders"""
        try:
            url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": self.my_phone_number,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "header": {
                        "type": "text",
                        "text": "Reminder Confirmation"
                    },
                    "body": {
                        "text": f"Do you want to send the reminder for the appointment at {appointment_time}?"
                    },
                    "footer": {
                        "text": "Click an option to confirm."
                    },
                    "action": {
                        "buttons": [
                            {
                                "type": "reply",
                                "reply": {
                                    "id": f"yes_confirmation${appointment_time}",
                                    "title": "Yes"
                                }
                            },
                            {
                                "type": "reply",
                                "reply": {
                                    "id": f"no_confirmation${appointment_time}",
                                    "title": "No"
                                }
                            }
                        ]
                    }
                }
            }

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                print("response: ", response)
                self.pending_confirmations[customer_number+'$'+appointment_time] = {'customer_number': customer_number, 'start_time': appointment_time}
                print(f"Pending Confirmations: {self.pending_confirmations}")
                print("Confirmation request with buttons sent to you successfully.")
            else:
                print(f"Failed to send confirmation. Status: {response.status_code}, Response: {response.text}")

        except Exception as e:
            print(f"Error sending confirmation request: {e}")


    def send_whatsapp_reminder(self, customer_number ,appointment_time):
        """Send a button confirmation request to yourself before sending reminders"""
        try:
            url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": customer_number,
                "type": "text",
                "text": {
                    "body": self.reminder_body.format(start_time=appointment_time)

                }
            }

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                print("Message sent to customer.")
            else:
                print(f"Failed to send message to customer. Status: {response.status_code}, Response: {response.text}")

        except Exception as e:
            print(f"Error sending reminder message request: {e}")

    def run_daily_check(self):
        """Scan for appointments and send confirmation requests."""
        print("Checking appointments...")
        appointments = self.get_tomorrow_tipul_appointments()

        for _, description, start_time in appointments:
            customer_number = self.extract_phone_number(description)
            if customer_number:
                self.send_confirmation_request(start_time, customer_number)
            else:
                print("No phone number found.")

    def extract_phone_number(self, description):
        """Extract phone number from event description."""
        match = re.search(r"(?:\+9725|05)\d{8}", description)
        if match:
            phone_number = match.group(0)
            return '972' + phone_number[1:] if phone_number.startswith('05') else phone_number
        return None


# if __name__ == "__main__":
#     from collections import defaultdict

#     # Shared pending confirmation dictionary
#     pending_confirmations = defaultdict(dict)
#     bot = CalendarReminderBot(pending_confirmations)
#     bot.run_daily_check()

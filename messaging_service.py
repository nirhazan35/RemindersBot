import requests

class MessagingService:
    def __init__(self, config):
        self.access_token = config.ACCESS_TOKEN
        self.phone_number_id = config.PHONE_NUMBER_ID
        self.my_phone_number = config.MY_PHONE_NUMBER
        self.api_version = config.API_VERSION
        self.reminder_body = config.REMINDER_BODY

    def send_confirmation_request(self, appointment_time, customer_number):
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
                "header": {"type": "text", "text": "Reminder Confirmation"},
                "body": {"text": f"Do you want to send the reminder for the appointment at {appointment_time}?"},
                "footer": {"text": "Click an option to confirm."},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": f"yes_confirmation${appointment_time}", "title": "Yes"}},
                        {"type": "reply", "reply": {"id": f"no_confirmation${appointment_time}", "title": "No"}},
                    ]
                },
            },
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"Failed to send confirmation: {response.text}")

    def send_customer_whatsapp_reminder(self, customer_number, appointment_time):
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": customer_number,
            "type": "text",
            "text": {"body": self.reminder_body.format(start_time=appointment_time)},
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"Failed to send reminder: {response.text}")

    def send_acknowledgement(self, customer_number, appointment_time, response):
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        if response == "yes_confirmation":
            payload = {
                "messaging_product": "whatsapp",
                "to": self.my_phone_number,
                "type": "text",
                "text": {"body": f"Reminder sent to {customer_number} for the appointment at {appointment_time}."},
            }
        else:
            payload = {
                "messaging_product": "whatsapp",
                "to": self.my_phone_number,
                "type": "text",
                "text": {"body": f"Reminder declined to {customer_number} for the appointment at {appointment_time}."},
            }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"Failed to send reminder: {response.text}")
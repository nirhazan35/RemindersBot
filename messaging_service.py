import requests

class MessagingService:
    def __init__(self, config):
        # Initialize WhatsApp API credentials
        self.access_token = config.ACCESS_TOKEN
        self.phone_number_id = config.PHONE_NUMBER_ID
        self.my_phone_number = config.MY_PHONE_NUMBER
        self.api_version = config.API_VERSION
        self.reminder_body = config.REMINDER_BODY

    def send_confirmation_request(self, appointment_time, customer_name):
        # Send a confirmation request
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
                "header": {"type": "text", "text": "אישור שליחת תזכורת"},
                "body": {"text": f"האם תרצי לשלוח הודעת תזכורת לטיפול של {customer_name} שמתקיים בשעה {appointment_time}?"},
                "footer": {"text": "בחרי אופציה."},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": f"yes_confirmation${appointment_time}", "title": "כן"}},
                        {"type": "reply", "reply": {"id": f"no_confirmation${appointment_time}", "title": "לא"}},
                    ]
                },
            },
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"Failed to send confirmation: {response.text}")

    def send_customer_whatsapp_reminder(self, customer_number, appointment_time):
        # Send a WhatsApp reminder to the customer
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

    def send_acknowledgement(self, customer_name, appointment_time, response):
        # Send a WhatsApp message to the user that the reminder has been sent
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
                "text": {"body": f"✅ נשלחה תזכורת ל{customer_name} לטיפול שיתקיים בשעה {appointment_time}."},
            }
        else:
            payload = {
                "messaging_product": "whatsapp",
                "to": self.my_phone_number,
                "type": "text",
                "text": {"body": f"❌ לא נשלחה תזכורת ל{customer_name} לטיפול שיתקיים בשעה {appointment_time}."},
            }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"Failed to send reminder: {response.text}")

    def send_no_appointments_message(self):
        # Send a message to the user if there are no appointments
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": self.my_phone_number,
            "type": "text",
            "text": {"body": "לא נמצאו טיפולים למחר."},
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"Failed to send no appointments message: {response.text}")

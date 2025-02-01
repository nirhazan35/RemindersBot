import logging
import requests
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class WhatsappMessagingService:
    """
    A service to interact with the WhatsApp Business API via Facebook Graph.
    Handles sending various types of messages, such as confirmations, reminders, and notifications.
    """

    def __init__(self, config: Any) -> None:
        """
        Initializes WhatsApp API credentials from config.

        :param config: An object or dict containing required credentials like:
                       - ACCESS_TOKEN
                       - PHONE_NUMBER_ID
                       - MY_PHONE_NUMBER
                       - API_VERSION
                       - REMINDER_BODY
        """
        self.access_token = config.ACCESS_TOKEN
        self.phone_number_id = config.PHONE_NUMBER_ID
        self.my_phone_number = config.MY_PHONE_NUMBER
        self.api_version = config.API_VERSION
        self.reminder_body = config.REMINDER_BODY

    def send_confirmation_request(self, appointment_time: str, customer_name: str) -> None:
        """
        Sends a WhatsApp confirmation request to the user's own WhatsApp 
        (self.my_phone_number). The request includes interactive buttons 
        for 'yes' or 'no' confirmation.

        :param appointment_time: The appointment time (string).
        :param customer_name: Customer name for personalized messaging.
        """
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
                "body": {
                    "text": (
                        f"האם תרצי לשלוח הודעת תזכורת לטיפול של {customer_name} "
                        f"שמתקיים בשעה {appointment_time}?"
                    )
                },
                "footer": {"text": "בחרי אופציה."},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"yes_confirmation${appointment_time}",
                                "title": "כן",
                            },
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"no_confirmation${appointment_time}",
                                "title": "לא",
                            },
                        },
                    ]
                },
            },
        }

        logger.debug("Sending confirmation request payload: %s", payload)
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            logger.warning("Failed to send confirmation: %s", resp.text)

    def send_customer_whatsapp_reminder(self, customer_number: str, appointment_time: str) -> None:
        """
        Sends a WhatsApp reminder message to the given customer number.

        :param customer_number: Customer's WhatsApp phone number in the correct format.
        :param appointment_time: The appointment time (string).
        """
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

        logger.debug("Sending reminder payload: %s", payload)
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            logger.warning("Failed to send reminder: %s", resp.text)

    def send_acknowledgement(self, customer_name: str, appointment_time: str, user_response: str) -> None:
        """
        Sends an acknowledgement message to the user’s own WhatsApp (self.my_phone_number),
        indicating whether a reminder was sent or not.

        :param customer_name: Name of the customer
        :param appointment_time: The appointment time
        :param user_response: Either 'yes_confirmation' or something else (interpreted as 'no')
        """
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        if user_response == "yes_confirmation":
            text_body = f"✅ נשלחה תזכורת ל{customer_name} לטיפול שיתקיים בשעה {appointment_time}."
        else:
            text_body = f"❌ לא נשלחה תזכורת ל{customer_name} לטיפול שיתקיים בשעה {appointment_time}."

        payload = {
            "messaging_product": "whatsapp",
            "to": self.my_phone_number,
            "type": "text",
            "text": {"body": text_body},
        }

        logger.debug("Sending acknowledgement payload: %s", payload)
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            logger.warning("Failed to send acknowledgement: %s", resp.text)

    def send_no_appointments_message(self) -> None:
        """
        Sends a message to the user’s own WhatsApp indicating no appointments found for tomorrow.
        """
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

        logger.debug("Sending no appointments message payload: %s", payload)
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            logger.warning("Failed to send no appointments message: %s", resp.text)

    def test(self) -> None:
        """
        Sends a test message to a hard-coded phone number for debugging.
        """
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": "972527332808",
            "type": "text",
            "text": {"body": "This is a test message."},
        }

        logger.debug("Sending test message payload: %s", payload)
        resp = requests.post(url, headers=headers, json=payload)
        logger.info("Test message response: %d %s", resp.status_code, resp.text)

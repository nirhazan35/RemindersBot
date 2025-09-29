# app/whatsapp_messaging_service.py
"""
WhatsApp messaging service that talks to the local Baileys adapter.
Handles sending reminders, confirmations, and acknowledgements.
"""
import logging
import os
from typing import Any, Optional, Dict

import httpx

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Adapter configuration (override via env or your app config as needed)
WA_ADAPTER_URL = os.getenv("WA_ADAPTER_URL", "http://wa-adapter:3001")
WA_SHARED_SECRET = os.getenv("WA_SHARED_SECRET", "change_me_strong_shared_secret")


def _to_msisdn(jid_or_number: str) -> str:
    """
    Normalize to a bare MSISDN (digits only, no @s.whatsapp.net).
    """
    if "@s.whatsapp.net" in jid_or_number:
        jid_or_number = jid_or_number.split("@", 1)[0]
    return "".join(ch for ch in jid_or_number if ch.isdigit())


class WhatsappMessagingService:
    """
    WhatsApp messaging service that talks to the local Baileys adapter.
    Preserves the previous public API used by your app.
    """

    def __init__(self, config: Any) -> None:
        """
        :param config: object/dict with:
            - MY_PHONE_NUMBER
            - REMINDER_BODY (format string supporting {start_time})
        """
        # Keep the same fields you previously relied on:
        self.my_phone_number: Optional[str] = getattr(config, "MY_PHONE_NUMBER", None)
        self.reminder_body: str = getattr(
            config,
            "REMINDER_BODY",
            "תזכורת: הטיפול יתקיים בשעה {start_time}.",
        )

        # Adapter endpoint + auth
        self.base_url: str = getattr(config, "WA_ADAPTER_URL", WA_ADAPTER_URL)
        self.shared_token: str = getattr(config, "WA_SHARED_SECRET", WA_SHARED_SECRET)

        if not self.shared_token or self.shared_token == "change_me_strong_shared_secret":
            logger.warning("WA_SHARED_SECRET is not set to a strong value.")

    # ---------- Low-level HTTP helpers ----------

    async def _post(self, path: str, json: Dict) -> Dict:
        """Send POST request to WhatsApp adapter."""
        url = f"{self.base_url}{path}"
        headers = {"X-Token": self.shared_token}
        logger.debug("POST %s payload=%s", url, json)
        
        try:
            async with httpx.AsyncClient(timeout=20, headers=headers) as client:
                resp = await client.post(url, json=json)
                resp.raise_for_status()
                data = resp.json()
                logger.debug("Response %s -> %s", url, data)
                return data
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error %s for %s: %s", e.response.status_code, url, e.response.text)
            raise
        except httpx.TimeoutException:
            logger.error("Timeout calling WhatsApp adapter: %s", url)
            raise
        except Exception as e:
            logger.error("Unexpected error calling WhatsApp adapter %s: %s", url, str(e))
            raise

    async def _get(self, path: str) -> Dict:
        """Send GET request to WhatsApp adapter."""
        url = f"{self.base_url}{path}"
        logger.debug("GET %s", url)
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                logger.debug("Response %s -> %s", url, data)
                return data
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error %s for %s: %s", e.response.status_code, url, e.response.text)
            raise
        except httpx.TimeoutException:
            logger.error("Timeout calling WhatsApp adapter: %s", url)
            raise
        except Exception as e:
            logger.error("Unexpected error calling WhatsApp adapter %s: %s", url, str(e))
            raise

    # ---------- Optional utilities you may use elsewhere ----------

    async def health(self) -> Dict:
        """Check adapter readiness."""
        return await self._get("/health")

    async def get_qr(self) -> Dict:
        """
        Get current QR if not logged in. Useful to render in an admin page.
        Returns: {"loggedIn": bool, "qr": str|None}
        """
        return await self._get("/qr")

    # ---------- Public API (same names as before) ----------

    async def send_confirmation_request(self, appointment_time: str, customer_name: str) -> None:
        """
        Sends an approval prompt as text message to your own WhatsApp (MY_PHONE_NUMBER).
        User can reply with 'כן' or 'לא' as simple text.
        """
        if not self.my_phone_number:
            raise ValueError("MY_PHONE_NUMBER is required to send confirmation requests.")

        body_text = (
            f"🔔 *אישור שליחת תזכורת*\n\n"
            f"האם לשלוח הודעת תזכורת ל*{customer_name}* "
            f"בשעה *{appointment_time}*?\n\n"
            f"💡 השב/י:\n"
            f"• *כן* - לשליחת התזכורת\n"
            f"• *לא* - לביטול השליחה\n\n"
            f"🕐 זמן טיפול: {appointment_time}\n"
            f"👤 לקוח: {customer_name}"
        )

        payload = {
            "to": _to_msisdn(self.my_phone_number),
            "text": body_text
        }

        await self._post("/send/text", payload)

    async def send_customer_whatsapp_reminder(self, customer_number: str, appointment_time: str) -> None:
        """
        Sends a reminder text to the given customer number.
        """
        text = self.reminder_body.format(start_time=appointment_time)
        payload = {"to": _to_msisdn(customer_number), "text": text}
        await self._post("/send/text", payload)

    async def send_acknowledgement(self, customer_name: str, appointment_time: str, user_response: str) -> None:
        """
        Sends an acknowledgement to your own WhatsApp indicating whether a reminder was sent.
        Can also be used to send custom messages by passing text in user_response.
        """
        if not self.my_phone_number:
            raise ValueError("MY_PHONE_NUMBER is required to send acknowledgements.")

        # Handle custom messages (when customer_name is empty)
        if not customer_name and not appointment_time:
            text_body = user_response
        elif user_response == "yes_confirmation":
            text_body = f"✅ נשלחה תזכורת ל*{customer_name}* לטיפול בשעה *{appointment_time}*."
        elif user_response == "no_confirmation":
            text_body = f"❌ לא נשלחה תזכורת ל*{customer_name}* לטיפול בשעה *{appointment_time}*."
        else:
            # For other custom messages
            text_body = user_response

        payload = {"to": _to_msisdn(self.my_phone_number), "text": text_body}
        await self._post("/send/text", payload)

    async def send_no_appointments_message(self) -> None:
        """
        Notifies you that no appointments were found for tomorrow.
        """
        if not self.my_phone_number:
            raise ValueError("MY_PHONE_NUMBER is required to send notifications.")
        payload = {"to": _to_msisdn(self.my_phone_number), "text": "לא נמצאו טיפולים למחר."}
        await self._post("/send/text", payload)

    async def test(self) -> None:
        """
        Sends a simple test message to your own WhatsApp.
        """
        if not self.my_phone_number:
            raise ValueError("MY_PHONE_NUMBER is required to send test messages.")
        payload = {"to": _to_msisdn(self.my_phone_number), "text": "This is a test message."}
        await self._post("/send/text", payload)
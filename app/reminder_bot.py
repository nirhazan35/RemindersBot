import re
from typing import List, Tuple, Optional

class ReminderBot:
    """
    Coordinates daily checks for tomorrow's appointments:
    - Fetches appointments from a CalendarService
    - Extracts phone numbers from the event description
    - Stores them in a PendingConfirmationManager
    - Sends messages via a MessagingService
    """
    def __init__(self, calendar_service, messaging_service, confirmation_manager):
        """
        :param calendar_service: An instance with a method get_tomorrow_appointments() that returns List of (summary, description, start_time).
        :param messaging_service: An instance responsible for sending messages (WhatsApp, SMS, etc.).
        :param confirmation_manager: Manages "pending confirmations" in storage.
        """
        self.calendar_service = calendar_service
        self.messaging_service = messaging_service
        self.confirmation_manager = confirmation_manager

    async def run_daily_check(self) -> None:
        """
        Fetch tomorrow's appointments. If none, notify that no appointments exist.
        Otherwise, for each appointment:
         - Extract phone number from description
         - Derive a customer name from summary
         - Add a pending confirmation record
         - Send a WhatsApp message to the customer
        """
        appointments: List[Tuple[str, str, str]] = self.calendar_service.get_tomorrow_appointments()
        if not appointments:
            self.messaging_service.send_no_appointments_message()
            return

        for summary, description, start_time in appointments:
            customer_number = self.extract_phone_number(description)
            # Safely handle name extraction from summary
            customer_name = self._extract_customer_name(summary)

            if customer_number:
                # Build a unique key with phone number + start_time
                key = f"{customer_number}${start_time}"

                # Store in DB (pending confirmation)
                await self.confirmation_manager.add_confirmation(
                    key,
                    {
                        "customer_name": customer_name,
                        "customer_number": customer_number,
                        "start_time": start_time,
                    },
                )

                # Send message
                self.messaging_service.send_confirmation_request(start_time, customer_name)


    @staticmethod
    def extract_phone_number(description: str) -> Optional[str]:
        """
        Extracts a phone number from the event description. 
        Accepts Israeli phone formats: +9725XXXXXXXX or 05XXXXXXXX.

        :param description: The event description string.
        :return: A normalized phone number with '972' prefix if it starts with '05', 
                 otherwise the matched phone. Returns None if no match found.
        """
        match = re.search(r"(?:\+9725|05)\d{8}", description)
        if match:
            phone_number = match.group(0)
            # If it starts with '05', convert to '9725...'
            if phone_number.startswith("05"):
                return "972" + phone_number[1:]
            return phone_number
        return None

    @staticmethod
    def _extract_customer_name(summary: str) -> str:
        """
        Extracts a customer name from the summary by splitting on space
        and taking the second token if possible. If not, returns a fallback name.

        :param summary: The event summary.
        :return: A best-guess name from the summary, or 'Unknown' if not parseable.
        """
        parts = summary.split()
        return parts[1] if len(parts) > 1 else "Unknown"

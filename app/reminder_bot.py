"""
ReminderBot coordinates daily checks for tomorrow's appointments.
Fetches appointments, extracts contact info, and manages reminder confirmations.
"""
import logging
import re
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

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
        :param calendar_service: An instance with a method get_tomorrow_appointments() -> List[(summary, description, start_time)]
        :param messaging_service: An instance with async methods to send WhatsApp messages.
        :param confirmation_manager: Manages "pending confirmations" in storage (async).
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
         - Send a WhatsApp approval request to the operator
        """
        try:
            appointments: List[Tuple[str, str, str]] = self.calendar_service.get_tomorrow_appointments()
            logger.info(f"Found {len(appointments)} appointments for tomorrow")
            
            if not appointments:
                await self.messaging_service.send_no_appointments_message()
                return

            processed_count = 0
            for summary, description, start_time in appointments:
                try:
                    customer_number = self.extract_phone_number(description)
                    customer_name = self._extract_customer_name(summary)

                    if customer_number:
                        # Unique key with phone number + start_time
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

                        # Ask the operator for approval
                        await self.messaging_service.send_confirmation_request(start_time, customer_name)
                        processed_count += 1
                        logger.info(f"Added confirmation request for {customer_name} at {start_time}")
                    else:
                        logger.warning(f"No phone number found for appointment: {summary} at {start_time}")
                        
                except Exception as e:
                    logger.error(f"Error processing appointment {summary}: {str(e)}")
                    continue
                    
            logger.info(f"Daily check completed. Processed {processed_count} appointments")
            
        except Exception as e:
            logger.error(f"Error during daily check: {str(e)}")
            raise

    @staticmethod
    def extract_phone_number(description: str) -> Optional[str]:
        """
        Extract phone number from the description using a regex.
        Looks for `טלפון: 05X-XXXXXXX` or `טלפון: 05XXXXXXXX` or plain 05XXXXXXXX patterns.
        """
        if not description:
            return None

        # Common Israeli mobile patterns; normalize to digits only (no dashes/spaces).
        patterns = [
            r"טלפון:\s*(05\d[-\s]?\d{7})",
            r"(05\d[-\s]?\d{7})",
        ]
        for pat in patterns:
            m = re.search(pat, description)
            if m:
                phone = re.sub(r"\D", "", m.group(1))
                # Basic sanity: start with '05' and length 10
                if phone.startswith("05") and len(phone) == 10:
                    # Convert to international without leading 0: 9725XXXXXXX
                    return "972" + phone[1:]
        return None

    @staticmethod
    def _extract_customer_name(summary: str) -> str:
        """
        Extract a customer name from the summary by splitting on space
        and taking the second token if possible. If not, returns a fallback name.
        """
        if not summary:
            return "Unknown"
        parts = summary.split()
        return parts[1] if len(parts) > 1 else "Unknown"
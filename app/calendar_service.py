import logging
import caldav
import pytz
import datetime
from typing import List, Tuple

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class CalendarService:
    """
    Handles interaction with a CalDAV server to fetch appointments for tomorrow.
    """

    def __init__(self, config):
        """
        :param config: An object that provides CALENDAR_URL, CALENDAR_USERNAME, 
                       CALENDAR_PASSWORD, TIMEZONE, etc.
        """
        self.calendar_url = config.CALENDAR_URL
        self.username = config.CALENDAR_USERNAME
        self.password = config.CALENDAR_PASSWORD
        self.timezone = pytz.timezone(config.TIMEZONE)

    def get_tomorrow_appointments(self) -> List[Tuple[str, str, str]]:
        """
        Fetch tomorrow's appointments from all calendars under the configured principal.
        Returns a list of tuples: (summary, description, start_time_string).

        Only returns events whose summary starts with "טיפול" or "tipul".

        :return: List[ (summary, description, start_time) ] 
                 Where start_time is a string in "HH:MM" format
        """
        try:
            client = caldav.DAVClient(
                url=self.calendar_url,
                username=self.username,
                password=self.password
            )
            principal = client.principal()
            calendars = principal.calendars()

            tomorrow_start, tomorrow_end = self.get_tomorrow_time()
            appointments = []

            for calendar in calendars:
                events = calendar.date_search(start=tomorrow_start, end=tomorrow_end)
                if events is None:
                    continue

                for event in events:
                    # Some CalDAV servers attach the raw data under event.instance
                    # If "instance" is present, use .vevent for summary/description
                    if hasattr(event, "instance"):
                        vevent = event.instance.vevent
                        summary = getattr(vevent.summary, "value", "")
                        description = getattr(vevent.description, "value", "")
                        dtstart = vevent.dtstart.value.astimezone(self.timezone)
                    else:
                        # Fallback: some servers store summary/description top-level
                        summary = getattr(event, "summary", "") or ""
                        description = getattr(event, "description", "") or ""
                        # dtstart may not be accessible this way depending on the CalDAV server
                        dtstart = None  

                    # Build a readable time string if dtstart is available
                    start_time_str = ""
                    if dtstart:
                        start_time_str = f"{dtstart.hour}:{dtstart.minute:02d}"

                    # Filter: only if summary starts with טיפול / tipul
                    if summary.lower().startswith("טיפול") or summary.lower().startswith("tipul"):
                        appointments.append((summary, description, start_time_str))

            if not appointments:
                logger.debug("No appointments found for tomorrow.")
            return appointments

        except Exception as e:
            logger.error(f"Error retrieving appointments: {e}")
            return []

    def get_tomorrow_time(self) -> Tuple[datetime.datetime, datetime.datetime]:
        """
        Calculate tomorrow's start (00:00) and end (23:59) in the configured timezone.
        
        :return: (tomorrow_start, tomorrow_end) as localized datetime objects
        """
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        # Start of day
        tomorrow_start = self.timezone.localize(
            datetime.datetime.combine(tomorrow, datetime.time.min)
        )
        # End of day
        tomorrow_end = self.timezone.localize(
            datetime.datetime.combine(tomorrow, datetime.time.max)
        )
        return tomorrow_start, tomorrow_end

import caldav
import pytz
import datetime

class CalendarService:
    def __init__(self, config):
        # Set up calendar credentials
        self.calendar_url = config.CALENDAR_URL
        self.username = config.CALENDAR_USERNAME
        self.password = config.CALENDAR_PASSWORD
        self.timezone = pytz.timezone(config.TIMEZONE)

    def get_tomorrow_appointments(self):
        # Fetch tomorrow's appointments
        try:
            client = caldav.DAVClient(url=self.calendar_url, username=self.username, password=self.password)
            principal = client.principal()
            calendars = principal.calendars()

            tomorrow_start, tomorrow_end = self.get_tomorrow_time()
            appointments = []

            for calendar in calendars:
                events = calendar.date_search(start=tomorrow_start, end=tomorrow_end)
                for event in events:
                    if hasattr(event, 'instance'):
                        event_data = event.instance.vevent
                        summary = event_data.summary.value if hasattr(event_data, 'summary') else ''
                        description = event_data.description.value if hasattr(event_data, 'description') else ''
                        start_time = f"{event_data.dtstart.value.astimezone(self.timezone).hour}:{event_data.dtstart.value.astimezone(self.timezone).minute:02d}"
                    else:
                        summary = getattr(event, 'summary', '')
                        description = getattr(event, 'description', '')
                    if summary.lower().startswith("טיפול") or summary.lower().startswith("tipul"):
                        appointments.append((summary, description, start_time))
            return appointments
        except Exception as e:
            print(f"Error retrieving appointments: {e}")
            return []

    def get_tomorrow_time(self):
        # Calculate tomorrow's start and end time
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        tomorrow_start = self.timezone.localize(datetime.datetime.combine(tomorrow, datetime.time.min))
        tomorrow_end = self.timezone.localize(datetime.datetime.combine(tomorrow, datetime.time.max))
        return tomorrow_start, tomorrow_end
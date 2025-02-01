import pytest
import datetime
import pytz
from freezegun import freeze_time
from unittest.mock import patch, MagicMock
from app.calendar_service import CalendarService

class MockConfig:
    CALENDAR_URL = "http://fake-calendar-url.com"
    CALENDAR_USERNAME = "test_user"
    CALENDAR_PASSWORD = "test_pass"
    TIMEZONE = "Asia/Jerusalem"

@pytest.fixture
def calendar_service():
    """
    A pytest fixture creating a CalendarService with mock config.
    """
    return CalendarService(MockConfig())

@freeze_time("2025-01-01")
def test_get_tomorrow_time(calendar_service):
    """
    Test get_tomorrow_time returns correct date range for tomorrow,
    by freezing the system date to 2025-01-01.
    """
    tomorrow_start, tomorrow_end = calendar_service.get_tomorrow_time()

    # If "today" is 2025-01-01, tomorrow should be 2025-01-02
    assert tomorrow_start.year == 2025
    assert tomorrow_start.month == 1
    assert tomorrow_start.day == 2
    assert tomorrow_start.hour == 0
    assert tomorrow_start.minute == 0

    assert tomorrow_end.year == 2025
    assert tomorrow_end.month == 1
    assert tomorrow_end.day == 2
    assert tomorrow_end.hour == 23
    assert tomorrow_end.minute == 59


@patch("app.calendar_service.caldav.DAVClient")
def test_get_tomorrow_appointments_no_calendars(mock_dav_client, calendar_service):
    """
    Test when principal.calendars() returns an empty list => we get empty appointments.
    """
    mock_client = MagicMock()
    mock_principal = MagicMock()
    mock_principal.calendars.return_value = []
    mock_client.principal.return_value = mock_principal
    mock_dav_client.return_value = mock_client

    appointments = calendar_service.get_tomorrow_appointments()
    assert appointments == []


@patch("app.calendar_service.caldav.DAVClient")
def test_get_tomorrow_appointments_no_tipul(mock_dav_client, calendar_service):
    """
    If we have events, but none have summary starting with טיפול or tipul,
    we should get an empty list.
    """
    mock_client = MagicMock()
    mock_principal = MagicMock()
    mock_calendar = MagicMock()

    mock_principal.calendars.return_value = [mock_calendar]
    mock_client.principal.return_value = mock_principal
    mock_dav_client.return_value = mock_client

    # The calendar has some events, but none start with טיפל or tipul
    fake_event = MagicMock()
    fake_event.instance.vevent.summary.value = "Meeting with John"
    fake_event.instance.vevent.description.value = "Discuss project"

    tz = pytz.timezone("Asia/Jerusalem")
    fake_event.instance.vevent.dtstart.value = tz.localize(datetime.datetime(2025, 1, 2, 10, 0))

    mock_calendar.date_search.return_value = [fake_event]

    appointments = calendar_service.get_tomorrow_appointments()
    assert appointments == []


@patch("app.calendar_service.caldav.DAVClient")
def test_get_tomorrow_appointments_tipul_events(mock_dav_client, calendar_service):
    """
    If events have summary that starts with 'טיפול' or 'tipul',
    they should appear in the appointments list.
    """
    mock_client = MagicMock()
    mock_principal = MagicMock()
    mock_calendar = MagicMock()
    tz = pytz.timezone("Asia/Jerusalem")

    mock_principal.calendars.return_value = [mock_calendar]
    mock_client.principal.return_value = mock_principal
    mock_dav_client.return_value = mock_client

    fake_event_1 = MagicMock()
    fake_event_1.instance.vevent.summary.value = "טיפול John"
    fake_event_1.instance.vevent.description.value = "John's therapy session"
    # Attach tzinfo=Asia/Jerusalem so it stays at 9:30 local
    fake_event_1.instance.vevent.dtstart.value = tz.localize(datetime.datetime(2025, 1, 2, 9, 30))

    fake_event_2 = MagicMock()
    fake_event_2.instance.vevent.summary.value = "tipul Mary"
    fake_event_2.instance.vevent.description.value = "Mary's appointment"
    fake_event_2.instance.vevent.dtstart.value = tz.localize(datetime.datetime(2025, 1, 2, 14, 45))

    # Non-matching event
    fake_event_3 = MagicMock()
    fake_event_3.instance.vevent.summary.value = "Meeting with Bob"
    fake_event_3.instance.vevent.description.value = "Project discussion"
    fake_event_3.instance.vevent.dtstart.value = tz.localize(datetime.datetime(2025, 1, 2, 11, 15))

    mock_calendar.date_search.return_value = [fake_event_1, fake_event_2, fake_event_3]

    appointments = calendar_service.get_tomorrow_appointments()
    assert len(appointments) == 2  # Only the ones starting with 'טיפול' or 'tipul'

    # Check the data from the first event
    assert appointments[0] == ("טיפול John", "John's therapy session", "9:30")

    # Check the data from the second event
    assert appointments[1] == ("tipul Mary", "Mary's appointment", "14:45")


@patch("app.calendar_service.caldav.DAVClient", side_effect=Exception("Connection error"))
def test_get_tomorrow_appointments_exception(mock_dav_client, calendar_service):
    """
    If there's an exception, the method should catch it and return [].
    """
    appointments = calendar_service.get_tomorrow_appointments()
    assert appointments == []

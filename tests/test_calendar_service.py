import pytest
from app.calendar_service import CalendarService
from app.config import Config
from datetime import datetime, timedelta

@pytest.fixture
def calendar_service():
    config = Config()
    return CalendarService(config)


def test_get_tomorrow_time(calendar_service):
    # Get the start and end times for tomorrow
    start, end = calendar_service.get_tomorrow_time()

    # Calculate tomorrow's date
    today = datetime.now(calendar_service.timezone).date()
    tomorrow = today + timedelta(days=1)

    # Assert that start and end are both on tomorrow's date
    assert start.date() == tomorrow, f"Start date {start.date()} is not tomorrow's date {tomorrow}"
    assert end.date() == tomorrow, f"End date {end.date()} is not tomorrow's date {tomorrow}"

    # Assert that start is at midnight
    assert start.hour == 0 and start.minute == 0 and start.second == 0, "Start time is not midnight"

    # Normalize end time to remove microseconds
    end = end.replace(microsecond=0)

    # Assert that end is at the last second of the day
    assert end.hour == 23 and end.minute == 59 and end.second == 59, "End time is not the last second of the day"


def test_get_tomorrow_appointments_without_events(calendar_service, mocker):
    # Mock the caldav.DAVClient used in calendar_service
    mock_client = mocker.patch('app.calendar_service.caldav.DAVClient')
    
    # Mock the behavior of the client's methods
    mock_client_instance = mock_client.return_value
    mock_principal = mock_client_instance.principal.return_value
    mock_principal.calendars.return_value = []
    
    appointments = calendar_service.get_tomorrow_appointments()
    
    # Assert the expected outcome
    assert appointments == []
    mock_client.assert_called_once()

def test_get_tomorrow_appointments_with_events(calendar_service, mocker):
    # Mock the caldav.DAVClient used in calendar_service
    mock_client = mocker.patch('app.calendar_service.caldav.DAVClient')
    
    # Mock the behavior of the client's methods
    mock_client_instance = mock_client.return_value
    mock_principal = mock_client_instance.principal.return_value
    mock_calendar = mocker.Mock()  # Mock a calendar object
    
    # Mock events returned by the calendar's date_search method
    mock_event = mocker.Mock()
    mock_event.instance.vevent.summary.value = "טיפול יוסי"
    mock_event.instance.vevent.description.value = "+972501234567"
    mock_event.instance.vevent.dtstart.value = datetime(2024, 12, 27, 15, 0, 0, tzinfo=calendar_service.timezone)

    mock_calendar.date_search.return_value = [mock_event]
    mock_principal.calendars.return_value = [mock_calendar]
    
    # Call the method
    appointments = calendar_service.get_tomorrow_appointments()

    # Assert the expected outcome
    assert len(appointments) == 1
    assert appointments[0] == (
        "טיפול יוסי",
        "+972501234567",
        "15:00",
    )

    mock_client.assert_called_once()

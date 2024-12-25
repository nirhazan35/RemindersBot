import pytest
from app.reminder_bot import ReminderBot

@pytest.fixture
def reminder_bot(mocker):
    calendar_service = mocker.Mock()
    messaging_service = mocker.Mock()
    confirmation_manager = mocker.Mock()
    return ReminderBot(calendar_service, messaging_service, confirmation_manager)

@pytest.mark.asyncio
async def test_run_daily_check_no_appointments(reminder_bot):
    reminder_bot.calendar_service.get_tomorrow_appointments.return_value = []
    await reminder_bot.run_daily_check()
    reminder_bot.messaging_service.send_no_appointments_message.assert_called_once()

@pytest.mark.asyncio
async def test_run_daily_check_with_appointments(reminder_bot):
    reminder_bot.calendar_service.get_tomorrow_appointments.return_value = [
        ("John Appointment", "desc +972501234567", "15:00")
    ]
    await reminder_bot.run_daily_check()
    reminder_bot.messaging_service.send_confirmation_request.assert_called_once()

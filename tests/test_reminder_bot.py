import pytest
from unittest.mock import AsyncMock, MagicMock
from app.reminder_bot import ReminderBot

@pytest.mark.asyncio
async def test_run_daily_check_no_appointments():
    """
    If get_tomorrow_appointments returns [], 
    the bot should call messaging_service.send_no_appointments_message() 
    and do nothing else.
    """
    mock_calendar_service = MagicMock()
    mock_calendar_service.get_tomorrow_appointments.return_value = []

    mock_messaging_service = MagicMock()
    mock_confirmation_manager = AsyncMock()

    bot = ReminderBot(
        calendar_service=mock_calendar_service,
        messaging_service=mock_messaging_service,
        confirmation_manager=mock_confirmation_manager
    )

    await bot.run_daily_check()

    # Ensure the "no appointments" message was sent
    mock_messaging_service.send_no_appointments_message.assert_called_once()

    # And that we didn't add any confirmations or send confirmation requests
    mock_confirmation_manager.add_confirmation.assert_not_awaited()
    mock_messaging_service.send_confirmation_request.assert_not_called()


@pytest.mark.asyncio
async def test_run_daily_check_with_appointments():
    """
    If get_tomorrow_appointments returns a list,
    we add each to confirmation_manager and call send_confirmation_request 
    for each appointment.
    """
    mock_calendar_service = MagicMock()
    mock_calendar_service.get_tomorrow_appointments.return_value = [
        ("טיפול Nir", "Patient Nir phone 0501234567", "10:00"),
        ("טיפול John", "Patient John phone +972501234567", "11:00")
    ]

    mock_messaging_service = MagicMock()
    mock_messaging_service.reminder_body = "Reminder text"  # Not actually used now
    mock_confirmation_manager = AsyncMock()

    bot = ReminderBot(
        calendar_service=mock_calendar_service,
        messaging_service=mock_messaging_service,
        confirmation_manager=mock_confirmation_manager
    )

    await bot.run_daily_check()

    # Should not send the "no appointments" message
    mock_messaging_service.send_no_appointments_message.assert_not_called()

    # We have 2 appointments, so we should do "add_confirmation" twice, each with the right key
    assert mock_confirmation_manager.add_confirmation.await_count == 2

    # 1st call: phone 972501234567 + start_time 10:00 => key '972501234567$10:00'
    first_call = mock_confirmation_manager.add_confirmation.await_args_list[0]
    assert first_call[0][0] == "972501234567$10:00"  # the key
    assert first_call[0][1]["customer_name"] == "Nir"
    assert first_call[0][1]["customer_number"] == "972501234567"
    assert first_call[0][1]["start_time"] == "10:00"

    # 2nd call: phone +972501234567 => no need to reformat if it starts with +9725
    second_call = mock_confirmation_manager.add_confirmation.await_args_list[1]
    assert second_call[0][0] == "+972501234567$11:00"
    assert second_call[0][1]["customer_name"] == "John"
    assert second_call[0][1]["customer_number"] == "+972501234567"
    assert second_call[0][1]["start_time"] == "11:00"

    # Confirm we called send_confirmation_request twice
    assert mock_messaging_service.send_confirmation_request.call_count == 2

    # Check the arguments passed to send_confirmation_request
    # The bot calls: messaging_service.send_confirmation_request(start_time, customer_name)
    first_req_call_args = mock_messaging_service.send_confirmation_request.call_args_list[0][0]
    assert first_req_call_args == ("10:00", "Nir")

    second_req_call_args = mock_messaging_service.send_confirmation_request.call_args_list[1][0]
    assert second_req_call_args == ("11:00", "John")


def test_extract_phone_number_no_match():
    """
    If no phone is present, extract_phone_number returns None.
    """
    description = "Some event without a phone number"
    result = ReminderBot.extract_phone_number(description)
    assert result is None


def test_extract_phone_number_05_format():
    """
    If phone is 0501234567, it should become 972501234567.
    """
    description = "Patient phone 0501234567"
    result = ReminderBot.extract_phone_number(description)
    assert result == "972501234567"


def test_extract_phone_number_plus_972():
    """
    If phone is already in +9725... form, we keep it as is.
    """
    description = "Patient phone +972501234567"
    result = ReminderBot.extract_phone_number(description)
    assert result == "+972501234567"


def test_extract_customer_name_simple():
    """
    If summary has multiple words, use the second word as the name.
    """
    bot = ReminderBot(None, None, None)
    name = bot._extract_customer_name("טיפול Nir Oren")
    assert name == "Nir"


def test_extract_customer_name_not_enough_parts():
    """
    If the summary doesn't have a second token, return 'Unknown'.
    """
    bot = ReminderBot(None, None, None)
    name = bot._extract_customer_name("טיפול")
    assert name == "Unknown"

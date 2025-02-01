import pytest
from unittest.mock import patch, MagicMock
from app.whatsapp_messaging_service import WhatsappMessagingService

class MockConfig:
    ACCESS_TOKEN = "test_access_token"
    PHONE_NUMBER_ID = "test_phone_id"
    MY_PHONE_NUMBER = "test_user_number"
    API_VERSION = "v14.0"
    REMINDER_BODY = "Reminder! Your appointment is at {start_time}."

@pytest.fixture
def whatsapp_service():
    """
    A pytest fixture providing a WhatsappMessagingService instance with mock config.
    """
    return WhatsappMessagingService(MockConfig())

@patch("app.whatsapp_messaging_service.requests.post")
def test_send_confirmation_request(mock_post, whatsapp_service):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    whatsapp_service.send_confirmation_request("10:00", "John Doe")

    mock_post.assert_called_once()
    url = f"https://graph.facebook.com/{MockConfig.API_VERSION}/{MockConfig.PHONE_NUMBER_ID}/messages"
    args, kwargs = mock_post.call_args

    assert args[0] == url
    headers = kwargs["headers"]
    assert headers["Authorization"] == f"Bearer {MockConfig.ACCESS_TOKEN}"
    assert headers["Content-Type"] == "application/json"

    # Check the JSON payload
    json_data = kwargs["json"]
    assert json_data["messaging_product"] == "whatsapp"
    assert json_data["to"] == MockConfig.MY_PHONE_NUMBER
    assert json_data["type"] == "interactive"

@patch("app.whatsapp_messaging_service.requests.post")
def test_send_customer_whatsapp_reminder(mock_post, whatsapp_service):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    whatsapp_service.send_customer_whatsapp_reminder("972501234567", "15:00")

    mock_post.assert_called_once()
    url = f"https://graph.facebook.com/{MockConfig.API_VERSION}/{MockConfig.PHONE_NUMBER_ID}/messages"
    args, kwargs = mock_post.call_args

    assert args[0] == url
    json_data = kwargs["json"]
    assert json_data["to"] == "972501234567"
    assert json_data["type"] == "text"
    assert json_data["text"]["body"] == "Reminder! Your appointment is at 15:00."

@patch("app.whatsapp_messaging_service.requests.post")
def test_send_acknowledgement_yes(mock_post, whatsapp_service):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    whatsapp_service.send_acknowledgement("John Doe", "10:00", "yes_confirmation")

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    json_data = kwargs["json"]
    assert "✅ נשלחה תזכורת" in json_data["text"]["body"]

@patch("app.whatsapp_messaging_service.requests.post")
def test_send_acknowledgement_no(mock_post, whatsapp_service):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    whatsapp_service.send_acknowledgement("John Doe", "10:00", "no_confirmation")

    mock_post.assert_called_once()
    json_data = mock_post.call_args[1]["json"]
    assert "❌ לא נשלחה תזכורת" in json_data["text"]["body"]

@patch("app.whatsapp_messaging_service.requests.post")
def test_send_no_appointments_message(mock_post, whatsapp_service):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    whatsapp_service.send_no_appointments_message()

    mock_post.assert_called_once()
    json_data = mock_post.call_args[1]["json"]
    assert "לא נמצאו טיפולים למחר." in json_data["text"]["body"]

@patch("app.whatsapp_messaging_service.requests.post")
def test_test_method(mock_post, whatsapp_service):
    """
    Tests the .test() method, which sends a hard-coded message to a phone number.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    whatsapp_service.test()

    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["json"]["to"] == "972527332808"
    assert kwargs["json"]["text"]["body"] == "This is a test message."

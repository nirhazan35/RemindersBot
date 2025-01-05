# import pytest
# from app.messaging_service import MessagingService
# from app.config import Config

# @pytest.fixture
# def messaging_service():
#     config = Config()
#     return MessagingService(config)

# def test_send_confirmation_request(messaging_service, mocker):
#     mock_post = mocker.patch('requests.post')
#     mock_post.return_value.status_code = 200

#     messaging_service.send_confirmation_request("15:00", "John Doe")
#     mock_post.assert_called_once()

# def test_send_no_appointments_message(messaging_service, mocker):
#     mock_post = mocker.patch('requests.post')
#     mock_post.return_value.status_code = 200

#     messaging_service.send_no_appointments_message()
#     mock_post.assert_called_once()

import pytest
from app.messaging_service import MessagingService
from app.config import Config

@pytest.fixture
def messaging_service():
    config = Config()
    return MessagingService(config)

def test_send_confirmation_request_success(messaging_service, mocker):
    # Mock requests.post
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 200  # Simulate success

    messaging_service.send_confirmation_request("15:00", "John Doe")

    # Asserts that requests.post was called
    mock_post.assert_called_once()

def test_send_confirmation_request_failure(messaging_service, mocker):
    # Mock requests.post
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 500  # Simulate failure

    messaging_service.send_confirmation_request("15:00", "John Doe")

    # Asserts that requests.post was called
    mock_post.assert_called_once()

def test_send_no_appointments_message(messaging_service, mocker):
    # Mock requests.post
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 200

    # Call the function
    messaging_service.send_no_appointments_message()

    # Assert that the request was made
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "לא נמצאו טיפולים למחר." in kwargs["json"]["text"]["body"]

# def test_send_customer_whatsapp_reminder(messaging_service, mocker):
#     # Mock requests.post
#     mock_post = mocker.patch('requests.post')
#     mock_post.return_value.status_code = 200

#     # Call the function
#     messaging_service.send_customer_whatsapp_reminder("972501234567", "15:00")

#     # Assert that the request was made
#     mock_post.assert_called_once()
#     args, kwargs = mock_post.call_args
#     assert kwargs["json"]["to"] == "972501234567"
#     assert "15:00" in kwargs["json"]["text"]["body"]

def test_send_acknowledgement_yes(messaging_service, mocker):
    # Mock requests.post
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 200

    # Call the function with "yes_confirmation"
    messaging_service.send_acknowledgement("John Doe", "15:00", "yes_confirmation")

    # Assert that the request was made
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "✅ נשלחה תזכורת לJohn Doe לטיפול שיתקיים בשעה 15:00." in kwargs["json"]["text"]["body"]

def test_send_acknowledgement_no(messaging_service, mocker):
    # Mock requests.post
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 200

    # Call the function with "no_confirmation"
    messaging_service.send_acknowledgement("John Doe", "15:00", "no_confirmation")

    # Assert that the request was made
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "❌ לא נשלחה תזכורת לJohn Doe לטיפול שיתקיים בשעה 15:00." in kwargs["json"]["text"]["body"]


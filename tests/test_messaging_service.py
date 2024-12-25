import pytest
from app.messaging_service import MessagingService
from app.config import Config

@pytest.fixture
def messaging_service():
    config = Config()
    return MessagingService(config)

def test_send_confirmation_request(messaging_service, mocker):
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 200

    messaging_service.send_confirmation_request("15:00", "John Doe")
    mock_post.assert_called_once()

def test_send_no_appointments_message(messaging_service, mocker):
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 200

    messaging_service.send_no_appointments_message()
    mock_post.assert_called_once()

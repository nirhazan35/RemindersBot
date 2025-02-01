from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
from app.main import app
from app.routers.webhook import router as webhook_router  # Import the specific router

client = TestClient(app)

def test_verify_webhook_success():
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "test_token",
        "hub.challenge": "CHALLENGE_CODE"
    }
    mock_config = MagicMock()
    mock_config.VERIFY_TOKEN = "test_token"
    
    # Patch the specific router's services
    with patch.object(webhook_router, 'services', {"config": mock_config}):
        response = client.get("/webhook", params=params)
        assert response.status_code == 200
        assert response.text == "CHALLENGE_CODE"

def test_verify_webhook_failure():
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong_token",
        "hub.challenge": "CHALLENGE_CODE"
    }
    mock_config = MagicMock()
    mock_config.VERIFY_TOKEN = "correct_token"
    
    with patch.object(webhook_router, 'services', {"config": mock_config}):
        response = client.get("/webhook", params=params)
        assert response.status_code == 403
        assert response.json()["status"] == "error"

def test_handle_webhook_no_action_taken():
    data = {"entry": [{"changes": [{"value": {"messages": []}}]}]}
    response = client.post("/webhook", json=data)
    assert response.status_code == 200
    assert response.json() == {"status": "No action taken"}

def test_handle_webhook_yes_confirmation():
    """
    Test that when a webhook message has a "yes_confirmation" button response,
    the system sends the WhatsApp reminder and acknowledgement correctly.
    """
    data = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "12345",
                        "interactive": {
                            "button_reply": {
                                "id": "yes_confirmation$2025-02-01T10:00:00"
                            }
                        }
                    }]
                }
            }]
        }]
    }

    # Create mock services for confirmation_manager and messaging_service
    mock_confirmation_manager = AsyncMock()
    # Simulate that we DO have a stored confirmation
    mock_confirmation_manager.has_confirmation.return_value = True
    mock_confirmation_manager.get_confirmation.return_value = {
        "customer_number": "12345",
        "start_time": "2025-02-01T10:00:00",
        "customer_name": "John Doe"
    }

    mock_messaging_service = MagicMock()

    # Combine them in a dict the same way your code expects them
    mock_services = {
        "config": MagicMock(),
        "confirmation_manager": mock_confirmation_manager,
        "messaging_service": mock_messaging_service
    }

    # Patch the router's services so the endpoint uses our mocks
    with patch.object(webhook_router, 'services', mock_services):
        response = client.post("/webhook", json=data)

    # Assert correct response
    assert response.status_code == 200
    assert response.json() == {"status": "Reminder sent"}

    # Verify confirmation_manager calls
    mock_confirmation_manager.has_confirmation.assert_awaited_once_with("12345$2025-02-01T10:00:00")
    mock_confirmation_manager.get_confirmation.assert_awaited_once_with("12345$2025-02-01T10:00:00")

    # Verify messaging_service calls
    mock_messaging_service.send_customer_whatsapp_reminder.assert_called_once_with(
        "12345",  # from the stored confirmation
        "2025-02-01T10:00:00"
    )
    mock_messaging_service.send_acknowledgement.assert_called_once_with(
        "John Doe",                # reminder["customer_name"]
        "2025-02-01T10:00:00", 
        "yes_confirmation"
    )

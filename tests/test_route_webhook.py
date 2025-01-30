# tests/test_webhook.py

import json
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
from app.main import app

client = TestClient(app)

def test_verify_webhook_success():
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "test_token",
        "hub.challenge": "CHALLENGE_CODE"
    }
    mock_config = MagicMock()
    mock_config.VERIFY_TOKEN = "test_token"
    
    with patch.object(app.routes[-1], 'services', {'config': mock_config}):
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
    
    with patch.object(app.routes[-1], 'services', {'config': mock_config}):
        response = client.get("/webhook", params=params)
        assert response.status_code == 403
        assert response.json()["status"] == "error"

def test_handle_webhook_no_action_taken():
    data = {"entry": [{"changes": [{"value": {"messages": []}}]}]}
    response = client.post("/webhook", json=data)
    assert response.status_code == 200
    assert response.json() == {"status": "No action taken"}

def test_handle_webhook_yes_confirmation():
    data = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "12345",
                        "interactive": {
                            "button_reply": {"id": "yes_confirmation$2025-02-01T10:00:00"}
                        }
                    }]
                }
            }]
        }]
    }
    
    mock_services = {
        "config": MagicMock(),
        "confirmation_manager": AsyncMock(),
        "messaging_service": MagicMock()
    }
    mock_services["confirmation_manager"].has_confirmation.return_value = True
    mock_services["confirmation_manager"].get_confirmation.return_value = {
        "customer_number": "5551234",
        "start_time": "2025-02-01T10:00:00",
        "customer_name": "John Doe"
    }
    
    with patch.object(app.routes[-1], 'services', mock_services):
        response = client.post("/webhook", json=data)
        assert response.status_code == 200
        assert response.json()["status"] == "Reminder sent"

def test_handle_webhook_decline_confirmation():
    data = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "12345",
                        "interactive": {
                            "button_reply": {"id": "no_confirmation$2025-02-01T10:00:00"}
                        }
                    }]
                }
            }]
        }]
    }
    
    mock_services = {
        "config": MagicMock(),
        "confirmation_manager": AsyncMock(),
        "messaging_service": MagicMock()
    }
    mock_services["confirmation_manager"].has_confirmation.return_value = True
    mock_services["confirmation_manager"].get_confirmation.return_value = {
        "customer_number": "5551234",
        "start_time": "2025-02-01T10:00:00",
        "customer_name": "John Doe"
    }
    
    with patch.object(app.routes[-1], 'services', mock_services):
        response = client.post("/webhook", json=data)
        assert response.status_code == 200
        assert response.json()["status"] == "Confirmation declined"
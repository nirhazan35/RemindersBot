# tests/test_webhook.py

import json
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
    mock_
# tests/test_run_check.py

from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from app.main import app

client = TestClient(app)

def test_run_check_success():
    with patch("app.routers.run_check.router.services") as mock_services:
        mock_bot = MagicMock()
        # Make sure run_daily_check is async so we can await it without error
        mock_bot.run_daily_check = AsyncMock(return_value=None)

        # Return the mock_bot when the code asks for "bot"
        mock_services.__getitem__.side_effect = lambda key: mock_bot if key == "bot" else None

        response = client.post("/run-check")
        assert response.status_code == 200
        assert response.json()["status"] == "Check completed successfully"
        # verify we awaited run_daily_check
        mock_bot.run_daily_check.assert_awaited_once()

def test_run_check_exception():
    with patch("app.routers.run_check.router.services") as mock_services:
        mock_bot = MagicMock()
        # Force run_daily_check to raise an exception
        async def raise_exception():
            raise ValueError("Some error")

        mock_bot.run_daily_check.side_effect = raise_exception
        mock_services.__getitem__.side_effect = lambda key: mock_bot if key == "bot" else None

        response = client.post("/run-check")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Some error" in data["message"]

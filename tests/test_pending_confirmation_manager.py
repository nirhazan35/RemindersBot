import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from app.pending_confirmation_manager import PendingConfirmationManager

@pytest.mark.asyncio
async def test_add_confirmation():
    """
    Verify that add_confirmation calls update_one with expected arguments.
    """
    # Mock the database and collection
    mock_db = MagicMock()
    mock_collection = AsyncMock()
    mock_db.pending_confirmations = mock_collection

    manager = PendingConfirmationManager(mock_db)

    key = "12345$2025-02-01T10:00:00"
    data = {
        "customer_name": "John Doe",
        "customer_number": "555-1234",
        "start_time": "2025-02-01T10:00:00",
    }

    # Execute
    await manager.add_confirmation(key, data)

    # Validate the call
    mock_collection.update_one.assert_awaited_once()
    args, kwargs = mock_collection.update_one.await_args

    # Check the filter
    assert args[0] == {"key": key}

    # Check the $set operation
    set_operation = args[1]["$set"]
    assert set_operation["customer_name"] == "John Doe"
    assert set_operation["customer_number"] == "555-1234"
    assert set_operation["appointment_time"] == "2025-02-01T10:00:00"
    assert "created_at" in set_operation  # We won't compare exact times

    # Check upsert=True
    assert kwargs["upsert"] is True

@pytest.mark.asyncio
async def test_get_confirmation_found():
    """
    If a confirmation document is found, ensure it's returned and the document is deleted.
    """
    mock_db = MagicMock()
    mock_collection = AsyncMock()
    mock_db.pending_confirmations = mock_collection

    manager = PendingConfirmationManager(mock_db)
    key = "some_unique_key"

    # Simulate a found doc
    mock_collection.find_one.return_value = {
        "key": key,
        "customer_name": "John Doe",
        "customer_number": "555-1234",
        "appointment_time": "2025-02-01T10:00:00"
    }

    result = await manager.get_confirmation(key)

    # Ensure find_one and delete_one were called
    mock_collection.find_one.assert_awaited_once_with({"key": key})
    mock_collection.delete_one.assert_awaited_once_with({"key": key})

    # Check the returned dictionary
    assert result == {
        "customer_name": "John Doe",
        "customer_number": "555-1234",
        "start_time": "2025-02-01T10:00:00"
    }

@pytest.mark.asyncio
async def test_get_confirmation_not_found():
    """
    If no document is found, we should return None and not call delete_one.
    """
    mock_db = MagicMock()
    mock_collection = AsyncMock()
    mock_db.pending_confirmations = mock_collection
    mock_collection.find_one.return_value = None

    manager = PendingConfirmationManager(mock_db)
    key = "non_existent_key"

    result = await manager.get_confirmation(key)

    mock_collection.find_one.assert_awaited_once_with({"key": key})
    mock_collection.delete_one.assert_not_awaited()
    assert result is None

@pytest.mark.asyncio
async def test_has_confirmation_true():
    """
    has_confirmation should return True when a document is found.
    """
    mock_db = MagicMock()
    mock_collection = AsyncMock()
    mock_db.pending_confirmations = mock_collection

    # Simulate a document being returned
    mock_collection.find_one.return_value = {"key": "some_key"}

    manager = PendingConfirmationManager(mock_db)
    exists = await manager.has_confirmation("some_key")

    mock_collection.find_one.assert_awaited_once_with({"key": "some_key"})
    assert exists is True

@pytest.mark.asyncio
async def test_has_confirmation_false():
    """
    has_confirmation should return False when no document is found.
    """
    mock_db = MagicMock()
    mock_collection = AsyncMock()
    mock_db.pending_confirmations = mock_collection

    # Simulate no document found
    mock_collection.find_one.return_value = None

    manager = PendingConfirmationManager(mock_db)
    exists = await manager.has_confirmation("some_key")

    mock_collection.find_one.assert_awaited_once_with({"key": "some_key"})
    assert exists is False

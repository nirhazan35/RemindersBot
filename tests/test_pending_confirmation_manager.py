# import pytest
# from app.pending_confirmation_manager import PendingConfirmationManager

# @pytest.fixture
# def mock_db(mocker):
#     return mocker.Mock()

# @pytest.fixture
# def manager(mock_db):
#     return PendingConfirmationManager(mock_db)

# @pytest.mark.asyncio
# async def test_add_confirmation(manager):
#     await manager.add_confirmation("key", {"customer_name": "John", "customer_number": "123456", "start_time": "15:00"})
#     manager.collection.update_one.assert_called_once()

# @pytest.mark.asyncio
# async def test_get_confirmation(manager):
#     manager.collection.find_one.return_value = {"key": "key", "customer_name": "John", "start_time": "15:00"}
#     confirmation = await manager.get_confirmation("key")
#     assert confirmation["customer_name"] == "John"

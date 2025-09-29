"""
PendingConfirmationManager manages pending confirmations in a MongoDB collection.
Handles CRUD operations for appointment confirmation requests.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class PendingConfirmationManager:
    """
    Manages pending confirmations in a MongoDB collection.
    """

    def __init__(self, db):
        """
        :param db: The database client or database object (e.g., `db = client.get_default_database()`)
        """
        # The collection is assumed to exist on `db` named `pending_confirmations`.
        self.collection = db.pending_confirmations

    async def add_confirmation(self, key: str, data: Dict[str, Any]) -> None:
        """
        Adds or updates a confirmation document in the database.

        :param key: A unique string identifying this confirmation, e.g. '9725XXXXXXX$2025-02-01T10:00:00'.
        :param data: A dictionary containing:
          - "customer_name"
          - "customer_number"
          - "start_time"
        """
        try:
            result = await self.collection.update_one(
                {"key": key},
                {
                    "$set": {
                        "customer_name": data["customer_name"],
                        "customer_number": data["customer_number"],
                        "appointment_time": data["start_time"],
                        "created_at": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            
            action = "updated" if result.matched_count > 0 else "created"
            logger.info(f"Confirmation {action} for key: {key}")
            
        except Exception as e:
            logger.error(f"Error adding confirmation for key {key}: {str(e)}")
            raise

    async def get_confirmation(self, key: str) -> Optional[Dict[str, str]]:
        """
        Retrieves and deletes a confirmation by key.

        :param key: The unique string identifier for the confirmation.
        :return: A dictionary with "customer_name", "customer_number", "start_time",
                 or None if no document was found.
        """
        try:
            confirmation = await self.collection.find_one({"key": key})
            if confirmation:
                await self.collection.delete_one({"key": key})
                logger.info(f"Retrieved and deleted confirmation for key: {key}")
                return {
                    "customer_name": confirmation["customer_name"],
                    "customer_number": confirmation["customer_number"],
                    "start_time": confirmation["appointment_time"],
                }
            else:
                logger.warning(f"No confirmation found for key: {key}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving confirmation for key {key}: {str(e)}")
            raise

    async def has_confirmation(self, key: str) -> bool:
        """
        Checks if a confirmation document exists for the given key.

        :param key: The unique string identifier.
        :return: True if a confirmation is found, otherwise False.
        """
        doc = await self.collection.find_one({"key": key})
        return doc is not None

    async def list_keys_for_sender(self, sender_number: str) -> list[str]:
        """
        Lists all pending confirmation keys for a specific sender number.

        :param sender_number: The phone number of the sender.
        :return: List of keys matching the sender.
        """
        try:
            # Keys are in format: "<sender_number>$<appointment_time>"
            pattern = f"^{sender_number}\\$"
            cursor = self.collection.find({"key": {"$regex": pattern}})
            
            keys = []
            async for doc in cursor:
                keys.append(doc["key"])
                
            logger.debug(f"Found {len(keys)} pending confirmations for sender {sender_number}")
            return keys
            
        except Exception as e:
            logger.error(f"Error listing keys for sender {sender_number}: {str(e)}")
            raise

    async def delete_confirmation(self, key: str) -> bool:
        """
        Deletes a confirmation document by key.

        :param key: The unique string identifier for the confirmation.
        :return: True if a document was deleted, False if not found.
        """
        try:
            result = await self.collection.delete_one({"key": key})
            success = result.deleted_count > 0
            
            if success:
                logger.info(f"Deleted confirmation for key: {key}")
            else:
                logger.warning(f"No confirmation found to delete for key: {key}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error deleting confirmation for key {key}: {str(e)}")
            raise

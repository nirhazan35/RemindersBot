from datetime import datetime, timezone
from typing import Optional, Dict, Any

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

        :param key: A unique string identifying this confirmation, e.g. '12345$2025-02-01T10:00:00'.
        :param data: A dictionary containing:
          - "customer_name"
          - "customer_number"
          - "start_time"
        """
        await self.collection.update_one(
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

    async def get_confirmation(self, key: str) -> Optional[Dict[str, str]]:
        """
        Retrieves and deletes a confirmation by key.

        :param key: The unique string identifier for the confirmation.
        :return: A dictionary with "customer_name", "customer_number", "start_time",
                 or None if no document was found.
        """
        confirmation = await self.collection.find_one({"key": key})
        if confirmation:
            await self.collection.delete_one({"key": key})
            return {
                "customer_name": confirmation["customer_name"],
                "customer_number": confirmation["customer_number"],
                "start_time": confirmation["appointment_time"],
            }
        return None

    async def has_confirmation(self, key: str) -> bool:
        """
        Checks if a confirmation document exists for the given key.

        :param key: The unique string identifier.
        :return: True if a confirmation is found, otherwise False.
        """
        doc = await self.collection.find_one({"key": key})
        return doc is not None

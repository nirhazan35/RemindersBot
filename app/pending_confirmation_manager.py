from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

class PendingConfirmationManager:
    def __init__(self, db):
        # Set up database collection
        self.collection = db.pending_confirmations

    async def add_confirmation(self, key, data):
        # Add or update a confirmation in MongoDB
        await self.collection.update_one(
            {"key": key}, 
            {"$set": {"customer_name": data["customer_name"], "customer_number": data["customer_number"], "appointment_time": data["start_time"], "created_at": datetime.utcnow()}}, 
            upsert=True
        )

    async def get_confirmation(self, key):
        # Retrieve and delete a confirmation
        confirmation = await self.collection.find_one({"key": key})
        if confirmation:
            await self.collection.delete_one({"key": key})
            return {"customer_name": confirmation["customer_name"], "customer_number": confirmation["customer_number"], "start_time": confirmation["appointment_time"]}
        return None

    async def has_confirmation(self, key):
        # Check if a confirmation exists
        return await self.collection.find_one({"key": key}) is not None

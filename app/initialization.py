from motor.motor_asyncio import AsyncIOMotorClient
from app import config
from app.calendar_service import CalendarService
from app.whatsapp_messaging_service import WhatsappMessagingService
from app.pending_confirmation_manager import PendingConfirmationManager
from app.reminder_bot import ReminderBot

def initialize_services():
    """
    Initializes and returns all the services (config, db client, custom services, etc.).
    """
    mongo_uri = getattr(config, "MONGO_URI", None)
    if not mongo_uri:
        raise RuntimeError("MONGO_URI is not set")

    client = AsyncIOMotorClient(mongo_uri)
    db = client.get_default_database()

    calendar_service = CalendarService(config)
    messaging_service = WhatsappMessagingService(config)
    confirmation_manager = PendingConfirmationManager(db)
    bot = ReminderBot(calendar_service, messaging_service, confirmation_manager)

    return {
        "config": config,
        "db": db,
        "calendar_service": calendar_service,
        "messaging_service": messaging_service,
        "confirmation_manager": confirmation_manager,
        "bot": bot,
    }
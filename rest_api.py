from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
from apscheduler.schedulers.background import BackgroundScheduler
from calendar_service import CalendarService
from messaging_service import MessagingService
from pending_confirmation_manager import PendingConfirmationManager
from reminder_bot import ReminderBot

app = FastAPI()

# Initialize services, DB manager and bot
config = Config()
client = AsyncIOMotorClient(config.MONGO_URI)
db = client.get_default_database()
calendar_service = CalendarService(config)
messaging_service = MessagingService(config)
confirmation_manager = PendingConfirmationManager(db)
bot = ReminderBot(calendar_service, messaging_service, confirmation_manager)

# Initialize and start the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(bot.run_daily_check, "cron", hour=20)  # Runs daily at 20:00
scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

@app.get("/webhook")
async def verify_webhook(hub_mode: str, hub_verify_token: str, hub_challenge: int):
    # Verify webhook URL
    if hub_mode == "subscribe" and hub_verify_token == config.VERIFY_TOKEN:
        return int(hub_challenge)
    return {"status": "Verification failed"}, 403

@app.post("/webhook")
async def handle_webhook(request: Request):
    # Handle WhatsApp webhook events
    try:
        data = await request.json()
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            message = messages[0]
            from_number = message.get("from")
            button_reply = message.get("interactive", {}).get("button_reply", {})

            if button_reply:
                reply_id = button_reply.get("id", "")
                action, appointment_time = reply_id.split("$")
                key = f"{from_number}${appointment_time}"

                if await confirmation_manager.has_confirmation(key):
                    reminder = await confirmation_manager.get_confirmation(key)
                    if action == "yes_confirmation":
                        print("customer name:", reminder['customer_name'])
                        messaging_service.send_customer_whatsapp_reminder(reminder['customer_number'], reminder['start_time'])
                        messaging_service.send_acknowledgement(reminder['customer_name'], appointment_time, action)
                        return {"status": "Reminder sent"}
                    else:
                        messaging_service.send_acknowledgement(reminder['customer_name'], appointment_time, action)
                        return {"status": "Confirmation declined"}

        return {"status": "No action taken"}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.post("/run-check")
async def run_check():
    # Run daily check on demand
    try:
        await bot.run_daily_check()
        return {"status": "Check completed successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

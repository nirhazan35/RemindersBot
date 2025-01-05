from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import Config
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.responses import PlainTextResponse
from app.calendar_service import CalendarService
from app.messaging_service import MessagingService
from app.pending_confirmation_manager import PendingConfirmationManager
from app.reminder_bot import ReminderBot

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
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == config.VERIFY_TOKEN:
        return PlainTextResponse(content=challenge) 
    else:
        return {"status": "error", "message": "Invalid token or mode"}, 403


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

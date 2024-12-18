from fastapi import FastAPI, Request
from config import Config
from calendar_service import CalendarService
from messaging_service import MessagingService
from pending_confirmation_manager import PendingConfirmationManager
from reminder_bot import ReminderBot

app = FastAPI()

config = Config()
calendar_service = CalendarService(config)
messaging_service = MessagingService(config)
confirmation_manager = PendingConfirmationManager()
bot = ReminderBot(calendar_service, messaging_service, confirmation_manager)

@app.get("/webhook")
async def verify_webhook(hub_mode: str, hub_verify_token: str, hub_challenge: int):
    if hub_mode == "subscribe" and hub_verify_token == config.VERIFY_TOKEN:
        return int(hub_challenge)
    return {"status": "Verification failed"}, 403

@app.post("/webhook")
async def handle_webhook(request: Request):
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

                if confirmation_manager.has_confirmation(key):
                    reminder = confirmation_manager.get_confirmation(key)
                    if action == "yes_confirmation":
                        messaging_service.send_customer_whatsapp_reminder(reminder['customer_number'], reminder['start_time'])
                        messaging_service.send_acknowledgement(from_number, appointment_time, action)
                        return {"status": "Reminder sent"}
                    else:
                        messaging_service.send_acknowledgement(from_number, appointment_time, action)
                        return {"status": "Confirmation declined"}

        return {"status": "No action taken"}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.post("/run-check")
async def run_check():
    try:
        bot.run_daily_check()
        return {"status": "Check completed successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

from fastapi import FastAPI, Request
from reminder_bot import CalendarReminderBot
from collections import defaultdict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# Shared pending confirmation dictionary
pending_confirmations = defaultdict(dict)
bot = CalendarReminderBot(pending_confirmations)
bot.run_daily_check()


@app.get("/webhook")
async def verify_webhook(hub_mode: str, hub_verify_token: str, hub_challenge: int):
    """Verify the webhook URL."""
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return {"status": "Verification failed"}, 403

def verify_number(number):
    for n in bot.pending_confirmations:
        if number == n.split('$')[0]:
            return True
    return False

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Process interactive replies from WhatsApp."""
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

            if button_reply and verify_number(from_number):
                reminder = bot.pending_confirmations.pop(from_number+'$'+button_reply["id"].split('$')[1])
                if button_reply["id"].split('$')[0] == "yes_confirmation":
                    bot.send_whatsapp_reminder(reminder['customer_number'], reminder['start_time'])
                    print("Reminder sent.")
                else:
                    print("Confirmation declined.")
            else:
                print("No pending confirmation for this number or no button reply received.")

        return {"status": "received"}

    except Exception as e:
        print(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}


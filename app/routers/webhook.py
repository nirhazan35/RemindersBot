from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
from typing import Dict, Any

router = APIRouter()

@router.get("/webhook")
async def verify_webhook(request: Request):
    config = router.services["config"]
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == config.VERIFY_TOKEN:
        return PlainTextResponse(content=challenge)
    else:
        return {"status": "error", "message": "Invalid token or mode"}, 403

@router.post("/webhook")
async def handle_webhook(request: Request):
    """
    Handle WhatsApp webhook events. 
    If we detect a button reply, check confirmation_manager, etc.
    """
    confirmation_manager = router.services["confirmation_manager"]
    messaging_service = router.services["messaging_service"]

    try:
        data: Dict[str, Any] = await request.json()
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
                action, appointment_time = reply_id.split("$", 1)
                key = f"{from_number}${appointment_time}"

                if await confirmation_manager.has_confirmation(key):
                    reminder = await confirmation_manager.get_confirmation(key)
                    if action == "yes_confirmation":
                        messaging_service.send_customer_whatsapp_reminder(
                            reminder["customer_number"], reminder["start_time"]
                        )
                        messaging_service.send_acknowledgement(
                            reminder["customer_name"], appointment_time, action
                        )
                        return {"status": "Reminder sent"}
                    else:
                        messaging_service.send_acknowledgement(
                            reminder["customer_name"], appointment_time, action
                        )
                        return {"status": "Confirmation declined"}

        return {"status": "No action taken"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

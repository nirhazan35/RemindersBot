import logging
from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)

router = APIRouter()

@router.get("/webhook")
async def verify_webhook(request: Request):
    logging.info("Webhook verification endpoint called")
    config = router.services["config"]
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    logging.info(f"Received webhook verification request: mode={mode}, token={token}, challenge={challenge}")

    if mode == "subscribe" and token == config.VERIFY_TOKEN:
        logging.info("Webhook verification successful")
        return PlainTextResponse(content=challenge)
    else:
        logging.warning("Webhook verification failed: Invalid token or mode")
        return JSONResponse(
            status_code=403,
            content={"status": "error", "message": "Invalid token or mode"}
        )


@router.post("/webhook")
async def handle_webhook(request: Request):
    """
    Handle WhatsApp webhook events. 
    If we detect a button reply, check confirmation_manager, etc.
    """
    logging.info("Received webhook event")
    confirmation_manager = router.services["confirmation_manager"]
    messaging_service = router.services["messaging_service"]

    try:
        data: Dict[str, Any] = await request.json()
        logging.info(f"Webhook payload received: {data}")

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
                logging.info(f"Button reply received: action={action}, appointment_time={appointment_time}")

                if await confirmation_manager.has_confirmation(key):
                    reminder = await confirmation_manager.get_confirmation(key)
                    if action == "yes_confirmation":
                        logging.info(f"Sending reminder to {reminder['customer_number']} for {reminder['start_time']}")
                        messaging_service.send_customer_whatsapp_reminder(
                            reminder["customer_number"], reminder["start_time"]
                        )
                        messaging_service.send_acknowledgement(
                            reminder["customer_name"], appointment_time, action
                        )
                        return {"status": "Reminder sent"}
                    else:
                        logging.info(f"Reminder declined for {reminder['customer_name']} at {appointment_time}")
                        messaging_service.send_acknowledgement(
                            reminder["customer_name"], appointment_time, action
                        )
                        return {"status": "Confirmation declined"}

        logging.info("No action taken in webhook")
        return {"status": "No action taken"}

    except Exception as e:
        logging.error(f"Error handling webhook: {e}")
        return {"status": "error", "message": str(e)}

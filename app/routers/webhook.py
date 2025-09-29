# app/routers/webhook.py
import logging
import os
import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter()
log = logging.getLogger(__name__)


def _normalize_msisdn(from_field: str) -> str:
    """
    Convert '9725XXXXXXX@s.whatsapp.net' -> '9725XXXXXXX', digits only for safety.
    """
    if "@s.whatsapp.net" in from_field:
        from_field = from_field.split("@", 1)[0]
    return re.sub(r"\D", "", from_field or "")


def _infer_action_from_text(text: str) -> Optional[str]:
    """
    Map free-text replies to yes/no actions (Hebrew & English).
    Returns 'yes_confirmation' / 'no_confirmation' / None.
    """
    t = (text or "").strip().lower()
    if t in {"כן", "כן.", "y", "yes", "ok", "approve", "אשר", "מאשר", "מאשרת"}:
        return "yes_confirmation"
    if t in {"לא", "לא.", "n", "no", "cancel", "בטל", "ביטול"}:
        return "no_confirmation"
    return None


@router.post("/webhook/wa")
async def wa_inbound(request: Request, x_token: str = Header(None)) -> Dict[str, Any]:
    """
    Inbound webhook for the Baileys Node adapter.

    Security:
      - Requires header: X-Token = WA_SHARED_SECRET (must match backend config)

    Behavior:
      - If a button payload is received, parse 'button.id' -> "<action>$<appointment_time>"
      - If a text payload is received, try to infer yes/no from the text
      - When action is determined, look up the pending confirmation by key "<from_number>$<appointment_time>"
      - If found and action is 'yes_confirmation' -> send patient reminder + ack to operator
        else -> send decline ack to operator
    """
    # Access shared services (set this in app startup code)
    services = getattr(router, "services", None)
    if not services:
        raise HTTPException(status_code=500, detail="services not initialized")

    config = services["config"]
    confirmation_manager = services["confirmation_manager"]
    messaging_service = services["messaging_service"]

    # Validate shared secret
    shared = getattr(config, "WA_SHARED_SECRET", None) or os.getenv("WA_SHARED_SECRET")
    if not shared or x_token != shared:
        raise HTTPException(status_code=401, detail="bad token")

    payload = await request.json()
    log.info("WA inbound payload: %s", payload)

    from_raw = payload.get("from", "")
    from_number = _normalize_msisdn(from_raw)
    if not from_number:
        return {"status": "ignored", "reason": "missing from"}

    # Text message handling: try to infer action from text
    action = _infer_action_from_text(payload.get("text", ""))
    if not action:
        log.info(f"Unrecognized text message: {payload.get('text', '')}")
        return {"status": "ignored", "reason": "unrecognized text"}
    
    log.info(f"Detected action '{action}' from text: {payload.get('text', '')}")
    appointment_time: Optional[str] = None

    # For text responses, we need to find all pending confirmations 
    # and match them by checking if any appointment_time appears in the message text
    all_keys = []
    cursor = confirmation_manager.collection.find({})
    async for doc in cursor:
        all_keys.append(doc["key"])
    
    if not all_keys:
        return {"status": "ignored", "reason": "no pending confirmations"}
    
    # Try to extract time from the user's message (like "כן 10:00" or "לא 14:30")
    message_text = payload.get("text", "")
    time_match = None
    for key in all_keys:
        try:
            customer_num, key_time = key.split("$", 1)
            # Extract just the hour:minute part from the full datetime
            # key_time might be like "2025-01-30T11:00:00" or just "11:00"
            if "T" in key_time:
                # ISO format: extract time part after T and before any timezone
                time_part = key_time.split("T")[1].split("+")[0].split("-")[0].split("Z")[0]
                # Take only HH:MM
                short_time = ":".join(time_part.split(":")[:2])
            else:
                # Assume it's already in short format
                short_time = key_time
            
            # Check if the short time appears in the message
            if short_time in message_text:
                appointment_time = key_time
                time_match = True
                log.info(f"Time match found: {short_time} in message: {message_text}")
                break
        except Exception as e:
            log.warning(f"Error parsing time from key {key}: {str(e)}")
            continue
    
    if not time_match:
        if len(all_keys) > 1:
            # Multiple pending - send list to user to clarify
            appointments_list = []
            for key in all_keys:
                try:
                    customer_num, time_part = key.split("$", 1)
                    
                    # Extract short time format for display
                    if "T" in time_part:
                        # ISO format: extract time part after T
                        time_display = time_part.split("T")[1].split("+")[0].split("-")[0].split("Z")[0]
                        # Take only HH:MM
                        short_time_display = ":".join(time_display.split(":")[:2])
                    else:
                        short_time_display = time_part
                    
                    # Get customer name from database
                    confirmation = await confirmation_manager.collection.find_one({"key": key})
                    customer_name = confirmation.get("customer_name", "Unknown") if confirmation else "Unknown"
                    appointments_list.append(f"• {short_time_display} - {customer_name}")
                except Exception as e:
                    log.warning(f"Error formatting appointment list item for key {key}: {str(e)}")
                    continue
            
            clarification_text = (
                f"📋 נמצאו {len(all_keys)} טיפולים הממתינים לאישור:\n\n"
                + "\n".join(appointments_list) + 
                "\n\n💡 אנא ציין/י את השעה המדויקת עם התשובה, למשל:\n"
                "*כן 10:00* או *לא 14:30*"
            )
            
            await messaging_service.send_acknowledgement("", "", clarification_text)
            return {"status": "multiple_pending", "reason": "sent clarification message"}
        else:
            # Single pending confirmation - use it
            try:
                _, appointment_time = all_keys[0].split("$", 1)
            except Exception:
                return {"status": "ignored", "reason": "invalid pending key format"}

    # Must have both action & appointment_time by here
    if not action or not appointment_time:
        return {"status": "ignored", "reason": "missing action or appointment_time"}

    # Find the correct key by appointment_time since keys are stored as customer_number$appointment_time
    matching_key = None
    cursor = confirmation_manager.collection.find({})
    async for doc in cursor:
        try:
            stored_key = doc["key"]
            _, stored_time = stored_key.split("$", 1)
            if stored_time == appointment_time:
                matching_key = stored_key
                break
        except Exception:
            continue
    
    if not matching_key:
        return {"status": "ignored", "reason": "no matching confirmation for appointment time"}

    reminder = await confirmation_manager.get_confirmation(matching_key)
    if not reminder:
        return {"status": "ignored", "reason": "failed to retrieve confirmation"}
        
    customer_name = reminder.get("customer_name", "Unknown")
    customer_number = reminder.get("customer_number")
    start_time = reminder.get("start_time", appointment_time)

    if action == "yes_confirmation":
        # Send reminder to patient, then ack to operator
        await messaging_service.send_customer_whatsapp_reminder(customer_number, start_time)
        await messaging_service.send_acknowledgement(customer_name, appointment_time, action)
        # Delete confirmation now that it's handled
        await confirmation_manager.delete_confirmation(matching_key)
        return {"status": "reminder_sent", "key": matching_key}

    # Decline path: send ack only
    await messaging_service.send_acknowledgement(customer_name, appointment_time, action)
    await confirmation_manager.delete_confirmation(matching_key)
    return {"status": "declined", "key": matching_key}
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

    cfg = services["config"]
    confirmation_manager = services["confirmation_manager"]
    messaging_service = services["messaging_service"]

    # Validate shared secret
    shared = getattr(cfg, "WA_SHARED_SECRET", None) or os.getenv("WA_SHARED_SECRET")
    if not shared or x_token != shared:
        raise HTTPException(status_code=401, detail="bad token")

    payload = await request.json()
    log.info("WA inbound payload: %s", payload)

    from_raw = payload.get("from", "")
    from_number = _normalize_msisdn(from_raw)
    if not from_number:
        return {"status": "ignored", "reason": "missing from"}

    msg_type = payload.get("type", "text")
    action: Optional[str] = None
    appointment_time: Optional[str] = None

    if msg_type == "button":
        btn = payload.get("button") or {}
        reply_id = btn.get("id", "")
        # Expected format: "<action>$<appointment_time>"
        if "$" in reply_id:
            action, appointment_time = reply_id.split("$", 1)
        else:
            return {"status": "ignored", "reason": "malformed button id"}
    else:
        # Free-text fallback: try to infer action; need appointment_time to match a pending key.
        action = _infer_action_from_text(payload.get("text", ""))
        if not action:
            return {"status": "ignored", "reason": "unrecognized text"}

        # If it's text and we don't know the appointment time, try to find *one* pending record
        # for this sender. If there are multiple, ignore to avoid ambiguity.
        pending_keys = await confirmation_manager.list_keys_for_sender(from_number)  # you may implement this helper
        if not pending_keys:
            return {"status": "ignored", "reason": "no pending confirmations for sender"}
        if len(pending_keys) > 1:
            return {"status": "ignored", "reason": "multiple pending confirmations; need button tap"}
        # pending key format: "<from_number>$<appointment_time>"
        try:
            _, appointment_time = pending_keys[0].split("$", 1)
        except Exception:
            return {"status": "ignored", "reason": "invalid pending key format"}

    # Must have both action & appointment_time by here
    if not action or not appointment_time:
        return {"status": "ignored", "reason": "missing action or appointment_time"}

    # Lookup the pending confirmation
    key = f"{from_number}${appointment_time}"
    if not await confirmation_manager.has_confirmation(key):
        return {"status": "ignored", "reason": "no matching confirmation"}

    reminder = await confirmation_manager.get_confirmation(key)
    customer_name = reminder.get("customer_name", "Unknown")
    customer_number = reminder.get("customer_number")
    start_time = reminder.get("start_time", appointment_time)

    if action == "yes_confirmation":
        # Send reminder to patient, then ack to operator
        await messaging_service.send_customer_whatsapp_reminder(customer_number, start_time)
        await messaging_service.send_acknowledgement(customer_name, appointment_time, action)
        # Optionally: delete confirmation now that it's handled
        await confirmation_manager.delete_confirmation(key)
        return {"status": "reminder_sent", "key": key}

    # Decline path: send ack only
    await messaging_service.send_acknowledgement(customer_name, appointment_time, action)
    await confirmation_manager.delete_confirmation(key)
    return {"status": "declined", "key": key}
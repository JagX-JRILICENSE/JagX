"""Consent-based social communication controls for JagX.

JagX may help prepare and send messages only through explicitly configured,
user-authorized integrations. It never scrapes private chats, silently logs in,
or auto-replies/posts on its own. Scheduled publishing is opt-in and requires
an enabled integration plus an explicit schedule.
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime

CONFIG_PATH = Path("./data/social_automation.json")


def _load():
    if not CONFIG_PATH.exists():
        return {"enabled": False, "platforms": {}, "schedules": [], "auto_reply": False, "auto_post": False}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"enabled": False, "platforms": {}, "schedules": [], "auto_reply": False, "auto_post": False}


def _save(data):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def communication_status() -> str:
    """Show communication integration status without exposing credentials or private chats."""
    d = _load()
    return json.dumps({"enabled": d.get("enabled", False), "platforms": list(d.get("platforms", {}).keys()), "auto_reply": d.get("auto_reply", False), "auto_post": d.get("auto_post", False), "schedules": len(d.get("schedules", []))}, indent=2)


def configure_communication(platform: str, enabled: bool = True) -> str:
    """Enable or disable a named, user-authorized communication integration. No credentials are accepted."""
    platform = str(platform).strip().lower()
    allowed = {"whatsapp", "telegram", "discord", "facebook", "instagram", "x", "email", "teams"}
    if platform not in allowed:
        return "Unsupported integration. Supported integrations: " + ", ".join(sorted(allowed))
    d = _load(); d["platforms"][platform] = bool(enabled); d["enabled"] = any(d["platforms"].values()); _save(d)
    return f"{platform} integration {'enabled' if enabled else 'disabled'}. Complete login/authorization in the supported integration UI before sending anything."


def set_social_schedule(platform: str, interval_minutes: int = 30, enabled: bool = True) -> str:
    """Create an opt-in publishing schedule; this stores policy only and does not send a post by itself."""
    interval_minutes = int(interval_minutes)
    if interval_minutes < 5 or interval_minutes > 10080:
        return "Interval must be between 5 minutes and 7 days."
    d = _load(); platform = str(platform).strip().lower()
    if not d["platforms"].get(platform, False):
        return "Enable and authorize that platform first."
    d["auto_post"] = bool(enabled)
    d["schedules"] = [{"platform": platform, "interval_minutes": interval_minutes, "enabled": bool(enabled), "created_at": datetime.now().isoformat()}]
    _save(d)
    return f"Posting schedule {'enabled' if enabled else 'disabled'} for {platform}: every {interval_minutes} minutes. JagX will not publish without an authorized integration and a queued user-approved post."


def queue_social_post(platform: str, text: str) -> str:
    """Queue a draft for later review; it does not publish immediately."""
    text = str(text).strip()
    if not text: return "Post text cannot be empty."
    d = _load(); platform = str(platform).strip().lower()
    if not d["platforms"].get(platform, False): return "Enable and authorize that platform first."
    drafts = d.setdefault("drafts", []); drafts.append({"platform": platform, "text": text, "created_at": datetime.now().isoformat(), "approved": False}); _save(d)
    return "Post saved as an unapproved draft. Review and explicitly approve it before publication."


def set_auto_reply(enabled: bool = True) -> str:
    """Enable/disable the auto-reply policy; replies remain draft-only until an integration provides an explicit send approval flow."""
    d = _load(); d["auto_reply"] = bool(enabled); _save(d)
    return f"Auto-reply policy {'enabled' if enabled else 'disabled'}. JagX will not impersonate you or send replies silently."


def prepare_reply(platform: str, conversation_hint: str, proposed_reply: str) -> str:
    """Prepare a reply from user-supplied context without reading private chats automatically."""
    if not str(proposed_reply).strip(): return "Reply cannot be empty."
    return json.dumps({"platform": str(platform).lower(), "conversation_hint": str(conversation_hint)[:200], "reply": str(proposed_reply), "send": False}, indent=2)


def call_control(action: str, contact: str = "") -> str:
    """Prepare a call action. Actual calling/answering must use an authorized OS/app integration and explicit policy."""
    action = str(action).strip().lower()
    if action not in {"dial", "answer", "decline", "hangup"}: return "Action must be dial, answer, decline, or hangup."
    return f"Call action prepared: {action}" + (f" for {contact}" if contact else "") + ". No call was placed or answered by this local policy tool."


SYSTEM_SOCIAL_TOOLS = [
 {"type":"function","function":{"name":"communication_status","description":"Show configured communication platforms and automation status without revealing secrets or private messages.","parameters":{"type":"object","properties":{},"additionalProperties":False}}},
 {"type":"function","function":{"name":"configure_communication","description":"Enable or disable a user-authorized social communication integration; never accepts passwords or tokens.","parameters":{"type":"object","properties":{"platform":{"type":"string"},"enabled":{"type":"boolean"}},"required":["platform"]}}},
 {"type":"function","function":{"name":"set_social_schedule","description":"Set an opt-in social posting interval policy; does not publish by itself.","parameters":{"type":"object","properties":{"platform":{"type":"string"},"interval_minutes":{"type":"integer"},"enabled":{"type":"boolean"}},"required":["platform"]}}},
 {"type":"function","function":{"name":"queue_social_post","description":"Save a social post as an unapproved draft; never silently publishes.","parameters":{"type":"object","properties":{"platform":{"type":"string"},"text":{"type":"string"}},"required":["platform","text"]}}},
 {"type":"function","function":{"name":"set_auto_reply","description":"Enable or disable communication auto-reply policy; sending remains explicitly controlled.","parameters":{"type":"object","properties":{"enabled":{"type":"boolean"}},"required":["enabled"]}}},
 {"type":"function","function":{"name":"prepare_reply","description":"Prepare a reply using context explicitly supplied by the user; does not read private chats automatically.","parameters":{"type":"object","properties":{"platform":{"type":"string"},"conversation_hint":{"type":"string"},"proposed_reply":{"type":"string"}},"required":["platform","conversation_hint","proposed_reply"]}}},
 {"type":"function","function":{"name":"call_control","description":"Prepare a dial/answer/decline/hangup action; actual telephony requires an authorized integration.","parameters":{"type":"object","properties":{"action":{"type":"string","enum":["dial","answer","decline","hangup"]},"contact":{"type":"string"}},"required":["action"]}}},
]
TOOL_FUNCTIONS={"communication_status":communication_status,"configure_communication":configure_communication,"set_social_schedule":set_social_schedule,"queue_social_post":queue_social_post,"set_auto_reply":set_auto_reply,"prepare_reply":prepare_reply,"call_control":call_control}

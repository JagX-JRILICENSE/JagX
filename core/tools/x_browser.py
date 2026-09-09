"""Primary X/Twitter browser automation for JagX.

Uses the same visible, persistent Playwright browser profile as JagX. The user
performs any CAPTCHA, 2FA, or unusual verification manually; JagX can then
continue the normal posting flow without bypassing those controls.
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from core.tools import browser as _browser_mod

DATA_PATH = Path("./data/x_automation.json")
X_HOME = "https://x.com/"
X_LOGIN = "https://x.com/i/flow/login"
X_COMPOSE = "https://x.com/compose/post"


def _page():
    return _browser_mod._ensure()


def _load():
    if not DATA_PATH.exists():
        return {"drafts": [], "schedule": None, "paused": False, "last_post": None}
    try:
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"drafts": [], "schedule": None, "paused": False, "last_post": None}


def _save(data):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def x_browser_status() -> str:
    page = _page()
    text = ""
    try:
        text = page.locator("body").inner_text(timeout=3000)[:2000]
    except Exception:
        pass
    logged_in = not any(x in text.lower() for x in ("sign in", "log in")) and "flow/login" not in page.url
    return json.dumps({"ready": True, "url": page.url, "title": page.title(), "session_persistent": True, "appears_logged_in": logged_in}, indent=2)


def x_open_login() -> str:
    page = _page()
    page.goto(X_LOGIN, wait_until="domcontentloaded", timeout=30000)
    return "X login opened in JagX's persistent browser. Complete login, CAPTCHA, 2FA, or verification manually; the session will be retained locally."


def x_check_login() -> str:
    page = _page()
    if "x.com" not in page.url:
        page.goto(X_HOME, wait_until="domcontentloaded", timeout=30000)
    try:
        body = page.locator("body").inner_text(timeout=5000).lower()
    except Exception:
        body = ""
    blocked = any(k in body for k in ("captcha", "verify", "verification", "suspicious login"))
    logged_in = not any(k in body for k in ("log in", "sign in")) and not blocked
    return json.dumps({"logged_in": logged_in, "manual_verification_needed": blocked, "url": page.url}, indent=2)


def x_wait_for_manual_verification(timeout_seconds: int = 300) -> str:
    page = _page()
    deadline = time.time() + max(5, min(int(timeout_seconds), 900))
    while time.time() < deadline:
        try:
            body = page.locator("body").inner_text(timeout=2000).lower()
            still_blocked = any(k in body for k in ("captcha", "verify", "verification", "suspicious login"))
            if not still_blocked:
                return "Manual verification appears complete. JagX can continue the X workflow."
        except Exception:
            pass
        time.sleep(2)
    return "Manual verification wait timed out. Leave the browser open and run the X action again after completing verification."


def x_open_home() -> str:
    page = _page()
    page.goto(X_HOME, wait_until="domcontentloaded", timeout=30000)
    return f"X home opened: {page.url}"


def x_open_compose() -> str:
    page = _page()
    page.goto(X_COMPOSE, wait_until="domcontentloaded", timeout=30000)
    return "X composer opened."


def _editor(page):
    selectors = ["[data-testid='tweetTextarea_0']", "div[role='textbox'][contenteditable='true']"]
    for selector in selectors:
        loc = page.locator(selector).first
        if loc.count():
            return loc
    raise RuntimeError("X post editor was not found. X may require login or its page layout may have changed.")


def _post_button(page):
    for selector in ("[data-testid='tweetButtonInline']", "[data-testid='tweetButton']"):
        loc = page.locator(selector).first
        if loc.count() and loc.is_enabled():
            return loc
    return None


def x_post(text: str, wait_for_manual_verification: bool = True, verification_timeout_seconds: int = 300) -> str:
    """Publish a post through the visible X browser session.

    CAPTCHA/2FA/verification is never bypassed. If X asks for manual action,
    JagX leaves the browser visible and waits for the user to finish it.
    """
    text = str(text).strip()
    if not text:
        return "Post text cannot be empty."
    if len(text) > 280:
        return "Post exceeds X's 280-character limit."
    page = _page()
    page.goto(X_COMPOSE, wait_until="domcontentloaded", timeout=30000)
    try:
        editor = _editor(page)
    except Exception as first_error:
        if wait_for_manual_verification:
            waited = x_wait_for_manual_verification(verification_timeout_seconds)
            if "complete" not in waited.lower():
                return waited
            page.goto(X_COMPOSE, wait_until="domcontentloaded", timeout=30000)
            editor = _editor(page)
        else:
            return f"X composer unavailable: {first_error}"
    editor.fill(text)
    button = _post_button(page)
    if button is None:
        if wait_for_manual_verification:
            x_wait_for_manual_verification(verification_timeout_seconds)
            button = _post_button(page)
        if button is None:
            return "X post button is unavailable. Complete any visible verification manually and retry."
    button.click(timeout=10000)
    time.sleep(2)
    data = _load()
    data["last_post"] = {"text": text, "posted_at": datetime.now().isoformat()}
    _save(data)
    return "X post published successfully through JagX's browser session."


def x_save_draft(text: str) -> str:
    text = str(text).strip()
    if not text:
        return "Draft cannot be empty."
    if len(text) > 280:
        return "Draft exceeds 280 characters."
    data = _load()
    draft_id = max([int(x.get("id", 0)) for x in data["drafts"]] or [0]) + 1
    data["drafts"].append({"id": draft_id, "text": text, "created_at": datetime.now().isoformat(), "approved": False})
    _save(data)
    return f"Saved X draft #{draft_id}. It is not published."


def x_list_drafts() -> str:
    return json.dumps(_load()["drafts"], indent=2)


def x_approve_draft(draft_id: int) -> str:
    data = _load()
    for draft in data["drafts"]:
        if int(draft.get("id", -1)) == int(draft_id):
            draft["approved"] = True
            draft["approved_at"] = datetime.now().isoformat()
            _save(data)
            return f"X draft #{draft_id} approved for publishing."
    return "X draft not found."


def x_publish_draft(draft_id: int) -> str:
    data = _load()
    for draft in data["drafts"]:
        if int(draft.get("id", -1)) == int(draft_id):
            if not draft.get("approved"):
                return "Draft is not approved. Approve it before publishing."
            result = x_post(draft["text"])
            if result.startswith("X post published"):
                data["drafts"] = [x for x in data["drafts"] if int(x.get("id", -1)) != int(draft_id)]
                _save(data)
            return result
    return "X draft not found."


def x_set_schedule(interval_minutes: int = 17, enabled: bool = False) -> str:
    n = int(interval_minutes)
    if n < 5 or n > 10080:
        return "Interval must be between 5 minutes and 7 days."
    data = _load()
    data["schedule"] = {"interval_minutes": n, "enabled": bool(enabled), "updated_at": datetime.now().isoformat()}
    _save(data)
    return f"X browser posting schedule {'enabled' if enabled else 'disabled'}: every {n} minutes. The scheduler publishes only approved drafts and does not bypass X limits or verification."


def x_schedule_status() -> str:
    data = _load()
    return json.dumps({"schedule": data.get("schedule"), "paused": bool(data.get("paused")), "last_post": data.get("last_post")}, indent=2)


def x_pause_automation() -> str:
    data = _load(); data["paused"] = True; _save(data)
    return "X browser automation paused."


def x_resume_automation() -> str:
    data = _load(); data["paused"] = False; _save(data)
    return "X browser automation resumed."


def x_open_profile() -> str:
    page = _page(); page.goto(X_HOME, wait_until="domcontentloaded", timeout=30000)
    return "X profile/home opened in the persistent JagX browser."


X_TOOLS = []
_TOOL_NAMES = [
    "x_browser_status", "x_open_login", "x_check_login", "x_wait_for_manual_verification",
    "x_open_home", "x_open_compose", "x_post", "x_save_draft", "x_list_drafts",
    "x_approve_draft", "x_publish_draft", "x_set_schedule", "x_schedule_status",
    "x_pause_automation", "x_resume_automation", "x_open_profile"
]
for _name in _TOOL_NAMES:
    X_TOOLS.append({"type":"function","function":{"name":_name,"description":globals()[_name].__doc__ or _name.replace("_", " ").title(),"parameters":{"type":"object","properties":{},"additionalProperties":True}}})
TOOL_FUNCTIONS = {name: globals()[name] for name in _TOOL_NAMES}

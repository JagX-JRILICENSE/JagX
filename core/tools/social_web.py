"""
JagX Social tools — X, Facebook, Instagram, WhatsApp Web, etc.
Uses browser session (you log in once). Confirm before public posts.
JRILICENSE
"""

from __future__ import annotations

try:
    from core.tools.browser import (
        browser_navigate,
        browser_get_page_text,
        _ensure,
    )
except Exception:
    browser_navigate = browser_get_page_text = None
    _ensure = None


def open_x() -> str:
    return browser_navigate("https://x.com/home") if browser_navigate else "Browser unavailable"


def open_facebook() -> str:
    return browser_navigate("https://www.facebook.com/") if browser_navigate else "Browser unavailable"


def open_instagram() -> str:
    return browser_navigate("https://www.instagram.com/") if browser_navigate else "Browser unavailable"


def open_linkedin() -> str:
    return browser_navigate("https://www.linkedin.com/feed/") if browser_navigate else "Browser unavailable"


def open_reddit() -> str:
    return browser_navigate("https://www.reddit.com/") if browser_navigate else "Browser unavailable"


def open_youtube() -> str:
    return browser_navigate("https://www.youtube.com/") if browser_navigate else "Browser unavailable"


def open_gmail() -> str:
    return browser_navigate("https://mail.google.com/") if browser_navigate else "Browser unavailable"


def open_whatsapp_web() -> str:
    return browser_navigate("https://web.whatsapp.com/") if browser_navigate else "Browser unavailable"


def open_github() -> str:
    return browser_navigate("https://github.com/") if browser_navigate else "Browser unavailable"


def open_any_url(url: str) -> str:
    if not browser_navigate:
        return "Browser unavailable"
    u = (url or "").strip()
    if not u:
        return "URL required"
    if not u.startswith("http"):
        u = "https://" + u
    return browser_navigate(u)


def x_compose_post(text: str) -> str:
    if not browser_navigate:
        return "Browser unavailable"
    steps = [browser_navigate("https://x.com/compose/post")]
    try:
        page = _ensure()
        for sel in [
            "div[data-testid='tweetTextarea_0']",
            "div[role='textbox']",
            "div.public-DraftEditor-content",
        ]:
            try:
                page.locator(sel).first.click(timeout=3000)
                page.locator(sel).first.fill(text)
                steps.append("Draft typed")
                return " | ".join(steps) + " | Review, then ask to publish if you approve."
            except Exception:
                continue
        steps.append("Compose opened; log in to X if needed, then retry.")
    except Exception as e:
        steps.append(str(e))
    return " | ".join(steps)


def x_click_post_button() -> str:
    if not _ensure:
        return "Browser unavailable"
    page = _ensure()
    for sel in ["button[data-testid='tweetButton']", "button[data-testid='tweetButtonInline']"]:
        try:
            page.locator(sel).first.click(timeout=5000)
            return "Posted on X"
        except Exception:
            continue
    return "Post button not found — are you logged in with compose open?"


def x_like_first_visible() -> str:
    if not _ensure:
        return "Browser unavailable"
    page = _ensure()
    try:
        page.locator("button[data-testid='like']").first.click(timeout=5000)
        return "Liked first visible post"
    except Exception as e:
        return f"Like failed: {e}"


def x_open_messages() -> str:
    return browser_navigate("https://x.com/messages") if browser_navigate else "Browser unavailable"


def x_reply_in_compose(text: str) -> str:
    """Type a reply in the focused X reply/DM box."""
    if not _ensure:
        return "Browser unavailable"
    page = _ensure()
    for sel in ["div[data-testid='tweetTextarea_0']", "div[role='textbox']"]:
        try:
            page.locator(sel).first.click(timeout=3000)
            page.locator(sel).first.fill(text)
            return "Reply text entered. Review, then ask to click Post/Send."
        except Exception:
            continue
    return "Could not find reply box. Open the conversation first."


def facebook_compose_post(text: str) -> str:
    if not browser_navigate:
        return "Browser unavailable"
    r = browser_navigate("https://www.facebook.com/")
    try:
        page = _ensure()
        for sel in ["div[role='textbox']", "div[contenteditable='true']"]:
            try:
                page.locator(sel).first.click(timeout=4000)
                page.locator(sel).first.fill(text)
                return r + " | Facebook draft ready — review before posting."
            except Exception:
                continue
        return r + " | Opened Facebook; log in if needed."
    except Exception as e:
        return f"{r} | {e}"


def whatsapp_search_chat(name: str) -> str:
    """Open WhatsApp Web and search for a chat by name."""
    if not browser_navigate:
        return "Browser unavailable"
    r = browser_navigate("https://web.whatsapp.com/")
    try:
        page = _ensure()
        for sel in [
            "div[contenteditable='true'][data-tab='3']",
            "div[title='Search input textbox']",
            "div[role='textbox']",
        ]:
            try:
                page.locator(sel).first.click(timeout=4000)
                page.locator(sel).first.fill(name)
                return r + f" | Searched chats for '{name}'. Click the chat, then ask to type a reply."
            except Exception:
                continue
        return r + " | WhatsApp opened. Scan QR if needed, then search the contact."
    except Exception as e:
        return f"{r} | {e}"


def whatsapp_type_message(text: str) -> str:
    """Type a message into the active WhatsApp chat box (does not auto-send unless user asks)."""
    if not _ensure:
        return "Browser unavailable"
    page = _ensure()
    for sel in [
        "div[contenteditable='true'][data-tab='10']",
        "div[title='Type a message']",
        "footer div[contenteditable='true']",
        "div[role='textbox']",
    ]:
        try:
            loc = page.locator(sel).last
            loc.click(timeout=4000)
            loc.fill(text)
            return "Message typed in WhatsApp. Review, then ask JagX to send if you approve."
        except Exception:
            continue
    return "Could not find WhatsApp message box. Open a chat first."


def whatsapp_send_message() -> str:
    """Press Enter / click send on WhatsApp after user approval."""
    if not _ensure:
        return "Browser unavailable"
    page = _ensure()
    try:
        page.keyboard.press("Enter")
        return "Send key pressed on WhatsApp"
    except Exception as e:
        return f"Send failed: {e}"


def social_read_page() -> str:
    if not browser_get_page_text:
        return "Browser unavailable"
    return browser_get_page_text(8000)


SOCIAL_WEB_TOOLS = [
    {"type": "function", "function": {"name": "open_x", "description": "Open X home.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_facebook", "description": "Open Facebook.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_instagram", "description": "Open Instagram.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_linkedin", "description": "Open LinkedIn.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_reddit", "description": "Open Reddit.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_youtube", "description": "Open YouTube.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_gmail", "description": "Open Gmail.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_whatsapp_web", "description": "Open WhatsApp Web.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_github", "description": "Open GitHub in browser.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_any_url", "description": "Open any website URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "x_compose_post", "description": "Draft an X post.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "x_click_post_button", "description": "Publish drafted X post after user approval.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "x_like_first_visible", "description": "Like first visible X post.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "x_open_messages", "description": "Open X messages.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "x_reply_in_compose", "description": "Type a reply/DM on X.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "facebook_compose_post", "description": "Draft a Facebook post.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "whatsapp_search_chat", "description": "Search a WhatsApp chat by contact name.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "whatsapp_type_message", "description": "Type a WhatsApp message in the open chat.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "whatsapp_send_message", "description": "Send the typed WhatsApp message after user approval.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "social_read_page", "description": "Read current page text.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]

TOOL_FUNCTIONS = {
    "open_x": open_x,
    "open_facebook": open_facebook,
    "open_instagram": open_instagram,
    "open_linkedin": open_linkedin,
    "open_reddit": open_reddit,
    "open_youtube": open_youtube,
    "open_gmail": open_gmail,
    "open_whatsapp_web": open_whatsapp_web,
    "open_github": open_github,
    "open_any_url": open_any_url,
    "x_compose_post": x_compose_post,
    "x_click_post_button": x_click_post_button,
    "x_like_first_visible": x_like_first_visible,
    "x_open_messages": x_open_messages,
    "x_reply_in_compose": x_reply_in_compose,
    "facebook_compose_post": facebook_compose_post,
    "whatsapp_search_chat": whatsapp_search_chat,
    "whatsapp_type_message": whatsapp_type_message,
    "whatsapp_send_message": whatsapp_send_message,
    "social_read_page": social_read_page,
}

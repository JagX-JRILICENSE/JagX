"""
JagX Social + Internet power tools
Post / like / open on X, Facebook, Instagram (user's own sessions via browser profile).
Confirm before public posts.
JRILICENSE
"""

from __future__ import annotations

from typing import Optional

try:
    from core.tools.browser import (
        browser_navigate,
        browser_click,
        browser_type,
        browser_get_page_text,
        browser_status,
        _ensure,
    )
except Exception:
    browser_navigate = browser_click = browser_type = browser_get_page_text = browser_status = None
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
    """Open any http(s) website needed for work."""
    if not browser_navigate:
        return "Browser unavailable"
    u = (url or "").strip()
    if not u:
        return "URL required"
    return browser_navigate(u)


def x_compose_post(text: str) -> str:
    """Open X compose and type a draft. User should confirm before posting."""
    if not browser_navigate:
        return "Browser unavailable"
    steps = [browser_navigate("https://x.com/compose/post")]
    try:
        page = _ensure()
        # Try common compose selectors
        for sel in [
            "div[data-testid='tweetTextarea_0']",
            "div[role='textbox']",
            "div.public-DraftEditor-content",
        ]:
            try:
                page.locator(sel).first.click(timeout=3000)
                page.locator(sel).first.fill(text)
                steps.append(f"Draft typed into {sel}")
                return " | ".join(steps) + " | Review the draft, then ask JagX to click Post if you approve."
            except Exception:
                continue
        steps.append("Opened compose; could not auto-fill — type manually or try again while logged in.")
    except Exception as e:
        steps.append(str(e))
    return " | ".join(steps)


def x_click_post_button() -> str:
    """Click the Post button on X (only after user asked to publish)."""
    if not _ensure:
        return "Browser unavailable"
    page = _ensure()
    for sel in ["button[data-testid='tweetButton']", "button[data-testid='tweetButtonInline']"]:
        try:
            page.locator(sel).first.click(timeout=5000)
            return f"Clicked Post via {sel}"
        except Exception:
            continue
    return "Could not find Post button. Make sure compose is open and you are logged in."


def x_like_first_visible() -> str:
    if not _ensure:
        return "Browser unavailable"
    page = _ensure()
    try:
        page.locator("button[data-testid='like']").first.click(timeout=5000)
        return "Liked the first visible post"
    except Exception as e:
        return f"Like failed (are you on the feed and logged in?): {e}"


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
                return r + " | Draft entered on Facebook. Review, then post manually or ask to click Post."
            except Exception:
                continue
        return r + " | Opened Facebook; auto-fill failed — ensure you are logged in."
    except Exception as e:
        return f"{r} | {e}"


def instagram_open_home() -> str:
    return open_instagram()


def social_read_page() -> str:
    if not browser_get_page_text:
        return "Browser unavailable"
    return browser_get_page_text(8000)


SOCIAL_WEB_TOOLS = [
    {"type": "function", "function": {"name": "open_x", "description": "Open X (Twitter) home in JagX browser.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_facebook", "description": "Open Facebook in JagX browser.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_instagram", "description": "Open Instagram in JagX browser.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_linkedin", "description": "Open LinkedIn feed.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_reddit", "description": "Open Reddit.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_youtube", "description": "Open YouTube.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_gmail", "description": "Open Gmail.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_whatsapp_web", "description": "Open WhatsApp Web.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_github", "description": "Open GitHub website.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_any_url", "description": "Open any website URL needed for work.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "x_compose_post", "description": "Draft a post on X. Confirm with user before publishing.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "x_click_post_button", "description": "Publish the drafted X post (only when user asked to post).", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "x_like_first_visible", "description": "Like the first visible post on X feed.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "facebook_compose_post", "description": "Draft a Facebook post.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "instagram_open_home", "description": "Open Instagram home.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "social_read_page", "description": "Read text from the current social/web page.", "parameters": {"type": "object", "properties": {}, "required": []}}},
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
    "facebook_compose_post": facebook_compose_post,
    "instagram_open_home": instagram_open_home,
    "social_read_page": social_read_page,
}

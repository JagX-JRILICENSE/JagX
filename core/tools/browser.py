"""JagX browser automation using a persistent visible Chrome/Edge profile.

Normal typing refuses password/OTP fields. Saved credentials can be filled only
by a dedicated local tool which retrieves the secret from the OS credential
store and inserts it directly into the browser; the secret is never returned.
JRILICENSE
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

try:
    from core.tools.credentials import get_credential
except Exception:
    get_credential = None

_browser = None
_context = None
_page = None
_pw = None


def _ensure():
    global _pw, _browser, _context, _page
    if sync_playwright is None:
        raise RuntimeError("Browser control requires Playwright. Install: pip install playwright")
    if _page is not None and not _page.is_closed():
        return _page
    if _pw is None:
        _pw = sync_playwright().start()
    profile = Path.home() / ".jagx" / "browser-profile"
    profile.mkdir(parents=True, exist_ok=True)
    candidates = []
    if os.name == "nt":
        candidates = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        ]
    executable = next((p for p in candidates if Path(p).exists()), None)
    launch = {"headless": False, "user_data_dir": str(profile), "accept_downloads": True, "viewport": {"width": 1440, "height": 900}}
    if executable:
        launch["executable_path"] = executable
    _context = _pw.chromium.launch_persistent_context(**launch)
    _browser = _context
    pages = _context.pages
    _page = pages[0] if pages else _context.new_page()
    return _page


def browser_status() -> str:
    try:
        page = _ensure()
        return f"Browser ready: {page.title()} — {page.url} — persistent profile enabled"
    except Exception as e:
        return f"Browser unavailable: {e}"


def browser_navigate(url: str) -> str:
    page = _ensure()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    return f"Navigated to: {page.url}\nTitle: {page.title()}"


def browser_back() -> str:
    page = _ensure(); page.go_back(wait_until="domcontentloaded", timeout=30000); return f"Current page: {page.title()} — {page.url}"


def browser_forward() -> str:
    page = _ensure(); page.go_forward(wait_until="domcontentloaded", timeout=30000); return f"Current page: {page.title()} — {page.url}"


def browser_get_page_text(max_chars: int = 12000) -> str:
    return _ensure().locator("body").inner_text(timeout=10000)[:max_chars]


def browser_find_links(max_results: int = 40) -> str:
    page = _ensure(); links = page.locator("a"); count = min(links.count(), max_results); rows = []
    for i in range(count):
        link = links.nth(i)
        label = (link.inner_text(timeout=3000) or "").strip().replace("\n", " ")
        href = link.get_attribute("href") or ""
        if label or href:
            rows.append(f"{i}: {label[:100]} -> {href[:300]}")
    return "\n".join(rows) or "No links found."


def _is_sensitive(target) -> bool:
    input_type = (target.get_attribute("type") or "").lower()
    name = ((target.get_attribute("name") or "") + " " + (target.get_attribute("aria-label") or "") + " " + (target.get_attribute("placeholder") or "")).lower()
    return input_type == "password" or any(x in name for x in ("password", "passcode", "otp", "one-time", "verification code", "security code"))


def browser_click(selector: str) -> str:
    page = _ensure(); target = page.locator(selector).first
    if _is_sensitive(target):
        return "Blocked: credential/verification controls cannot be automated by normal browser_click."
    tag = target.evaluate("el => el.tagName.toLowerCase()"); target.click(timeout=10000); return f"Clicked {tag} matching: {selector}"


def browser_type(selector: str, text: str, clear: bool = True) -> str:
    page = _ensure(); target = page.locator(selector).first
    if _is_sensitive(target):
        return "Blocked: use browser_fill_saved_credential for a stored password; OTP and verification codes remain manual."
    if clear:
        target.fill(text)
    else:
        target.type(text)
    return f"Entered text into: {selector}"


def browser_fill_saved_credential(account: str, selector: str = "input[type='password']") -> str:
    if get_credential is None:
        return "Secure credential integration unavailable."
    page = _ensure(); result = get_credential(account)
    if not result.startswith("SECURE_CREDENTIAL:"):
        return "Saved credential unavailable for that account."
    secret = result[len("SECURE_CREDENTIAL:"):]
    try:
        target = page.locator(selector).first; input_type = (target.get_attribute("type") or "").lower()
        if input_type != "password":
            return "Blocked: the selected field is not a password field."
        target.fill(secret)
        return "Stored credential filled into the selected password field. The password was not returned or logged."
    finally:
        secret = ""; result = ""


def browser_select(selector: str, value: str) -> str:
    target = _ensure().locator(selector).first; return f"Selected: {target.select_option(value=value)}"


def browser_download(selector: str, save_path: str = "") -> str:
    page = _ensure()
    with page.expect_download(timeout=30000) as info:
        page.locator(selector).first.click(timeout=10000)
    download = info.value
    if save_path:
        target = Path(save_path).expanduser().resolve(); target.parent.mkdir(parents=True, exist_ok=True); download.save_as(str(target)); return f"Downloaded: {target}"
    return f"Download ready: {download.suggested_filename}"


def browser_screenshot(path: str = "jagx_browser.png") -> str:
    target = Path(path).expanduser().resolve(); target.parent.mkdir(parents=True, exist_ok=True); _ensure().screenshot(path=str(target), full_page=True); return f"Browser screenshot saved: {target}"


def browser_close() -> str:
    global _pw, _browser, _context, _page
    try:
        if _context:
            _context.close()
        if _pw:
            _pw.stop()
    finally:
        _pw = _browser = _context = _page = None
    return "JagX browser closed. The persistent profile remains saved for the next session."


BROWSER_TOOLS = [
    {"type":"function","function":{"name":"browser_status","description":"Check the JagX-controlled visible browser and persistent profile status.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"browser_navigate","description":"Navigate the JagX-controlled browser to a website.","parameters":{"type":"object","properties":{"url":{"type":"string"}},"required":["url"]}}},
    {"type":"function","function":{"name":"browser_back","description":"Go back one page in the JagX-controlled browser.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"browser_forward","description":"Go forward one page in the JagX-controlled browser.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"browser_get_page_text","description":"Read visible text from the current browser page.","parameters":{"type":"object","properties":{"max_chars":{"type":"integer","default":12000}},"required":[]}}},
    {"type":"function","function":{"name":"browser_find_links","description":"List useful links on the current page.","parameters":{"type":"object","properties":{"max_results":{"type":"integer","default":40}},"required":[]}}},
    {"type":"function","function":{"name":"browser_click","description":"Click a normal webpage element. Credential controls are blocked.","parameters":{"type":"object","properties":{"selector":{"type":"string"}},"required":["selector"]}}},
    {"type":"function","function":{"name":"browser_type","description":"Enter non-secret text. Password, OTP and verification fields are blocked.","parameters":{"type":"object","properties":{"selector":{"type":"string"},"text":{"type":"string"},"clear":{"type":"boolean","default":True}},"required":["selector","text"]}}},
    {"type":"function","function":{"name":"browser_fill_saved_credential","description":"Fill a password field from JagX's OS credential store without returning the password. OTP/verification remains manual.","parameters":{"type":"object","properties":{"account":{"type":"string"},"selector":{"type":"string","default":"input[type='password']"}},"required":["account"]}}},
    {"type":"function","function":{"name":"browser_select","description":"Select an option from a webpage select element.","parameters":{"type":"object","properties":{"selector":{"type":"string"},"value":{"type":"string"}},"required":["selector","value"]}}},
    {"type":"function","function":{"name":"browser_download","description":"Click a webpage download control and save the file. User confirmation is required.","parameters":{"type":"object","properties":{"selector":{"type":"string"},"save_path":{"type":"string","default":""}},"required":["selector"]}}},
    {"type":"function","function":{"name":"browser_screenshot","description":"Capture the current browser page as an image.","parameters":{"type":"object","properties":{"path":{"type":"string","default":"jagx_browser.png"}},"required":[]}}},
    {"type":"function","function":{"name":"browser_close","description":"Close the browser while keeping its persistent login profile.","parameters":{"type":"object","properties":{},"required":[]}}},
]
TOOL_FUNCTIONS = {name: globals()[name] for name in ["browser_status","browser_navigate","browser_back","browser_forward","browser_get_page_text","browser_find_links","browser_click","browser_type","browser_fill_saved_credential","browser_select","browser_download","browser_screenshot","browser_close"]}

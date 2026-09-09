"""
JagX Extra Useful Tools
Clipboard, notifications, open URLs, quick actions.

JRILICENSE
"""

from __future__ import annotations

import subprocess
import platform
import webbrowser
from typing import Optional

from rich.console import Console

console = Console()

try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False


def get_clipboard() -> str:
    """Get current clipboard text."""
    if not HAS_CLIPBOARD:
        return "Clipboard library not available."
    try:
        return pyperclip.paste() or "(clipboard empty)"
    except Exception as e:
        return f"Clipboard error: {e}"


def set_clipboard(text: str) -> str:
    """Copy text to the clipboard."""
    if not HAS_CLIPBOARD:
        return "Clipboard library not available."
    try:
        pyperclip.copy(text)
        return f"Copied to clipboard ({len(text)} characters)"
    except Exception as e:
        return f"Clipboard error: {e}"


def open_url(url: str) -> str:
    """Open a URL in the default browser."""
    try:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        return f"Opened {url}"
    except Exception as e:
        return f"Failed to open URL: {e}"


def notify(title: str, message: str) -> str:
    """Show a desktop notification (Windows / macOS / Linux)."""
    system = platform.system().lower()
    try:
        if system == "windows":
            # PowerShell balloon / toast style
            script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $textNodes = $template.GetElementsByTagName("text")
            $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) | Out-Null
            $textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) | Out-Null
            $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("JagX").Show($toast)
            '''
            subprocess.run(["powershell", "-Command", script], capture_output=True, timeout=10)
            return "Notification sent (Windows)"
        elif system == "darwin":
            subprocess.run([
                "osascript", "-e",
                f'display notification "{message}" with title "{title}"'
            ], capture_output=True, timeout=5)
            return "Notification sent (macOS)"
        else:
            subprocess.run(["notify-send", title, message], capture_output=True, timeout=5)
            return "Notification sent (Linux)"
    except Exception as e:
        return f"Notification failed: {e}"


def open_app(app_name: str) -> str:
    """Try to launch an application by name."""
    system = platform.system().lower()
    try:
        if system == "windows":
            subprocess.Popen(["start", app_name], shell=True)
            return f"Launched {app_name}"
        elif system == "darwin":
            subprocess.Popen(["open", "-a", app_name])
            return f"Launched {app_name}"
        else:
            subprocess.Popen([app_name])
            return f"Launched {app_name}"
    except Exception as e:
        return f"Could not launch {app_name}: {e}"


EXTRA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_clipboard",
            "description": "Get the current text content of the system clipboard.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_clipboard",
            "description": "Copy the given text to the system clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open a website URL in the default browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notify",
            "description": "Show a desktop notification to the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "message": {"type": "string"}
                },
                "required": ["title", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Launch an application by name (e.g. notepad, chrome, calculator).",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string"}
                },
                "required": ["app_name"]
            }
        }
    }
]

TOOL_FUNCTIONS = {
    "get_clipboard": get_clipboard,
    "set_clipboard": set_clipboard,
    "open_url": open_url,
    "notify": notify,
    "open_app": open_app,
}

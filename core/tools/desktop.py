"""
JagX Desktop Control Tools
Mouse, keyboard, window management.

JRILICENSE
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console

console = Console()

try:
    import pyautogui
    import pyperclip
    from pynput.keyboard import Key, Controller as KeyboardController
    from pynput.mouse import Button, Controller as MouseController
    HAS_CONTROL = True
except ImportError:
    HAS_CONTROL = False
    console.print("[yellow]Desktop control libraries not fully installed. Run: pip install pyautogui pynput pyperclip[/yellow]")


def move_mouse(x: int, y: int, duration: float = 0.3) -> str:
    """Move the mouse cursor to screen coordinates (x, y)."""
    if not HAS_CONTROL:
        return "Desktop control not available."
    try:
        pyautogui.moveTo(x, y, duration=duration)
        return f"Mouse moved to ({x}, {y})"
    except Exception as e:
        return f"Failed to move mouse: {e}"


def click(x: Optional[int] = None, y: Optional[int] = None, button: str = "left", clicks: int = 1) -> str:
    """Click at current position or at (x, y). button = left/right/middle"""
    if not HAS_CONTROL:
        return "Desktop control not available."
    try:
        if x is not None and y is not None:
            pyautogui.click(x=x, y=y, button=button, clicks=clicks)
            return f"Clicked {button} {clicks} time(s) at ({x}, {y})"
        else:
            pyautogui.click(button=button, clicks=clicks)
            return f"Clicked {button} {clicks} time(s) at current position"
    except Exception as e:
        return f"Click failed: {e}"


def type_text(text: str, interval: float = 0.02) -> str:
    """Type text using the keyboard."""
    if not HAS_CONTROL:
        return "Desktop control not available."
    try:
        pyautogui.write(text, interval=interval)
        return f"Typed: {text[:50]}{'...' if len(text) > 50 else ''}"
    except Exception as e:
        return f"Typing failed: {e}"


def press_key(key: str) -> str:
    """Press a single key or key combination (e.g. 'enter', 'ctrl+c', 'cmd+space')."""
    if not HAS_CONTROL:
        return "Desktop control not available."
    try:
        pyautogui.hotkey(*key.split('+'))
        return f"Pressed: {key}"
    except Exception as e:
        return f"Key press failed: {e}"


def get_mouse_position() -> str:
    """Get current mouse coordinates."""
    if not HAS_CONTROL:
        return "Desktop control not available."
    try:
        x, y = pyautogui.position()
        return f"Mouse is at ({x}, {y})"
    except Exception as e:
        return f"Could not get mouse position: {e}"


def screenshot(path: str = "screenshot.png") -> str:
    """Take a screenshot and save it."""
    if not HAS_CONTROL:
        return "Desktop control not available."
    try:
        img = pyautogui.screenshot()
        img.save(path)
        return f"Screenshot saved to {path}"
    except Exception as e:
        return f"Screenshot failed: {e}"


# Tool definitions
DESKTOP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "move_mouse",
            "description": "Move the mouse cursor to specific screen coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "duration": {"type": "number", "default": 0.3}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Perform a mouse click. Can click at current position or specific coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
                    "clicks": {"type": "integer", "default": 1}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text as if using the keyboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "interval": {"type": "number", "default": 0.02}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press a key or key combination (examples: enter, ctrl+c, alt+tab, cmd+space).",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_mouse_position",
            "description": "Get the current position of the mouse cursor.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "screenshot",
            "description": "Take a screenshot of the screen and save it to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "default": "screenshot.png"}
                },
                "required": []
            }
        }
    }
]

TOOL_FUNCTIONS = {
    "move_mouse": move_mouse,
    "click": click,
    "type_text": type_text,
    "press_key": press_key,
    "get_mouse_position": get_mouse_position,
    "screenshot": screenshot,
}

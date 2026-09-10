"""
JagX Desktop Control Tools
Reliable mouse, keyboard, and screen control for Windows.

JRILICENSE
"""

from __future__ import annotations

import time
from typing import Optional

from rich.console import Console

console = Console()

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    HAS_CONTROL = True
except Exception:
    HAS_CONTROL = False


def _ok() -> bool:
    return HAS_CONTROL


def move_mouse(x: int, y: int, duration: float = 0.25) -> str:
    if not _ok():
        return "Desktop control not available. Install pyautogui and rebuild."
    try:
        screen_w, screen_h = pyautogui.size()
        x = max(0, min(int(x), screen_w - 1))
        y = max(0, min(int(y), screen_h - 1))
        pyautogui.moveTo(x, y, duration=max(0.0, float(duration)))
        return f"Mouse moved to ({x}, {y})"
    except Exception as e:
        return f"Failed to move mouse: {e}"


def click(x: Optional[int] = None, y: Optional[int] = None, button: str = "left", clicks: int = 1) -> str:
    if not _ok():
        return "Desktop control not available."
    try:
        btn = button if button in ("left", "right", "middle") else "left"
        clicks = max(1, int(clicks))
        if x is not None and y is not None:
            pyautogui.click(x=int(x), y=int(y), button=btn, clicks=clicks)
            return f"Clicked {btn} x{clicks} at ({x}, {y})"
        pyautogui.click(button=btn, clicks=clicks)
        return f"Clicked {btn} x{clicks} at current position"
    except Exception as e:
        return f"Click failed: {e}"


def double_click(x: Optional[int] = None, y: Optional[int] = None) -> str:
    return click(x=x, y=y, button="left", clicks=2)


def type_text(text: str, interval: float = 0.02) -> str:
    if not _ok():
        return "Desktop control not available."
    try:
        import pyperclip
        old = None
        try:
            old = pyperclip.paste()
        except Exception:
            pass
        pyperclip.copy(text)
        time.sleep(0.05)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.05)
        if old is not None:
            try:
                pyperclip.copy(old)
            except Exception:
                pass
        return f"Typed/pasted text ({len(text)} chars)"
    except Exception:
        try:
            pyautogui.write(text, interval=interval)
            return f"Typed: {text[:60]}{'...' if len(text) > 60 else ''}"
        except Exception as e:
            return f"Typing failed: {e}"


def press_key(key: str) -> str:
    if not _ok():
        return "Desktop control not available."
    try:
        parts = [p.strip().lower() for p in key.replace("-", "+").split("+") if p.strip()]
        alias = {"control": "ctrl", "cmd": "win", "command": "win", "return": "enter", "esc": "escape"}
        parts = [alias.get(p, p) for p in parts]
        pyautogui.hotkey(*parts)
        return f"Pressed: {'+'.join(parts)}"
    except Exception as e:
        return f"Key press failed: {e}"


def get_mouse_position() -> str:
    if not _ok():
        return "Desktop control not available."
    try:
        x, y = pyautogui.position()
        w, h = pyautogui.size()
        return f"Mouse is at ({x}, {y}). Screen size: {w}x{h}"
    except Exception as e:
        return f"Could not get mouse position: {e}"


def screenshot(path: str = "screenshot.png") -> str:
    if not _ok():
        return "Desktop control not available."
    try:
        from pathlib import Path
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        img = pyautogui.screenshot()
        img.save(str(p))
        return f"Screenshot saved to {p.resolve()}"
    except Exception as e:
        return f"Screenshot failed: {e}"


def scroll_mouse(clicks: int = -3) -> str:
    if not _ok():
        return "Desktop control not available."
    try:
        pyautogui.scroll(int(clicks))
        return f"Scrolled {clicks}"
    except Exception as e:
        return f"Scroll failed: {e}"


def drag_mouse(x: int, y: int, duration: float = 0.4) -> str:
    if not _ok():
        return "Desktop control not available."
    try:
        pyautogui.dragTo(int(x), int(y), duration=float(duration), button="left")
        return f"Dragged to ({x}, {y})"
    except Exception as e:
        return f"Drag failed: {e}"


DESKTOP_TOOLS = [
    {"type": "function", "function": {"name": "move_mouse", "description": "Move the real mouse cursor to screen coordinates (x, y).", "parameters": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "duration": {"type": "number", "default": 0.25}}, "required": ["x", "y"]}}},
    {"type": "function", "function": {"name": "click", "description": "Click the mouse at x,y or current position.", "parameters": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"}, "clicks": {"type": "integer", "default": 1}}, "required": []}}},
    {"type": "function", "function": {"name": "double_click", "description": "Double-click at x,y or current position.", "parameters": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}}, "required": []}}},
    {"type": "function", "function": {"name": "type_text", "description": "Type or paste text into the focused window.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "interval": {"type": "number", "default": 0.02}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "press_key", "description": "Press a key or combination (enter, ctrl+c, alt+tab, win+e, escape).", "parameters": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}}},
    {"type": "function", "function": {"name": "get_mouse_position", "description": "Get current mouse position and screen size.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "screenshot", "description": "Capture the screen and save it.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "default": "screenshot.png"}}, "required": []}}},
    {"type": "function", "function": {"name": "scroll_mouse", "description": "Scroll mouse wheel. Negative = down.", "parameters": {"type": "object", "properties": {"clicks": {"type": "integer", "default": -3}}, "required": []}}},
    {"type": "function", "function": {"name": "drag_mouse", "description": "Drag mouse from current position to (x, y).", "parameters": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "duration": {"type": "number", "default": 0.4}}, "required": ["x", "y"]}}},
]

TOOL_FUNCTIONS = {
    "move_mouse": move_mouse,
    "click": click,
    "double_click": double_click,
    "type_text": type_text,
    "press_key": press_key,
    "get_mouse_position": get_mouse_position,
    "screenshot": screenshot,
    "scroll_mouse": scroll_mouse,
    "drag_mouse": drag_mouse,
}

"""JagX screen understanding tools.

Captures the Windows desktop and, when a local Ollama vision model is installed,
asks that model to describe/interpret what is visible. No passwords or keyboard
input are collected by this module.

JRILICENSE
"""
from __future__ import annotations

import base64
import os
from typing import Optional

import httpx

try:
    import pyautogui
    HAS_SCREEN = True
except ImportError:
    HAS_SCREEN = False


def _ollama_url() -> str:
    return os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def _find_vision_model(base_url: str, preferred: str = "") -> Optional[str]:
    try:
        r = httpx.get(f"{base_url}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m.get("name", "") for m in r.json().get("models", [])]
    except Exception:
        return None
    # Prefer explicit vision-capable models. qwen2.5 itself is text-only, so do
    # not pretend it can see an image. qwen2.5-vl is preferred when available.
    candidates = [preferred, "qwen2.5-vl", "qwen2.5-vl:latest", "llama3.2-vision", "llava", "llava:latest", "gemma3"]
    for candidate in candidates:
        if candidate and candidate in models:
            return candidate
    for name in models:
        low = name.lower()
        if any(tag in low for tag in ("vision", "vl", "llava")):
            return name
    return None


def understand_screen(prompt: str = "Describe the current screen. Identify the active application, important visible text, buttons, dialogs, errors, and useful UI elements. Do not guess text that is not visible.", save_path: str = "data/screen/latest.png") -> str:
    """Capture the screen and have a local Ollama vision model understand it."""
    if not HAS_SCREEN:
        return "Screen capture is unavailable. Install pyautogui."
    try:
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        image = pyautogui.screenshot()
        image.save(save_path)
    except Exception as e:
        return f"Screen capture failed: {e}"

    model = _find_vision_model(_ollama_url())
    if not model:
        return (f"Screenshot saved to {save_path}. No Ollama vision model is installed. "
                "Install a vision model such as qwen2.5-vl, llama3.2-vision, or llava in Ollama, "
                "then JagX can visually interpret the screen. Your qwen2.5 text model remains usable for normal chat.")

    try:
        with open(save_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")
        payload = {
            "model": model,
            "stream": False,
            "messages": [{"role": "user", "content": prompt, "images": [encoded]}],
            "options": {"temperature": 0.2},
        }
        r = httpx.post(f"{_ollama_url()}/api/chat", json=payload, timeout=120)
        r.raise_for_status()
        answer = r.json().get("message", {}).get("content", "").strip()
        if not answer:
            return f"The vision model returned no description. Screenshot saved to {save_path}."
        return f"Screen understanding (model: {model}):\n{answer}\n\nScreenshot saved to {save_path}."
    except Exception as e:
        return f"Vision analysis failed: {e}. Screenshot was saved to {save_path}."


def get_screen_size() -> str:
    """Return the current screen dimensions."""
    if not HAS_SCREEN:
        return "Screen capture is unavailable."
    try:
        width, height = pyautogui.size()
        return f"Screen size: {width}x{height}"
    except Exception as e:
        return f"Could not read screen size: {e}"


SCREEN_TOOLS = [
    {"type": "function", "function": {
        "name": "understand_screen",
        "description": "Capture the current Windows screen and visually understand its visible UI, text, dialogs, errors, and controls using an installed local Ollama vision model.",
        "parameters": {"type": "object", "properties": {
            "prompt": {"type": "string", "description": "What JagX should look for on the screen."},
            "save_path": {"type": "string", "default": "data/screen/latest.png"}
        }, "required": []}
    }},
    {"type": "function", "function": {
        "name": "get_screen_size",
        "description": "Get the current Windows screen width and height.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }}
]

TOOL_FUNCTIONS = {"understand_screen": understand_screen, "get_screen_size": get_screen_size}

"""
JagX on-screen game helpers
Open common game launchers / browser games and send keyboard/mouse input.
JRILICENSE
"""
from __future__ import annotations

import os
import subprocess
import time
import webbrowser
from typing import List

try:
    import pyautogui

    pyautogui.FAILSAFE = True
    HAS_GUI = True
except Exception:
    HAS_GUI = False


def _start(cmd: str) -> str:
    try:
        if os.name == "nt":
            os.system(f'start "" {cmd}')
        else:
            subprocess.Popen(cmd, shell=True)
        return f"Started {cmd}"
    except Exception as e:
        return str(e)


def open_steam() -> str:
    return _start("steam:") if os.name == "nt" else _start("steam")


def open_xbox_app() -> str:
    return _start("ms-xbox:") if os.name == "nt" else "Xbox app is Windows-only"


def open_epic() -> str:
    return _start("com.epicgames.launcher://") if os.name == "nt" else _start("epic")


def open_browser_game(url: str = "https://play2048.co/") -> str:
    webbrowser.open(url)
    return f"Opened game: {url}"


def open_pacman() -> str:
    return open_browser_game("https://www.google.com/search?q=pacman")


def open_dino_game() -> str:
    # Chrome dino needs offline; open a web clone
    return open_browser_game("https://chromedino.com/")


def open_2048() -> str:
    return open_browser_game("https://play2048.co/")


def open_snake() -> str:
    return open_browser_game("https://playsnake.org/")


def open_chess() -> str:
    return open_browser_game("https://www.chess.com/play/online")


def open_ludo() -> str:
    return open_browser_game("https://www.crazygames.com/game/ludo-king")


def game_press_key(key: str, times: int = 1) -> str:
    if not HAS_GUI:
        return "pyautogui missing"
    k = (key or "").strip().lower()
    n = max(1, min(int(times), 50))
    for _ in range(n):
        pyautogui.press(k)
        time.sleep(0.05)
    return f"Pressed {k} x{n}"


def game_hold_key(key: str, seconds: float = 0.5) -> str:
    if not HAS_GUI:
        return "pyautogui missing"
    k = (key or "").strip().lower()
    s = max(0.05, min(float(seconds), 5.0))
    pyautogui.keyDown(k)
    time.sleep(s)
    pyautogui.keyUp(k)
    return f"Held {k} for {s}s"


def game_combo(keys: str) -> str:
    """Press a sequence like 'up,up,down,down,left,right' or 'w,a,s,d'."""
    if not HAS_GUI:
        return "pyautogui missing"
    parts = [p.strip().lower() for p in (keys or "").split(",") if p.strip()]
    for k in parts[:40]:
        pyautogui.press(k)
        time.sleep(0.08)
    return f"Combo: {','.join(parts)}"


def game_click(x: int = 0, y: int = 0) -> str:
    if not HAS_GUI:
        return "pyautogui missing"
    if x or y:
        pyautogui.click(int(x), int(y))
        return f"Clicked {x},{y}"
    pyautogui.click()
    return "Clicked current position"


def game_move_mouse(x: int, y: int) -> str:
    if not HAS_GUI:
        return "pyautogui missing"
    pyautogui.moveTo(int(x), int(y), duration=0.2)
    return f"Mouse → {x},{y}"


def game_wasd_burst(direction: str = "w", taps: int = 5) -> str:
    return game_press_key(direction, taps)


def game_arrow_burst(direction: str = "up", taps: int = 5) -> str:
    return game_press_key(direction, taps)


def play_simple_loop(action: str = "space", times: int = 10, delay: float = 0.3) -> str:
    """Spam a key for simple endless runners / clickers."""
    if not HAS_GUI:
        return "pyautogui missing"
    n = max(1, min(int(times), 100))
    d = max(0.05, min(float(delay), 2.0))
    for _ in range(n):
        pyautogui.press(action)
        time.sleep(d)
    return f"Played {action} x{n}"


GAME_TOOLS = [
    {"type": "function", "function": {"name": "open_steam", "description": "Open Steam client.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_xbox_app", "description": "Open Xbox app.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_epic", "description": "Open Epic Games launcher.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_browser_game", "description": "Open any browser game URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "open_pacman", "description": "Open Pac-Man style web game.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_dino_game", "description": "Open Chrome dino clone.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_2048", "description": "Open 2048 game.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_snake", "description": "Open snake game.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_chess", "description": "Open chess.com play.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_ludo", "description": "Open Ludo online.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "game_press_key", "description": "Press a keyboard key in the active game.", "parameters": {"type": "object", "properties": {"key": {"type": "string"}, "times": {"type": "integer", "default": 1}}, "required": ["key"]}}},
    {"type": "function", "function": {"name": "game_hold_key", "description": "Hold a key briefly.", "parameters": {"type": "object", "properties": {"key": {"type": "string"}, "seconds": {"type": "number", "default": 0.5}}, "required": ["key"]}}},
    {"type": "function", "function": {"name": "game_combo", "description": "Press a comma-separated key combo.", "parameters": {"type": "object", "properties": {"keys": {"type": "string"}}, "required": ["keys"]}}},
    {"type": "function", "function": {"name": "game_click", "description": "Click on screen for games.", "parameters": {"type": "object", "properties": {"x": {"type": "integer", "default": 0}, "y": {"type": "integer", "default": 0}}, "required": []}}},
    {"type": "function", "function": {"name": "game_move_mouse", "description": "Move mouse for games.", "parameters": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}}, "required": ["x", "y"]}}},
    {"type": "function", "function": {"name": "game_wasd_burst", "description": "Tap WASD direction for movement.", "parameters": {"type": "object", "properties": {"direction": {"type": "string", "default": "w"}, "taps": {"type": "integer", "default": 5}}, "required": []}}},
    {"type": "function", "function": {"name": "game_arrow_burst", "description": "Tap arrow keys for games like 2048/snake.", "parameters": {"type": "object", "properties": {"direction": {"type": "string", "default": "up"}, "taps": {"type": "integer", "default": 5}}, "required": []}}},
    {"type": "function", "function": {"name": "play_simple_loop", "description": "Spam a key for simple auto-play (space jump etc).", "parameters": {"type": "object", "properties": {"action": {"type": "string", "default": "space"}, "times": {"type": "integer", "default": 10}, "delay": {"type": "number", "default": 0.3}}, "required": []}}},
]

TOOL_FUNCTIONS = {
    "open_steam": open_steam,
    "open_xbox_app": open_xbox_app,
    "open_epic": open_epic,
    "open_browser_game": open_browser_game,
    "open_pacman": open_pacman,
    "open_dino_game": open_dino_game,
    "open_2048": open_2048,
    "open_snake": open_snake,
    "open_chess": open_chess,
    "open_ludo": open_ludo,
    "game_press_key": game_press_key,
    "game_hold_key": game_hold_key,
    "game_combo": game_combo,
    "game_click": game_click,
    "game_move_mouse": game_move_mouse,
    "game_wasd_burst": game_wasd_burst,
    "game_arrow_burst": game_arrow_burst,
    "play_simple_loop": play_simple_loop,
}

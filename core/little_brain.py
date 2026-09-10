"""
JagX Little Brain — offline fallback that always works for core actions.
JRILICENSE
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parent.parent
BRAIN_DIR = ROOT / "data" / "little_brain"
BRAIN_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA_TINY = ["qwen2.5:0.5b", "tinydolphin", "tinyllama"]
GGUF_NAME = "little_brain.gguf"
GGUF_PATH = BRAIN_DIR / GGUF_NAME


class RuleBrain:
    """Instant offline commands — no model required."""

    PATTERNS = [
        (r"^(hi|hello|hey|good morning|good evening)\b", None, {}, "Hey! I'm JagX. Try: open notepad"),
        (r"\b(open|launch|start)\s+(notepad)\b", "open_app", {"app_name": "notepad"}, "Opening Notepad"),
        (r"\b(open|launch|start)\s+(calculator|calc)\b", "open_app", {"app_name": "calculator"}, "Opening Calculator"),
        (r"\b(open|launch)\s+(file\s*)?explorer\b", "open_app", {"app_name": "explorer"}, "Opening File Explorer"),
        (r"\b(open|launch|start)\s+(chrome|google chrome)\b", "open_app", {"app_name": "chrome"}, "Opening Chrome"),
        (r"\b(open|launch|start)\s+(edge)\b", "open_app", {"app_name": "edge"}, "Opening Edge"),
        (r"\b(open|launch)\s+(whatsapp)\b", "open_whatsapp_web", {}, "Opening WhatsApp"),
        (r"\b(take\s+)?screenshot\b", "screenshot_and_open", {}, "Taking screenshot"),
        (r"\bsystem briefing\b", "system_briefing", {}, "System briefing"),
        (r"\borganize downloads\b", "organize_downloads", {}, "Organizing downloads"),
        (r"\b(clean temp|cleanup)\b", "empty_temp_folder", {}, "Cleaning temp files"),
        (r"\b(quick )?virus scan\b", "quick_virus_scan", {}, "Starting virus scan"),
        (r"\bvirus status\b|\bdefender status\b", "virus_guard_report", {}, "Checking virus protection"),
        (r"\bprivacy scan\b", "privacy_guard_scan", {}, "Running privacy scan"),
        (r"\bcheck (my )?ip\b", "check_ip_reputation", {}, "Checking IP"),
        (r"\b(open )?2048\b|\bplay 2048\b", "open_2048", {}, "Opening 2048"),
        (r"\b(open )?dino\b|\bplay dino\b", "open_dino_game", {}, "Opening dino game"),
        (r"\bopen steam\b", "open_steam", {}, "Opening Steam"),
        (r"\bopen obs\b", "open_obs", {}, "Opening OBS"),
        (r"\bbuild (a )?website\b", "build_animated_website", {"title": "JagX Site", "headline": "Welcome", "subtitle": "Built by JagX"}, "Building website"),
    ]

    def interpret(self, text: str) -> Optional[Dict[str, Any]]:
        low = (text or "").strip().lower()
        for pat, name, args, say in self.PATTERNS:
            if re.search(pat, low):
                return {"tool": name, "args": dict(args), "say": say}
        return None

    def chat(self, text: str) -> str:
        hit = self.interpret(text)
        if hit and hit.get("tool") is None:
            return hit["say"]
        if hit:
            return hit["say"]
        return (
            "I'm here. Try: open notepad | take a screenshot | quick virus scan | privacy scan | open 2048"
        )


class LittleBrain:
    def __init__(self):
        self.rules = RuleBrain()
        self.mode = "rules"
        self.model_name = "little-brain-rules"
        self._llm = None

    def status(self) -> Dict[str, Any]:
        size_mb = round(GGUF_PATH.stat().st_size / (1024 * 1024), 1) if GGUF_PATH.exists() else 0
        return {"mode": self.mode, "model": self.model_name, "gguf_mb": size_mb, "ready": True}

    def ensure(self) -> Dict[str, Any]:
        self.mode = "rules"
        self.model_name = "little-brain-rules"
        return self.status()

    def respond(self, user_text: str) -> Dict[str, Any]:
        hit = self.rules.interpret(user_text)
        if hit and hit.get("tool") is None:
            return {"role": "assistant", "content": hit["say"]}
        if hit and hit.get("tool"):
            return {
                "role": "assistant",
                "content": hit["say"],
                "tool_calls": [
                    {
                        "id": "lb1",
                        "function": {"name": hit["tool"], "arguments": json.dumps(hit["args"])},
                    }
                ],
            }
        return {"role": "assistant", "content": self.rules.chat(user_text)}


_LITTLE: Optional[LittleBrain] = None


def get_little_brain() -> LittleBrain:
    global _LITTLE
    if _LITTLE is None:
        _LITTLE = LittleBrain()
        _LITTLE.ensure()
    return _LITTLE

"""
JagX Little Brain — offline fallback model (~100–200MB class).
Used when Ollama / larger models are unavailable.

Strategy:
1. Prefer a tiny Ollama tag if present (qwen2.5:0.5b / tinydolphin / etc.)
2. Otherwise download a small GGUF into data/little_brain/ and run via llama-cpp if installed
3. Last resort: deterministic rule brain for core PC actions (always works offline)

JRILICENSE
"""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
BRAIN_DIR = ROOT / "data" / "little_brain"
BRAIN_DIR.mkdir(parents=True, exist_ok=True)

# ~100-200MB class targets (best-effort; exact size depends on quant)
OLLAMA_TINY = ["qwen2.5:0.5b", "tinydolphin", "tinyllama", "gemma2:2b"]

# Optional small GGUF (user can replace file). SmolLM / tiny quants vary by host.
GGUF_NAME = "little_brain.gguf"
GGUF_PATH = BRAIN_DIR / GGUF_NAME


class RuleBrain:
    """Always-available offline brain for essential desktop commands."""

    PATTERNS = [
        (r"\b(open|launch|start)\s+(notepad)\b", "open_app", {"app_name": "notepad"}),
        (r"\b(open|launch|start)\s+(calculator|calc)\b", "open_app", {"app_name": "calculator"}),
        (r"\b(open|launch)\s+(file\s*)?explorer\b", "open_app", {"app_name": "explorer"}),
        (r"\b(open|launch|start)\s+(chrome|google chrome)\b", "open_app", {"app_name": "chrome"}),
        (r"\b(open|launch|start)\s+(edge)\b", "open_app", {"app_name": "edge"}),
        (r"\b(open|launch)\s+(whatsapp)\b", "open_app", {"app_name": "whatsapp"}),
        (r"\b(take\s+)?screenshot\b", "screenshot_and_open", {}),
        (r"\bsystem briefing\b|\bstatus\b", "system_briefing", {}),
        (r"\borganize downloads\b", "organize_downloads", {}),
        (r"\bclean temp\b|\bcleanup\b", "clean_temp_files", {}),
        (r"\bmute\b", "volume_mute_toggle", {}),
        (r"\bvolume up\b", "volume_up", {"steps": 4}),
        (r"\bvolume down\b", "volume_down", {"steps": 4}),
        (r"\bbattery\b", "battery_status", {}),
        (r"\bwi-?fi status\b", "wifi_status", {}),
        (r"\bmouse position\b", "get_mouse_position", {}),
    ]

    def interpret(self, text: str) -> Optional[Dict[str, Any]]:
        low = (text or "").strip().lower()
        for pat, name, args in self.PATTERNS:
            if re.search(pat, low):
                return {"tool": name, "args": dict(args), "say": f"Doing {name.replace('_', ' ')}"}
        return None

    def chat(self, text: str) -> str:
        hit = self.interpret(text)
        if hit:
            return json.dumps({"tool_calls": [{"name": hit["tool"], "arguments": hit["args"]}], "content": hit["say"]})
        return (
            "Little Brain online (offline mode). I can open apps, screenshot, volume, "
            "cleanup, organize downloads, battery, wifi, and system briefing. "
            "Try: open notepad | take a screenshot | system briefing"
        )


class LittleBrain:
    def __init__(self):
        self.rules = RuleBrain()
        self.mode = "rules"  # rules | ollama-tiny | gguf
        self.model_name = "little-brain-rules"
        self._llm = None

    def status(self) -> Dict[str, Any]:
        size_mb = 0
        if GGUF_PATH.exists():
            size_mb = round(GGUF_PATH.stat().st_size / (1024 * 1024), 1)
        return {
            "mode": self.mode,
            "model": self.model_name,
            "gguf_path": str(GGUF_PATH),
            "gguf_mb": size_mb,
            "ready": True,
        }

    def try_attach_ollama_tiny(self, base_url: str = "http://127.0.0.1:11434") -> bool:
        try:
            from core.setup_ai import list_models, pull_model, ollama_available

            if not ollama_available(base_url):
                return False
            installed = list_models(base_url)
            for tag in OLLAMA_TINY:
                if any(tag in m for m in installed):
                    self.mode = "ollama-tiny"
                    self.model_name = next(m for m in installed if tag in m)
                    return True
            # try pull smallest
            ok, _ = pull_model("qwen2.5:0.5b")
            if ok:
                self.mode = "ollama-tiny"
                self.model_name = "qwen2.5:0.5b"
                return True
        except Exception:
            return False
        return False

    def try_attach_gguf(self) -> bool:
        if not GGUF_PATH.exists():
            return False
        try:
            from llama_cpp import Llama  # type: ignore

            self._llm = Llama(model_path=str(GGUF_PATH), n_ctx=1024, verbose=False)
            self.mode = "gguf"
            self.model_name = GGUF_NAME
            return True
        except Exception:
            return False

    def ensure(self) -> Dict[str, Any]:
        if self.try_attach_ollama_tiny():
            return self.status()
        if self.try_attach_gguf():
            return self.status()
        self.mode = "rules"
        self.model_name = "little-brain-rules"
        return self.status()

    def respond(self, user_text: str) -> Dict[str, Any]:
        """Return a message dict compatible with agent tool loop expectations."""
        # Always try rule shortcuts first — instant offline actions
        hit = self.rules.interpret(user_text)
        if hit:
            return {
                "role": "assistant",
                "content": hit["say"],
                "tool_calls": [
                    {
                        "id": "little_brain_1",
                        "function": {
                            "name": hit["tool"],
                            "arguments": json.dumps(hit["args"]),
                        },
                    }
                ],
            }

        if self.mode == "gguf" and self._llm is not None:
            try:
                out = self._llm.create_chat_completion(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are JagX Little Brain. Be short. If user wants an action, say the action clearly.",
                        },
                        {"role": "user", "content": user_text},
                    ],
                    max_tokens=128,
                )
                content = out["choices"][0]["message"]["content"]
                return {"role": "assistant", "content": content}
            except Exception as e:
                return {"role": "assistant", "content": f"Little Brain GGUF error: {e}"}

        if self.mode == "ollama-tiny":
            try:
                import httpx

                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": "You are JagX. Be short and action-oriented."},
                        {"role": "user", "content": user_text},
                    ],
                    "stream": False,
                    "options": {"num_predict": 128, "temperature": 0.3},
                }
                with httpx.Client(timeout=60.0) as client:
                    r = client.post("http://127.0.0.1:11434/api/chat", json=payload)
                    r.raise_for_status()
                    msg = r.json().get("message") or {}
                    return {"role": "assistant", "content": msg.get("content") or "OK"}
            except Exception as e:
                return {"role": "assistant", "content": self.rules.chat(user_text) + f"\n(Note: tiny model error: {e})"}

        return {"role": "assistant", "content": self.rules.chat(user_text)}


_LITTLE: Optional[LittleBrain] = None


def get_little_brain() -> LittleBrain:
    global _LITTLE
    if _LITTLE is None:
        _LITTLE = LittleBrain()
        _LITTLE.ensure()
    return _LITTLE

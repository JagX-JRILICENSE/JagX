"""
JagX Personal Memory
Simple persistent memory so JagX remembers the user across sessions.

JRILICENSE
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from rich.console import Console

console = Console()

class Memory:
    def __init__(self, path: str = "./data/memory"):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.file = self.path / "memory.json"
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.file.exists():
            try:
                return json.loads(self.file.read_text(encoding="utf-8"))
            except Exception:
                return {"notes": [], "preferences": {}, "facts": []}
        return {"notes": [], "preferences": {}, "facts": []}

    def _save(self):
        self.file.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")

    def add_note(self, text: str, tags: Optional[List[str]] = None):
        """Add a free-form note / memory."""
        entry = {
            "text": text,
            "tags": tags or [],
            "timestamp": datetime.now().isoformat()
        }
        self.data.setdefault("notes", []).append(entry)
        self._save()

    def add_fact(self, fact: str):
        """Store a long-term fact about the user."""
        if fact not in self.data.get("facts", []):
            self.data.setdefault("facts", []).append(fact)
            self._save()

    def set_preference(self, key: str, value: Any):
        self.data.setdefault("preferences", {})[key] = value
        self._save()

    def get_preference(self, key: str, default=None):
        return self.data.get("preferences", {}).get(key, default)

    def get_context_summary(self, max_notes: int = 8) -> str:
        """Return a short text summary for the LLM system prompt / context."""
        parts = []

        facts = self.data.get("facts", [])
        if facts:
            parts.append("Known facts about the user:\n- " + "\n- ".join(facts[-10:]))

        prefs = self.data.get("preferences", {})
        if prefs:
            pref_str = ", ".join(f"{k}={v}" for k, v in prefs.items())
            parts.append(f"Preferences: {pref_str}")

        notes = self.data.get("notes", [])[-max_notes:]
        if notes:
            note_texts = [n["text"] for n in notes]
            parts.append("Recent notes:\n- " + "\n- ".join(note_texts))

        return "\n\n".join(parts) if parts else "No long-term memory yet."

    def clear(self):
        self.data = {"notes": [], "preferences": {}, "facts": []}
        self._save()

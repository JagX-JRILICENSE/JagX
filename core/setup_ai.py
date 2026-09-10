"""
JagX automatic local AI setup.
Ensures Ollama is reachable and a fast usable model is installed.

JRILICENSE
"""

from __future__ import annotations

import shutil
import subprocess
import time
from typing import Callable, List, Optional, Tuple

import httpx

PREFERRED_MODELS = [
    "qwen2.5:3b",
    "qwen2.5:1.5b",
    "llama3.2:3b",
    "llama3.2:1b",
    "phi3:mini",
    "qwen2.5",
]

# Avoid tiny coder-only tags as primary chat brain
AVOID_SUBSTRINGS = ["coder", "code", "embed"]


def ollama_available(base_url: str = "http://127.0.0.1:11434") -> bool:
    try:
        with httpx.Client(timeout=3.0) as client:
            r = client.get(f"{base_url.rstrip('/')}/api/tags")
            return r.status_code == 200
    except Exception:
        return False


def list_models(base_url: str = "http://127.0.0.1:11434") -> List[str]:
    try:
        with httpx.Client(timeout=8.0) as client:
            r = client.get(f"{base_url.rstrip('/')}/api/tags")
            r.raise_for_status()
            return [str(m.get("name", "")).strip() for m in r.json().get("models", []) if m.get("name")]
    except Exception:
        return []


def _is_good_chat_model(name: str) -> bool:
    low = name.lower()
    return not any(bad in low for bad in AVOID_SUBSTRINGS)


def choose_best_model(installed: List[str], preferred: str = "qwen2.5:3b") -> Optional[str]:
    if not installed:
        return None
    # Exact preferred
    if preferred in installed and _is_good_chat_model(preferred):
        return preferred
    for cand in PREFERRED_MODELS:
        if cand in installed and _is_good_chat_model(cand):
            return cand
    # Any qwen2.5 non-coder
    for name in installed:
        if name.lower().startswith("qwen2.5") and _is_good_chat_model(name):
            return name
    # Any non-coder model
    for name in installed:
        if _is_good_chat_model(name):
            return name
    return installed[0]


def pull_model(model: str, on_progress: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
    """Pull a model with the ollama CLI if available."""
    exe = shutil.which("ollama")
    if not exe:
        return False, "Ollama CLI not found on PATH. Install Ollama from https://ollama.com"

    if on_progress:
        on_progress(f"Downloading model {model}… this can take a few minutes")

    try:
        proc = subprocess.Popen(
            [exe, "pull", model],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        lines = []
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            lines.append(line)
            if on_progress:
                on_progress(line[:120])
        code = proc.wait(timeout=3600)
        if code == 0:
            return True, f"Model {model} installed"
        return False, "\n".join(lines[-8:]) or f"pull failed with code {code}"
    except Exception as e:
        return False, str(e)


def ensure_local_ai(
    base_url: str = "http://127.0.0.1:11434",
    preferred_model: str = "qwen2.5:3b",
    auto_pull: bool = True,
    on_progress: Optional[Callable[[str], None]] = None,
) -> dict:
    """
    Make sure a usable local model exists.
    Returns status dict: ok, model, message, available
    """
    def log(msg: str):
        if on_progress:
            on_progress(msg)

    if not ollama_available(base_url):
        return {
            "ok": False,
            "model": None,
            "available": [],
            "message": "Ollama is not running. Install/start Ollama from https://ollama.com then reopen JagX.",
        }

    installed = list_models(base_url)
    best = choose_best_model(installed, preferred_model)
    if best:
        log(f"Using local model: {best}")
        return {"ok": True, "model": best, "available": installed, "message": f"Ready with {best}"}

    if not auto_pull:
        return {
            "ok": False,
            "model": None,
            "available": installed,
            "message": "No suitable chat model found. Run: ollama pull qwen2.5:3b",
        }

    log(f"No good chat model found. Auto-installing {preferred_model}…")
    ok, msg = pull_model(preferred_model, on_progress=on_progress)
    if not ok:
        # fallback attempt
        log("Primary pull failed, trying llama3.2:3b…")
        ok2, msg2 = pull_model("llama3.2:3b", on_progress=on_progress)
        if not ok2:
            return {"ok": False, "model": None, "available": list_models(base_url), "message": msg2 or msg}

    time.sleep(1)
    installed = list_models(base_url)
    best = choose_best_model(installed, preferred_model)
    if best:
        return {"ok": True, "model": best, "available": installed, "message": f"Installed and ready: {best}"}
    return {"ok": False, "model": None, "available": installed, "message": "Model pull finished but model not detected. Restart Ollama."}

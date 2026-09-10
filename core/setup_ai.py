"""
JagX automatic local AI setup.
- Detect Ollama
- Try to install Ollama on Windows if missing
- Auto-pull a fast chat model

JRILICENSE
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Callable, List, Optional, Tuple

import httpx

PREFERRED_MODELS = [
    "qwen2.5:3b",
    "llama3.2:3b",
    "qwen2.5:1.5b",
    "llama3.2:1b",
    "phi3:mini",
    "qwen2.5",
]

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
    if preferred in installed and _is_good_chat_model(preferred):
        return preferred
    for cand in PREFERRED_MODELS:
        if cand in installed and _is_good_chat_model(cand):
            return cand
    for name in installed:
        if name.lower().startswith("qwen2.5") and _is_good_chat_model(name):
            return name
    for name in installed:
        if _is_good_chat_model(name):
            return name
    return installed[0]


def _find_ollama_exe() -> Optional[str]:
    found = shutil.which("ollama")
    if found:
        return found
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Ollama" / "ollama.exe",
        Path.home() / "AppData" / "Local" / "Programs" / "Ollama" / "ollama.exe",
    ]
    for p in candidates:
        if p.is_file():
            return str(p)
    return None


def try_start_ollama(on_progress: Optional[Callable[[str], None]] = None) -> bool:
    def log(m: str):
        if on_progress:
            on_progress(m)

    if ollama_available():
        return True

    exe = _find_ollama_exe()
    if not exe:
        return False

    log("Starting Ollama service…")
    try:
        subprocess.Popen([exe, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        try:
            # Windows app entry
            subprocess.Popen([exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            return False

    for _ in range(20):
        time.sleep(1)
        if ollama_available():
            log("Ollama is running")
            return True
    return False


def try_install_ollama_windows(on_progress: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
    """Download and run the official Ollama Windows installer (user may see UAC)."""
    def log(m: str):
        if on_progress:
            on_progress(m)

    if os.name != "nt":
        return False, "Auto-install of Ollama is only implemented for Windows."

    if _find_ollama_exe() or ollama_available():
        return True, "Ollama already present"

    url = "https://ollama.com/download/OllamaSetup.exe"
    log("Downloading Ollama installer…")
    try:
        dest = Path(tempfile.gettempdir()) / "OllamaSetup.exe"
        with httpx.Client(timeout=120.0, follow_redirects=True) as client:
            with client.stream("GET", url) as resp:
                resp.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in resp.iter_bytes():
                        f.write(chunk)
        log("Running Ollama installer (approve UAC if Windows asks)…")
        # Silent-ish install; may still prompt for elevation
        subprocess.run([str(dest), "/SILENT"], timeout=600, check=False)
        time.sleep(3)
        if try_start_ollama(on_progress):
            return True, "Ollama installed and started"
        if _find_ollama_exe():
            return True, "Ollama installed — start it from the Start menu if needed"
        return False, "Installer finished but Ollama was not detected. Open Ollama from the Start menu."
    except Exception as e:
        return False, f"Could not auto-install Ollama: {e}. Install manually from https://ollama.com"


def pull_model(model: str, on_progress: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
    exe = _find_ollama_exe() or shutil.which("ollama")
    if not exe:
        return False, "Ollama CLI not found"

    if on_progress:
        on_progress(f"Downloading model {model}…")

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
        return False, "\n".join(lines[-8:]) or f"pull failed ({code})"
    except Exception as e:
        return False, str(e)


def ensure_local_ai(
    base_url: str = "http://127.0.0.1:11434",
    preferred_model: str = "qwen2.5:3b",
    auto_pull: bool = True,
    auto_install_ollama: bool = True,
    on_progress: Optional[Callable[[str], None]] = None,
) -> dict:
    def log(msg: str):
        if on_progress:
            on_progress(msg)

    # 1) Running already?
    if not ollama_available(base_url):
        log("Ollama not detected — trying to start it…")
        if not try_start_ollama(on_progress):
            if auto_install_ollama:
                log("Attempting automatic Ollama install…")
                ok, msg = try_install_ollama_windows(on_progress)
                log(msg)
                if not ok and not ollama_available(base_url):
                    return {
                        "ok": False,
                        "model": None,
                        "available": [],
                        "message": msg + " | Manual install: https://ollama.com",
                    }
            else:
                return {
                    "ok": False,
                    "model": None,
                    "available": [],
                    "message": "Ollama is not running. Install from https://ollama.com",
                }

    if not ollama_available(base_url):
        try_start_ollama(on_progress)

    if not ollama_available(base_url):
        return {
            "ok": False,
            "model": None,
            "available": [],
            "message": "Ollama still not reachable. Open the Ollama app, then click Fix AI model.",
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
            "message": "No chat model found. Run: ollama pull qwen2.5:3b",
        }

    for model in [preferred_model, "llama3.2:3b", "qwen2.5:1.5b"]:
        log(f"Auto-installing model {model}…")
        ok, msg = pull_model(model, on_progress=on_progress)
        if ok:
            time.sleep(1)
            installed = list_models(base_url)
            best = choose_best_model(installed, preferred_model)
            if best:
                return {
                    "ok": True,
                    "model": best,
                    "available": installed,
                    "message": f"Installed and ready: {best}",
                }
        log(msg)

    return {
        "ok": False,
        "model": None,
        "available": list_models(base_url),
        "message": "Could not install a chat model automatically. Run: ollama pull qwen2.5:3b",
    }

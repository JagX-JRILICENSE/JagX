"""
JagX automatic local AI setup + higher-model preference.
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
    "jagx",
    "jagx:latest",
    "qwen2.5:14b",
    "qwen2.5:7b",
    "llama3.1:8b",
    "qwen2.5:3b",
    "qwen2.5:latest",
    "qwen2.5",
    "llama3.2:3b",
    "qwen2.5:1.5b",
    "qwen2.5:0.5b",
    "qwen2.5-coder:7b",
    "qwen2.5-coder:1.5b",
    "tinyllama",
]


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


def _score_model(name: str) -> int:
    low = name.lower()
    score = 0
    if "embed" in low:
        return -100
    if low == "jagx" or low.startswith("jagx:"):
        score += 100  # specialized JagX model wins
    if "qwen2.5" in low and "coder" not in low:
        score += 50
    if "qwen2.5" in low and "coder" in low:
        score += 25
    if "llama3" in low:
        score += 40
    if ":14b" in low:
        score += 25
    if ":7b" in low or ":8b" in low:
        score += 18
    if ":3b" in low:
        score += 10
    if ":1.5b" in low or ":0.5b" in low or ":1b" in low:
        score += 3
    return score


def choose_best_model(installed: List[str], preferred: str = "jagx") -> Optional[str]:
    if not installed:
        return None
    for name in installed:
        if name == preferred or name.startswith(preferred + ":"):
            return name
    for cand in PREFERRED_MODELS:
        if cand in installed:
            return cand
    ranked = sorted(installed, key=_score_model, reverse=True)
    return ranked[0] if ranked else None


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
    log("Starting Ollama…")
    try:
        subprocess.Popen([exe, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        try:
            subprocess.Popen([exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            return False
    for _ in range(25):
        time.sleep(1)
        if ollama_available():
            log("Ollama is running")
            return True
    return False


def try_install_ollama_windows(on_progress: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
    def log(m: str):
        if on_progress:
            on_progress(m)

    if os.name != "nt":
        return False, "Auto-install only on Windows."
    if _find_ollama_exe() or ollama_available():
        return True, "Ollama already present"
    url = "https://ollama.com/download/OllamaSetup.exe"
    log("Downloading Ollama installer…")
    try:
        dest = Path(tempfile.gettempdir()) / "OllamaSetup.exe"
        with httpx.Client(timeout=180.0, follow_redirects=True) as client:
            with client.stream("GET", url) as resp:
                resp.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in resp.iter_bytes():
                        f.write(chunk)
        log("Running installer (approve UAC if asked)…")
        subprocess.run([str(dest), "/SILENT"], timeout=600, check=False)
        time.sleep(4)
        if try_start_ollama(on_progress):
            return True, "Ollama installed and started"
        if _find_ollama_exe():
            return True, "Ollama installed"
        return False, "Installer ran but Ollama not detected"
    except Exception as e:
        return False, f"Auto-install failed: {e}"


def pull_model(model: str, on_progress: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
    exe = _find_ollama_exe() or shutil.which("ollama")
    if not exe:
        return False, "Ollama CLI not found"
    if on_progress:
        on_progress(f"Downloading {model}…")
    try:
        proc = subprocess.Popen([exe, "pull", model], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        assert proc.stdout is not None
        lines = []
        for line in proc.stdout:
            line = line.strip()
            if line:
                lines.append(line)
                if on_progress:
                    on_progress(line[:120])
        code = proc.wait(timeout=3600)
        if code == 0:
            return True, f"Installed {model}"
        return False, "\n".join(lines[-8:]) or f"pull failed ({code})"
    except Exception as e:
        return False, str(e)


def ensure_local_ai(
    base_url: str = "http://127.0.0.1:11434",
    preferred_model: str = "jagx",
    auto_pull: bool = True,
    auto_install_ollama: bool = True,
    specialize: bool = False,
    on_progress: Optional[Callable[[str], None]] = None,
) -> dict:
    def log(msg: str):
        if on_progress:
            on_progress(msg)

    if not ollama_available(base_url):
        log("Ollama not running — starting…")
        if not try_start_ollama(on_progress):
            if auto_install_ollama:
                ok, msg = try_install_ollama_windows(on_progress)
                log(msg)
                try_start_ollama(on_progress)
                if not ollama_available(base_url):
                    return {"ok": False, "model": None, "available": [], "message": msg}
            else:
                return {"ok": False, "model": None, "available": [], "message": "Start Ollama first"}

    # Optional: build specialized higher model for this PC
    if specialize and auto_pull:
        try:
            from core.train_jagx import install_best_jagx_model

            result = install_best_jagx_model(on_progress=on_progress, force_recreate=False)
            if result.get("ok") and result.get("model"):
                installed = list_models(base_url)
                return {
                    "ok": True,
                    "model": result["model"],
                    "available": installed,
                    "message": result.get("message") or f"Ready with {result['model']}",
                }
        except Exception as e:
            log(f"Specialization skipped: {e}")

    installed = list_models(base_url)
    log(f"Installed models: {', '.join(installed) if installed else '(none)'}")

    best = choose_best_model(installed, preferred_model)
    if best:
        log(f"Using model: {best}")
        return {"ok": True, "model": best, "available": installed, "message": f"Ready with {best}"}

    if not auto_pull:
        return {"ok": False, "model": None, "available": installed, "message": "No models installed"}

    for model in ["qwen2.5:7b", "qwen2.5:3b", "llama3.2:3b", "qwen2.5:0.5b"]:
        log(f"Pulling {model}…")
        ok, msg = pull_model(model, on_progress=on_progress)
        log(msg)
        if ok:
            time.sleep(1)
            installed = list_models(base_url)
            best = choose_best_model(installed, preferred_model)
            if best:
                return {"ok": True, "model": best, "available": installed, "message": f"Ready with {best}"}

    return {
        "ok": False,
        "model": None,
        "available": list_models(base_url),
        "message": "Could not prepare a model",
    }

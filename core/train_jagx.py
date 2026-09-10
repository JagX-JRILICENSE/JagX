"""
JagX model specialization on install.
Pull best base model and create specialized "jagx" via Ollama Modelfile.
JRILICENSE
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Optional, Tuple

from core.setup_ai import (
    choose_best_model,
    list_models,
    ollama_available,
    pull_model,
    try_start_ollama,
    _find_ollama_exe,
)

JAGX_SYSTEM = (
    "You are JagX, a premium personal AI that controls a Windows laptop. "
    "You were specialized for real actions: open apps, files, mouse, keyboard, screenshots, system status. "
    "When the user asks you to do something, CALL TOOLS. Do not only describe. "
    "Be short. Confirm in one line, then act. "
    "Never invent tool results. Never store bank PINs or auto-transfer money. "
    "You are JagX by JagX and JRILICENSE."
)

TIER_MODELS = {
    "high": ["qwen2.5:7b", "qwen2.5:3b", "llama3.2:3b"],
    "mid": ["qwen2.5:3b", "qwen2.5:1.5b", "llama3.2:3b"],
    "low": ["qwen2.5:1.5b", "qwen2.5:3b", "qwen2.5-coder:1.5b", "tinyllama"],
}


def detect_tier() -> str:
    try:
        import psutil

        gb = psutil.virtual_memory().total / (1024 ** 3)
        if gb >= 24:
            return "high"
        if gb >= 12:
            return "mid"
        return "low"
    except Exception:
        return "low"


def _write_modelfile(base_model: str) -> Path:
    # Avoid nested triple-quote breakage; single SYSTEM line is valid for Ollama
    safe_system = JAGX_SYSTEM.replace('"', "'")
    lines = [
        f"FROM {base_model}",
        f"SYSTEM {safe_system}",
        "PARAMETER temperature 0.3",
        "PARAMETER num_ctx 4096",
        "",
    ]
    path = Path(tempfile.gettempdir()) / "JagX.Modelfile"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def create_specialized_model(
    base_model: str,
    name: str = "jagx",
    on_progress: Optional[Callable[[str], None]] = None,
) -> Tuple[bool, str]:
    exe = _find_ollama_exe() or shutil.which("ollama")
    if not exe:
        return False, "Ollama CLI not found"

    def log(m: str):
        if on_progress:
            on_progress(m)

    modelfile = _write_modelfile(base_model)
    log(f"Creating specialized model '{name}' from {base_model}…")
    try:
        r = subprocess.run(
            [exe, "create", name, "-f", str(modelfile)],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if r.returncode == 0:
            return True, f"Specialized model ready: {name} (from {base_model})"
        err = (r.stderr or r.stdout or "create failed")[:500]
        return False, err
    except Exception as e:
        return False, str(e)


def install_best_jagx_model(
    on_progress: Optional[Callable[[str], None]] = None,
    force_recreate: bool = False,
) -> dict:
    def log(m: str):
        if on_progress:
            on_progress(m)

    if not ollama_available():
        log("Starting Ollama…")
        if not try_start_ollama(on_progress):
            return {
                "ok": False,
                "model": None,
                "tier": detect_tier(),
                "message": "Ollama not running. Open CMD and run: ollama serve",
            }

    tier = detect_tier()
    log(f"Hardware tier: {tier}")

    installed = list_models()
    log(f"Installed models: {', '.join(installed) if installed else '(none)'}")

    if not force_recreate and any(m == "jagx" or m.startswith("jagx:") for m in installed):
        name = "jagx" if "jagx" in installed else next(m for m in installed if m.startswith("jagx"))
        log(f"Using existing specialized model: {name}")
        return {"ok": True, "model": name, "tier": tier, "message": f"Ready with specialized {name}"}

    # Prefer non-coder models when possible
    base = None
    preferred = TIER_MODELS.get(tier, TIER_MODELS["low"])
    for candidate in preferred:
        for m in installed:
            if m == candidate or m.startswith(candidate):
                base = m
                break
        if base:
            break

    # If only coder model exists, still use it as base
    if not base and installed:
        # Prefer any qwen2.5 that is not only coder if available
        for m in installed:
            if "qwen" in m.lower() and "coder" not in m.lower():
                base = m
                break
        if not base:
            base = installed[0]

    if not base:
        for candidate in preferred:
            log(f"Pulling {candidate}…")
            ok, msg = pull_model(candidate, on_progress=on_progress)
            log(msg)
            if ok:
                installed = list_models()
                base = choose_best_model(installed, candidate) or candidate
                break

    if not base:
        installed = list_models()
        base = choose_best_model(installed, "qwen2.5:3b") if installed else None
    if not base and installed:
        base = installed[0]

    if not base:
        return {
            "ok": False,
            "model": None,
            "tier": tier,
            "message": "No model found. In CMD run: ollama pull qwen2.5:3b",
        }

    log(f"Base model: {base}")
    ok, msg = create_specialized_model(base, name="jagx", on_progress=on_progress)
    if ok:
        return {"ok": True, "model": "jagx", "tier": tier, "message": msg}

    log(f"Specialization failed ({msg}); using base {base}")
    return {
        "ok": True,
        "model": base,
        "tier": tier,
        "message": f"Using model {base} (specialization skipped: {msg[:120]})",
    }

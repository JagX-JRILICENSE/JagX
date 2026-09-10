"""
JagX model specialization on install.

True deep training from scratch is not practical during install on a laptop.
Instead we:
1. Detect RAM / hardware class
2. Pull the strongest sensible base model
3. Create a specialized Ollama model named "jagx" with a desktop-control system prompt
   and few-shot tool-use guidance (Modelfile)

JRILICENSE
"""

from __future__ import annotations

import os
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

JAGX_SYSTEM = '''You are JagX, a premium personal AI that controls a Windows laptop.
You were specialized for real actions: open apps, files, mouse, keyboard, screenshots, system status.
When the user asks you to do something, CALL TOOLS. Do not only describe.
Be short. Confirm in one line, then act.
Never invent tool results. Never store bank PINs or auto-transfer money.
You are JagX by JagX and JRILICENSE.'''

# Hardware tiers → preferred base model to pull
TIER_MODELS = {
    "high": ["qwen2.5:14b", "qwen2.5:7b", "llama3.1:8b"],
    "mid": ["qwen2.5:7b", "qwen2.5:3b", "llama3.2:3b"],
    "low": ["qwen2.5:3b", "qwen2.5:1.5b", "qwen2.5:0.5b", "tinyllama"],
}


def detect_tier() -> str:
    """Rough local hardware tier from RAM."""
    try:
        import psutil

        gb = psutil.virtual_memory().total / (1024 ** 3)
        if gb >= 24:
            return "high"
        if gb >= 12:
            return "mid"
        return "low"
    except Exception:
        return "mid"


def _write_modelfile(base_model: str) -> Path:
    content = f"""FROM {base_model}
SYSTEM """{JAGX_SYSTEM}"""
PARAMETER temperature 0.3
PARAMETER num_ctx 4096
"""
    path = Path(tempfile.gettempdir()) / "JagX.Modelfile"
    path.write_text(content, encoding="utf-8")
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
        return False, (r.stderr or r.stdout or "create failed")[:500]
    except Exception as e:
        return False, str(e)


def install_best_jagx_model(
    on_progress: Optional[Callable[[str], None]] = None,
    force_recreate: bool = False,
) -> dict:
    """
    Install / specialize the best JagX model for this machine.
    Returns {ok, model, tier, message}.
    """
    def log(m: str):
        if on_progress:
            on_progress(m)

    if not ollama_available():
        log("Starting Ollama…")
        if not try_start_ollama(on_progress):
            return {"ok": False, "model": None, "tier": detect_tier(), "message": "Ollama not running"}

    tier = detect_tier()
    log(f"Hardware tier: {tier}")

    installed = list_models()
    # If specialized jagx already exists and not forcing, use it
    if not force_recreate and any(m == "jagx" or m.startswith("jagx:") for m in installed):
        name = "jagx" if "jagx" in installed else next(m for m in installed if m.startswith("jagx"))
        log(f"Using existing specialized model: {name}")
        return {"ok": True, "model": name, "tier": tier, "message": f"Ready with specialized {name}"}

    # Choose / pull strongest base for tier
    base = None
    for candidate in TIER_MODELS.get(tier, TIER_MODELS["mid"]):
        if any(candidate == m or m.startswith(candidate.split(":")[0]) for m in installed):
            # prefer exact-ish match
            for m in installed:
                if m == candidate or candidate in m:
                    base = m
                    break
        if base:
            break

    if not base:
        for candidate in TIER_MODELS.get(tier, TIER_MODELS["mid"]):
            log(f"Pulling higher model {candidate} (best for your PC)…")
            ok, msg = pull_model(candidate, on_progress=on_progress)
            log(msg)
            if ok:
                installed = list_models()
                base = choose_best_model(installed, candidate) or candidate
                break

    if not base:
        installed = list_models()
        base = choose_best_model(installed, "qwen2.5:3b")
    if not base:
        return {"ok": False, "model": None, "tier": tier, "message": "No base model available to specialize"}

    log(f"Base model for specialization: {base}")
    ok, msg = create_specialized_model(base, name="jagx", on_progress=on_progress)
    if ok:
        return {"ok": True, "model": "jagx", "tier": tier, "message": msg}

    # Fall back to base itself
    log(f"Specialization failed ({msg}); using base {base}")
    return {"ok": True, "model": base, "tier": tier, "message": f"Using base model {base}"}

"""AI/local-model tools for JagX."""
from __future__ import annotations

import httpx


def ollama_status(base_url: str = "http://localhost:11434") -> str:
    """Check whether the local Ollama service is reachable."""
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(base_url.rstrip("/") + "/api/tags")
            r.raise_for_status()
            models = [m.get("name", "") for m in r.json().get("models", [])]
        return f"Ollama is online. Installed models: {', '.join(models) if models else 'none'}"
    except Exception as e:
        return f"Ollama is not reachable at {base_url}: {e}"


def list_local_models(base_url: str = "http://localhost:11434") -> str:
    """List models installed in the user's local Ollama instance."""
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(base_url.rstrip("/") + "/api/tags")
            r.raise_for_status()
            models = r.json().get("models", [])
        if not models:
            return "No local Ollama models are installed."
        lines = []
        for m in models:
            lines.append(f"- {m.get('name', 'unknown')} ({m.get('details', {}).get('parameter_size', 'size unknown')})")
        return "Installed local models:\n" + "\n".join(lines)
    except Exception as e:
        return f"Could not list local models: {e}"


AI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "ollama_status",
            "description": "Check local Ollama availability and installed models.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_local_models",
            "description": "List models installed in local Ollama so JagX can choose an available model.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
]

TOOL_FUNCTIONS = {
    "ollama_status": ollama_status,
    "list_local_models": list_local_models,
}

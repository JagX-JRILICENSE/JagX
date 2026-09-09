"""JagX LLM interface with automatic local Ollama model discovery."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx
from rich.console import Console

console = Console()


class LLMClient:
    """Unified LLM client for local Ollama and OpenAI-compatible APIs."""

    def __init__(self, provider: str = "ollama", model: str = "qwen2.5",
                 base_url: str = "http://localhost:11434", api_key: Optional[str] = None,
                 temperature: float = 0.7, system_prompt: Optional[str] = None):
        self.provider = provider.lower()
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("GROK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.temperature = temperature
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.endpoint = (f"{self.base_url}/v1/chat/completions" if self.provider == "ollama"
                         else f"{self.base_url}/chat/completions")
        if self.provider == "ollama":
            self._auto_select_model()

    def _auto_select_model(self) -> None:
        """Prefer qwen2.5 when installed; otherwise use configured/available model."""
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.get(f"{self.base_url}/api/tags")
                r.raise_for_status()
                installed = [m.get("name", "") for m in r.json().get("models", [])]
            if not installed:
                return
            configured = self.model
            candidates = [configured, "qwen2.5", "qwen2.5:latest", "llama3.1", "llama3.1:latest"]
            for candidate in candidates:
                if candidate in installed:
                    self.model = candidate
                    return
            self.model = installed[0]
        except Exception:
            # Ollama may start after JagX; the normal request path still reports a useful error.
            pass

    def refresh_model(self) -> str:
        """Refresh local models and select the best available configured model."""
        old = self.model
        self._auto_select_model()
        return f"AI model: {self.model} (previously {old})"

    def _default_system_prompt(self) -> str:
        return """You are JagX, a highly capable personal AI assistant running on the user's Windows laptop.

Your job is to turn natural-language requests into useful, safe actions.
Capabilities include conversation, web research, file and app operations, desktop control,
productivity, media, privacy checks, coding/project work, and local AI model awareness.

Behavior:
- Be direct, practical, and proactive.
- For multi-step tasks, make a plan and use the available tools in sequence.
- For coding/building tasks, inspect the project first, make focused changes, then run appropriate tests/build checks.
- Use web tools when current internet information is needed.
- Never claim an action succeeded unless a tool actually reports success.
- Ask for confirmation before destructive, sensitive, or security-impacting actions.
- Never steal, expose, guess, or store passwords, tokens, or private credentials.
- Do not perform hacking, credential theft, covert surveillance, malware, or unauthorized access.
- You are JagX, created by JagX and JRILICENSE.
"""

    def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None,
             tool_choice: str = "auto") -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "system", "content": self.system_prompt}] + messages,
            "temperature": self.temperature,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice
        headers = {"Content-Type": "application/json"}
        if self.api_key and self.provider != "ollama":
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(self.endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]
        except httpx.ConnectError:
            return {"role": "assistant", "content": "I cannot reach the local AI service. Please make sure Ollama is running."}
        except Exception as e:
            return {"role": "assistant", "content": f"Something went wrong with the model: {e}"}

    def simple_chat(self, user_message: str) -> str:
        return self.chat([{"role": "user", "content": user_message}]).get("content") or ""


def create_llm_from_config(config: Dict[str, Any]) -> LLMClient:
    llm_cfg = config.get("llm", {})
    return LLMClient(
        provider=llm_cfg.get("provider", "ollama"),
        model=llm_cfg.get("model", "qwen2.5"),
        base_url=llm_cfg.get("base_url", "http://localhost:11434"),
        temperature=llm_cfg.get("temperature", 0.7),
    )

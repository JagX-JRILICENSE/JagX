"""JagX LLM interface with reliable local Ollama support."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx
from rich.console import Console

console = Console()


class LLMClient:
    """Unified LLM client with a robust local Ollama path."""

    def __init__(
        self,
        provider: str = "ollama",
        model: str = "qwen2.5",
        base_url: str = "http://127.0.0.1:11434",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ):
        self.provider = provider.lower().strip()
        self.model = model.strip() or "qwen2.5"
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("GROK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.temperature = temperature
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.endpoint = (
            f"{self.base_url}/api/chat"
            if self.provider == "ollama"
            else f"{self.base_url}/chat/completions"
        )
        self.last_error = ""
        self.available_models: List[str] = []
        if self.provider == "ollama":
            self._auto_select_model()

    @staticmethod
    def _model_base(name: str) -> str:
        return name.split(":", 1)[0].strip().lower()

    def _auto_select_model(self) -> None:
        """Discover Ollama models and select the configured Qwen model reliably."""
        try:
            with httpx.Client(timeout=8.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                models = response.json().get("models", [])
            installed = [str(m.get("name", "")).strip() for m in models if m.get("name")]
            self.available_models = installed
            if not installed:
                self.last_error = "Ollama is reachable, but no models are installed."
                return

            configured = self.model
            candidates = [
                configured,
                "qwen2.5",
                "qwen2.5:latest",
                "qwen2.5:7b",
                "qwen2.5:3b",
                "qwen2.5:14b",
            ]
            for candidate in candidates:
                if candidate in installed:
                    self.model = candidate
                    return

            # Also match a Qwen 2.5 variant such as qwen2.5:7b when the exact tag differs.
            for installed_name in installed:
                if self._model_base(installed_name) == "qwen2.5":
                    self.model = installed_name
                    return

            # Last resort: use the first installed local model rather than failing silently.
            self.model = installed[0]
        except Exception as exc:
            self.last_error = f"Cannot reach Ollama at {self.base_url}: {exc}"

    def refresh_model(self) -> str:
        """Refresh local models and report the selected model and connection state."""
        old = self.model
        self.last_error = ""
        self._auto_select_model()
        if self.available_models:
            return f"AI model: {self.model} (previously {old}); Ollama connected. Available: {', '.join(self.available_models)}"
        return f"AI model: {self.model}; Ollama unavailable or has no installed models. {self.last_error}".strip()

    def status(self) -> Dict[str, Any]:
        """Return a local diagnostic snapshot without generating a model response."""
        if self.provider != "ollama":
            return {"provider": self.provider, "model": self.model, "reachable": None, "error": self.last_error}
        self._auto_select_model()
        return {
            "provider": "ollama",
            "base_url": self.base_url,
            "model": self.model,
            "reachable": bool(self.available_models),
            "available_models": self.available_models,
            "error": self.last_error,
        }

    def _default_system_prompt(self) -> str:
        return """You are JagX, a highly capable personal AI assistant running on the user's Windows laptop.

Your job is to turn natural-language requests into useful, safe actions.
Capabilities include conversation, web research, file and app operations, desktop control,
productivity, media, privacy checks, coding/project work, local AI model awareness, and screen understanding.

Behavior:
- Be direct, practical, and proactive.
- For multi-step tasks, make a plan and use the available tools in sequence.
- For coding/building tasks, inspect the project first, make focused changes, then run appropriate tests/build checks.
- Use web tools when current internet information is needed.
- When the user asks what is on the screen, asks where to click, reports a UI error, or needs help with a visible application, use understand_screen before acting when useful.
- Treat screen observations as evidence only: do not guess text, passwords, OTPs, or hidden UI state.
- Screen capture may contain private information; use it only to fulfill the user's request and do not save or repeat sensitive content unnecessarily.
- Never claim an action succeeded unless a tool actually reports success.
- Ask for confirmation before destructive, sensitive, or security-impacting actions.
- Never steal, expose, guess, or store passwords, tokens, or private credentials.
- Do not perform hacking, credential theft, covert surveillance, malware, or unauthorized access.
- You are JagX, created by JagX and JRILICENSE.
"""

    def _build_payload(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]], tool_choice: str) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "system", "content": self.system_prompt}] + messages,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        if tools:
            payload["tools"] = tools
            # Ollama's native API accepts auto/required/none-style tool choices on current versions.
            if tool_choice:
                payload["tool_choice"] = tool_choice
        return payload

    def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None,
             tool_choice: str = "auto") -> Dict[str, Any]:
        """Generate a response from Ollama, with a compatibility fallback for older servers."""
        if self.provider != "ollama":
            payload = {
                "model": self.model,
                "messages": [{"role": "system", "content": self.system_prompt}] + messages,
                "temperature": self.temperature,
                "stream": False,
            }
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = tool_choice
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            try:
                with httpx.Client(timeout=120.0) as client:
                    resp = client.post(self.endpoint, json=payload, headers=headers)
                    resp.raise_for_status()
                    return resp.json()["choices"][0]["message"]
            except Exception as exc:
                self.last_error = str(exc)
                return {"role": "assistant", "content": f"Something went wrong with the model: {exc}"}

        if not self.available_models:
            self._auto_select_model()
        if not self.available_models:
            return {
                "role": "assistant",
                "content": "I cannot reach Ollama or no local model is installed. Start Ollama and make sure qwen2.5 appears in `ollama list`.",
            }

        payload = self._build_payload(messages, tools, tool_choice)
        headers = {"Content-Type": "application/json"}
        try:
            with httpx.Client(timeout=180.0) as client:
                resp = client.post(self.endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                message = data.get("message")
                if not isinstance(message, dict):
                    raise RuntimeError(f"Ollama returned an unexpected response: {data}")
                self.last_error = ""
                return message
        except httpx.ConnectError:
            self.last_error = f"Cannot connect to Ollama at {self.base_url}"
            return {"role": "assistant", "content": "I cannot reach Ollama. Please start Ollama and try again."}
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            self.last_error = f"Ollama HTTP {exc.response.status_code}: {detail}"
            return {"role": "assistant", "content": f"Ollama returned an error ({exc.response.status_code}). Selected model: {self.model}. {detail}"}
        except Exception as exc:
            self.last_error = str(exc)
            return {"role": "assistant", "content": f"Ollama model error ({self.model}): {exc}"}

    def simple_chat(self, user_message: str) -> str:
        return self.chat([{"role": "user", "content": user_message}]).get("content") or ""


def create_llm_from_config(config: Dict[str, Any]) -> LLMClient:
    llm_cfg = config.get("llm", {})
    return LLMClient(
        provider=llm_cfg.get("provider", "ollama"),
        model=llm_cfg.get("model", "qwen2.5"),
        base_url=llm_cfg.get("base_url", "http://127.0.0.1:11434"),
        temperature=llm_cfg.get("temperature", 0.7),
    )

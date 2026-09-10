"""JagX LLM interface — local Ollama with warm-up and longer timeouts."""
from __future__ import annotations

import os
import threading
from typing import Any, Dict, List, Optional

import httpx
from rich.console import Console

console = Console()


class LLMClient:
    def __init__(
        self,
        provider: str = "ollama",
        model: str = "qwen2.5:3b",
        base_url: str = "http://127.0.0.1:11434",
        api_key: Optional[str] = None,
        temperature: float = 0.4,
        system_prompt: Optional[str] = None,
        timeout: float = 180.0,
    ):
        self.provider = provider.lower().strip()
        self.model = model.strip() or "qwen2.5:3b"
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("GROK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.temperature = temperature
        self.timeout = max(float(timeout), 180.0)
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.endpoint = (
            f"{self.base_url}/api/chat"
            if self.provider == "ollama"
            else f"{self.base_url}/chat/completions"
        )
        self.last_error = ""
        self.available_models: List[str] = []
        self._warmed = False
        if self.provider == "ollama":
            self._auto_select_model()
            threading.Thread(target=self.warm_up, daemon=True).start()

    @staticmethod
    def _model_base(name: str) -> str:
        return name.split(":", 1)[0].strip().lower()

    def _auto_select_model(self) -> None:
        try:
            from core.setup_ai import choose_best_model, list_models

            installed = list_models(self.base_url)
            self.available_models = installed
            if not installed:
                self.last_error = "Ollama reachable but no models installed"
                return
            # Prefer non-coder qwen2.5:3b over coder:1.5b
            best = choose_best_model(installed, self.model)
            if best:
                self.model = best
            # Explicit upgrade away from tiny coder when 3b exists
            names = {m.lower(): m for m in installed}
            if "qwen2.5:3b" in names:
                self.model = names["qwen2.5:3b"]
            elif any("qwen2.5:3b" in m.lower() for m in installed):
                self.model = next(m for m in installed if "qwen2.5:3b" in m.lower())
        except Exception as exc:
            self.last_error = str(exc)

    def warm_up(self) -> None:
        """Load model into RAM so first user message is faster."""
        if self.provider != "ollama" or self._warmed:
            return
        try:
            with httpx.Client(timeout=120.0) as client:
                client.post(
                    self.endpoint,
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "hi"}],
                        "stream": False,
                        "options": {"num_predict": 8, "temperature": 0},
                    },
                    headers={"Content-Type": "application/json"},
                )
            self._warmed = True
            self.last_error = ""
        except Exception as exc:
            self.last_error = f"warm-up: {exc}"

    def refresh_model(self) -> str:
        old = self.model
        self.last_error = ""
        self._auto_select_model()
        self._warmed = False
        threading.Thread(target=self.warm_up, daemon=True).start()
        if self.available_models:
            return f"AI model: {self.model} (was {old}). Available: {', '.join(self.available_models)}"
        return f"AI unavailable. {self.last_error}".strip()

    def status(self) -> Dict[str, Any]:
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
            "warmed": self._warmed,
        }

    def _default_system_prompt(self) -> str:
        return (
            "You are JagX, a fast personal Windows assistant by JagX and JRILICENSE.\n"
            "When the user asks you to DO something, call tools immediately.\n"
            "Be short. For greetings like hi/hello, reply briefly and friendly.\n"
            "Never pretend an action succeeded unless a tool result says so.\n"
        )

    def _trim_tools(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        if not tools:
            return tools
        if len(tools) <= 16:
            return tools
        priority = {
            "open_app", "run_shell", "list_directory", "read_file", "write_file",
            "move_mouse", "click", "type_text", "press_key", "screenshot",
            "screenshot_and_open", "web_search", "open_url", "system_briefing",
            "quick_virus_scan", "privacy_guard_scan", "generate_image",
        }
        essential = [t for t in tools if (t.get("function") or {}).get("name") in priority]
        if len(essential) >= 6:
            return essential[:16]
        return tools[:16]

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
    ) -> Dict[str, Any]:
        tools = self._trim_tools(tools)

        if self.provider != "ollama":
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
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(self.endpoint, json=payload, headers=headers)
                    resp.raise_for_status()
                    return resp.json()["choices"][0]["message"]
            except Exception as exc:
                self.last_error = str(exc)
                return {"role": "assistant", "content": f"Model error: {exc}"}

        if not self.available_models:
            self._auto_select_model()
        if not self.available_models:
            return {
                "role": "assistant",
                "content": "Local AI is not ready. Start Ollama and install a model.",
            }

        # Force preferred model if 3b is installed
        for m in self.available_models:
            if m.lower() == "qwen2.5:3b" or m.lower().startswith("qwen2.5:3b"):
                self.model = m
                break

        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": self.system_prompt}] + messages,
            "stream": False,
            "options": {"temperature": self.temperature, "num_predict": 256},
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(self.endpoint, json=payload, headers={"Content-Type": "application/json"})
                resp.raise_for_status()
                data = resp.json()
                message = data.get("message")
                if not isinstance(message, dict):
                    raise RuntimeError(str(data)[:300])
                self.last_error = ""
                self._warmed = True
                return message
        except httpx.ConnectError:
            self.last_error = f"Cannot connect to Ollama at {self.base_url}"
            return {"role": "assistant", "content": "Cannot reach Ollama. Keep Ollama running and try again."}
        except httpx.ReadTimeout:
            self.last_error = "timeout"
            # Retry once without tools (much faster)
            if tools:
                try:
                    simple = {
                        "model": self.model,
                        "messages": [{"role": "system", "content": self.system_prompt}] + messages,
                        "stream": False,
                        "options": {"temperature": 0.4, "num_predict": 128},
                    }
                    with httpx.Client(timeout=120.0) as client:
                        resp = client.post(self.endpoint, json=simple, headers={"Content-Type": "application/json"})
                        resp.raise_for_status()
                        message = resp.json().get("message")
                        if isinstance(message, dict):
                            self.last_error = ""
                            return message
                except Exception:
                    pass
            return {
                "role": "assistant",
                "content": (
                    f"Model is still loading ({self.model}). Wait 20 seconds and try again. "
                    "First answer after install can be slow."
                ),
            }
        except Exception as exc:
            self.last_error = str(exc)
            return {"role": "assistant", "content": f"Model error ({self.model}): {exc}"}

    def simple_chat(self, user_message: str) -> str:
        return self.chat([{"role": "user", "content": user_message}], tools=None).get("content") or ""


def create_llm_from_config(config: Dict[str, Any]) -> LLMClient:
    llm_cfg = config.get("llm", {})
    return LLMClient(
        provider=llm_cfg.get("provider", "ollama"),
        model=llm_cfg.get("model", "qwen2.5:3b"),
        base_url=llm_cfg.get("base_url", "http://127.0.0.1:11434"),
        temperature=llm_cfg.get("temperature", 0.4),
        timeout=float(llm_cfg.get("timeout", 180)),
    )

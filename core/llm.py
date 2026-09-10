"""JagX LLM interface — fast local Ollama path with auto model selection."""
from __future__ import annotations

import os
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
        timeout: float = 90.0,
    ):
        self.provider = provider.lower().strip()
        self.model = model.strip() or "qwen2.5:3b"
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("GROK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.temperature = temperature
        self.timeout = timeout
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
        try:
            from core.setup_ai import choose_best_model, list_models

            installed = list_models(self.base_url)
            self.available_models = installed
            if not installed:
                self.last_error = "Ollama reachable but no models installed"
                return
            best = choose_best_model(installed, self.model)
            if best:
                self.model = best
        except Exception as exc:
            self.last_error = str(exc)

    def refresh_model(self) -> str:
        old = self.model
        self.last_error = ""
        self._auto_select_model()
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
        }

    def _default_system_prompt(self) -> str:
        return (
            "You are JagX, a fast personal Windows assistant by JagX and JRILICENSE.\n"
            "When the user asks you to DO something, call tools immediately.\n"
            "Be short. Confirm the plan in one sentence, then use tools.\n"
            "Never pretend an action succeeded unless a tool result says so.\n"
            "For mouse/keyboard: use move_mouse, click, type_text, press_key.\n"
            "For apps/files: use open_app, run_shell, list_directory, etc.\n"
        )

    def _trim_tools(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        """Small models choke on huge tool lists — keep the most useful ones."""
        if not tools:
            return tools
        if len(tools) <= 24:
            return tools
        priority = {
            "open_app", "run_shell", "list_directory", "read_file", "write_file",
            "delete_path", "move_mouse", "click", "double_click", "type_text",
            "press_key", "get_mouse_position", "screenshot", "web_search", "fetch_url",
            "get_clipboard", "set_clipboard", "open_url", "notify",
            "check_camera_mic_usage", "get_system_info", "uninstall_app",
        }
        essential = [t for t in tools if (t.get("function") or {}).get("name") in priority]
        if len(essential) >= 8:
            return essential
        return tools[:24]

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
                "content": "Local AI is not ready. Start Ollama and install a model (JagX can auto-pull qwen2.5:3b).",
            }

        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": self.system_prompt}] + messages,
            "stream": False,
            "options": {"temperature": self.temperature, "num_predict": 512},
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
                return message
        except httpx.ConnectError:
            self.last_error = f"Cannot connect to Ollama at {self.base_url}"
            return {"role": "assistant", "content": "Cannot reach Ollama. Open the Ollama app and try again."}
        except httpx.ReadTimeout:
            self.last_error = "timeout"
            return {
                "role": "assistant",
                "content": (
                    f"Model timed out ({self.model}). "
                    "JagX will work better with qwen2.5:3b. Click 'Fix AI / Install Model' or run: ollama pull qwen2.5:3b"
                ),
            }
        except Exception as exc:
            self.last_error = str(exc)
            return {"role": "assistant", "content": f"Model error ({self.model}): {exc}"}

    def simple_chat(self, user_message: str) -> str:
        return self.chat([{"role": "user", "content": user_message}]).get("content") or ""


def create_llm_from_config(config: Dict[str, Any]) -> LLMClient:
    llm_cfg = config.get("llm", {})
    return LLMClient(
        provider=llm_cfg.get("provider", "ollama"),
        model=llm_cfg.get("model", "qwen2.5:3b"),
        base_url=llm_cfg.get("base_url", "http://127.0.0.1:11434"),
        temperature=llm_cfg.get("temperature", 0.4),
        timeout=float(llm_cfg.get("timeout", 90)),
    )

"""
JagX LLM Interface
Supports local Ollama + any OpenAI-compatible API (Grok, OpenAI, Claude via proxy, etc.)
Tool calling enabled.

JRILICENSE
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Callable

import httpx
from rich.console import Console

console = Console()

class LLMClient:
    """
    Unified LLM client for JagX.

    Priority:
    1. Local Ollama (default, private, free)
    2. OpenAI-compatible cloud endpoints (Grok, OpenAI, etc.)
    """

    def __init__(
        self,
        provider: str = "ollama",
        model: str = "llama3.1",
        base_url: str = "http://localhost:11434",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ):
        self.provider = provider.lower()
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("GROK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.temperature = temperature
        self.system_prompt = system_prompt or self._default_system_prompt()

        # For Ollama we use the /api/chat or OpenAI-compatible /v1/chat/completions
        if self.provider == "ollama":
            self.endpoint = f"{self.base_url}/v1/chat/completions"
        else:
            self.endpoint = f"{self.base_url}/chat/completions"

    def _default_system_prompt(self) -> str:
        return """You are JagX, a highly capable personal AI jaguar companion running on the user's laptop.

You have deep access to the local system and the internet (when the laptop is connected).

Your personality:
- Loyal, sharp, slightly wild like a jaguar
- Direct and useful
- Always protect the user and their machine

Rules:
1. When you need information from the internet, use the available web tools.
2. When you need to act on the computer (open files, control mouse, run commands, update software...), use the system tools.
3. Prefer local knowledge and tools first. Only go online when necessary.
4. Be careful with destructive actions. Confirm when unsure.
5. Always respond as JagX.

You are running with full local privileges when the laptop is connected to the network or hotspot.
"""

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
    ) -> Dict[str, Any]:
        """
        Send a chat completion request with optional tool calling.

        Returns the full response message from the model.
        """
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
                data = resp.json()

            choice = data["choices"][0]["message"]
            return choice

        except httpx.ConnectError:
            console.print("[red]Could not connect to LLM. Is Ollama running? (ollama serve)[/red]")
            return {"role": "assistant", "content": "I cannot reach the local model. Please make sure Ollama is running."}
        except Exception as e:
            console.print(f"[red]LLM Error:[/red] {e}")
            return {"role": "assistant", "content": f"Something went wrong with the model: {e}"}

    def simple_chat(self, user_message: str) -> str:
        """Quick one-shot chat without tools."""
        result = self.chat([{"role": "user", "content": user_message}])
        return result.get("content") or ""


def create_llm_from_config(config: Dict[str, Any]) -> LLMClient:
    """Helper to create LLMClient from settings.yaml"""
    llm_cfg = config.get("llm", {})
    return LLMClient(
        provider=llm_cfg.get("provider", "ollama"),
        model=llm_cfg.get("model", "llama3.1"),
        base_url=llm_cfg.get("base_url", "http://localhost:11434"),
        temperature=llm_cfg.get("temperature", 0.7),
    )

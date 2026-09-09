"""
JagX Agent - The brain of the jaguar.
Full tool-calling agent with internet + local system access.

JRILICENSE
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console
from rich.markdown import Markdown

from core.llm import LLMClient, create_llm_from_config
from core.tools.web import WEB_TOOLS, TOOL_FUNCTIONS as WEB_FUNCS
from core.tools.system import SYSTEM_TOOLS, TOOL_FUNCTIONS as SYSTEM_FUNCS

console = Console()

class JagXAgent:
    """
    Main agent loop for JagX.

    - Uses local LLM (Ollama) by default
    - Can call web tools when internet/hotspot is available
    - Can control the local laptop (files, shell, etc.)
    """

    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.llm = create_llm_from_config(self.config)
        self.messages: List[Dict[str, Any]] = []
        self.running = False

        # Register all tools
        self.tool_functions = {**WEB_FUNCS, **SYSTEM_FUNCS}
        self.tool_definitions = WEB_TOOLS + SYSTEM_TOOLS

        console.print("[bold orange1]JagX Agent initialized[/bold orange1]")
        console.print(f"[dim]LLM: {self.llm.provider} / {self.llm.model}[/dim]")
        console.print(f"[dim]Tools loaded: {len(self.tool_definitions)}[/dim]")

    def _load_config(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Run a tool and return its output as string."""
        func = self.tool_functions.get(name)
        if not func:
            return f"Unknown tool: {name}"

        console.print(f"[cyan]→ Calling tool:[/cyan] {name}({arguments})")

        try:
            result = func(**arguments)
            return str(result)
        except TypeError as e:
            return f"Tool argument error: {e}"
        except Exception as e:
            return f"Tool execution error: {e}"

    def think(self, user_input: str) -> str:
        """
        Full agent loop with tool calling.
        The model can decide to call web_search, fetch_url, list_directory,
        run_shell, etc. as needed.
        """
        self.messages.append({"role": "user", "content": user_input})

        # Allow multiple rounds of tool calls
        max_rounds = 8
        for _ in range(max_rounds):
            response = self.llm.chat(
                messages=self.messages,
                tools=self.tool_definitions,
                tool_choice="auto",
            )

            # If the model wants to call tools
            tool_calls = response.get("tool_calls")
            if tool_calls:
                # Add the assistant message that requested tools
                self.messages.append(response)

                for call in tool_calls:
                    fn = call["function"]
                    name = fn["name"]
                    try:
                        args = json.loads(fn.get("arguments", "{}"))
                    except json.JSONDecodeError:
                        args = {}

                    result = self._execute_tool(name, args)

                    # Feed tool result back to the model
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": call.get("id", name),
                        "name": name,
                        "content": result,
                    })
                # Continue the loop so the model can see results and respond
                continue

            # Normal text response
            content = response.get("content") or ""
            self.messages.append({"role": "assistant", "content": content})
            return content

        return "I reached the maximum number of tool rounds. Please try a simpler request."

    def run(self):
        """Main interactive loop (text for now)."""
        self.running = True
        console.print("[green]JagX is now awake and listening...[/green]")
        console.print("[dim]Internet tools work when your laptop/hotspot has connection.[/dim]")
        console.print("[dim]Type your request or 'exit' to sleep. Ctrl+C also works.[/dim]\n")

        while self.running:
            try:
                user_input = input("[You] > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in {"exit", "quit", "stop", "sleep"}:
                    console.print("[yellow]JagX going to sleep...[/yellow]")
                    break

                with console.status("[bold orange1]JagX is thinking...[/bold orange1]", spinner="dots"):
                    response = self.think(user_input)

                console.print()
                console.print(f"[bold orange1]JagX[/bold orange1]:")
                console.print(Markdown(response))
                console.print()

            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")

        self.running = False
        console.print("[bold]JagX offline.[/bold]")


if __name__ == "__main__":
    agent = JagXAgent()
    agent.run()

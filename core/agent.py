"""
JagX Agent - The brain of the jaguar.
Full tool-calling agent with internet, local system, desktop control,
privacy guard, easy delete/uninstall, and personal memory.

Safety: Only asks for confirmation on high-risk / hacking-related actions.

JRILICENSE
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Confirm

from core.llm import create_llm_from_config
from core.memory import Memory
from core.tools.web import WEB_TOOLS, TOOL_FUNCTIONS as WEB_FUNCS
from core.tools.system import SYSTEM_TOOLS, TOOL_FUNCTIONS as SYSTEM_FUNCS
from core.tools.desktop import DESKTOP_TOOLS, TOOL_FUNCTIONS as DESKTOP_FUNCS
from core.tools.privacy import PRIVACY_TOOLS, TOOL_FUNCTIONS as PRIVACY_FUNCS

console = Console()

# Patterns that are considered high-risk / hacking-related → require confirmation
HIGH_RISK_PATTERNS = [
    r"hack", r"exploit", r"payload", r"metasploit", r"nmap", r"sqlmap",
    r"keylog", r"rat\b", r"backdoor", r"rootkit", r"c2\b", r"command.?and.?control",
    r"reverse.?shell", r"bind.?shell", r"privilege.?escalation",
    r"mimikatz", r"credential.?dump", r"password.?crack",
    r"ddos", r"botnet", r"ransomware",
    r"format\s+c:", r"rm\s+-rf\s+/", r"mkfs", r"dd\s+if=",
]

class JagXAgent:
    """
    Main agent loop for JagX.
    """

    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.llm = create_llm_from_config(self.config)
        self.memory = Memory(self.config.get("memory", {}).get("path", "./data/memory"))
        self.messages: List[Dict[str, Any]] = []
        self.running = False

        # Inject memory into system prompt
        memory_context = self.memory.get_context_summary()
        if memory_context and memory_context != "No long-term memory yet.":
            self.llm.system_prompt += f"\n\n### Personal Memory\n{memory_context}"

        # Register all tools
        self.tool_functions = {
            **WEB_FUNCS,
            **SYSTEM_FUNCS,
            **DESKTOP_FUNCS,
            **PRIVACY_FUNCS,
        }
        self.tool_definitions = WEB_TOOLS + SYSTEM_TOOLS + DESKTOP_TOOLS + PRIVACY_TOOLS

        console.print("[bold orange1]JagX Agent initialized[/bold orange1]")
        console.print(f"[dim]LLM: {self.llm.provider} / {self.llm.model}[/dim]")
        console.print(f"[dim]Tools loaded: {len(self.tool_definitions)}[/dim]")
        console.print("[dim]Safety: Confirmation only for high-risk / hacking-related actions[/dim]")

    def _load_config(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _is_high_risk(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Return True only if the action looks hacking-related or extremely destructive."""
        text_to_check = tool_name + " " + json.dumps(arguments).lower()

        for pattern in HIGH_RISK_PATTERNS:
            if re.search(pattern, text_to_check, re.IGNORECASE):
                return True

        # Extra check for run_shell
        if tool_name == "run_shell":
            cmd = arguments.get("command", "").lower()
            if any(re.search(p, cmd, re.IGNORECASE) for p in HIGH_RISK_PATTERNS):
                return True

        return False

    def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Run a tool, with selective confirmation only for high-risk actions."""
        func = self.tool_functions.get(name)
        if not func:
            return f"Unknown tool: {name}"

        # Selective safety
        if self._is_high_risk(name, arguments):
            console.print(f"[bold red]HIGH RISK ACTION DETECTED[/bold red]: {name}({arguments})")
            if not Confirm.ask("This looks related to hacking or highly destructive. Proceed?", default=False):
                return "Action cancelled by user (high-risk protection)."

        console.print(f"[cyan]→ Calling tool:[/cyan] {name}({arguments})")

        try:
            result = func(**arguments)
            return str(result)
        except TypeError as e:
            return f"Tool argument error: {e}"
        except Exception as e:
            return f"Tool execution error: {e}"

    def think(self, user_input: str) -> str:
        """Full agent loop with tool calling."""
        self.messages.append({"role": "user", "content": user_input})

        max_rounds = 10
        for _ in range(max_rounds):
            response = self.llm.chat(
                messages=self.messages,
                tools=self.tool_definitions,
                tool_choice="auto",
            )

            tool_calls = response.get("tool_calls")
            if tool_calls:
                self.messages.append(response)

                for call in tool_calls:
                    fn = call["function"]
                    name = fn["name"]
                    try:
                        args = json.loads(fn.get("arguments", "{}"))
                    except json.JSONDecodeError:
                        args = {}

                    result = self._execute_tool(name, args)

                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": call.get("id", name),
                        "name": name,
                        "content": result,
                    })
                continue

            content = response.get("content") or ""
            self.messages.append({"role": "assistant", "content": content})

            # Auto-save interesting things to memory (simple heuristic)
            if any(word in user_input.lower() for word in ["remember", "my name is", "i like", "i prefer", "note that"]):
                self.memory.add_note(user_input)

            return content

        return "I reached the maximum number of tool rounds. Please try a simpler request."

    def run(self):
        """Main interactive loop (text for now — voice coming next)."""
        self.running = True
        console.print("[green]JagX is now awake and listening...[/green]")
        console.print("[dim]Internet + full laptop control + privacy guard active.[/dim]")
        console.print("[dim]Confirmation only required for high-risk / hacking-related actions.[/dim]")
        console.print("[dim]Type your request or 'exit' to sleep.[/dim]\n")

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

"""
JagX Agent - The brain of the jaguar.

JRILICENSE
"""

from typing import Any, Dict, List
from rich.console import Console

console = Console()

class JagXAgent:
    """
    Main agent loop for JagX.

    Responsibilities:
    - Receive user intent (text or voice)
    - Call LLM with tools
    - Execute system actions (files, cursor, shell, apps...)
    - Speak responses
    - Maintain personal memory
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}
        self.tools = {}
        self.memory = None
        self.running = False
        console.print("[bold orange1]JagX Agent initialized[/bold orange1]")

    def register_tool(self, name: str, func):
        self.tools[name] = func

    def think(self, user_input: str) -> str:
        """
        Core reasoning step.
        Later this will call the LLM with tool definitions.
        """
        # Placeholder
        return f"JagX heard: {user_input}. Full tool-calling agent coming soon."

    def act(self, plan: str):
        """Execute planned actions."""
        pass

    def run(self):
        """Main always-on loop."""
        self.running = True
        console.print("[green]JagX is now awake and listening...[/green]")
        console.print("[dim]Say 'JagX' or type commands. Ctrl+C to stop.[/dim]\n")

        while self.running:
            try:
                # Temporary text interface until voice is ready
                user_input = input("[You] > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in {"exit", "quit", "stop", "sleep"}:
                    console.print("[yellow]JagX going to sleep...[/yellow]")
                    break

                response = self.think(user_input)
                console.print(f"[bold orange1]JagX[/bold orange1]: {response}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")

        self.running = False
        console.print("[bold]JagX offline.[/bold]")

if __name__ == "__main__":
    agent = JagXAgent()
    agent.run()

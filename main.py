#!/usr/bin/env python3
"""
JagX - Personal Jaguar AI Companion
Entry point.

JRILICENSE
"""

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from rich.console import Console
from rich.panel import Panel
from core.agent import JagXAgent

console = Console()

def print_banner():
    console.print(Panel.fit(
        "[bold orange1]JagX[/bold orange1] 🐆\n"
        "[dim]Personal Jaguar AI Companion[/dim]\n\n"
        "[yellow]JRILICENSE[/yellow]",
        border_style="orange1"
    ))

def main():
    print_banner()
    console.print("[bold green]JagX is starting...[/bold green]\n")

    agent = JagXAgent()
    agent.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]JagX shutting down...[/bold red]")
        sys.exit(0)

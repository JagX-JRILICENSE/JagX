"""
JagX Local System Tools
Gives the agent real access to the laptop filesystem and shell.

WARNING: These tools are powerful. Use confirmation mode in production.

JRILICENSE
"""

from __future__ import annotations

import os
import subprocess
import platform
from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console

console = Console()

def list_directory(path: str = ".") -> str:
    """List files and folders in a directory."""
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"Path does not exist: {p}"
        if not p.is_dir():
            return f"Not a directory: {p}"

        entries = []
        for item in sorted(p.iterdir()):
            kind = "DIR " if item.is_dir() else "FILE"
            size = f"{item.stat().st_size:,} bytes" if item.is_file() else ""
            entries.append(f"{kind}  {item.name}  {size}")

        return f"Contents of {p}:\n" + "\n".join(entries[:100])
    except Exception as e:
        return f"Error listing directory: {e}"


def read_file(path: str, max_chars: int = 15000) -> str:
    """Read the content of a text file."""
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"File not found: {p}"
        if not p.is_file():
            return f"Not a file: {p}"

        content = p.read_text(encoding="utf-8", errors="replace")
        if len(content) > max_chars:
            return content[:max_chars] + f"\n\n... [truncated, total {len(content)} chars]"
        return content
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to a file (creates or overwrites)."""
    try:
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} characters to {p}"
    except Exception as e:
        return f"Error writing file: {e}"


def run_shell(command: str, timeout: int = 60) -> str:
    """
    Execute a shell command on the local machine.
    Extremely powerful — use with care.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.expanduser("~"),
        )
        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
        output += f"Exit code: {result.returncode}"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s"
    except Exception as e:
        return f"Shell error: {e}"


def get_system_info() -> str:
    """Get basic information about the laptop."""
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "home": str(Path.home()),
        "cwd": str(Path.cwd()),
    }
    return json.dumps(info, indent=2)


import json

# Tool definitions for the LLM
SYSTEM_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and folders in a local directory on the laptop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (default: current)", "default": "."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a local text file on the laptop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Full or relative path to the file"},
                    "max_chars": {"type": "integer", "default": 15000}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file on the laptop with the given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path where to write the file"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Run a shell/terminal command on the local laptop. Very powerful. Use for installing packages, system updates, launching apps, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The full shell command to execute"},
                    "timeout": {"type": "integer", "default": 60}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Get basic information about the laptop (OS, home directory, etc.).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

TOOL_FUNCTIONS = {
    "list_directory": list_directory,
    "read_file": read_file,
    "write_file": write_file,
    "run_shell": run_shell,
    "get_system_info": get_system_info,
}

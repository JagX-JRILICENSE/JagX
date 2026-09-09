"""
JagX Local System Tools
Gives the agent real access to the laptop filesystem and shell.
Easy delete and uninstall helpers included.

JRILICENSE
"""

from __future__ import annotations

import json
import os
import shutil
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


def delete_path(path: str, recursive: bool = False) -> str:
    """
    Delete a file or folder easily.
    Set recursive=True to delete folders and everything inside.
    """
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"Path does not exist: {p}"

        if p.is_file() or p.is_symlink():
            p.unlink()
            return f"Deleted file: {p}"
        elif p.is_dir():
            if recursive:
                shutil.rmtree(p)
                return f"Deleted folder and all contents: {p}"
            else:
                # Only delete if empty
                p.rmdir()
                return f"Deleted empty folder: {p}"
        else:
            return f"Unknown path type: {p}"
    except Exception as e:
        return f"Delete failed: {e}"


def uninstall_app(app_name: str) -> str:
    """
    Attempt to uninstall an application by name.
    Works best on Windows (winget/choco) and Linux (apt/dnf/pacman).
    On macOS it tries common methods.
    """
    system = platform.system().lower()
    try:
        if system == "windows":
            # Prefer winget
            result = subprocess.run(
                ["winget", "uninstall", "--name", app_name, "--accept-source-agreements"],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                return f"Uninstalled via winget: {app_name}\n{result.stdout}"
            # Fallback to chocolatey if available
            result2 = subprocess.run(
                ["choco", "uninstall", app_name, "-y"],
                capture_output=True, text=True, timeout=120
            )
            return f"Winget result: {result.stdout or result.stderr}\nChoco result: {result2.stdout or result2.stderr}"

        elif system == "darwin":
            # Try brew if it's a brew package
            result = subprocess.run(
                ["brew", "uninstall", app_name],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                return f"Uninstalled via Homebrew: {app_name}"
            return f"Homebrew attempt: {result.stderr or result.stdout}\nOn macOS you may need to drag the app to Trash or use System Settings."

        else:  # Linux
            # Try common package managers
            for cmd in [
                ["sudo", "apt", "remove", "-y", app_name],
                ["sudo", "dnf", "remove", "-y", app_name],
                ["sudo", "pacman", "-R", "--noconfirm", app_name],
                ["sudo", "snap", "remove", app_name],
            ]:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
                if result.returncode == 0:
                    return f"Uninstalled with {' '.join(cmd)}: {app_name}\n{result.stdout}"
            return "Tried apt/dnf/pacman/snap. None succeeded. Try run_shell with the correct command."

    except Exception as e:
        return f"Uninstall failed: {e}"


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
            "name": "delete_path",
            "description": "Easily delete a file or folder. Use recursive=True to delete a folder and everything inside it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file or folder to delete"},
                    "recursive": {"type": "boolean", "description": "Delete folder contents too", "default": False}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "uninstall_app",
            "description": "Uninstall an application by name. Works with winget/choco (Windows), brew (macOS), apt/dnf/pacman/snap (Linux).",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the application to uninstall"}
                },
                "required": ["app_name"]
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
    "delete_path": delete_path,
    "uninstall_app": uninstall_app,
    "run_shell": run_shell,
    "get_system_info": get_system_info,
}

"""JagX Automation Tools — practical Windows/laptop automation helpers.

JRILICENSE
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import urllib.parse
import webbrowser
from pathlib import Path


def _path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def open_application(application: str, arguments: str = "") -> str:
    """Open an installed application, optionally with command-line arguments."""
    try:
        if os.name == "nt":
            command = f'start "" "{application}" {arguments}'.strip()
            subprocess.Popen(command, shell=True)
        elif platform.system() == "Darwin":
            cmd = ["open", "-a", application]
            if arguments:
                cmd += ["--args", *arguments.split()]
            subprocess.Popen(cmd)
        else:
            subprocess.Popen([application, *arguments.split()])
        return f"Opened application: {application}"
    except Exception as e:
        return f"Could not open application '{application}': {e}"


def close_application(application: str) -> str:
    """Close an application/process by executable name."""
    try:
        if os.name == "nt":
            result = subprocess.run(["taskkill", "/IM", application, "/T"], capture_output=True, text=True, timeout=30)
        else:
            result = subprocess.run(["pkill", "-TERM", "-x", application], capture_output=True, text=True, timeout=30)
        output = (result.stdout or result.stderr).strip()
        return output or f"Close request sent for: {application}"
    except Exception as e:
        return f"Could not close '{application}': {e}"


def open_file(path: str) -> str:
    """Open a file with the operating system's default associated application."""
    target = _path(path)
    if not target.exists():
        return f"File does not exist: {target}"
    try:
        if os.name == "nt":
            os.startfile(str(target))
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
        return f"Opened file: {target}"
    except Exception as e:
        return f"Could not open file '{target}': {e}"


def open_folder(path: str = "~") -> str:
    """Open a folder in the system file manager."""
    target = _path(path)
    if not target.exists() or not target.is_dir():
        return f"Folder does not exist: {target}"
    try:
        if os.name == "nt":
            os.startfile(str(target))
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
        return f"Opened folder: {target}"
    except Exception as e:
        return f"Could not open folder '{target}': {e}"


def create_folder(path: str) -> str:
    """Create a folder and any missing parent folders."""
    target = _path(path)
    try:
        target.mkdir(parents=True, exist_ok=True)
        return f"Folder ready: {target}"
    except Exception as e:
        return f"Could not create folder '{target}': {e}"


def copy_path(source: str, destination: str) -> str:
    """Copy a file or folder to a destination."""
    src, dst = _path(source), _path(destination)
    if not src.exists():
        return f"Source does not exist: {src}"
    try:
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        return f"Copied '{src}' to '{dst}'"
    except Exception as e:
        return f"Copy failed: {e}"


def move_path(source: str, destination: str) -> str:
    """Move or rename a file or folder."""
    src, dst = _path(source), _path(destination)
    if not src.exists():
        return f"Source does not exist: {src}"
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return f"Moved '{src}' to '{dst}'"
    except Exception as e:
        return f"Move failed: {e}"


def delete_path(path: str) -> str:
    """Permanently delete a file or folder. Agent confirmation is required."""
    target = _path(path)
    if not target.exists():
        return f"Path does not exist: {target}"
    try:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        return f"Deleted: {target}"
    except Exception as e:
        return f"Delete failed: {e}"


def search_files(query: str, root: str = "~", max_results: int = 50) -> str:
    """Find files/folders by name under a user-selected root."""
    base = _path(root)
    if not base.exists():
        return f"Search root does not exist: {base}"
    matches = []
    query_l = query.lower()
    try:
        for p in base.rglob("*"):
            if query_l in p.name.lower():
                matches.append(str(p))
                if len(matches) >= max_results:
                    break
        return (f"Found {len(matches)} matches:\n" + "\n".join(matches)) if matches else f"No files found matching '{query}'."
    except Exception as e:
        return f"File search failed: {e}"


def list_directory(path: str = "~", max_results: int = 100) -> str:
    """List files and folders in a directory."""
    base = _path(path)
    if not base.exists() or not base.is_dir():
        return f"Directory does not exist: {base}"
    try:
        entries = sorted(base.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        lines = [("[DIR] " if p.is_dir() else "[FILE] ") + p.name for p in entries[:max_results]]
        return f"Contents of {base}:\n" + ("\n".join(lines) if lines else "(empty)")
    except Exception as e:
        return f"Could not list directory: {e}"


def list_processes(filter_text: str = "", max_results: int = 80) -> str:
    """List running processes, optionally filtered by name."""
    try:
        if os.name == "nt":
            cmd = ["tasklist", "/FO", "CSV", "/NH"]
        else:
            cmd = ["ps", "-eo", "pid=,comm="]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        lines = result.stdout.splitlines()
        if filter_text:
            lines = [x for x in lines if filter_text.lower() in x.lower()]
        return "\n".join(lines[:max_results]) or "No matching processes found."
    except Exception as e:
        return f"Could not list processes: {e}"


def get_environment_variable(name: str) -> str:
    """Read a named environment variable without exposing the entire environment."""
    value = os.getenv(name)
    if value is None:
        return f"Environment variable '{name}' is not set."
    if any(token in name.lower() for token in ("key", "token", "secret", "password")):
        return f"Environment variable '{name}' exists, but its value is hidden for security."
    return f"{name}={value}"


def web_search_and_open(query: str) -> str:
    """Search the web in the default browser."""
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
    webbrowser.open(url)
    return f"Opened browser search for: {query}"


AUTOMATION_TOOLS = [
    {"type":"function","function":{"name":"open_application","description":"Open an installed application, optionally with arguments.","parameters":{"type":"object","properties":{"application":{"type":"string"},"arguments":{"type":"string","default":""}},"required":["application"]}}},
    {"type":"function","function":{"name":"close_application","description":"Close an application/process by executable name.","parameters":{"type":"object","properties":{"application":{"type":"string"}},"required":["application"]}}},
    {"type":"function","function":{"name":"open_file","description":"Open a file with its default Windows application.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
    {"type":"function","function":{"name":"open_folder","description":"Open a folder in the system file manager.","parameters":{"type":"object","properties":{"path":{"type":"string","default":"~"}},"required":[]}}},
    {"type":"function","function":{"name":"create_folder","description":"Create a folder and missing parent folders.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
    {"type":"function","function":{"name":"copy_path","description":"Copy a file or folder to a destination.","parameters":{"type":"object","properties":{"source":{"type":"string"},"destination":{"type":"string"}},"required":["source","destination"]}}},
    {"type":"function","function":{"name":"move_path","description":"Move or rename a file or folder.","parameters":{"type":"object","properties":{"source":{"type":"string"},"destination":{"type":"string"}},"required":["source","destination"]}}},
    {"type":"function","function":{"name":"delete_path","description":"Permanently delete a file or folder; user confirmation is required.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
    {"type":"function","function":{"name":"search_files","description":"Search a folder recursively for files or folders by name.","parameters":{"type":"object","properties":{"query":{"type":"string"},"root":{"type":"string","default":"~"},"max_results":{"type":"integer","default":50}},"required":["query"]}}},
    {"type":"function","function":{"name":"list_directory","description":"List files and folders in a directory.","parameters":{"type":"object","properties":{"path":{"type":"string","default":"~"},"max_results":{"type":"integer","default":100}},"required":[]}}},
    {"type":"function","function":{"name":"list_processes","description":"List running applications/processes, optionally filtered by name.","parameters":{"type":"object","properties":{"filter_text":{"type":"string","default":""},"max_results":{"type":"integer","default":80}},"required":[]}}},
    {"type":"function","function":{"name":"get_environment_variable","description":"Read one environment variable; sensitive variable values are automatically hidden.","parameters":{"type":"object","properties":{"name":{"type":"string"}},"required":["name"]}}},
    {"type":"function","function":{"name":"web_search_and_open","description":"Open a web search in the default browser.","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}},
]

TOOL_FUNCTIONS = {name: globals()[name] for name in [
    "open_application", "close_application", "open_file", "open_folder", "create_folder",
    "copy_path", "move_path", "delete_path", "search_files", "list_directory",
    "list_processes", "get_environment_variable", "web_search_and_open"
]}

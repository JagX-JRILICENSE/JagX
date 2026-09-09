"""JagX Automation Tools — practical Windows/laptop automation helpers.

JRILICENSE
"""
from __future__ import annotations

import os
import platform
import subprocess
import urllib.parse
import webbrowser
from pathlib import Path


def open_application(application: str) -> str:
    """Open an installed application by executable/name using the OS launcher."""
    try:
        if os.name == "nt":
            subprocess.Popen(["cmd", "/c", "start", "", application], shell=False)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", "-a", application])
        else:
            subprocess.Popen([application])
        return f"Opened application: {application}"
    except Exception as e:
        return f"Could not open application '{application}': {e}"


def open_url(url: str) -> str:
    """Open a website or URL in the default browser."""
    webbrowser.open(url)
    return f"Opened URL: {url}"


def search_files(query: str, root: str = "~", max_results: int = 50) -> str:
    """Find files/folders by name under a user-selected root."""
    base = Path(root).expanduser().resolve()
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
    {"type":"function","function":{"name":"open_application","description":"Open an installed application on the user's computer.","parameters":{"type":"object","properties":{"application":{"type":"string"}},"required":["application"]}}},
    {"type":"function","function":{"name":"open_url","description":"Open a website or URL in the default browser.","parameters":{"type":"object","properties":{"url":{"type":"string"}},"required":["url"]}}},
    {"type":"function","function":{"name":"search_files","description":"Search the user's selected folder for files or folders by name.","parameters":{"type":"object","properties":{"query":{"type":"string"},"root":{"type":"string","default":"~"},"max_results":{"type":"integer","default":50}},"required":["query"]}}},
    {"type":"function","function":{"name":"list_processes","description":"List running applications/processes, optionally filtered by name.","parameters":{"type":"object","properties":{"filter_text":{"type":"string","default":""},"max_results":{"type":"integer","default":80}},"required":[]}}},
    {"type":"function","function":{"name":"get_environment_variable","description":"Read one environment variable; sensitive variable values are automatically hidden.","parameters":{"type":"object","properties":{"name":{"type":"string"}},"required":["name"]}}},
    {"type":"function","function":{"name":"web_search_and_open","description":"Open a web search in the default browser.","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}},
]

TOOL_FUNCTIONS = {name: globals()[name] for name in [
    "open_application", "open_url", "search_files", "list_processes",
    "get_environment_variable", "web_search_and_open"
]}

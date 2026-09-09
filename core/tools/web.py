"""
JagX Web / Internet Tools
Allows the agent to gather information from the internet when the laptop is online (hotspot or any connection).

JRILICENSE
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import httpx
from rich.console import Console

console = Console()

# Simple DuckDuckGo HTML search (no API key needed)
DDG_URL = "https://html.duckduckgo.com/html/"

def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web and return summarized results.
    Works whenever the laptop has internet (hotspot, Wi-Fi, etc.).
    """
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            resp = client.post(
                DDG_URL,
                data={"q": query, "b": ""},
                headers={"User-Agent": "Mozilla/5.0 (compatible; JagX/0.1)"},
            )
            resp.raise_for_status()
            html = resp.text

        # Very light parsing (good enough for agent use)
        results = []
        # DuckDuckGo HTML results contain class="result__a"
        import re
        links = re.findall(r'class="result__a"[^>]*href="(.*?)"[^>]*>(.*?)</a>', html, re.DOTALL)

        for i, (url, title) in enumerate(links[:max_results]):
            title = re.sub(r"<.*?>", "", title).strip()
            results.append(f"{i+1}. {title}\n   {url}")

        if not results:
            return f"No results found for: {query}"

        return f"Web search results for '{query}':\n\n" + "\n\n".join(results)

    except Exception as e:
        return f"Web search failed (is the laptop online?): {e}"


def fetch_url(url: str, max_chars: int = 8000) -> str:
    """
    Fetch the text content of a webpage.
    Useful after searching when JagX needs more details.
    """
    try:
        with httpx.Client(timeout=25.0, follow_redirects=True) as client:
            resp = client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; JagX/0.1)"},
            )
            resp.raise_for_status()
            text = resp.text

        # Strip scripts/styles roughly
        import re
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text[:max_chars] + ("..." if len(text) > max_chars else "")

    except Exception as e:
        return f"Failed to fetch {url}: {e}"


# Tool definitions in OpenAI format for the LLM
WEB_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the internet for current information. Use this when you need facts, news, documentation, or anything not in your training data. Works only when the laptop has internet access (hotspot, Wi-Fi, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results to return (default 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": "Download and extract the main text content from a specific URL. Use after web_search when you need the full page content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Full URL to fetch"
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters to return",
                        "default": 8000
                    }
                },
                "required": ["url"]
            }
        }
    }
]

TOOL_FUNCTIONS = {
    "web_search": web_search,
    "fetch_url": fetch_url,
}

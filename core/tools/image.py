"""JagX Image generation — ComfyUI local + free Pollinations web fallback."""
from __future__ import annotations

import json
import random
import time
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path


def _config():
    try:
        import yaml

        with open("config/settings.yaml", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _cfg():
    return _config().get("image_generation", {})


def _output_dir():
    p = Path(_cfg().get("output_dir", "./data/generated_images"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _url():
    return str(_cfg().get("comfyui_url", "http://127.0.0.1:8188")).rstrip("/")


def _workflow_path():
    return Path(_cfg().get("workflow_path", "./config/image_workflow.json"))


def _request(path, data=None, method="GET"):
    payload = None if data is None else json.dumps(data).encode("utf-8")
    req = urllib.request.Request(_url() + path, data=payload, method=method)
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def _reachable():
    try:
        _request("/system_stats")
        return True
    except Exception:
        return False


def _replace(value, replacements):
    if isinstance(value, dict):
        return {k: _replace(v, replacements) for k, v in value.items()}
    if isinstance(value, list):
        return [_replace(v, replacements) for v in value]
    if isinstance(value, str):
        for key, replacement in replacements.items():
            value = value.replace(key, str(replacement))
        return value
    return value


def image_status() -> str:
    if _reachable():
        return f"ComfyUI ready at {_url()}"
    return "ComfyUI offline — will use free Pollinations web image generation."


def generate_image_pollinations(prompt: str, open_browser: bool = True) -> str:
    """Free online image generation via Pollinations (no API key)."""
    if not (prompt or "").strip():
        return "Prompt required"
    q = urllib.parse.quote(prompt.strip()[:300])
    url = f"https://image.pollinations.ai/prompt/{q}?width=1024&height=1024&nologo=true"
    # Also try to save a copy
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JagX/1.0"})
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read()
        target = _output_dir() / f"pollinations_{int(time.time())}.jpg"
        target.write_bytes(data)
        if open_browser:
            webbrowser.open(target.as_uri())
        return f"IMAGE_GENERATED: {target}"
    except Exception as e:
        if open_browser:
            webbrowser.open(url)
        return f"Opened image URL (download failed: {e}): {url}"


def generate_image(prompt: str, size: str = "1024x1024", quality: str = "auto") -> str:
    """Prefer local ComfyUI; fall back to free Pollinations."""
    if not (prompt or "").strip():
        return "IMAGE_GENERATION_ERROR: prompt is required."

    if _reachable():
        workflow_path = _workflow_path()
        if workflow_path.exists():
            try:
                workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
                try:
                    width, height = [int(x) for x in size.lower().split("x", 1)]
                except Exception:
                    width, height = 1024, 1024
                seed = random.randint(1, 2**63 - 1)
                replacements = {
                    "__PROMPT__": prompt,
                    "__NEGATIVE_PROMPT__": "",
                    "__WIDTH__": width,
                    "__HEIGHT__": height,
                    "__SEED__": seed,
                    "__FILENAME_PREFIX__": "JagX",
                }
                workflow = _replace(workflow, replacements)
                result = _request("/prompt", {"prompt": workflow, "client_id": "JagX"}, method="POST")
                prompt_id = result.get("prompt_id")
                if not prompt_id:
                    return generate_image_pollinations(prompt)
                deadline = time.time() + 300
                while time.time() < deadline:
                    time.sleep(1.5)
                    try:
                        history = _request("/history/" + urllib.parse.quote(prompt_id, safe=""))
                    except Exception:
                        continue
                    item = history.get(prompt_id) or {}
                    outputs = item.get("outputs") or {}
                    for node_output in outputs.values():
                        for image in node_output.get("images", []) or []:
                            filename = image.get("filename")
                            subfolder = image.get("subfolder", "")
                            img_type = image.get("type", "output")
                            if not filename:
                                continue
                            query = urllib.parse.urlencode(
                                {"filename": filename, "subfolder": subfolder, "type": img_type}
                            )
                            with urllib.request.urlopen(_url() + "/view?" + query, timeout=30) as response:
                                data = response.read()
                            target = _output_dir() / Path(filename).name
                            if target.exists():
                                target = _output_dir() / f"JagX_{int(time.time())}_{target.name}"
                            target.write_bytes(data)
                            webbrowser.open(target.as_uri())
                            return f"IMAGE_GENERATED: {target}"
                return generate_image_pollinations(prompt)
            except Exception:
                return generate_image_pollinations(prompt)

    return generate_image_pollinations(prompt)


def open_image_studio_online() -> str:
    webbrowser.open("https://www.bing.com/images/create")
    return "Opened Bing Image Creator (sign in with Microsoft account)"


IMAGE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "Generate an image from a text prompt (ComfyUI or free Pollinations).",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "size": {"type": "string", "default": "1024x1024"},
                    "quality": {"type": "string", "default": "auto"},
                },
                "required": ["prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_image_pollinations",
            "description": "Generate image with free Pollinations API.",
            "parameters": {
                "type": "object",
                "properties": {"prompt": {"type": "string"}, "open_browser": {"type": "boolean", "default": True}},
                "required": ["prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "image_status",
            "description": "Check image generation backend status.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_image_studio_online",
            "description": "Open Bing Image Creator in the browser.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

TOOL_FUNCTIONS = {
    "generate_image": generate_image,
    "generate_image_pollinations": generate_image_pollinations,
    "image_status": image_status,
    "open_image_studio_online": open_image_studio_online,
}

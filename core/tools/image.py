"""JagX Image Studio local ComfyUI backend."""
from __future__ import annotations
import json
import random
import time
import urllib.parse
import urllib.request
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


def image_status():
    if not _cfg().get("enabled", True):
        return "Image Studio is disabled."
    workflow = _workflow_path()
    if _reachable():
        if workflow.exists():
            return f"Image Studio ready: local ComfyUI detected at {_url()} with workflow {workflow}."
        return f"ComfyUI is running at {_url()}, but no workflow was found at {workflow}. Export a ComfyUI API workflow there."
    return "Image Studio is enabled for free local generation, but ComfyUI is not running."


def generate_image(prompt: str, size: str = "1024x1024", quality: str = "auto"):
    """Submit a ComfyUI API workflow and save its first generated image locally."""
    if not prompt.strip():
        return "IMAGE_GENERATION_ERROR: prompt is required."
    if not _reachable():
        return "IMAGE_GENERATION_ERROR: local ComfyUI backend is unavailable."
    workflow_path = _workflow_path()
    if not workflow_path.exists():
        return f"IMAGE_GENERATION_ERROR: export a ComfyUI API workflow to {workflow_path}."
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
            return f"IMAGE_GENERATION_ERROR: ComfyUI did not return a prompt id: {result}"
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
                    query = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": img_type})
                    with urllib.request.urlopen(_url() + "/view?" + query, timeout=30) as response:
                        data = response.read()
                    target = _output_dir() / Path(filename).name
                    if target.exists():
                        target = _output_dir() / f"JagX_{int(time.time())}_{target.name}"
                    target.write_bytes(data)
                    return f"IMAGE_GENERATED: {target}"
        return "IMAGE_GENERATION_ERROR: generation timed out before ComfyUI returned an image."
    except Exception as exc:
        return f"IMAGE_GENERATION_ERROR: {exc}"


IMAGE_TOOLS = [
    {"type": "function", "function": {"name": "generate_image", "description": "Create an original image using JagX's free local ComfyUI backend and save it to the configured output folder.", "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}, "size": {"type": "string", "enum": ["1024x1024", "1536x1024", "1024x1536"], "default": "1024x1024"}, "quality": {"type": "string", "enum": ["auto", "low", "medium", "high"], "default": "auto"}}, "required": ["prompt"]}}},
    {"type": "function", "function": {"name": "image_status", "description": "Check local Image Studio and ComfyUI availability.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]
TOOL_FUNCTIONS = {"generate_image": generate_image, "image_status": image_status}

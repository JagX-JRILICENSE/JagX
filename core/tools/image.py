"""JagX image creation tools."""
from __future__ import annotations

import base64
import os
import time
from pathlib import Path


def _config():
    try:
        import yaml
        with open("config/settings.yaml", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _output_dir() -> Path:
    cfg = _config().get("image_generation", {})
    path = Path(cfg.get("output_dir", "./data/generated_images"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def image_status() -> str:
    """Report whether JagX's configured image-generation backend is ready."""
    cfg = _config().get("image_generation", {})
    if not cfg.get("enabled", True):
        return "Image generation is disabled in JagX configuration."
    provider = str(cfg.get("provider", "auto")).lower()
    key_present = bool(os.getenv("OPENAI_API_KEY"))
    if provider in {"auto", "openai"} and key_present:
        model = cfg.get("openai_model", "gpt-image-1")
        return f"Image Studio ready: OpenAI image generation is configured with model {model}. Output folder: {_output_dir()}"
    if provider == "openai":
        return "Image Studio is configured for OpenAI, but OPENAI_API_KEY is not set. Set it in the Windows environment and restart JagX."
    return "Image Studio is installed, but no image-generation provider is configured. Set image_generation.provider to openai and provide OPENAI_API_KEY."


def generate_image(prompt: str, size: str = "1024x1024", quality: str = "auto") -> str:
    """Generate an image from a prompt and save it locally without overwriting existing files."""
    if not prompt or not prompt.strip():
        return "IMAGE_GENERATION_ERROR: prompt is required."
    cfg = _config().get("image_generation", {})
    if not cfg.get("enabled", True):
        return "IMAGE_GENERATION_ERROR: image generation is disabled in configuration."
    provider = str(cfg.get("provider", "auto")).lower()
    if provider not in {"auto", "openai"}:
        return f"IMAGE_GENERATION_ERROR: unsupported provider '{provider}'."
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "IMAGE_GENERATION_ERROR: OPENAI_API_KEY is not configured. Image Studio is installed and ready once an OpenAI API key is provided."

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        model = cfg.get("openai_model", "gpt-image-1")
        result = client.images.generate(model=model, prompt=prompt.strip(), size=size, quality=quality, n=1)
        item = result.data[0]
        if not getattr(item, "b64_json", None):
            return "IMAGE_GENERATION_ERROR: the image provider returned no image data."
        filename = f"jagx_{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time()*1000)%1000:03d}.png"
        output = _output_dir() / filename
        output.write_bytes(base64.b64decode(item.b64_json))
        if cfg.get("open_after_generate", False):
            try:
                os.startfile(str(output))
            except Exception:
                pass
        return f"IMAGE_GENERATED: {output.resolve()}"
    except Exception as exc:
        return f"IMAGE_GENERATION_ERROR: {exc}"


IMAGE_TOOLS = [
    {"type": "function", "function": {"name": "generate_image", "description": "Create an image from a natural-language prompt and save it locally. Use Image Studio for logos, illustrations, UI assets, concept art, backgrounds, and other original images.", "parameters": {"type": "object", "properties": {"prompt": {"type": "string", "description": "Detailed description of the desired image."}, "size": {"type": "string", "enum": ["1024x1024", "1536x1024", "1024x1536"], "default": "1024x1024"}, "quality": {"type": "string", "enum": ["auto", "low", "medium", "high"], "default": "auto"}}, "required": ["prompt"]}}},
    {"type": "function", "function": {"name": "image_status", "description": "Check whether JagX Image Studio has a configured image-generation provider.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]

TOOL_FUNCTIONS = {"generate_image": generate_image, "image_status": image_status}

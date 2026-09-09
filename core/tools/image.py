"""JagX Image Studio local backend."""
from __future__ import annotations
import urllib.request
from pathlib import Path

def _config():
    try:
        import yaml
        with open("config/settings.yaml",encoding="utf-8") as f:return yaml.safe_load(f) or {}
    except Exception:return {}

def _cfg(): return _config().get("image_generation",{})
def _output_dir():
    p=Path(_cfg().get("output_dir","./data/generated_images")); p.mkdir(parents=True,exist_ok=True); return p
def _url(): return str(_cfg().get("comfyui_url","http://127.0.0.1:8188")).rstrip("/")
def _reachable():
    try:
        with urllib.request.urlopen(_url()+"/system_stats",timeout=2) as r:return r.status==200
    except Exception:return False

def image_status():
    if not _cfg().get("enabled",True): return "Image Studio is disabled."
    if _reachable(): return f"Image Studio ready: local ComfyUI detected at {_url()}. Output: {_output_dir()}"
    return "Image Studio is ready for local use, but the local ComfyUI backend is not running."

def generate_image(prompt: str, size: str="1024x1024", quality: str="auto"):
    if not prompt.strip(): return "IMAGE_GENERATION_ERROR: prompt is required."
    if not _reachable(): return "IMAGE_GENERATION_ERROR: local ComfyUI backend is unavailable."
    return "IMAGE_GENERATION_ERROR: local ComfyUI is detected, but JagX needs a configured workflow file at config/image_workflow.json before generation can run."

IMAGE_TOOLS=[
 {"type":"function","function":{"name":"generate_image","description":"Create an original image with JagX's local image-generation backend.","parameters":{"type":"object","properties":{"prompt":{"type":"string"},"size":{"type":"string","enum":["1024x1024","1536x1024","1024x1536"],"default":"1024x1024"},"quality":{"type":"string","enum":["auto","low","medium","high"],"default":"auto"}},"required":["prompt"]}}},
 {"type":"function","function":{"name":"image_status","description":"Check local Image Studio availability.","parameters":{"type":"object","properties":{},"required":[]}}}
]
TOOL_FUNCTIONS={"generate_image":generate_image,"image_status":image_status}

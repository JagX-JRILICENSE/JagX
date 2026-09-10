"""
JagX Animated Website Builder
Creates modern animated HTML sites locally and opens them in the browser.
JRILICENSE
"""
from __future__ import annotations

import os
import time
import webbrowser
from pathlib import Path
from typing import Optional

OUT = Path(__file__).resolve().parents[2] / "data" / "websites"
OUT.mkdir(parents=True, exist_ok=True)


def _write_and_open(name: str, html: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:40] or "site"
    path = OUT / f"{safe}_{int(time.time())}.html"
    path.write_text(html, encoding="utf-8")
    webbrowser.open(path.as_uri())
    return f"Website built and opened: {path}"


def build_animated_website(
    title: str = "My Site",
    headline: str = "Welcome",
    subtitle: str = "Built by JagX",
    theme: str = "dark",
) -> str:
    """Build a single-page animated website with CSS motion."""
    dark = theme.lower() != "light"
    bg = "#0b1020" if dark else "#f6f7fb"
    fg = "#f0f3f6" if dark else "#111827"
    accent = "#ff7a18" if dark else "#2563eb"
    card = "#141a2e" if dark else "#ffffff"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<style>
  :root {{ --bg:{bg}; --fg:{fg}; --accent:{accent}; --card:{card}; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{
    font-family: Segoe UI, system-ui, sans-serif;
    background: radial-gradient(1200px 600px at 10% -10%, #ff7a1833, transparent),
                radial-gradient(900px 500px at 110% 10%, #2f81f733, transparent),
                var(--bg);
    color: var(--fg); min-height:100vh; overflow-x:hidden;
  }}
  nav {{
    display:flex; justify-content:space-between; align-items:center;
    padding:1rem 8%; position:sticky; top:0; backdrop-filter: blur(10px);
    background: color-mix(in srgb, var(--bg) 80%, transparent);
    border-bottom:1px solid #ffffff15; z-index:10;
  }}
  .logo {{ font-weight:800; letter-spacing:.5px; }}
  .btn {{
    background: var(--accent); color:white; border:0; border-radius:999px;
    padding:.7rem 1.2rem; font-weight:700; cursor:pointer;
    box-shadow:0 10px 30px #0004; transition: transform .2s ease;
  }}
  .btn:hover {{ transform: translateY(-2px) scale(1.02); }}
  .hero {{
    min-height: 78vh; display:grid; place-items:center; text-align:center; padding:2rem;
  }}
  h1 {{
    font-size: clamp(2.2rem, 6vw, 4.5rem); line-height:1.05; margin-bottom:1rem;
    animation: rise .9s ease both;
  }}
  p.sub {{
    opacity:.85; font-size:1.15rem; max-width:640px; margin:0 auto 1.5rem;
    animation: rise 1.1s ease both;
  }}
  .grid {{
    display:grid; gap:1rem; grid-template-columns: repeat(auto-fit,minmax(220px,1fr));
    width:min(1000px,92%); margin:0 auto 4rem;
  }}
  .card {{
    background: var(--card); border:1px solid #ffffff12; border-radius:18px;
    padding:1.25rem; transform: translateY(20px); opacity:0;
    animation: rise .8s ease forwards;
  }}
  .card:nth-child(2){{ animation-delay:.15s }}
  .card:nth-child(3){{ animation-delay:.3s }}
  .blob {{
    position:fixed; width:280px; height:280px; border-radius:50%;
    background: radial-gradient(circle, var(--accent), transparent 70%);
    filter: blur(20px); opacity:.25; pointer-events:none;
    animation: float 8s ease-in-out infinite;
  }}
  .blob.a {{ top:10%; left:-60px; }}
  .blob.b {{ bottom:5%; right:-40px; animation-delay: -3s; }}
  @keyframes rise {{ from {{ opacity:0; transform:translateY(24px)}} to {{opacity:1; transform:none}} }}
  @keyframes float {{ 0%,100%{{ transform:translateY(0)}} 50%{{ transform:translateY(-24px)}} }}
  footer {{ text-align:center; padding:2rem; opacity:.6; }}
</style>
</head>
<body>
  <div class="blob a"></div><div class="blob b"></div>
  <nav>
    <div class="logo">🐆 {title}</div>
    <button class="btn" onclick="document.getElementById('cta').scrollIntoView({{behavior:'smooth'}})">Get started</button>
  </nav>
  <section class="hero">
    <div>
      <h1>{headline}</h1>
      <p class="sub">{subtitle}</p>
      <button class="btn" id="cta" onclick="alert('Built with JagX')">Explore</button>
    </div>
  </section>
  <section class="grid">
    <div class="card"><h3>Fast</h3><p>Lightweight animated landing page.</p></div>
    <div class="card"><h3>Modern</h3><p>Responsive layout with motion.</p></div>
    <div class="card"><h3>Yours</h3><p>Edit the HTML anytime in your project folder.</p></div>
  </section>
  <footer>Built by JagX · JRILICENSE</footer>
</body>
</html>
"""
    return _write_and_open(title, html)


def build_portfolio_site(name: str = "Creator", bio: str = "Builder & streamer") -> str:
    return build_animated_website(
        title=f"{name} Portfolio",
        headline=name,
        subtitle=bio,
        theme="dark",
    )


def build_product_landing(
    product: str = "My Product",
    tagline: str = "Ship faster with AI",
) -> str:
    return build_animated_website(
        title=product,
        headline=product,
        subtitle=tagline,
        theme="dark",
    )


def build_custom_html_site(filename: str, html: str) -> str:
    """Write full custom HTML and open it."""
    if not html or "<" not in html:
        return "Provide full HTML content."
    name = filename or "custom"
    return _write_and_open(name, html)


def list_built_websites() -> str:
    files = sorted(OUT.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]
    if not files:
        return "No websites built yet."
    return "\n".join(str(f) for f in files)


def open_latest_website() -> str:
    files = sorted(OUT.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return "No website found."
    webbrowser.open(files[0].as_uri())
    return f"Opened {files[0]}"


WEB_BUILDER_TOOLS = [
    {"type": "function", "function": {"name": "build_animated_website", "description": "Build and open an animated single-page website.", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "headline": {"type": "string"}, "subtitle": {"type": "string"}, "theme": {"type": "string", "default": "dark"}}, "required": []}}},
    {"type": "function", "function": {"name": "build_portfolio_site", "description": "Build an animated portfolio website.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "bio": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "build_product_landing", "description": "Build a product landing page with animation.", "parameters": {"type": "object", "properties": {"product": {"type": "string"}, "tagline": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "build_custom_html_site", "description": "Save custom HTML and open it as a website.", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "html": {"type": "string"}}, "required": ["filename", "html"]}}},
    {"type": "function", "function": {"name": "list_built_websites", "description": "List websites JagX has generated.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_latest_website", "description": "Open the most recently built website.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]

TOOL_FUNCTIONS = {
    "build_animated_website": build_animated_website,
    "build_portfolio_site": build_portfolio_site,
    "build_product_landing": build_product_landing,
    "build_custom_html_site": build_custom_html_site,
    "list_built_websites": list_built_websites,
    "open_latest_website": open_latest_website,
}

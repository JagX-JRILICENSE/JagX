"""
JagX System Tray
Keeps JagX running in the background with a tray icon.

JRILICENSE
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable, Optional

from rich.console import Console

console = Console()

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False


def _create_icon_image():
    """Create a simple jaguar-orange icon."""
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    # Orange circle
    draw.ellipse([4, 4, size-4, size-4], fill=(255, 140, 0, 255))
    # Simple eyes
    draw.ellipse([18, 22, 28, 32], fill=(0, 0, 0, 255))
    draw.ellipse([36, 22, 46, 32], fill=(0, 0, 0, 255))
    return image


class JagXTray:
    """System tray icon for always-on mode."""

    def __init__(
        self,
        on_show: Optional[Callable] = None,
        on_quit: Optional[Callable] = None,
        on_voice_toggle: Optional[Callable] = None,
    ):
        self.on_show = on_show
        self.on_quit = on_quit
        self.on_voice_toggle = on_voice_toggle
        self.icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

    def _setup_menu(self):
        return pystray.Menu(
            pystray.MenuItem("JagX is running", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open / Focus", self._on_show),
            pystray.MenuItem("Toggle Voice", self._on_voice),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit JagX", self._on_quit),
        )

    def _on_show(self, icon, item):
        if self.on_show:
            self.on_show()

    def _on_voice(self, icon, item):
        if self.on_voice_toggle:
            self.on_voice_toggle()

    def _on_quit(self, icon, item):
        if self.on_quit:
            self.on_quit()
        if self.icon:
            self.icon.stop()

    def start(self):
        if not HAS_TRAY:
            console.print("[yellow]pystray / Pillow not available. Tray disabled.[/yellow]")
            return

        image = _create_icon_image()
        self.icon = pystray.Icon(
            "JagX",
            image,
            "JagX - Personal Jaguar AI",
            menu=self._setup_menu(),
        )

        self._thread = threading.Thread(target=self.icon.run, daemon=True)
        self._thread.start()
        console.print("[green]System tray icon started.[/green]")

    def stop(self):
        if self.icon:
            self.icon.stop()

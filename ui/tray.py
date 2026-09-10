"""
JagX System Tray — premium jaguar companion in the Windows notification area.
JRILICENSE
"""

from __future__ import annotations

import threading
from typing import Callable, Optional

from rich.console import Console

console = Console()

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False
    pystray = None


def create_jaguar_icon(size: int = 64, talking: bool = False) -> "Image.Image":
    """Draw a simple premium jaguar face icon (orange + spots)."""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    # Face
    d.ellipse([2, 2, size - 2, size - 2], fill=(255, 149, 0, 255))
    # Ears
    d.polygon([(8, 18), (4, 2), (22, 10)], fill=(255, 149, 0, 255))
    d.polygon([(size - 8, 18), (size - 4, 2), (size - 22, 10)], fill=(255, 149, 0, 255))
    # Inner ears
    d.polygon([(10, 16), (8, 6), (18, 12)], fill=(40, 24, 12, 255))
    d.polygon([(size - 10, 16), (size - 8, 6), (size - 18, 12)], fill=(40, 24, 12, 255))
    # Spots
    for cx, cy, r in [(18, 40, 3), (28, 48, 2), (42, 38, 3), (48, 50, 2), (22, 52, 2)]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(30, 18, 8, 255))
    # Eyes
    d.ellipse([18, 24, 28, 34], fill=(20, 12, 6, 255))
    d.ellipse([36, 24, 46, 34], fill=(20, 12, 6, 255))
    d.ellipse([21, 26, 25, 30], fill=(255, 230, 80, 255))
    d.ellipse([39, 26, 43, 30], fill=(255, 230, 80, 255))
    # Nose
    d.ellipse([28, 36, 36, 42], fill=(40, 20, 10, 255))
    # Mouth — open if talking
    if talking:
        d.ellipse([24, 44, 40, 54], fill=(40, 15, 10, 255))
    else:
        d.arc([24, 42, 40, 52], 10, 170, fill=(40, 15, 10, 255), width=2)
    return image


class JagXTray:
    """Always-visible jaguar in the system tray."""

    def __init__(
        self,
        on_open: Optional[Callable] = None,
        on_type: Optional[Callable] = None,
        on_voice_toggle: Optional[Callable] = None,
        on_quit: Optional[Callable] = None,
    ):
        self.on_open = on_open
        self.on_type = on_type
        self.on_voice_toggle = on_voice_toggle
        self.on_quit = on_quit
        self.icon = None
        self._thread: Optional[threading.Thread] = None
        self._talking = False

    def _menu(self):
        return pystray.Menu(
            pystray.MenuItem("🐆 JagX — JRILICENSE", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open JagX", self._open, default=True),
            pystray.MenuItem("Type a command", self._type),
            pystray.MenuItem("Toggle voice", self._voice),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit),
        )

    def _open(self, icon=None, item=None):
        if self.on_open:
            self.on_open()

    def _type(self, icon=None, item=None):
        if self.on_type:
            self.on_type()
        elif self.on_open:
            self.on_open()

    def _voice(self, icon=None, item=None):
        if self.on_voice_toggle:
            self.on_voice_toggle()

    def _quit(self, icon=None, item=None):
        if self.on_quit:
            self.on_quit()
        self.stop()

    def set_talking(self, talking: bool):
        """Animate icon mouth when speaking."""
        self._talking = talking
        if self.icon and HAS_TRAY:
            try:
                self.icon.icon = create_jaguar_icon(64, talking=talking)
            except Exception:
                pass

    def notify(self, title: str, message: str):
        if self.icon:
            try:
                self.icon.notify(message, title)
            except Exception:
                pass

    def start(self):
        if not HAS_TRAY:
            console.print("[yellow]Tray unavailable — install pystray and Pillow.[/yellow]")
            return False
        image = create_jaguar_icon(64, talking=False)
        self.icon = pystray.Icon(
            "JagX",
            image,
            "JagX 🐆 — Personal Jaguar AI (JRILICENSE)",
            menu=self._menu(),
        )
        self._thread = threading.Thread(target=self.icon.run, daemon=True)
        self._thread.start()
        console.print("[green]Jaguar tray icon is live.[/green]")
        return True

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass

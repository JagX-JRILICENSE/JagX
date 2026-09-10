"""
JagX Live Desktop Companion
An always-on-top jaguar that walks around the screen, reacts, and opens the AI.
JRILICENSE
"""

from __future__ import annotations

import math
import random
import threading
import time
import tkinter as tk
from typing import Callable, Optional, Tuple


class JaguarCompanion:
    """Floating jaguar pet on the desktop — walks, idles, talks."""

    def __init__(
        self,
        on_click: Optional[Callable] = None,
        on_double_click: Optional[Callable] = None,
    ):
        self.on_click = on_click
        self.on_double_click = on_double_click
        self.root: Optional[tk.Toplevel] = None
        self.canvas: Optional[tk.Canvas] = None
        self._running = False
        self._talking = False
        self._status = "idle"  # idle | walk | talk | happy
        self._x = 100.0
        self._y = 100.0
        self._dir = 1  # 1 right, -1 left
        self._frame = 0
        self._target: Optional[Tuple[float, float]] = None
        self._bubble: Optional[str] = None
        self._bubble_until = 0.0
        self._size = 96
        self._screen_w = 1920
        self._screen_h = 1080

    def start(self, master: Optional[tk.Tk] = None):
        """Create the floating companion. master can be the main Tk app."""
        if self.root:
            return

        if master is None:
            # Standalone hidden root if needed
            self._owns_root = True
            master = tk.Tk()
            master.withdraw()
            self._master = master
        else:
            self._owns_root = False
            self._master = master

        self._screen_w = master.winfo_screenwidth()
        self._screen_h = master.winfo_screenheight()
        self._x = float(self._screen_w - 160)
        self._y = float(self._screen_h - 220)

        top = tk.Toplevel(master)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        try:
            top.attributes("-transparentcolor", "#00FF00")
        except Exception:
            pass
        top.configure(bg="#00FF00")
        top.geometry(f"{self._size + 40}x{self._size + 50}+{int(self._x)}+{int(self._y)}")

        canvas = tk.Canvas(
            top,
            width=self._size + 40,
            height=self._size + 50,
            bg="#00FF00",
            highlightthickness=0,
            bd=0,
        )
        canvas.pack(fill="both", expand=True)
        canvas.bind("<Button-1>", self._clicked)
        canvas.bind("<Double-Button-1>", self._double)
        canvas.bind("<B1-Motion>", self._drag)

        self.root = top
        self.canvas = canvas
        self._running = True
        self._draw()
        self.root.after(40, self._tick)

        # First hello
        self.say("Hey — I'm JagX", seconds=3)

    def stop(self):
        self._running = False
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
            self.root = None

    def say(self, text: str, seconds: float = 4.0):
        self._bubble = (text or "")[:48]
        self._bubble_until = time.time() + seconds
        self._talking = True
        self._status = "talk"
        self.root.after(int(seconds * 1000), self._end_talk)

    def _end_talk(self):
        self._talking = False
        if self._status == "talk":
            self._status = "idle"

    def celebrate(self):
        self._status = "happy"
        self.say("Done!", seconds=2)
        self.root.after(2000, lambda: setattr(self, "_status", "idle"))

    def _clicked(self, event):
        if self.on_click:
            self.on_click()
        self.say("Yes?", seconds=1.5)

    def _double(self, event):
        if self.on_double_click:
            self.on_double_click()
        elif self.on_click:
            self.on_click()

    def _drag(self, event):
        if not self.root:
            return
        x = self.root.winfo_pointerx() - self._size // 2
        y = self.root.winfo_pointery() - self._size // 2
        self._x, self._y = float(x), float(y)
        self._target = None
        self.root.geometry(f"+{x}+{y}")

    def _pick_target(self):
        margin = 40
        # Prefer walking along the lower third so it stays visible but not in the way
        tx = random.randint(margin, max(margin + 1, self._screen_w - self._size - margin))
        ty = random.randint(int(self._screen_h * 0.55), max(int(self._screen_h * 0.55) + 1, self._screen_h - self._size - 80))
        self._target = (float(tx), float(ty))
        self._status = "walk"

    def _tick(self):
        if not self._running or not self.root:
            return
        self._frame += 1

        # Occasionally choose a new place to walk
        if self._status in ("idle",) and random.random() < 0.02:
            self._pick_target()

        if self._target and self._status == "walk":
            tx, ty = self._target
            dx, dy = tx - self._x, ty - self._y
            dist = math.hypot(dx, dy)
            speed = 3.2
            if dist < speed:
                self._x, self._y = tx, ty
                self._target = None
                self._status = "idle"
            else:
                self._x += speed * dx / dist
                self._y += speed * dy / dist
                self._dir = 1 if dx >= 0 else -1

        # Keep on screen
        self._x = max(0, min(self._x, self._screen_w - self._size - 20))
        self._y = max(0, min(self._y, self._screen_h - self._size - 60))

        try:
            self.root.geometry(f"+{int(self._x)}+{int(self._y)}")
        except Exception:
            pass

        if self._bubble and time.time() > self._bubble_until:
            self._bubble = None

        self._draw()
        self.root.after(40, self._tick)

    def _draw(self):
        if not self.canvas:
            return
        c = self.canvas
        c.delete("all")
        s = self._size
        ox, oy = 20, 20

        # Bob while walking / talking
        bob = 0
        if self._status == "walk":
            bob = int(3 * math.sin(self._frame * 0.4))
        elif self._talking:
            bob = int(2 * math.sin(self._frame * 0.5))
        elif self._status == "happy":
            bob = int(5 * abs(math.sin(self._frame * 0.5)))

        # Shadow
        c.create_oval(ox + 18, oy + s - 8, ox + s - 10, oy + s + 4, fill="#003300", outline="")

        # Body
        body_color = "#FF9500"
        c.create_oval(ox + 12, oy + 28 + bob, ox + s - 8, oy + s - 10 + bob, fill=body_color, outline="#C46A00", width=2)

        # Head
        c.create_oval(ox + 22, oy + 8 + bob, ox + s - 14, oy + 48 + bob, fill=body_color, outline="#C46A00", width=2)

        # Ears
        if self._dir >= 0:
            c.create_polygon(ox + 28, oy + 18 + bob, ox + 22, oy + 2 + bob, ox + 40, oy + 12 + bob, fill=body_color, outline="#C46A00")
            c.create_polygon(ox + s - 28, oy + 18 + bob, ox + s - 18, oy + 2 + bob, ox + s - 36, oy + 12 + bob, fill=body_color, outline="#C46A00")
        else:
            c.create_polygon(ox + 28, oy + 18 + bob, ox + 18, oy + 2 + bob, ox + 40, oy + 12 + bob, fill=body_color, outline="#C46A00")
            c.create_polygon(ox + s - 28, oy + 18 + bob, ox + s - 22, oy + 2 + bob, ox + s - 36, oy + 12 + bob, fill=body_color, outline="#C46A00")

        # Spots
        for px, py, r in [(30, 55, 3), (48, 62, 2), (60, 50, 3), (40, 70, 2)]:
            c.create_oval(ox + px - r, oy + py - r + bob, ox + px + r, oy + py + r + bob, fill="#3A2410", outline="")

        # Eyes
        eye_y = oy + 24 + bob
        c.create_oval(ox + 34, eye_y, ox + 44, eye_y + 10, fill="#1A1008", outline="")
        c.create_oval(ox + 50, eye_y, ox + 60, eye_y + 10, fill="#1A1008", outline="")
        c.create_oval(ox + 37, eye_y + 3, ox + 41, eye_y + 7, fill="#FFE650", outline="")
        c.create_oval(ox + 53, eye_y + 3, ox + 57, eye_y + 7, fill="#FFE650", outline="")

        # Nose
        c.create_oval(ox + 44, oy + 34 + bob, ox + 52, oy + 40 + bob, fill="#2A150A", outline="")

        # Mouth
        if self._talking or self._status == "talk":
            c.create_oval(ox + 40, oy + 40 + bob, ox + 56, oy + 50 + bob, fill="#2A1008", outline="")
        else:
            c.create_arc(ox + 40, oy + 38 + bob, ox + 56, oy + 50 + bob, start=20, extent=140, style="arc", outline="#2A1008", width=2)

        # Legs (simple walk cycle)
        leg_phase = int(4 * math.sin(self._frame * 0.35)) if self._status == "walk" else 0
        c.create_rectangle(ox + 28, oy + s - 22 + bob, ox + 36, oy + s - 4 + bob + leg_phase, fill="#E07E00", outline="")
        c.create_rectangle(ox + s - 36, oy + s - 22 + bob, ox + s - 28, oy + s - 4 + bob - leg_phase, fill="#E07E00", outline="")

        # Speech bubble
        if self._bubble:
            c.create_round_rect = getattr(c, "create_round_rect", None)
            bx1, by1, bx2, by2 = 2, 0, self._size + 38, 18
            c.create_rectangle(bx1, by1, bx2, by2, fill="#161b22", outline="#FF9500", width=2)
            c.create_text((bx1 + bx2) // 2, (by1 + by2) // 2, text=self._bubble, fill="#f0f3f6", font=("Segoe UI", 8, "bold"))


def attach_companion(master: tk.Tk, on_open: Optional[Callable] = None) -> JaguarCompanion:
    pet = JaguarCompanion(on_click=on_open, on_double_click=on_open)
    pet.start(master=master)
    return pet

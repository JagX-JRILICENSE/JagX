"""
JagX Live Desktop Companion
Walking jaguar + talking bubble + friends that celebrate success.
JRILICENSE
"""

from __future__ import annotations

import math
import random
import time
import tkinter as tk
from typing import Callable, List, Optional, Tuple


class _Friend:
    def __init__(self, canvas_root: tk.Toplevel, x: float, y: float, life: float):
        self.root = canvas_root
        self.x = x
        self.y = y
        self.life = life
        self.born = time.time()
        self.frame = 0
        self.dir = random.choice([-1, 1])


class JaguarCompanion:
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
        self._status = "idle"
        self._x = 100.0
        self._y = 100.0
        self._dir = 1
        self._frame = 0
        self._target: Optional[Tuple[float, float]] = None
        self._bubble: Optional[str] = None
        self._bubble_until = 0.0
        self._size = 100
        self._screen_w = 1920
        self._screen_h = 1080
        self._friends: List[dict] = []
        self._glow = False

    def start(self, master: Optional[tk.Tk] = None):
        if self.root:
            return
        if master is None:
            master = tk.Tk()
            master.withdraw()
        self._master = master
        self._screen_w = master.winfo_screenwidth()
        self._screen_h = master.winfo_screenheight()
        self._x = float(self._screen_w - 180)
        self._y = float(self._screen_h - 240)

        top = tk.Toplevel(master)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        try:
            top.attributes("-transparentcolor", "#00FF00")
        except Exception:
            pass
        top.configure(bg="#00FF00")
        w, h = 280, 160
        top.geometry(f"{w}x{h}+{int(self._x)}+{int(self._y)}")

        canvas = tk.Canvas(top, width=w, height=h, bg="#00FF00", highlightthickness=0, bd=0)
        canvas.pack(fill="both", expand=True)
        canvas.bind("<Button-1>", self._clicked)
        canvas.bind("<Double-Button-1>", self._double)
        canvas.bind("<B1-Motion>", self._drag)

        self.root = top
        self.canvas = canvas
        self._running = True
        self._draw()
        self.root.after(40, self._tick)
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
        self._bubble = (text or "")[:52]
        self._bubble_until = time.time() + seconds
        self._talking = True
        self._status = "talk"
        self._glow = True
        if self.root:
            self.root.after(int(seconds * 1000), self._end_talk)

    def _end_talk(self):
        self._talking = False
        self._glow = False
        if self._status == "talk":
            self._status = "idle"

    def celebrate(self):
        """Main jaguar celebrates and friends run in."""
        self._status = "happy"
        self.say("Yes! Done!", seconds=2.5)
        self._spawn_friends(5)
        if self.root:
            self.root.after(2800, lambda: setattr(self, "_status", "idle"))

    def _spawn_friends(self, n: int = 4):
        now = time.time()
        for i in range(n):
            self._friends.append(
                {
                    "x": self._x + random.randint(-80, 80),
                    "y": self._y + random.randint(-30, 40),
                    "dir": random.choice([-1, 1]),
                    "born": now,
                    "life": 2.8 + random.random(),
                    "phase": random.random() * 6,
                }
            )

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
        x = self.root.winfo_pointerx() - 60
        y = self.root.winfo_pointery() - 60
        self._x, self._y = float(x), float(y)
        self._target = None
        self.root.geometry(f"+{x}+{y}")

    def _pick_target(self):
        margin = 30
        tx = random.randint(margin, max(margin + 1, self._screen_w - 200))
        ty = random.randint(int(self._screen_h * 0.5), max(int(self._screen_h * 0.5) + 1, self._screen_h - 180))
        self._target = (float(tx), float(ty))
        self._status = "walk"

    def _tick(self):
        if not self._running or not self.root:
            return
        self._frame += 1

        if self._status == "idle" and random.random() < 0.018:
            self._pick_target()

        if self._target and self._status == "walk":
            tx, ty = self._target
            dx, dy = tx - self._x, ty - self._y
            dist = math.hypot(dx, dy)
            speed = 3.4
            if dist < speed:
                self._x, self._y = tx, ty
                self._target = None
                self._status = "idle"
            else:
                self._x += speed * dx / dist
                self._y += speed * dy / dist
                self._dir = 1 if dx >= 0 else -1

        self._x = max(0, min(self._x, self._screen_w - 200))
        self._y = max(0, min(self._y, self._screen_h - 160))

        # Friends physics
        now = time.time()
        alive = []
        for f in self._friends:
            age = now - f["born"]
            if age < f["life"]:
                f["x"] += f["dir"] * 2.2
                f["y"] += math.sin((self._frame + f["phase"]) * 0.3) * 1.5
                alive.append(f)
        self._friends = alive

        try:
            self.root.geometry(f"+{int(self._x)}+{int(self._y)}")
        except Exception:
            pass

        if self._bubble and time.time() > self._bubble_until:
            self._bubble = None

        self._draw()
        self.root.after(40, self._tick)

    def _draw_jaguar(self, c: tk.Canvas, ox: int, oy: int, scale: float = 1.0, talking: bool = False, happy: bool = False):
        s = int(self._size * scale)
        bob = 0
        if self._status == "walk" or happy:
            bob = int(3 * math.sin(self._frame * 0.4))
        if talking:
            bob = int(2 * math.sin(self._frame * 0.55))

        # glow when talking
        if talking or self._glow:
            c.create_oval(ox + 8, oy + 8 + bob, ox + s - 2, oy + s - 2 + bob, outline="#FFE08A", width=3)

        c.create_oval(ox + 14, oy + s - 12, ox + s - 10, oy + s + 2, fill="#003300", outline="")
        c.create_oval(ox + 12, oy + 28 + bob, ox + s - 8, oy + s - 10 + bob, fill="#FF9500", outline="#C46A00", width=2)
        c.create_oval(ox + 22, oy + 8 + bob, ox + s - 14, oy + 48 + bob, fill="#FF9500", outline="#C46A00", width=2)
        c.create_polygon(ox + 28, oy + 18 + bob, ox + 22, oy + 2 + bob, ox + 40, oy + 12 + bob, fill="#FF9500", outline="#C46A00")
        c.create_polygon(ox + s - 28, oy + 18 + bob, ox + s - 18, oy + 2 + bob, ox + s - 36, oy + 12 + bob, fill="#FF9500", outline="#C46A00")
        for px, py, r in [(30, 55, 3), (48, 62, 2), (60, 50, 3)]:
            c.create_oval(ox + int(px * scale) - r, oy + int(py * scale) - r + bob, ox + int(px * scale) + r, oy + int(py * scale) + r + bob, fill="#3A2410", outline="")
        eye_y = oy + 24 + bob
        c.create_oval(ox + 34, eye_y, ox + 44, eye_y + 10, fill="#1A1008", outline="")
        c.create_oval(ox + 50, eye_y, ox + 60, eye_y + 10, fill="#1A1008", outline="")
        c.create_oval(ox + 37, eye_y + 3, ox + 41, eye_y + 7, fill="#FFE650", outline="")
        c.create_oval(ox + 53, eye_y + 3, ox + 57, eye_y + 7, fill="#FFE650", outline="")
        c.create_oval(ox + 44, oy + 34 + bob, ox + 52, oy + 40 + bob, fill="#2A150A", outline="")
        if talking:
            c.create_oval(ox + 40, oy + 40 + bob, ox + 56, oy + 52 + bob, fill="#2A1008", outline="")
        else:
            c.create_arc(ox + 40, oy + 38 + bob, ox + 56, oy + 50 + bob, start=20, extent=140, style="arc", outline="#2A1008", width=2)
        leg = int(4 * math.sin(self._frame * 0.35)) if self._status == "walk" else 0
        c.create_rectangle(ox + 28, oy + s - 22 + bob, ox + 36, oy + s - 4 + bob + leg, fill="#E07E00", outline="")
        c.create_rectangle(ox + s - 36, oy + s - 22 + bob, ox + s - 28, oy + s - 4 + bob - leg, fill="#E07E00", outline="")

    def _draw(self):
        if not self.canvas:
            return
        c = self.canvas
        c.delete("all")

        # Friends behind / around
        for f in self._friends:
            # draw relative to main window coords — friends offset inside canvas
            fx = int(f["x"] - self._x) + 90
            fy = int(f["y"] - self._y) + 40
            self._draw_jaguar(c, fx, fy, scale=0.55, talking=False, happy=True)

        # Main jaguar
        self._draw_jaguar(
            c, 90, 40, scale=1.0,
            talking=self._talking or self._status == "talk",
            happy=self._status == "happy",
        )

        # Talking indicator ring + label
        if self._talking or self._status == "talk":
            c.create_text(140, 150, text="🔊 talking", fill="#FFE08A", font=("Segoe UI", 9, "bold"))

        if self._bubble:
            c.create_rectangle(4, 2, 276, 22, fill="#161b22", outline="#FF9500", width=2)
            c.create_text(140, 12, text=self._bubble, fill="#f0f3f6", font=("Segoe UI", 9, "bold"))


def attach_companion(master: tk.Tk, on_open: Optional[Callable] = None) -> JaguarCompanion:
    pet = JaguarCompanion(on_click=on_open, on_double_click=on_open)
    pet.start(master=master)
    return pet

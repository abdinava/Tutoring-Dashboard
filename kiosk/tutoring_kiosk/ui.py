"""Fullscreen Tkinter screens. Only draws the Flow's current state.

- Swipes arrive on a queue checked every 100 ms (no busy-wait loops).
- Messages and abandoned screens return home automatically.
- Ctrl+Shift+Q quits (Escape does not, so students can't close it).
"""

from __future__ import annotations

import queue
import time
import tkinter as tk
from typing import List

from .flow import CLASSES, CONFIRM, HOME, MANUAL, MESSAGE, Flow

BLUE, GOLD, WHITE, DARK = "#003DA5", "#FFC72C", "#FFFFFF", "#002A70"
MESSAGE_SECONDS = 3
IDLE_SECONDS = 30


class KioskUI:
    def __init__(self, root: tk.Tk, flow: Flow, courses: List[str], swipes: queue.Queue,
                 fullscreen: bool = True) -> None:
        self.root, self.flow, self.courses, self.swipes = root, flow, courses, swipes
        self.last_change = time.monotonic()

        root.title("ULA Tutoring Check-In")
        root.configure(bg=BLUE)
        root.attributes("-fullscreen", fullscreen)
        root.bind_all("<Control-Shift-KeyPress-Q>", lambda _e: root.destroy())
        size = max(root.winfo_screenheight(), 480)
        self.big = ("Helvetica", size // 16, "bold")
        self.text = ("Helvetica", size // 28)

        self.frame = tk.Frame(root, bg=BLUE)
        self.frame.pack(expand=True, fill="both")
        self.render()
        self.tick()

    # --- timing ---
    def tick(self) -> None:
        try:
            while True:
                self.do(self.flow.swipe, self.swipes.get_nowait())
        except queue.Empty:
            pass
        waited = time.monotonic() - self.last_change
        screen = self.flow.state.screen
        if (screen == MESSAGE and waited > MESSAGE_SECONDS) or \
                (screen != HOME and waited > IDLE_SECONDS):
            self.do(self.flow.reset)
        self.root.after(100, self.tick)

    def do(self, action, *args) -> None:
        """Run a Flow action, then redraw."""
        action(*args)
        self.last_change = time.monotonic()
        self.render()

    # --- drawing ---
    def render(self) -> None:
        for widget in self.frame.winfo_children():
            widget.destroy()
        {HOME: self.home, CONFIRM: self.confirm, MANUAL: self.manual,
         CLASSES: self.classes, MESSAGE: self.message}[self.flow.state.screen]()

    def label(self, text: str, big: bool = False) -> None:
        tk.Label(self.frame, text=text, font=self.big if big else self.text,
                 fg=GOLD if big else WHITE, bg=BLUE).pack(pady=15)

    def buttons(self, *specs) -> List[tk.Button]:
        row = tk.Frame(self.frame, bg=BLUE)
        row.pack(pady=25)
        made = []
        for text, command in specs:
            b = tk.Button(row, text=text, command=command, font=self.text,
                          bg=GOLD, fg=DARK, padx=30, pady=12)
            b.pack(side="left", padx=15)
            made.append(b)
        return made

    def home(self) -> None:
        self.label("ULA Tutoring Center", big=True)
        self.label("Swipe your R'Card to check in")
        self.buttons(("Check in without card", lambda: self.do(self.flow.start_manual)))

    def confirm(self) -> None:
        state = self.flow.state
        self.label("Is this you?")
        self.label(state.name or "ID ending in " + state.student_id[-4:], big=True)
        self.buttons(("Yes", lambda: self.do(self.flow.confirm, True)),
                     ("No", lambda: self.do(self.flow.confirm, False)))

    def manual(self) -> None:
        self.label("Enter your 9-digit Student ID")
        entry = tk.Entry(self.frame, font=self.big, width=11, justify="center")
        entry.pack(pady=10)
        entry.focus_set()
        submit = lambda *_: self.do(self.flow.enter_id, entry.get())  # noqa: E731
        entry.bind("<Return>", submit)
        self.buttons(("Continue", submit), ("Cancel", lambda: self.do(self.flow.reset)))

    def classes(self) -> None:
        self.label("Which class(es) are you here for?")
        grid = tk.Frame(self.frame, bg=BLUE)
        grid.pack()
        selected = self.flow.state.selected
        for i, course in enumerate(self.courses):
            on = course in selected
            tk.Button(grid, text=("\u2713 " if on else "") + course, font=self.text, width=10,
                      bg=GOLD if on else WHITE, fg=DARK,
                      command=lambda c=course: self.do(self.flow.toggle, c),
                      ).grid(row=i // 4, column=i % 4, padx=8, pady=8)
        done, _ = self.buttons(("Done", lambda: self.do(self.flow.finish)),
                               ("Cancel", lambda: self.do(self.flow.reset)))
        done.config(state="normal" if selected else "disabled")

    def message(self) -> None:
        self.label(self.flow.state.message, big=True)

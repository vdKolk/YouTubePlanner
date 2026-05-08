"""
Hoofdapplicatie GUI - CustomTkinter
"""

import sys
import os
import threading
from datetime import datetime
from tkinter import messagebox
import tkinter as tk

try:
    import customtkinter as ctk
except ImportError:
    print("CustomTkinter niet gevonden. Installeer via: pip install customtkinter")
    sys.exit(1)

from src.settings import SettingsManager
from src.youtube import YouTubeManager
from src.database import BroadcastDB
from src.frames.plan_frame import PlanFrame
from src.frames.overview_frame import OverviewFrame
from src.frames.archive_frame import ArchiveFrame
from src.frames.settings_frame import SettingsFrame


# Kleurschema
COLORS = {
    "bg": "#0f1117",
    "sidebar": "#161b22",
    "card": "#1c2128",
    "border": "#30363d",
    "accent": "#c0392b",       # Kerkenrood
    "accent_hover": "#e74c3c",
    "accent2": "#2980b9",      # Blauw voor secondaire acties
    "text": "#e6edf3",
    "text_muted": "#7d8590",
    "success": "#2ea043",
    "warning": "#d29922",
    "error": "#f85149",
}


class App:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.settings = SettingsManager()
        self.youtube = YouTubeManager(self.settings)
        self.db = BroadcastDB(self.settings.get_data_dir())

        self.root = ctk.CTk()
        self.root.title("YouTube Livestream Planner")
        self.root.geometry("1100x750")
        self.root.minsize(900, 650)
        self.root.configure(fg_color=COLORS["bg"])

        # Zet icoon als beschikbaar
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        self._build_ui()
        self._connect_accounts()

    def _build_ui(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self.root,
            width=220,
            corner_radius=0,
            fg_color=COLORS["sidebar"],
            border_width=1,
            border_color=COLORS["border"],
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo/titel in sidebar
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(24, 8))

        ctk.CTkLabel(
            logo_frame,
            text="▶",
            font=ctk.CTkFont(size=28),
            text_color=COLORS["accent"],
        ).pack(side="left", padx=(0, 8))

        title_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(
            title_frame,
            text="Stream",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_frame,
            text="Planner",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w")

        # Scheidingslijn
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(
            fill="x", padx=12, pady=16
        )

        # Navigatie items
        self.nav_buttons = {}
        nav_items = [
            ("plan", "  📅  Stream inplannen", PlanFrame),
            ("overview", "  📋  Overzicht", OverviewFrame),
            ("archive", "  🗃  Archiveren", ArchiveFrame),
            ("settings", "  ⚙  Instellingen", SettingsFrame),
        ]

        for key, label, _ in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color=COLORS["card"],
                text_color=COLORS["text_muted"],
                height=42,
                corner_radius=8,
                command=lambda k=key: self._navigate(k),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self.nav_buttons[key] = btn

        # Status-indicatoren onderaan sidebar
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(
            fill="x", padx=12, pady=16, side="bottom"
        )

        status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        status_frame.pack(fill="x", padx=12, pady=(0, 16), side="bottom")

        self.status_main = self._make_status_dot(
            status_frame,
            self.settings.get("accounts", "main", "name") or "Hoofdstream",
        )
        self.status_tolk = self._make_status_dot(
            status_frame,
            self.settings.get("accounts", "tolk", "name") or "Tolkstream",
        )

        # Hoofdgebied
        self.main_area = ctk.CTkFrame(self.root, fg_color=COLORS["bg"], corner_radius=0)
        self.main_area.pack(side="left", fill="both", expand=True)

        # Frames aanmaken
        self.frames = {}
        frame_classes = {k: fc for k, _, fc in nav_items}
        for key, frame_class in frame_classes.items():
            frame = frame_class(self.main_area, self)
            frame.place(relwidth=1, relheight=1)
            self.frames[key] = frame

        # Start met plan scherm
        self._navigate("plan")

    def _make_status_dot(self, parent, label: str) -> ctk.CTkLabel:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        dot = ctk.CTkLabel(row, text="●", font=ctk.CTkFont(size=10), text_color=COLORS["text_muted"])
        dot.pack(side="left", padx=(0, 6))
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]).pack(side="left")
        return dot

    def _navigate(self, key: str):
        # Reset alle knoppen
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(
                    fg_color=COLORS["card"],
                    text_color=COLORS["text"],
                    border_width=0,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_muted"],
                )

        # Toon juiste frame
        frame = self.frames.get(key)
        if frame:
            frame.lift()
            if hasattr(frame, "on_show"):
                frame.on_show()

    def _connect_accounts(self):
        """Verbind accounts op achtergrond"""
        def _connect():
            self.youtube.connect_all()
            self.root.after(0, self._update_status_indicators)

        threading.Thread(target=_connect, daemon=True).start()

    def _update_status_indicators(self):
        main_ok = self.youtube.main.is_authenticated()
        tolk_ok = self.youtube.tolk.is_authenticated()

        self.status_main.configure(
            text_color=COLORS["success"] if main_ok else COLORS["error"]
        )
        self.status_tolk.configure(
            text_color=COLORS["success"] if tolk_ok else COLORS["error"]
        )

    def refresh_status(self):
        self._update_status_indicators()

    def run(self):
        self.root.mainloop()

"""
Overzicht scherm - geplande en recente uitzendingen
"""

from datetime import datetime
import tkinter as tk
try:
    import customtkinter as ctk
except ImportError:
    pass

COLORS = {
    "bg": "#0f1117",
    "card": "#1c2128",
    "border": "#30363d",
    "accent": "#c0392b",
    "accent2": "#2980b9",
    "text": "#e6edf3",
    "text_muted": "#7d8590",
    "success": "#2ea043",
    "warning": "#d29922",
    "error": "#f85149",
    "input_bg": "#21262d",
}


class OverviewFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self.app = app
        self._build()

    def _build(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(28, 0))

        ctk.CTkLabel(
            header,
            text="Overzicht uitzendingen",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="🔄 Vernieuwen",
            width=110,
            height=32,
            fg_color=COLORS["card"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=12),
            command=self.on_show,
        ).pack(side="right")

        # Tabs
        tab_frame = ctk.CTkFrame(self, fg_color="transparent")
        tab_frame.pack(fill="x", padx=32, pady=(16, 0))

        self.active_tab = tk.StringVar(value="upcoming")

        for label, val in [("Aankomend", "upcoming"), ("Recent", "past")]:
            ctk.CTkButton(
                tab_frame,
                text=label,
                width=120,
                height=34,
                fg_color=COLORS["accent"] if val == "upcoming" else COLORS["card"],
                hover_color=COLORS["accent"] if val == "upcoming" else COLORS["border"],
                text_color="white",
                font=ctk.CTkFont(size=13),
                command=lambda v=val: self._switch_tab(v),
            ).pack(side="left", padx=(0, 8))

        # Content area
        self.content = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color=COLORS["border"]
        )
        self.content.pack(fill="both", expand=True, padx=32, pady=16)

    def _switch_tab(self, tab: str):
        self.active_tab.set(tab)
        self._render()

    def _render(self):
        for widget in self.content.winfo_children():
            widget.destroy()

        tab = self.active_tab.get()
        if tab == "upcoming":
            records = self.app.db.get_upcoming()
        else:
            records = self.app.db.get_past()

        if not records:
            ctk.CTkLabel(
                self.content,
                text="Geen uitzendingen gevonden.",
                font=ctk.CTkFont(size=14),
                text_color=COLORS["text_muted"],
            ).pack(pady=40)
            return

        for record in sorted(records, key=lambda r: r.get("scheduled_start", ""), reverse=(tab == "past")):
            self._render_card(record)

    def _render_card(self, record: dict):
        card = ctk.CTkFrame(
            self.content,
            fg_color=COLORS["card"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.pack(fill="x", pady=6)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        # Titel
        ctk.CTkLabel(
            inner,
            text=record.get("title", "Onbekende titel"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(fill="x")

        # Datum/tijd
        try:
            dt = datetime.fromisoformat(record["scheduled_start"])
            dt_str = dt.strftime("%A %d %B %Y, %H:%M")
        except Exception:
            dt_str = record.get("scheduled_start", "")

        meta_frame = ctk.CTkFrame(inner, fg_color="transparent")
        meta_frame.pack(fill="x", pady=(6, 0))

        ctk.CTkLabel(
            meta_frame,
            text=f"📅 {dt_str}",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        ).pack(side="left", padx=(0, 16))

        # Tolkstream indicator
        tolk_color = COLORS["success"] if record.get("include_tolk") else COLORS["text_muted"]
        ctk.CTkLabel(
            meta_frame,
            text="🎧 Tolkstream" if record.get("include_tolk") else "Geen tolkstream",
            font=ctk.CTkFont(size=12),
            text_color=tolk_color,
        ).pack(side="left", padx=(0, 16))

        # Broadcast IDs
        if record.get("main_broadcast_id"):
            ctk.CTkLabel(
                meta_frame,
                text=f"ID: {record['main_broadcast_id']}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_muted"],
            ).pack(side="right")

    def on_show(self):
        self._render()

"""
Archiveren scherm - zet oude streams op verborgen
"""

import threading
from datetime import datetime, timezone, timedelta
import tkinter as tk
from tkinter import messagebox

try:
    import customtkinter as ctk
except ImportError:
    pass

COLORS = {
    "bg": "#0f1117",
    "card": "#1c2128",
    "border": "#30363d",
    "accent": "#c0392b",
    "accent_hover": "#e74c3c",
    "accent2": "#2980b9",
    "text": "#e6edf3",
    "text_muted": "#7d8590",
    "success": "#2ea043",
    "warning": "#d29922",
    "error": "#f85149",
}


class ArchiveFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self.app = app
        self.found_broadcasts = {"main": [], "tolk": []}
        self._build()

    def _build(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(28, 0))

        ctk.CTkLabel(
            header,
            text="Archiveren",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left")

        # Uitleg
        info_card = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        info_card.pack(fill="x", padx=32, pady=16)
        ctk.CTkLabel(
            info_card,
            text=(
                "Met deze functie kun je alle afgelopen uitzendingen die ouder zijn dan het ingestelde\n"
                "aantal dagen (standaard 180) in één keer verbergen op YouTube."
            ),
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"],
            justify="left",
        ).pack(padx=16, pady=12, anchor="w")

        # Instellingen
        settings_card = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        settings_card.pack(fill="x", padx=32, pady=(0, 16))

        s_inner = ctk.CTkFrame(settings_card, fg_color="transparent")
        s_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            s_inner,
            text="Verberg streams ouder dan:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"],
        ).pack(side="left", padx=(0, 12))

        self.days_var = tk.StringVar(value=str(self.app.settings.get("app", "archive_after_days") or 180))
        days_entry = ctk.CTkEntry(
            s_inner,
            textvariable=self.days_var,
            width=80,
            fg_color="#21262d",
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
            height=36,
        )
        days_entry.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            s_inner,
            text="dagen",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"],
        ).pack(side="left")

        # Accounts selectie
        acc_frame = ctk.CTkFrame(settings_card, fg_color="transparent")
        acc_frame.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(
            acc_frame,
            text="Accounts:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"],
        ).pack(side="left", padx=(0, 12))

        self.include_main = tk.BooleanVar(value=True)
        self.include_tolk = tk.BooleanVar(value=True)

        ctk.CTkCheckBox(
            acc_frame,
            text="Hoofdstream",
            variable=self.include_main,
            fg_color=COLORS["accent"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 16))

        ctk.CTkCheckBox(
            acc_frame,
            text="Tolkstream",
            variable=self.include_tolk,
            fg_color=COLORS["accent"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left")

        # Knoppen
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=32, pady=(0, 16))

        ctk.CTkButton(
            btn_row,
            text="🔍  Zoeken naar oude streams",
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["accent2"],
            hover_color="#1a6fa3",
            text_color="white",
            corner_radius=8,
            command=self._search,
        ).pack(side="left", padx=(0, 12))

        self.archive_btn = ctk.CTkButton(
            btn_row,
            text="🗃️  Alles verbergen",
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
            corner_radius=8,
            state="disabled",
            command=self._archive_all,
        )
        self.archive_btn.pack(side="left")

        self.status_label = ctk.CTkLabel(
            btn_row,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"],
        )
        self.status_label.pack(side="left", padx=12)

        # Resultaten
        ctk.CTkLabel(
            self,
            text="Gevonden uitzendingen",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=32)

        self.results_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color=COLORS["border"]
        )
        self.results_frame.pack(fill="both", expand=True, padx=32, pady=(8, 24))

        self._show_empty("Zoek eerst naar oude streams.")

    def _show_empty(self, msg: str):
        for w in self.results_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.results_frame,
            text=msg,
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"],
        ).pack(pady=32)

    def _search(self):
        try:
            days = int(self.days_var.get())
        except ValueError:
            messagebox.showerror("Fout", "Voer een geldig aantal dagen in.")
            return

        self._show_empty("Bezig met zoeken...")
        self.status_label.configure(text="Zoeken...", text_color=COLORS["warning"])
        self.archive_btn.configure(state="disabled")

        def _do_search():
            found = {"main": [], "tolk": []}

            if self.include_main.get():
                acc = self.app.youtube.main
                if not acc.is_authenticated():
                    acc.connect()
                try:
                    found["main"] = acc.get_all_old_broadcasts(days)
                except Exception as e:
                    self.after(0, lambda: self.status_label.configure(
                        text=f"Hoofdstream fout: {e}", text_color=COLORS["error"]
                    ))

            if self.include_tolk.get():
                acc = self.app.youtube.tolk
                if not acc.is_authenticated():
                    acc.connect()
                try:
                    found["tolk"] = acc.get_all_old_broadcasts(days)
                except Exception as e:
                    self.after(0, lambda: self.status_label.configure(
                        text=f"Tolkstream fout: {e}", text_color=COLORS["error"]
                    ))

            self.found_broadcasts = found
            self.after(0, lambda: self._show_results(found))

        threading.Thread(target=_do_search, daemon=True).start()

    def _show_results(self, found: dict):
        for w in self.results_frame.winfo_children():
            w.destroy()

        total = len(found["main"]) + len(found["tolk"])
        self.status_label.configure(
            text=f"{total} stream(s) gevonden",
            text_color=COLORS["success"] if total > 0 else COLORS["text_muted"],
        )

        if total == 0:
            self._show_empty("Geen streams gevonden die ouder zijn dan de ingestelde termijn.")
            return

        self.archive_btn.configure(state="normal")

        for acc_key, items in found.items():
            if not items:
                continue
            acc_name = self.app.settings.get("accounts", acc_key, "name") or acc_key

            ctk.CTkLabel(
                self.results_frame,
                text=f"── {acc_name} ({len(items)} streams) ──",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS["text_muted"],
            ).pack(anchor="w", pady=(12, 4))

            for item in items:
                self._render_result_row(item)

    def _render_result_row(self, item: dict):
        snippet = item.get("snippet", {})
        title = snippet.get("title", "Onbekend")
        start = snippet.get("actualStartTime") or snippet.get("scheduledStartTime", "")

        try:
            dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            dt_str = dt.strftime("%d %b %Y")
        except Exception:
            dt_str = start

        row = ctk.CTkFrame(
            self.results_frame,
            fg_color=COLORS["card"],
            corner_radius=6,
            border_width=1,
            border_color=COLORS["border"],
        )
        row.pack(fill="x", pady=3)
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(
            inner,
            text=title,
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            inner,
            text=dt_str,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        ).pack(side="right")

    def _archive_all(self):
        total = len(self.found_broadcasts["main"]) + len(self.found_broadcasts["tolk"])
        if not messagebox.askyesno(
            "Bevestigen",
            f"Weet u zeker dat u {total} stream(s) wilt verbergen?\nDit kan niet ongedaan worden gemaakt via dit programma.",
        ):
            return

        self.archive_btn.configure(state="disabled", text="Bezig...")
        self.status_label.configure(text="Streams worden verborgen...", text_color=COLORS["warning"])

        def _do_archive():
            done = 0
            errors = 0

            for acc_key, items in self.found_broadcasts.items():
                acc = self.app.youtube.get_account(acc_key)
                for item in items:
                    try:
                        acc.set_broadcast_privacy(item["id"], "private")
                        done += 1
                    except Exception:
                        errors += 1

            self.after(0, lambda: self._archive_done(done, errors))

        threading.Thread(target=_do_archive, daemon=True).start()

    def _archive_done(self, done: int, errors: int):
        self.archive_btn.configure(state="normal", text="🗃️  Alles verbergen")
        msg = f"✓ {done} stream(s) verborgen."
        if errors:
            msg += f" {errors} fout(en)."
        self.status_label.configure(
            text=msg,
            text_color=COLORS["success"] if not errors else COLORS["warning"],
        )
        self.found_broadcasts = {"main": [], "tolk": []}
        messagebox.showinfo("Klaar", msg)

    def on_show(self):
        pass

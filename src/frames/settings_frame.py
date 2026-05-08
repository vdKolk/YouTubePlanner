"""
Instellingen scherm
"""

import os
import threading
import shutil
from pathlib import Path
from tkinter import messagebox, filedialog
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
    "accent_hover": "#e74c3c",
    "accent2": "#2980b9",
    "text": "#e6edf3",
    "text_muted": "#7d8590",
    "success": "#2ea043",
    "warning": "#d29922",
    "error": "#f85149",
    "input_bg": "#21262d",
}


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self.app = app
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self,
            text="Instellingen",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=32, pady=(28, 16))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=COLORS["border"])
        scroll.pack(fill="both", expand=True, padx=32, pady=(0, 24))

        self._build_accounts_section(scroll)
        self._build_predikanten_section(scroll)
        self._build_template_section(scroll)
        self._build_description_section(scroll)
        self._build_stream_defaults_section(scroll)
        self._build_misc_section(scroll)

        # Opslaan knop
        ctk.CTkButton(
            scroll,
            text="  💾  Instellingen opslaan",
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
            corner_radius=8,
            command=self._save,
        ).pack(anchor="w", pady=(16, 0))

    def _section(self, parent, title: str):
        ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", pady=(20, 6))

    def _card(self, parent) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["card"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.pack(fill="x", pady=(0, 4))
        return card

    def _label_entry(self, parent, label: str, default: str = "", placeholder: str = "") -> ctk.CTkEntry:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"], width=180, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(
            row,
            placeholder_text=placeholder,
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
            height=32,
        )
        entry.pack(side="left", fill="x", expand=True)
        if default:
            entry.insert(0, default)
        return entry

    # ── Accounts ──────────────────────────────────────────────────────────

    def _build_accounts_section(self, parent):
        self._section(parent, "📡  Google Accounts")

        for acc_key in ["main", "tolk"]:
            acc = self.app.youtube.get_account(acc_key)
            card = self._card(parent)

            title_row = ctk.CTkFrame(card, fg_color="transparent")
            title_row.pack(fill="x", padx=16, pady=(12, 4))

            acc_name = self.app.settings.get("accounts", acc_key, "name") or acc_key
            ctk.CTkLabel(
                title_row,
                text=acc_name,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLORS["text"],
            ).pack(side="left")

            status_dot = ctk.CTkLabel(
                title_row,
                text="● Verbonden" if acc.is_authenticated() else "● Niet ingelogd",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["success"] if acc.is_authenticated() else COLORS["text_muted"],
            )
            status_dot.pack(side="right")

            # Naam instelling
            name_entry = self._label_entry(
                card, "Weergavenaam:", self.app.settings.get("accounts", acc_key, "name") or ""
            )

            # Credentials bestand
            cred_row = ctk.CTkFrame(card, fg_color="transparent")
            cred_row.pack(fill="x", padx=16, pady=6)
            ctk.CTkLabel(cred_row, text="Credentials bestand:", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"], width=180, anchor="w").pack(side="left")

            cred_status = "✓ Aanwezig" if acc.credentials_file.exists() else "✗ Niet gevonden"
            cred_color = COLORS["success"] if acc.credentials_file.exists() else COLORS["error"]
            ctk.CTkLabel(cred_row, text=cred_status, font=ctk.CTkFont(size=12), text_color=cred_color).pack(side="left", padx=(0, 12))

            ctk.CTkButton(
                cred_row,
                text="Bestand importeren",
                width=150,
                height=30,
                fg_color=COLORS["border"],
                hover_color=COLORS["accent2"],
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=12),
                command=lambda k=acc_key: self._import_credentials(k),
            ).pack(side="left")

            # Login knop
            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=16, pady=(4, 12))

            ctk.CTkButton(
                btn_row,
                text="🔑  Inloggen via browser",
                width=200,
                height=36,
                fg_color=COLORS["accent2"],
                hover_color="#1a6fa3",
                text_color="white",
                font=ctk.CTkFont(size=13),
                command=lambda k=acc_key, sd=status_dot: self._authenticate(k, sd),
            ).pack(side="left", padx=(0, 12))

            if acc.is_authenticated():
                ctk.CTkButton(
                    btn_row,
                    text="Uitloggen",
                    width=100,
                    height=36,
                    fg_color=COLORS["card"],
                    hover_color=COLORS["error"],
                    text_color=COLORS["text_muted"],
                    font=ctk.CTkFont(size=12),
                    command=lambda k=acc_key: self._logout(k),
                ).pack(side="left")

            # Naam opslaan bij wijziging
            def _save_name(event, k=acc_key, e=name_entry):
                self.app.settings.set("accounts", k, "name", e.get().strip())

            name_entry.bind("<FocusOut>", _save_name)

    def _import_credentials(self, acc_key: str):
        path = filedialog.askopenfilename(
            title=f"Selecteer credentials.json voor {acc_key}",
            filetypes=[("JSON bestanden", "*.json")],
        )
        if not path:
            return

        acc = self.app.youtube.get_account(acc_key)
        dest = acc.credentials_file
        shutil.copy2(path, dest)
        messagebox.showinfo("Geïmporteerd", f"Credentials opgeslagen als:\n{dest.name}\n\nLog nu in via de knop 'Inloggen via browser'.")
        self.on_show()

    def _authenticate(self, acc_key: str, status_label):
        def _do():
            try:
                acc = self.app.youtube.get_account(acc_key)
                acc.authenticate()
                self.after(0, lambda: status_label.configure(text="● Verbonden", text_color=COLORS["success"]))
                self.after(0, self.app.refresh_status)
                self.after(0, lambda: messagebox.showinfo("Succes", f"Succesvol ingelogd voor {acc.name}!"))
            except FileNotFoundError as e:
                self.after(0, lambda: messagebox.showerror("Fout", str(e)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Fout", f"Inloggen mislukt:\n{e}"))

        threading.Thread(target=_do, daemon=True).start()

    def _logout(self, acc_key: str):
        if not messagebox.askyesno("Uitloggen", f"Weet u zeker dat u wilt uitloggen?"):
            return
        acc = self.app.youtube.get_account(acc_key)
        if acc.token_file.exists():
            acc.token_file.unlink()
        acc.service = None
        self.app.refresh_status()
        self.on_show()

    # ── Predikanten ───────────────────────────────────────────────────────

    def _build_predikanten_section(self, parent):
        self._section(parent, "👤  Predikanten")
        card = self._card(parent)

        self.pred_list_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.pred_list_frame.pack(fill="x", padx=16, pady=12)
        self._render_predikanten()

        add_row = ctk.CTkFrame(card, fg_color="transparent")
        add_row.pack(fill="x", padx=16, pady=(0, 12))

        self.new_pred_entry = ctk.CTkEntry(
            add_row,
            placeholder_text="Naam predikant (bijv. ds. J. Janssen)",
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
            height=34,
        )
        self.new_pred_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            add_row,
            text="+ Toevoegen",
            width=120,
            height=34,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
            font=ctk.CTkFont(size=13),
            command=self._add_predikant,
        ).pack(side="left")

    def _render_predikanten(self):
        for w in self.pred_list_frame.winfo_children():
            w.destroy()

        predikanten = self.app.settings.get_predikanten()
        if not predikanten:
            ctk.CTkLabel(
                self.pred_list_frame,
                text="Geen predikanten ingesteld.",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_muted"],
            ).pack(anchor="w")
            return

        for pred in predikanten:
            row = ctk.CTkFrame(self.pred_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(
                row,
                text=pred["naam"],
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text"],
            ).pack(side="left")
            ctk.CTkButton(
                row,
                text="✕",
                width=28,
                height=24,
                fg_color="transparent",
                hover_color=COLORS["error"],
                text_color=COLORS["text_muted"],
                font=ctk.CTkFont(size=12),
                command=lambda n=pred["naam"]: self._remove_predikant(n),
            ).pack(side="right")

    def _add_predikant(self):
        naam = self.new_pred_entry.get().strip()
        if not naam:
            return
        self.app.settings.add_predikant(naam)
        self.new_pred_entry.delete(0, "end")
        self._render_predikanten()

    def _remove_predikant(self, naam: str):
        self.app.settings.remove_predikant(naam)
        self._render_predikanten()

    # ── Titel template ────────────────────────────────────────────────────

    def _build_template_section(self, parent):
        self._section(parent, "📝  Titel template")
        card = self._card(parent)

        ctk.CTkLabel(
            card,
            text="Gebruik {predikant} en {schriftgedeelte} als plaatshouders.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        self.template_entry = self._label_entry(
            card,
            "Template:",
            self.app.settings.get("titel_template") or "{predikant} | {schriftgedeelte}",
        )

        ctk.CTkLabel(
            card,
            text="Voorbeeld: 'Kerkdienst | {predikant} — {schriftgedeelte}'",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=16, pady=(2, 12))

    # ── Standaard omschrijving ────────────────────────────────────────────

    def _build_description_section(self, parent):
        self._section(parent, "📄  Standaard omschrijving")
        card = self._card(parent)

        ctk.CTkLabel(
            card,
            text="Deze omschrijving wordt standaard ingevuld bij elke nieuwe stream.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=16, pady=(12, 6))

        self.default_desc_text = ctk.CTkTextbox(
            card,
            height=100,
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
            border_width=1,
        )
        self.default_desc_text.pack(fill="x", padx=16, pady=(0, 12))
        default = self.app.settings.get("standaard_omschrijving") or ""
        if default:
            self.default_desc_text.insert("1.0", default)

    # ── Stream defaults ───────────────────────────────────────────────────

    def _build_stream_defaults_section(self, parent):
        self._section(parent, "📡  Stream standaardwaarden")
        card = self._card(parent)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        defaults = self.app.settings.get("stream_defaults") or {}

        # Privacy
        priv_row = ctk.CTkFrame(inner, fg_color="transparent")
        priv_row.pack(fill="x", pady=4)
        ctk.CTkLabel(priv_row, text="Standaard privacy:", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"], width=200, anchor="w").pack(side="left")
        self.privacy_var = tk.StringVar(value=defaults.get("privacy", "public"))
        ctk.CTkOptionMenu(
            priv_row,
            variable=self.privacy_var,
            values=["public", "unlisted", "private"],
            fg_color=COLORS["input_bg"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["card"],
            text_color=COLORS["text"],
            width=150,
            height=32,
        ).pack(side="left")

        # Latency
        lat_row = ctk.CTkFrame(inner, fg_color="transparent")
        lat_row.pack(fill="x", pady=4)
        ctk.CTkLabel(lat_row, text="Latency voorkeur:", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"], width=200, anchor="w").pack(side="left")
        self.latency_var = tk.StringVar(value=defaults.get("latency_preference", "normal"))
        ctk.CTkOptionMenu(
            lat_row,
            variable=self.latency_var,
            values=["normal", "low", "ultraLow"],
            fg_color=COLORS["input_bg"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["card"],
            text_color=COLORS["text"],
            width=150,
            height=32,
        ).pack(side="left")

        # DVR
        self.dvr_var = tk.BooleanVar(value=defaults.get("enable_dvr", True))
        ctk.CTkCheckBox(
            inner,
            text="DVR inschakelen (terugkijken tijdens livestream)",
            variable=self.dvr_var,
            fg_color=COLORS["accent"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", pady=4)

        self.record_var = tk.BooleanVar(value=defaults.get("record_from_start", True))
        ctk.CTkCheckBox(
            inner,
            text="Opnemen vanaf het begin",
            variable=self.record_var,
            fg_color=COLORS["accent"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", pady=4)

    # ── Overige ───────────────────────────────────────────────────────────

    def _build_misc_section(self, parent):
        self._section(parent, "⚙️  Overige instellingen")
        card = self._card(parent)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        days_row = ctk.CTkFrame(inner, fg_color="transparent")
        days_row.pack(fill="x", pady=4)
        ctk.CTkLabel(days_row, text="Archiveren na (dagen):", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"], width=200, anchor="w").pack(side="left")
        self.archive_days_entry = ctk.CTkEntry(
            days_row,
            width=80,
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
            height=32,
        )
        self.archive_days_entry.insert(0, str(self.app.settings.get("app", "archive_after_days") or 180))
        self.archive_days_entry.pack(side="left")

        # Data directory info
        data_row = ctk.CTkFrame(inner, fg_color="transparent")
        data_row.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(data_row, text="Data locatie:", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"], width=200, anchor="w").pack(side="left")
        ctk.CTkLabel(
            data_row,
            text=str(self.app.settings.get_data_dir()),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
        ).pack(side="left")

    # ── Opslaan ───────────────────────────────────────────────────────────

    def _save(self):
        # Template
        template = self.template_entry.get().strip()
        if template:
            self.app.settings.set("titel_template", template)

        # Omschrijving
        desc = self.default_desc_text.get("1.0", "end-1c").strip()
        self.app.settings.set("standaard_omschrijving", desc)

        # Stream defaults
        self.app.settings.set("stream_defaults", "privacy", self.privacy_var.get())
        self.app.settings.set("stream_defaults", "latency_preference", self.latency_var.get())
        self.app.settings.set("stream_defaults", "enable_dvr", self.dvr_var.get())
        self.app.settings.set("stream_defaults", "record_from_start", self.record_var.get())

        # Archief dagen
        try:
            days = int(self.archive_days_entry.get())
            self.app.settings.set("app", "archive_after_days", days)
        except ValueError:
            pass

        messagebox.showinfo("Opgeslagen", "Instellingen zijn opgeslagen.")

    def on_show(self):
        pass

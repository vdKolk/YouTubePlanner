"""
Stream inplannen scherm
"""

import threading
import calendar
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, Toplevel

try:
    import customtkinter as ctk
except ImportError:
    pass

COLORS = {
    "bg": "#0f1117",
    "sidebar": "#161b22",
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


class PlanFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self.app = app
        self.stream_keys_main = []
        self.stream_keys_tolk = []
        self._build()

    def _build(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(28, 0))

        ctk.CTkLabel(
            header,
            text="Stream inplannen",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left")

        # Scrollbaar gebied
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=COLORS["border"])
        scroll.pack(fill="both", expand=True, padx=32, pady=16)

        # ── Titelsectie ──────────────────────────────────────────────────
        self._section(scroll, "Uitzending titel")

        # Modus selector
        mode_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        mode_frame.pack(fill="x", pady=(4, 12))

        self.title_mode = tk.StringVar(value="auto")
        modes = [("Automatisch samenstellen", "auto"), ("Volledig handmatig", "manual")]
        for label, val in modes:
            ctk.CTkRadioButton(
                mode_frame,
                text=label,
                variable=self.title_mode,
                value=val,
                command=self._on_title_mode_change,
                text_color=COLORS["text"],
                fg_color=COLORS["accent"],
                border_color=COLORS["border"],
                font=ctk.CTkFont(size=13),
            ).pack(side="left", padx=(0, 24))

        # Automatische velden
        self.auto_frame = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        self.auto_frame.pack(fill="x", pady=(0, 8))

        inner = ctk.CTkFrame(self.auto_frame, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        # Predikant
        left_col = ctk.CTkFrame(inner, fg_color="transparent")
        left_col.pack(side="left", fill="x", expand=True, padx=(0, 12))

        ctk.CTkLabel(left_col, text="Predikant", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(anchor="w", pady=(0, 4))

        predikanten = [p["naam"] for p in self.app.settings.get_predikanten()]
        predikanten.append("Handmatig invoeren...")

        self.predikant_var = tk.StringVar(value=predikanten[0] if predikanten else "")
        self.predikant_menu = ctk.CTkOptionMenu(
            left_col,
            variable=self.predikant_var,
            values=predikanten,
            command=self._on_predikant_change,
            fg_color=COLORS["input_bg"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["card"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
            height=36,
        )
        self.predikant_menu.pack(fill="x")

        self.predikant_manual_entry = ctk.CTkEntry(
            left_col,
            placeholder_text="Naam predikant invoeren...",
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
            height=36,
        )
        # Pas zichtbaar bij "Handmatig invoeren"

        # Schriftgedeelte
        right_col = ctk.CTkFrame(inner, fg_color="transparent")
        right_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(right_col, text="Schriftgedeelte", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(anchor="w", pady=(0, 4))
        self.schrift_entry = ctk.CTkEntry(
            right_col,
            placeholder_text="bijv. Johannes 3:16",
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
            height=36,
        )
        self.schrift_entry.pack(fill="x")
        self.schrift_entry.bind("<KeyRelease>", lambda e: self._update_preview())

        # Titel preview
        preview_frame = ctk.CTkFrame(self.auto_frame, fg_color="transparent")
        preview_frame.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkLabel(preview_frame, text="Voorbeeld:", font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]).pack(side="left", padx=(0, 8))
        self.title_preview = ctk.CTkLabel(
            preview_frame,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["accent2"],
        )
        self.title_preview.pack(side="left")

        # Handmatige titel
        self.manual_frame = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        ctk.CTkLabel(
            self.manual_frame,
            text="Handmatige titel",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=16, pady=(12, 4))
        self.manual_title_entry = ctk.CTkEntry(
            self.manual_frame,
            placeholder_text="Volledige titel invoeren...",
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
            height=36,
        )
        self.manual_title_entry.pack(fill="x", padx=16, pady=(0, 12))

        # Begin met auto modus zichtbaar
        self._on_title_mode_change()

        # ── Datum & Tijd ─────────────────────────────────────────────────
        self._section(scroll, "Datum & tijdstip")

        dt_card = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        dt_card.pack(fill="x", pady=(0, 8))
        dt_inner = ctk.CTkFrame(dt_card, fg_color="transparent")
        dt_inner.pack(fill="x", padx=16, pady=12)

        # Datum
        date_col = ctk.CTkFrame(dt_inner, fg_color="transparent")
        date_col.pack(side="left", fill="x", expand=True, padx=(0, 12))
        ctk.CTkLabel(date_col, text="Datum (DD-MM-JJJJ)", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(anchor="w", pady=(0, 4))

        date_row = ctk.CTkFrame(date_col, fg_color="transparent")
        date_row.pack(fill="x")
        self.date_entry = ctk.CTkEntry(
            date_row,
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
            height=36,
        )
        self.date_entry.insert(0, datetime.now().strftime("%d-%m-%Y"))
        self.date_entry.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            date_row,
            text="📅",
            width=36,
            height=36,
            fg_color=COLORS["border"],
            hover_color=COLORS["accent2"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=14),
            command=self._open_calendar,
        ).pack(side="left", padx=(4, 0))

        # Tijd
        time_col = ctk.CTkFrame(dt_inner, fg_color="transparent")
        time_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(time_col, text="Begintijd (UU:MM)", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(anchor="w", pady=(0, 4))
        self.time_entry = ctk.CTkEntry(
            time_col,
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
            height=36,
        )
        self.time_entry.insert(0, self._smart_default_time())
        self.time_entry.pack(fill="x")

        # ── Omschrijving ─────────────────────────────────────────────────
        self._section(scroll, "Omschrijving")

        desc_card = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        desc_card.pack(fill="x", pady=(0, 8))

        # Knop om standaard omschrijving te laden
        desc_top = ctk.CTkFrame(desc_card, fg_color="transparent")
        desc_top.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(desc_top, text="Omschrijving", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(side="left")
        ctk.CTkButton(
            desc_top,
            text="Standaard laden",
            width=130,
            height=26,
            fg_color=COLORS["border"],
            hover_color=COLORS["accent2"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=11),
            command=self._load_default_description,
        ).pack(side="right")

        self.desc_text = ctk.CTkTextbox(
            desc_card,
            height=100,
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
            border_width=1,
        )
        self.desc_text.pack(fill="x", padx=16, pady=(0, 12))

        default_desc = self.app.settings.get("standaard_omschrijving") or ""
        if default_desc:
            self.desc_text.insert("1.0", default_desc)

        # ── Streamkeys ───────────────────────────────────────────────────
        self._section(scroll, "Streamkeys")

        sk_card = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        sk_card.pack(fill="x", pady=(0, 8))
        sk_inner = ctk.CTkFrame(sk_card, fg_color="transparent")
        sk_inner.pack(fill="x", padx=16, pady=12)

        # Hoofd streamkey
        main_col = ctk.CTkFrame(sk_inner, fg_color="transparent")
        main_col.pack(side="left", fill="x", expand=True, padx=(0, 12))
        ctk.CTkLabel(main_col, text="Hoofdstream — streamkey", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(anchor="w", pady=(0, 4))

        self.streamkey_main_var = tk.StringVar(value="Laden...")
        self.streamkey_main_menu = ctk.CTkOptionMenu(
            main_col,
            variable=self.streamkey_main_var,
            values=["Laden..."],
            fg_color=COLORS["input_bg"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["card"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=12),
            height=36,
        )
        self.streamkey_main_menu.pack(fill="x")

        ctk.CTkButton(
            main_col,
            text="🔄 Vernieuwen",
            width=100,
            height=26,
            fg_color="transparent",
            hover_color=COLORS["card"],
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(size=11),
            command=lambda: self._load_stream_keys("main"),
        ).pack(anchor="w", pady=(4, 0))

        # Tolk streamkey
        tolk_col = ctk.CTkFrame(sk_inner, fg_color="transparent")
        tolk_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(tolk_col, text="Tolkstream — streamkey", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(anchor="w", pady=(0, 4))

        self.streamkey_tolk_var = tk.StringVar(value="Laden...")
        self.streamkey_tolk_menu = ctk.CTkOptionMenu(
            tolk_col,
            variable=self.streamkey_tolk_var,
            values=["Laden..."],
            fg_color=COLORS["input_bg"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["card"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=12),
            height=36,
        )
        self.streamkey_tolk_menu.pack(fill="x")

        ctk.CTkButton(
            tolk_col,
            text="🔄 Vernieuwen",
            width=100,
            height=26,
            fg_color="transparent",
            hover_color=COLORS["card"],
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(size=11),
            command=lambda: self._load_stream_keys("tolk"),
        ).pack(anchor="w", pady=(4, 0))

        # ── Tolkstream optie ─────────────────────────────────────────────
        self._section(scroll, "Tolkstream")

        tolk_toggle_card = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        tolk_toggle_card.pack(fill="x", pady=(0, 16))
        tolk_row = ctk.CTkFrame(tolk_toggle_card, fg_color="transparent")
        tolk_row.pack(fill="x", padx=16, pady=12)

        self.include_tolk = tk.BooleanVar(value=True)
        ctk.CTkSwitch(
            tolk_row,
            text="Tolkstream meenemen bij deze uitzending",
            variable=self.include_tolk,
            onvalue=True,
            offvalue=False,
            fg_color=COLORS["border"],
            progress_color=COLORS["accent"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left")

        # ── Actieknop ────────────────────────────────────────────────────
        action_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        action_frame.pack(fill="x", pady=(8, 24))

        self.plan_btn = ctk.CTkButton(
            action_frame,
            text="  ▶  Stream inplannen",
            height=48,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
            corner_radius=10,
            command=self._plan_stream,
        )
        self.plan_btn.pack(side="left", padx=(0, 12))

        self.status_label = ctk.CTkLabel(
            action_frame,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"],
        )
        self.status_label.pack(side="left")

        # Laad streamkeys na kleine vertraging
        self.after(500, self._load_all_stream_keys)

    def _section(self, parent, title: str):
        ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(16, 4))

    def _smart_default_time(self) -> str:
        """Geeft slimme standaard begintijd terug op basis van huidig tijdstip."""
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        current_minutes = hour * 60 + minute
        if current_minutes < 9 * 60 + 30:
            return "09:30"
        elif current_minutes < 16 * 60 + 30:
            return "16:30"
        else:
            return "19:30"

    def _open_calendar(self):
        """Open een kalender popup om een datum te kiezen."""
        # Lees huidige datum uit invoerveld
        try:
            current = datetime.strptime(self.date_entry.get().strip(), "%d-%m-%Y")
        except ValueError:
            current = datetime.now()

        popup = Toplevel(self.winfo_toplevel())
        popup.title("Datum kiezen")
        popup.configure(bg="#161b22")
        popup.resizable(False, False)
        popup.grab_set()  # modaal

        # Centreer popup
        popup.update_idletasks()
        x = self.winfo_toplevel().winfo_x() + self.winfo_toplevel().winfo_width() // 2 - 175
        y = self.winfo_toplevel().winfo_y() + self.winfo_toplevel().winfo_height() // 2 - 160
        popup.geometry(f"350x310+{x}+{y}")

        state = {"year": current.year, "month": current.month}

        # Header met maand/jaar navigatie
        header_frame = tk.Frame(popup, bg="#161b22")
        header_frame.pack(fill="x", padx=12, pady=(12, 6))

        month_label = tk.Label(
            header_frame, text="", bg="#161b22", fg="#e6edf3",
            font=("Segoe UI", 12, "bold")
        )
        month_label.pack(side="left", expand=True)

        def prev_month():
            if state["month"] == 1:
                state["month"] = 12
                state["year"] -= 1
            else:
                state["month"] -= 1
            render_calendar()

        def next_month():
            if state["month"] == 12:
                state["month"] = 1
                state["year"] += 1
            else:
                state["month"] += 1
            render_calendar()

        tk.Button(
            header_frame, text="◀", bg="#30363d", fg="#e6edf3",
            relief="flat", font=("Segoe UI", 11), cursor="hand2",
            activebackground="#c0392b", activeforeground="white",
            command=prev_month, padx=8
        ).pack(side="left", padx=(0, 4))

        tk.Button(
            header_frame, text="▶", bg="#30363d", fg="#e6edf3",
            relief="flat", font=("Segoe UI", 11), cursor="hand2",
            activebackground="#c0392b", activeforeground="white",
            command=next_month, padx=8
        ).pack(side="right", padx=(4, 0))

        # Kalender grid
        cal_frame = tk.Frame(popup, bg="#161b22")
        cal_frame.pack(fill="both", expand=True, padx=12, pady=4)

        MAANDEN_NL = [
            "", "Januari", "Februari", "Maart", "April", "Mei", "Juni",
            "Juli", "Augustus", "September", "Oktober", "November", "December"
        ]
        DAGEN_NL = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]

        def render_calendar():
            for w in cal_frame.winfo_children():
                w.destroy()
            month_label.configure(
                text=f"{MAANDEN_NL[state['month']]} {state['year']}"
            )
            # Dagnamen header
            for i, dag in enumerate(DAGEN_NL):
                tk.Label(
                    cal_frame, text=dag, bg="#161b22",
                    fg="#7d8590", font=("Segoe UI", 9, "bold"), width=4
                ).grid(row=0, column=i, padx=1, pady=(0, 4))

            cal = calendar.monthcalendar(state["year"], state["month"])
            for r, week in enumerate(cal):
                for c, day in enumerate(week):
                    if day == 0:
                        tk.Label(cal_frame, text="", bg="#161b22", width=4).grid(
                            row=r + 1, column=c, padx=1, pady=1
                        )
                    else:
                        is_today = (
                            day == datetime.now().day and
                            state["month"] == datetime.now().month and
                            state["year"] == datetime.now().year
                        )
                        is_selected = (
                            day == current.day and
                            state["month"] == current.month and
                            state["year"] == current.year
                        )
                        bg = "#c0392b" if is_selected else ("#2980b9" if is_today else "#21262d")
                        fg = "white" if (is_selected or is_today) else "#e6edf3"

                        def on_click(d=day):
                            chosen = datetime(state["year"], state["month"], d)
                            self.date_entry.delete(0, "end")
                            self.date_entry.insert(0, chosen.strftime("%d-%m-%Y"))
                            popup.destroy()

                        btn = tk.Button(
                            cal_frame, text=str(day), bg=bg, fg=fg,
                            relief="flat", font=("Segoe UI", 10),
                            cursor="hand2", width=3,
                            activebackground="#e74c3c", activeforeground="white",
                            command=on_click
                        )
                        btn.grid(row=r + 1, column=c, padx=1, pady=1, ipady=3)

        render_calendar()

        # Sluiten knop
        tk.Button(
            popup, text="Annuleren", bg="#30363d", fg="#7d8590",
            relief="flat", font=("Segoe UI", 10), cursor="hand2",
            activebackground="#21262d",
            command=popup.destroy
        ).pack(pady=(4, 12))

    def _on_title_mode_change(self):
        mode = self.title_mode.get()
        if mode == "auto":
            self.auto_frame.pack(fill="x", pady=(0, 8))
            self.manual_frame.pack_forget()
        else:
            self.auto_frame.pack_forget()
            self.manual_frame.pack(fill="x", pady=(0, 8))

    def _on_predikant_change(self, value):
        if value == "Handmatig invoeren...":
            self.predikant_manual_entry.pack(fill="x", pady=(6, 0))
            self.predikant_manual_entry.bind("<KeyRelease>", lambda e: self._update_preview())
        else:
            self.predikant_manual_entry.pack_forget()
        self._update_preview()

    def _update_preview(self):
        pred = self._get_predikant()
        schrift = self.schrift_entry.get().strip()
        template = self.app.settings.get("titel_template") or "{predikant} | {schriftgedeelte}"
        title = template.replace("{predikant}", pred).replace("{schriftgedeelte}", schrift)
        self.title_preview.configure(text=title)

    def _get_predikant(self) -> str:
        val = self.predikant_var.get()
        if val == "Handmatig invoeren...":
            return self.predikant_manual_entry.get().strip()
        return val

    def _get_title(self) -> str:
        if self.title_mode.get() == "manual":
            return self.manual_title_entry.get().strip()
        pred = self._get_predikant()
        schrift = self.schrift_entry.get().strip()
        template = self.app.settings.get("titel_template") or "{predikant} | {schriftgedeelte}"
        return template.replace("{predikant}", pred).replace("{schriftgedeelte}", schrift)

    def _get_description(self) -> str:
        return self.desc_text.get("1.0", "end-1c").strip()

    def _load_default_description(self):
        default = self.app.settings.get("standaard_omschrijving") or ""
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", default)

    def _load_all_stream_keys(self):
        self._load_stream_keys("main")
        self._load_stream_keys("tolk")

    def _load_stream_keys(self, account_key: str):
        def _fetch():
            acc = self.app.youtube.get_account(account_key)
            if not acc.is_authenticated():
                ok = acc.connect()
                if not ok:
                    self.after(0, lambda: self._set_streamkey_status(account_key, ["Niet ingelogd — zie Instellingen"]))
                    return
            keys = acc.get_stream_keys()
            if not keys:
                self.after(0, lambda: self._set_streamkey_status(account_key, ["Geen streamkeys gevonden"]))
                return
            labels = [f"{k['snippet']['title']} ({k['cdn'].get('streamName', 'onbekend')})" for k in keys]
            if account_key == "main":
                self.stream_keys_main = keys
            else:
                self.stream_keys_tolk = keys
            self.after(0, lambda: self._set_streamkey_status(account_key, labels))

        threading.Thread(target=_fetch, daemon=True).start()

    def _set_streamkey_status(self, account_key: str, labels: list):
        if account_key == "main":
            self.streamkey_main_menu.configure(values=labels)
            self.streamkey_main_var.set(labels[0])
        else:
            self.streamkey_tolk_menu.configure(values=labels)
            self.streamkey_tolk_var.set(labels[0])

    def _get_selected_stream_id(self, account_key: str) -> str:
        """Geef het stream_id terug van de geselecteerde streamkey"""
        if account_key == "main":
            keys = self.stream_keys_main
            label = self.streamkey_main_var.get()
        else:
            keys = self.stream_keys_tolk
            label = self.streamkey_tolk_var.get()

        for k in keys:
            key_label = f"{k['snippet']['title']} ({k['cdn'].get('streamName', 'onbekend')})"
            if key_label == label:
                return k["id"]
        return None

    def _parse_datetime(self) -> datetime:
        date_str = self.date_entry.get().strip()
        time_str = self.time_entry.get().strip()
        return datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M")

    def _plan_stream(self):
        title = self._get_title()
        if not title:
            messagebox.showerror("Fout", "Vul een titel in.")
            return

        try:
            scheduled_dt = self._parse_datetime()
        except ValueError:
            messagebox.showerror("Fout", "Ongeldige datum of tijd. Gebruik DD-MM-JJJJ en UU:MM.")
            return

        description = self._get_description()
        include_tolk = self.include_tolk.get()

        self.plan_btn.configure(state="disabled", text="Bezig...")
        self.status_label.configure(text="Streams worden aangemaakt...", text_color=COLORS["warning"])

        def _do_plan():
            result = {"success": True, "errors": []}
            record = {
                "title": title,
                "scheduled_start": scheduled_dt.isoformat(),
                "description": description,
                "include_tolk": include_tolk,
            }

            # Hoofdstream
            try:
                acc = self.app.youtube.main
                if not acc.is_authenticated():
                    acc.connect()

                broadcast = acc.create_broadcast(
                    title=title,
                    description=description,
                    scheduled_start=scheduled_dt,
                    **self._get_stream_defaults(),
                )
                broadcast_id = broadcast["id"]
                record["main_broadcast_id"] = broadcast_id

                stream_id = self._get_selected_stream_id("main")
                if stream_id:
                    acc.bind_broadcast_to_stream(broadcast_id, stream_id)
                    record["main_stream_id"] = stream_id

            except Exception as e:
                result["errors"].append(f"Hoofdstream: {e}")
                result["success"] = False

            # Tolkstream
            if include_tolk and result["success"]:
                try:
                    acc = self.app.youtube.tolk
                    if not acc.is_authenticated():
                        acc.connect()

                    broadcast = acc.create_broadcast(
                        title=title,
                        description=description,
                        scheduled_start=scheduled_dt,
                        **self._get_stream_defaults(),
                    )
                    broadcast_id = broadcast["id"]
                    record["tolk_broadcast_id"] = broadcast_id

                    stream_id = self._get_selected_stream_id("tolk")
                    if stream_id:
                        acc.bind_broadcast_to_stream(broadcast_id, stream_id)
                        record["tolk_stream_id"] = stream_id

                except Exception as e:
                    result["errors"].append(f"Tolkstream: {e}")

            self.app.db.add(record)
            self.after(0, lambda: self._plan_done(result))

        threading.Thread(target=_do_plan, daemon=True).start()

    def _get_stream_defaults(self) -> dict:
        d = self.app.settings.get("stream_defaults") or {}
        return {
            "privacy": d.get("privacy", "public"),
            "made_for_kids": d.get("made_for_kids", False),
            "enable_dvr": d.get("enable_dvr", True),
            "record_from_start": d.get("record_from_start", True),
            "latency_preference": d.get("latency_preference", "normal"),
        }

    def _plan_done(self, result: dict):
        self.plan_btn.configure(state="normal", text="  ▶  Stream inplannen")
        if result["success"]:
            self.status_label.configure(text="✓ Succesvol ingepland!", text_color=COLORS["success"])
            messagebox.showinfo("Succes", "De stream(s) zijn succesvol ingepland op YouTube!")
        else:
            errors = "\n".join(result["errors"])
            self.status_label.configure(text="Fout bij inplannen", text_color=COLORS["error"])
            messagebox.showerror("Fout", f"Er ging iets mis:\n{errors}")

    def on_show(self):
        # Ververs predikantenlijst
        predikanten = [p["naam"] for p in self.app.settings.get_predikanten()]
        predikanten.append("Handmatig invoeren...")
        current = self.predikant_var.get()
        self.predikant_menu.configure(values=predikanten)
        if current not in predikanten:
            self.predikant_var.set(predikanten[0] if predikanten else "")

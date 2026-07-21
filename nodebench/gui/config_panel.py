from __future__ import annotations
import json
from pathlib import Path
from tkinter import StringVar
import customtkinter as ctk
from nodebench.gui.i18n import t, set_language, CURRENT_LANG, LANGUAGES

CONFIG_PATH = Path(__file__).parent.parent.parent / "nodebench_config.json"

DEFAULTS = {
    "api": "http://127.0.0.1:9090", "secret": "",
    "proxy": "socks5://127.0.0.1:7890", "group": "",
    "download_bytes": 25_000_000, "upload_bytes": 25_000_000,
    "bandwidth_timeout": 20.0, "switch_wait": 0.5, "language": "zh",
}

# (key, internal_name, ftype, i18n_key)
FIELD_META = [
    ("api", "API", "str", "cfg_api"),
    ("secret", "Secret", "str", "cfg_secret"),
    ("proxy", "Proxy", "str", "cfg_proxy"),
    ("group", "Group", "combo", "cfg_group"),
    ("download_bytes", "Download", "int", "cfg_download"),
    ("upload_bytes", "Upload", "int", "cfg_upload"),
    ("bandwidth_timeout", "Bandwidth TO", "float", "cfg_bw_timeout"),
    ("switch_wait", "Switch Wait", "float", "cfg_switch_wait"),
]

def _load_config() -> dict:
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    return cfg

class ConfigPanel(ctk.CTkFrame):
    def __init__(self, master, on_lang_change=None, **kwargs):
        super().__init__(master, **kwargs)
        self._on_lang_change = on_lang_change
        self._entries: dict[str, ctk.CTkEntry] = {}
        self._string_vars: dict[str, StringVar] = {}
        self._combo_entries: dict[str, ctk.CTkComboBox] = {}
        self._combo_var: StringVar = StringVar(value="")
        self._labels: dict[str, ctk.CTkLabel] = {}
        self._build_ui()
        self._load_json()

    def _build_ui(self):
        self._content = ctk.CTkScrollableFrame(self, width=240)
        self._content.pack(fill="both", expand=True, padx=4, pady=4)

        # Language selector
        lang_row = ctk.CTkFrame(self._content, fg_color="transparent")
        lang_row.pack(fill="x", pady=1)
        self._lang_lbl = ctk.CTkLabel(lang_row, text=t("cfg_language"), width=100, anchor="w")
        self._lang_lbl.pack(side="left", padx=(0, 4))
        self._lang_combo = ctk.CTkComboBox(
            lang_row, width=130, height=26,
            values=list(LANGUAGES.values()),
            command=self._on_lang_select
        )
        self._lang_combo.set(LANGUAGES.get(CURRENT_LANG, "English"))
        self._lang_combo.pack(side="right")

        # Config fields
        for key, _, ftype, i18n_key in FIELD_META:
            row = ctk.CTkFrame(self._content, fg_color="transparent")
            row.pack(fill="x", pady=1)
            lbl = ctk.CTkLabel(row, text=t(i18n_key), width=100, anchor="w")
            lbl.pack(side="left", padx=(0, 4))
            self._labels[i18n_key] = lbl
            if ftype in ("str", "int", "float"):
                var = StringVar()
                entry = ctk.CTkEntry(row, width=130, height=26, textvariable=var)
                entry.pack(side="right")
                self._string_vars[key] = var
            elif ftype == "combo":
                auto_txt = t("cfg_auto_detect")
                combo = ctk.CTkComboBox(row, width=130, height=26, values=[auto_txt], variable=self._combo_var)
                combo.set(auto_txt)
                combo.pack(side="right")
                self._combo_entries[key] = combo
                entry = combo
            else:
                continue
            self._entries[key] = entry

        # Save button
        btn_row = ctk.CTkFrame(self._content, fg_color="transparent")
        btn_row.pack(fill="x", pady=(8, 0))
        self._btn_save = ctk.CTkButton(btn_row, text=t("cfg_save"), command=self.save_config, height=28, fg_color="#2E7D32")
        self._btn_save.pack(fill="x")

    def _on_lang_select(self, choice):
        lang_map = {v: k for k, v in LANGUAGES.items()}
        lang = lang_map.get(choice, "zh")
        set_language(lang)
        self._refresh_texts()
        if self._on_lang_change:
            self._on_lang_change()

    def _refresh_texts(self):
        self._lang_lbl.configure(text=t("cfg_language"))
        for i18n_key, lbl in self._labels.items():
            lbl.configure(text=t(i18n_key))
        self._btn_save.configure(text=t("cfg_save"))
        if "group" in self._combo_entries:
            auto_txt = t("cfg_auto_detect")
            combo = self._combo_entries["group"]
            combo.configure(values=[auto_txt])
            combo.set(auto_txt)

    def _load_json(self):
        cfg = _load_config()
        # Apply saved language
        saved_lang = cfg.get("language", "zh")
        if saved_lang in LANGUAGES:
            set_language(saved_lang)
            self._lang_combo.set(LANGUAGES[saved_lang])
        self._set_vals(cfg)
        self._refresh_texts()

    def _set_vals(self, cfg: dict):
        auto_txt = t("cfg_auto_detect")
        for key, _, ftype, _ in FIELD_META:
            val = cfg.get(key, DEFAULTS.get(key))
            if key in self._string_vars:
                if ftype == "int":
                    try:
                        display = int(val)
                        if key in ("download_bytes", "upload_bytes"):
                            display //= 1_000_000
                    except (ValueError, TypeError):
                        display = 25
                    self._string_vars[key].set(str(display))
                elif ftype == "float":
                    try:
                        self._string_vars[key].set(str(float(val)))
                    except (ValueError, TypeError):
                        self._string_vars[key].set(str(DEFAULTS.get(key, 0.0)))
                else:
                    self._string_vars[key].set(str(val or ""))
            elif ftype == "combo" and key in self._combo_entries:
                group_val = val if val and str(val).strip() else auto_txt
                self._combo_var.set(group_val)

    def get_config(self) -> dict:
        cfg = {}
        auto_txt = t("cfg_auto_detect")
        for key, _, ftype, _ in FIELD_META:
            if key in self._string_vars:
                raw = self._string_vars[key].get().strip()
                if ftype == "int":
                    try:
                        v = int(raw) if raw else 25
                        if key in ("download_bytes", "upload_bytes"):
                            v *= 1_000_000
                        cfg[key] = v
                    except ValueError:
                        cfg[key] = 25_000_000 if key in ("download_bytes", "upload_bytes") else 25
                elif ftype == "float":
                    try:
                        cfg[key] = float(raw) if raw else 0.0
                    except ValueError:
                        cfg[key] = 0.0
                else:
                    cfg[key] = raw
            elif ftype == "combo" and key in self._combo_entries:
                val = self._combo_var.get()
                cfg[key] = val if val != auto_txt else ""
        cfg["language"] = CURRENT_LANG
        return cfg

    def set_group_options(self, groups: list[str]):
        if "group" not in self._combo_entries:
            return
        auto_txt = t("cfg_auto_detect")
        options = [auto_txt] + sorted(groups)
        current = self._combo_var.get()
        self._combo_entries["group"].configure(values=options)
        if current and current in options:
            self._combo_var.set(current)

    def save_config(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.get_config(), f, indent=2)
        save_txt = t("cfg_saved")
        self._btn_save.configure(text=save_txt, fg_color="#388E3C")
        self.after(1200, lambda: self._btn_save.configure(text=t("cfg_save"), fg_color="#2E7D32"))

from __future__ import annotations
import json
from pathlib import Path
from tkinter import StringVar
import customtkinter as ctk

CONFIG_PATH = Path(__file__).parent.parent.parent / "nodebench_config.json"

DEFAULTS = {
    "api": "http://127.0.0.1:9090", "secret": "",
    "proxy": "socks5://127.0.0.1:7890", "group": "",
    "download_bytes": 25_000_000, "upload_bytes": 25_000_000,
    "bandwidth_timeout": 20.0, "switch_wait": 0.5,
}

FIELD_META = [
    ("api", "API", "str", "API Address"),
    ("secret", "Secret", "str", "Secret"),
    ("proxy", "Proxy", "str", "Proxy URL"),
    ("group", "Group", "combo", "Proxy Group"),
    ("download_bytes", "Download", "int", "Download (MB)"),
    ("upload_bytes", "Upload", "int", "Upload (MB)"),
    ("bandwidth_timeout", "Bandwidth TO", "float", "Bandwidth Timeout (s)"),
    ("switch_wait", "Switch Wait", "float", "Switch Wait (s)"),
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
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._entries: dict[str, ctk.CTkEntry] = {}
        self._string_vars: dict[str, StringVar] = {}
        self._combo_entries: dict[str, ctk.CTkComboBox] = {}
        self._combo_var: StringVar = StringVar(value="")
        self._build_ui()
        self._load_json()

    def _build_ui(self):
        self._content = ctk.CTkScrollableFrame(self, width=240)
        self._content.pack(fill="both", expand=True, padx=4, pady=4)
        for key, label, ftype, screen_name in FIELD_META:
            row = ctk.CTkFrame(self._content, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=screen_name, width=100, anchor="w").pack(side="left", padx=(0, 4))
            if ftype in ("str", "int", "float"):
                var = StringVar()
                entry = ctk.CTkEntry(row, width=130, height=26, textvariable=var)
                entry.pack(side="right")
                self._string_vars[key] = var
            elif ftype == "combo":
                combo = ctk.CTkComboBox(row, width=130, height=26, values=["(auto-detect)"], variable=self._combo_var)
                combo.set("(auto-detect)")
                combo.pack(side="right")
                self._combo_entries[key] = combo
                entry = combo
            else:
                continue
            self._entries[key] = entry

    def _load_json(self):
        self._set_vals(_load_config())

    def _set_vals(self, cfg: dict):
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
                group_val = val if val and str(val).strip() else "(auto-detect)"
                self._combo_var.set(group_val)

    def get_config(self) -> dict:
        cfg = {}
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
                cfg[key] = val if val != "(auto-detect)" else ""
        return cfg

    def set_group_options(self, groups: list[str]):
        if "group" not in self._combo_entries:
            return
        options = ["(auto-detect)"] + sorted(groups)
        current = self._combo_var.get()
        self._combo_entries["group"].configure(values=options)
        if current and current in options:
            self._combo_var.set(current)

    def save_config(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.get_config(), f, indent=2)

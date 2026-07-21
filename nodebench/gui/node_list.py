from __future__ import annotations
from typing import Optional
import customtkinter as ctk
from nodebench.models import Node
from nodebench.gui.i18n import t

COL_KEYS = [
    ("sel",    30,  None,    "center"),
    ("name",   180, "name",  "w"),
    ("lat",    70,  "lat",   "e"),
    ("dl",     75,  "dl",    "e"),
    ("ul",     75,  "ul",    "e"),
    ("status", 50,  "status", "center"),
]

def get_columns():
    return [
        ("",         30,  None,    "center"),
        (t("col_name"),     180, "name",  "w"),
        (t("col_latency"),  70,  "lat",   "e"),
        (t("col_download"), 75,  "dl",    "e"),
        (t("col_upload"),   75,  "ul",    "e"),
        (t("col_status"),   50,  "status", "center"),
    ]

ROW_HEIGHT = 28
COLORS = {
    "header_bg": ("gray25", "gray20"),
    "even_row": ("gray17", "gray14"),
    "odd_row": ("gray20", "gray17"),
    "selected": ("#2A5A8C", "#1E4A6E"),
    "text_ok": ("white", "white"),
    "text_dead": ("gray50", "gray50"),
    "text_muted": ("gray60", "gray50"),
}

def flag_emoji(country_code: str) -> str:
    if not country_code or len(country_code) != 2:
        return ""
    return chr(0x1F1E6 + ord(country_code[0]) - ord("A")) + chr(0x1F1E6 + ord(country_code[1]) - ord("A"))

class NodeTable(ctk.CTkScrollableFrame):
    def __init__(self, master, on_activate=None, **kwargs):
        super().__init__(master, **kwargs)
        self._rows: list[dict] = []
        self._last_clicked: int = -1
        self._selected_set: set[int] = set()
        self._on_activate = on_activate  # callback(node) when double-clicked

    def clear(self):
        for r in self._rows:
            r["frame"].destroy()
        self._rows.clear()
        self._last_clicked = -1
        self._selected_set.clear()

    def add_nodes(self, nodes: list[Node]):
        sorted_nodes = sorted(nodes, key=lambda n: (n.latency or 9999))
        self.clear()
        self._build_header()
        for i, node in enumerate(sorted_nodes):
            self._add_row(i, node)

    def get_selected(self) -> list[Node]:
        return [self._rows[i]["node"] for i in sorted(self._selected_set)]

    def select_all(self):
        self._selected_set.clear()
        for i, r in enumerate(self._rows):
            if r["node"].reachable:
                self._selected_set.add(i)
        self._refresh_colors()

    def deselect_all(self):
        self._selected_set.clear()
        self._refresh_colors()

    def update_node_by_name(self, name: str, download: Optional[float], upload: Optional[float]):
        for i, r in enumerate(self._rows):
            if r["node"].name == name:
                r["node"].download = download
                r["node"].upload = upload
                self._update_cells(i, r["node"])
                return

    def _build_header(self):
        hdr_frame = ctk.CTkFrame(self, height=ROW_HEIGHT, fg_color=COLORS["header_bg"])
        hdr_frame.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        columns = get_columns()
        for col_idx, (header, width, _, align) in enumerate(columns):
            lbl = ctk.CTkLabel(hdr_frame, text=header, width=width, anchor=align, font=ctk.CTkFont(size=12, weight="bold"))
            lbl.grid(row=0, column=col_idx, padx=1, sticky="nsew")
        hdr_frame.grid_columnconfigure(1, weight=1)

    def _add_row(self, index: int, node: Node):
        bg = COLORS["even_row"] if index % 2 == 0 else COLORS["odd_row"]
        frame = ctk.CTkFrame(self, height=ROW_HEIGHT, fg_color=bg)
        frame.grid(row=index + 1, column=0, sticky="ew", pady=1)
        cells = {}
        columns = get_columns()
        na = t("na")
        for col_idx, (_, width, key, align) in enumerate(columns):
            if key is None:
                text = "\u2713"
                color = COLORS["text_ok"] if node.reachable else COLORS["text_dead"]
            elif key == "name":
                text = node.name
                color = COLORS["text_ok"] if node.reachable else COLORS["text_dead"]
            elif key == "lat":
                text = f"{node.latency:.0f}{t('unit_ms')}" if node.latency else na
                color = COLORS["text_ok"]
            elif key == "dl":
                text = f"{node.download / 8:.1f}" if node.download else na
                color = COLORS["text_muted"]
            elif key == "ul":
                text = f"{node.upload / 8:.1f}" if node.upload else na
                color = COLORS["text_muted"]
            elif key == "status":
                text = "\u2713" if node.reachable else "\u2717"
                color = "#4CAF50" if node.reachable else "#F44336"
            else:
                text, color = na, COLORS["text_ok"]
            lbl = ctk.CTkLabel(frame, text=text, width=width, anchor=align, font=ctk.CTkFont(size=13), text_color=color)
            lbl.grid(row=0, column=col_idx, padx=1, sticky="nsew")
            cells[key or "sel"] = lbl
        frame.grid_columnconfigure(1, weight=1)
        frame.bind("<Button-1>", lambda e, idx=index: self._on_row_click(e, idx))
        frame.bind("<Double-Button-1>", lambda e, idx=index: self._on_double_click(idx))
        for l in cells.values():
            l.bind("<Button-1>", lambda e, idx=index: self._on_row_click(e, idx))
            l.bind("<Double-Button-1>", lambda e, idx=index: self._on_double_click(idx))
        self._rows.append({"frame": frame, "cells": cells, "node": node})
        if node.reachable:
            self._selected_set.add(index)

    def _on_row_click(self, event, index: int):
        state = int(event.state)
        if state & 0x0001:
            self._select_range(self._last_clicked, index)
        elif state & 0x0004:
            if index in self._selected_set:
                self._selected_set.discard(index)
            else:
                self._selected_set.add(index)
        else:
            if self._selected_set == {index}:
                self._selected_set.discard(index)
            else:
                self._selected_set.clear()
                self._selected_set.add(index)
        self._last_clicked = index
        self._refresh_colors()

    def _on_double_click(self, index: int):
        if self._on_activate and index < len(self._rows):
            self._on_activate(self._rows[index]["node"])

    def _select_range(self, start: int, end: int):
        if start < 0:
            start = 0
        lo, hi = min(start, end), max(start, end)
        self._selected_set.clear()
        for i in range(lo, hi + 1):
            if self._rows[i]["node"].reachable:
                self._selected_set.add(i)

    def _refresh_colors(self):
        for i, row_data in enumerate(self._rows):
            if i in self._selected_set:
                row_data["frame"].configure(fg_color=COLORS["selected"])
                row_data["cells"]["sel"].configure(text_color=("#88BBFF", "#88BBFF"))
            else:
                bg = COLORS["even_row"] if i % 2 == 0 else COLORS["odd_row"]
                row_data["frame"].configure(fg_color=bg)
                row_data["cells"]["sel"].configure(text_color=COLORS["text_muted"])

    def _update_cells(self, index: int, node: Node):
        if index >= len(self._rows):
            return
        na = t("na")
        cells = self._rows[index]["cells"]
        cells["lat"].configure(text=f"{node.latency:.0f}{t('unit_ms')}" if node.latency else na)
        cells["dl"].configure(text=f"{node.download / 8:.1f}" if node.download else na)
        cells["ul"].configure(text=f"{node.upload / 8:.1f}" if node.upload else na)

    def refresh_headers(self):
        """Rebuild header with current language."""
        if self._rows:
            self._rows.clear()
        self.clear()
        self._build_header()

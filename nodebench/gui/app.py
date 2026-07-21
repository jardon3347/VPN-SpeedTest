from __future__ import annotations
import csv
import queue
import threading
from pathlib import Path
import customtkinter as ctk
from nodebench.gui.config_panel import ConfigPanel
from nodebench.gui.log_panel import LogPanel
from nodebench.gui.node_list import NodeTable, flag_emoji
from nodebench.gui.test_runner import TestRunner
from nodebench.gui.i18n import t
from nodebench.mihomo_client import MihomoClient
from nodebench.models import TestConfig

OUTPUT_DIR = Path(__file__).parent.parent.parent / "outputs"

class NodeBenchApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title(t("window_title"))
        self.geometry("1050x750")
        self.minsize(950, 550)
        self._runner: TestRunner | None = None
        self._nodes: list = []
        self._all_nodes: list = []
        self._build_ui()
        self._refresh_all_texts()
        self._poll_messages()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0, minsize=260)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=3)
        self.grid_rowconfigure(1, weight=2)
        self._config = ConfigPanel(self, on_lang_change=self._refresh_all_texts)
        self._config.grid(row=0, column=0, sticky="nsew", padx=4, pady=(4, 2))
        self._log = LogPanel(self)
        self._log.grid(row=1, column=0, sticky="nsew", padx=4, pady=(2, 4))
        self._right = ctk.CTkFrame(self)
        self._right.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(0, 4), pady=4)
        self._right.grid_columnconfigure(0, weight=1)
        self._right.grid_rowconfigure(0, weight=0)
        self._right.grid_rowconfigure(1, weight=1)
        self._right.grid_rowconfigure(2, weight=0)
        self._build_toolbar()
        self._build_node_list()
        self._build_progress_area()

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self._right, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(2, 4))
        self._btn_stage1 = ctk.CTkButton(toolbar, text=t("btn_stage1"), command=self._on_stage1, width=140)
        self._btn_stage1.pack(side="left", padx=2)
        self._btn_stage2 = ctk.CTkButton(toolbar, text=t("btn_stage2"), command=self._on_stage2, width=140, state="disabled")
        self._btn_stage2.pack(side="left", padx=2)
        self._btn_all = ctk.CTkButton(toolbar, text=t("btn_select_all"), command=self._on_select_all, width=80, fg_color="gray")
        self._btn_all.pack(side="left", padx=2)
        self._btn_none = ctk.CTkButton(toolbar, text=t("btn_select_none"), command=self._on_select_none, width=60, fg_color="gray")
        self._btn_none.pack(side="left", padx=2)
        self._btn_export = ctk.CTkButton(toolbar, text=t("btn_export"), command=self._on_export, width=80, fg_color="gray")
        self._btn_export.pack(side="left", padx=2)
        self._search_var = ctk.StringVar(value="")
        self._search_entry = ctk.CTkEntry(toolbar, width=140, height=26, placeholder_text=t("search_placeholder"), textvariable=self._search_var)
        self._search_entry.pack(side="right", padx=(10, 2))
        self._search_var.trace_add("write", lambda *a: self._on_search())
        self._toolbar_widgets = [self._btn_stage1, self._btn_stage2, self._btn_all, self._btn_none, self._btn_export, self._search_entry]

    def _build_node_list(self):
        self._node_list = NodeTable(self._right, on_activate=self._on_activate_node)
        self._node_list.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)

    def _build_progress_area(self):
        pf = ctk.CTkFrame(self._right, fg_color="transparent")
        pf.grid(row=2, column=0, sticky="ew", pady=(2, 0))
        self._lbl_trace = ctk.CTkLabel(pf, text=t("lbl_hint"), anchor="w", font=ctk.CTkFont(size=12))
        self._lbl_trace.pack(fill="x", padx=4, pady=(2, 0))
        dlf = ctk.CTkFrame(pf, fg_color="transparent"); dlf.pack(fill="x", padx=4, pady=1)
        ctk.CTkLabel(dlf, text=t("lbl_dl"), width=25).pack(side="left")
        self._dl_bar = ctk.CTkProgressBar(dlf, height=14); self._dl_bar.pack(side="left", padx=4, fill="x", expand=True)
        self._dl_bar.set(0)
        self._lbl_dl = ctk.CTkLabel(dlf, text=t("lbl_default_speed"), width=170); self._lbl_dl.pack(side="right")
        ulf = ctk.CTkFrame(pf, fg_color="transparent"); ulf.pack(fill="x", padx=4, pady=1)
        ctk.CTkLabel(ulf, text=t("lbl_ul"), width=25).pack(side="left")
        self._ul_bar = ctk.CTkProgressBar(ulf, height=14); self._ul_bar.pack(side="left", padx=4, fill="x", expand=True)
        self._ul_bar.set(0)
        self._lbl_ul = ctk.CTkLabel(ulf, text=t("lbl_default_speed"), width=170); self._lbl_ul.pack(side="right")

    def _on_activate_node(self, node):
        """Double-click: switch to this node in background thread."""
        cfg = self._config.get_config()
        group = cfg.get("group", "")
        name = node.name
        self._lbl_trace.configure(text=t("msg_switch_to", group=group, name=name))
        def _switch():
            try:
                tc = TestConfig(
                    api_url=cfg.get("api", "http://127.0.0.1:9090"),
                    secret=cfg.get("secret", ""),
                    group_name=group,
                )
                with MihomoClient(tc) as mihomo:
                    g = group or self._auto_group(mihomo)
                    mihomo.switch_and_reset(name, group_name=g, wait=0.3)
            except Exception:
                pass
        threading.Thread(target=_switch, daemon=True).start()
        self._log.write(t("msg_switched", name=name), "#88BBFF")

    @staticmethod
    def _auto_group(mihomo) -> str:
        groups = [g for g in mihomo.list_groups() if g["name"] != "GLOBAL"]
        selectors = [g for g in groups if g["type"] == "Selector"]
        return selectors[0]["name"] if selectors else "Select"

    def _on_stage1(self):
        self._disable_buttons()
        self._log.clear()
        self._log.write(t("msg_stage1_start"), "#88BBFF")
        self._node_list.clear()
        self._runner = TestRunner(self._config.get_config(), mode="stage1")
        self._runner.start()

    def _on_stage2(self):
        selected = self._node_list.get_selected()
        if not selected:
            self._log.write(t("msg_no_nodes_selected"), "#F44336")
            return
        self._disable_buttons()
        self._log.write(t("msg_stage2_start", count=len(selected)), "#88BBFF")
        self._runner = TestRunner(self._config.get_config(), mode="stage2", selected_nodes=selected)
        self._runner.start()

    def _on_select_all(self): self._node_list.select_all()
    def _on_select_none(self): self._node_list.deselect_all()

    def _on_search(self):
        q = self._search_var.get().strip().lower()
        if not q:
            self._node_list.add_nodes(self._all_nodes)
            return
        filtered = [n for n in self._all_nodes if q in n.name.lower()]
        self._node_list.add_nodes(filtered)

    def _on_export(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUTPUT_DIR / "result.csv"
        selected = self._node_list.get_selected()
        if not selected:
            self._log.write(t("msg_nothing_to_export"), "#F44336")
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow([t("col_name"), "protocol", "latency_ms", "download_MBs", "upload_MBs", "reachable"])
            for n in selected:
                w.writerow([n.name, n.protocol, n.latency or "", n.download/8 if n.download else "", n.upload/8 if n.upload else "", n.reachable])
        self._log.write(t("msg_exported", name=path.name), "green")

    def _refresh_all_texts(self):
        self.title(t("window_title"))
        self._btn_stage1.configure(text=t("btn_stage1"))
        self._btn_stage2.configure(text=t("btn_stage2"))
        self._btn_all.configure(text=t("btn_select_all"))
        self._btn_none.configure(text=t("btn_select_none"))
        self._btn_export.configure(text=t("btn_export"))
        self._lbl_trace.configure(text=t("lbl_hint"))
        self._log.set_title(t("log_title"))
        self._node_list.refresh_headers()

    def _disable_buttons(self):
        for b in [self._btn_stage1, self._btn_stage2, self._btn_all, self._btn_none]:
            b.configure(state="disabled")
    def _enable_buttons(self):
        for b in [self._btn_stage1, self._btn_stage2, self._btn_all, self._btn_none]:
            b.configure(state="normal")

    def _poll_messages(self):
        runner = self._runner
        if runner is not None:
            try:
                while True:
                    msg = runner.messages.get_nowait()
                    self._handle_message(msg)
                    if self._runner is None:
                        break
            except queue.Empty:
                pass
        self.after(80, self._poll_messages)

    def _handle_message(self, msg: dict):
        mtype = msg.get("type", "")
        if mtype == "stage": pass
        elif mtype == "node_start":
            self._dl_bar.set(0); self._ul_bar.set(0)
            self._lbl_dl.configure(text=t("lbl_default_speed"))
            self._lbl_ul.configure(text=t("lbl_default_speed"))
        elif mtype == "stage1_done":
            nodes = msg["nodes"]
            self._all_nodes = list(nodes)
            self._nodes = nodes
            self._node_list.add_nodes(nodes)
            self._log.write(t("msg_stage1_done", reachable=msg['reachable'], total=msg['total']), "green")
            groups = msg.get("groups", [])
            current_group = msg.get("current_group", "")
            if groups:
                self._config.set_group_options(groups)
                if current_group:
                    self._config._combo_var.set(current_group)
            self._btn_stage2.configure(state="normal")
            self._btn_all.configure(state="normal")
            self._btn_none.configure(state="normal")
            self._enable_buttons()
        elif mtype == "trace":
            country = msg.get("country", "")
            colo = msg.get("colo", "")
            ip = msg.get("ip", "")
            group = msg.get("group", "")
            flag = flag_emoji(country) + " " if country else ""
            name = msg.get("name", "")
            self._lbl_trace.configure(text=f"[{group}] {name}  ->  {flag}{country}/{colo}  ({ip})")
        elif mtype == "dl_progress":
            done, total, speed = msg["done"], msg["total"], msg["speed"]
            if total > 0: self._dl_bar.set(done / total)
            self._lbl_dl.configure(text=f"{done/1e6:.1f}/{total/1e6:.0f} MB  {speed:.1f} Mbps")
        elif mtype == "ul_progress":
            done, total, speed = msg["done"], msg["total"], msg["speed"]
            if total > 0: self._ul_bar.set(done / total)
            self._lbl_ul.configure(text=f"{done/1e6:.1f}/{total/1e6:.0f} MB  {speed:.1f} Mbps")
        elif mtype == "node_done":
            self._log.write(t("msg_node_done", name=msg['name'][:42], download=msg['download'], upload=msg['upload']))
            self._node_list.update_node_by_name(msg["name"], msg["download"], msg["upload"])
        elif mtype == "best_node":
            self._log.write(t("msg_best_log", group=msg['group'], name=msg['name'][:40], download=msg['download'], upload=msg['upload']), "#4CAF50")
            self._lbl_trace.configure(text=t("msg_best_lbl", group=msg['group'], name=msg['name'], download=msg['download'], upload=msg['upload']))
        elif mtype == "done":
            self._log.write(t("msg_all_done", count=msg['count']), "#88BBFF")
            self._dl_bar.set(0); self._ul_bar.set(0)
            self._lbl_dl.configure(text=t("lbl_default_speed"))
            self._lbl_ul.configure(text=t("lbl_default_speed"))
            self._enable_buttons()
            self._runner = None
        elif mtype in ("error", "node_error"):
            self._log.write(t("msg_error_prefix", msg=msg.get('message', msg.get('error', 'unknown'))), "#F44336")
            if mtype == "error":
                self._enable_buttons()
                self._runner = None

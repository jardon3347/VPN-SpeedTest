from __future__ import annotations
import csv
import queue
from pathlib import Path
import customtkinter as ctk
from nodebench.gui.config_panel import ConfigPanel
from nodebench.gui.log_panel import LogPanel
from nodebench.gui.node_list import NodeTable, flag_emoji
from nodebench.gui.test_runner import TestRunner

OUTPUT_DIR = Path(__file__).parent.parent.parent / "outputs"

class NodeBenchApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("NodeBench GUI")
        self.geometry("1050x750")
        self.minsize(950, 550)
        self._runner: TestRunner | None = None
        self._nodes: list = []
        self._all_nodes: list = []
        self._build_ui()
        self._poll_messages()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0, minsize=260)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=3)
        self.grid_rowconfigure(1, weight=2)
        self._config = ConfigPanel(self)
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
        self._btn_stage1 = ctk.CTkButton(toolbar, text="Stage 1  Fetch Nodes", command=self._on_stage1, width=140)
        self._btn_stage1.pack(side="left", padx=2)
        self._btn_stage2 = ctk.CTkButton(toolbar, text="Stage 2  Test Selected", command=self._on_stage2, width=140, state="disabled")
        self._btn_stage2.pack(side="left", padx=2)
        self._btn_all = ctk.CTkButton(toolbar, text="Select All", command=self._on_select_all, width=80, fg_color="gray")
        self._btn_all.pack(side="left", padx=2)
        self._btn_none = ctk.CTkButton(toolbar, text="None", command=self._on_select_none, width=60, fg_color="gray")
        self._btn_none.pack(side="left", padx=2)
        self._btn_export = ctk.CTkButton(toolbar, text="Export CSV", command=self._on_export, width=80, fg_color="gray")
        self._btn_export.pack(side="left", padx=2)
        self._search_var = ctk.StringVar(value="")
        self._search_entry = ctk.CTkEntry(toolbar, width=140, height=26, placeholder_text="Search nodes...", textvariable=self._search_var)
        self._search_entry.pack(side="right", padx=(10, 2))
        self._search_var.trace_add("write", lambda *a: self._on_search())

    def _build_node_list(self):
        self._node_list = NodeTable(self._right)
        self._node_list.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)

    def _build_progress_area(self):
        pf = ctk.CTkFrame(self._right, fg_color="transparent")
        pf.grid(row=2, column=0, sticky="ew", pady=(2, 0))
        self._lbl_trace = ctk.CTkLabel(pf, text="Select nodes and click Stage 2.", anchor="w", font=ctk.CTkFont(size=12))
        self._lbl_trace.pack(fill="x", padx=4, pady=(2, 0))
        dlf = ctk.CTkFrame(pf, fg_color="transparent"); dlf.pack(fill="x", padx=4, pady=1)
        ctk.CTkLabel(dlf, text="DL", width=25).pack(side="left")
        self._dl_bar = ctk.CTkProgressBar(dlf, height=14); self._dl_bar.pack(side="left", padx=4, fill="x", expand=True)
        self._dl_bar.set(0)
        self._lbl_dl = ctk.CTkLabel(dlf, text="0/0 MB  0 Mbps", width=170); self._lbl_dl.pack(side="right")
        ulf = ctk.CTkFrame(pf, fg_color="transparent"); ulf.pack(fill="x", padx=4, pady=1)
        ctk.CTkLabel(ulf, text="UL", width=25).pack(side="left")
        self._ul_bar = ctk.CTkProgressBar(ulf, height=14); self._ul_bar.pack(side="left", padx=4, fill="x", expand=True)
        self._ul_bar.set(0)
        self._lbl_ul = ctk.CTkLabel(ulf, text="0/0 MB  0 Mbps", width=170); self._lbl_ul.pack(side="right")

    def _on_stage1(self):
        self._disable_buttons()
        self._log.clear()
        self._log.write("Stage 1: Fetching nodes from mihomo...", "#88BBFF")
        self._node_list.clear()
        self._runner = TestRunner(self._config.get_config(), mode="stage1")
        self._runner.start()

    def _on_stage2(self):
        selected = self._node_list.get_selected()
        if not selected:
            self._log.write("No nodes selected!", "#F44336")
            return
        self._disable_buttons()
        self._log.write(f"Stage 2: Testing {len(selected)} nodes...", "#88BBFF")
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
            self._log.write("Nothing to export!", "#F44336")
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["name","protocol","latency_ms","download_MBs","upload_MBs","reachable"])
            for n in selected:
                w.writerow([n.name, n.protocol, n.latency or "", n.download/8 if n.download else "", n.upload/8 if n.upload else "", n.reachable])
        self._log.write(f"Exported -> {path.name}", "green")

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
        elif mtype == "stage1_done":
            nodes = msg["nodes"]
            self._all_nodes = list(nodes)
            self._nodes = nodes
            self._node_list.add_nodes(nodes)
            self._log.write(f"Stage 1 done: {msg['reachable']}/{msg['total']} nodes (mihomo latency)", "green")
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
            self._log.write(f"  {msg['name'][:40]:<42} DL={msg['download']:5.1f}  UL={msg['upload']:5.1f} Mbps")
            self._node_list.update_node_by_name(msg["name"], msg["download"], msg["upload"])
        elif mtype == "best_node":
            self._log.write(f"Best -> [{msg['group']}] {msg['name'][:40]}  DL={msg['download']:.1f}  UL={msg['upload']:.1f} Mbps", "#4CAF50")
            self._lbl_trace.configure(text=f"Best: [{msg['group']}] {msg['name']}  DL={msg['download']:.1f}  UL={msg['upload']:.1f} Mbps")
        elif mtype == "done":
            self._log.write(f"All {msg['count']} nodes tested. Done.", "#88BBFF")
            self._dl_bar.set(0); self._ul_bar.set(0)
            self._lbl_dl.configure(text="0/0 MB  0 Mbps")
            self._lbl_ul.configure(text="0/0 MB  0 Mbps")
            self._enable_buttons()
            self._runner = None
        elif mtype in ("error", "node_error"):
            self._log.write(f"ERROR: {msg.get('message', msg.get('error', 'unknown'))}", "#F44336")
            if mtype == "error":
                self._enable_buttons()
                self._runner = None

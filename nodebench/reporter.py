from __future__ import annotations
import csv
import json
from pathlib import Path
from nodebench.models import Node

def _fmt(val, unit="") -> str:
    if val is None:
        return "-"
    return f"{val:.1f}{unit}"

class Reporter:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def info(self, msg: str):
        print(f"  {msg}")

    def error(self, msg: str):
        print(f"  [ERROR] {msg}")

    def progress(self, msg: str):
        if self.verbose:
            print(msg)

    def stage1_result(self, nodes: list[Node]):
        print(f"\n  Stage 1: {len(nodes)} reachable nodes")
        for i, n in enumerate(nodes):
            lat = f"{n.latency:.0f}ms" if n.latency else "N/A"
            print(f"    {i+1:>3}. {lat:>6}  {n.name}")

    def trace(self, name: str, trace):
        print(f"         -> {trace.country}/{trace.colo} ({trace.ip})")

    def bandwidth_result(self, node: Node):
        dl = _fmt(node.download, " Mbps") if node.download else "N/A"
        ul = _fmt(node.upload, " Mbps") if node.upload else "N/A"
        print(f"         DL={dl}  UL={ul}")

    def export(self, nodes: list[Node], path: str, fmt: str = ""):
        p = Path(path)
        fmt = fmt or p.suffix.lstrip(".")
        p.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "json":
            self._export_json(nodes, path)
        else:
            self._export_csv(nodes, path)
        print(f"  Exported -> {path}")

    def _export_csv(self, nodes: list[Node], path: str):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["name", "protocol", "latency_ms", "download_MBs", "upload_MBs", "reachable"])
            for n in nodes:
                dl = n.download / 8 if n.download is not None else ""
                ul = n.upload / 8 if n.upload is not None else ""
                w.writerow([n.name, n.protocol, n.latency or "", dl, ul, n.reachable])

    def _export_json(self, nodes: list[Node], path: str):
        data = []
        for n in nodes:
            data.append({"name": n.name, "protocol": n.protocol, "latency_ms": n.latency,
                         "download_mbps": n.download, "upload_mbps": n.upload,
                         "reachable": n.reachable, "error": n.error})
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

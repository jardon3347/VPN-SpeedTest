from __future__ import annotations
import json
import time
from pathlib import Path
from nodebench.models import TestConfig, Node
from nodebench.mihomo_client import MihomoClient
from nodebench.speedtest import CloudflareSpeedTest
from nodebench.prober import Prober

class Scheduler:
    def __init__(self, config: TestConfig):
        self._cfg = config

    def run_full(self, reporter, stage: int = 2, save_cache_path: str = "",
                 output_path: str = "", output_format: str = ""):
        nodes = []
        with MihomoClient(self._cfg) as mihomo:
            if not mihomo.healthcheck():
                reporter.error("Cannot connect to mihomo API")
                return
            group = self._cfg.group_name
            if not group:
                groups = mihomo.list_groups()
                group = self._auto_pick_group(groups)
                reporter.info(f"Auto-detected group: {group}")
            nodes = mihomo.get_node_list(group_name=group)
            reporter.info(f"Found {len(nodes)} nodes in group '{group}'")

        if not nodes:
            reporter.error("No nodes found")
            return

        # Stage 1: read mihomo latency
        for n in nodes:
            n.reachable = n.latency is not None
            if not n.reachable:
                n.error = "no mihomo latency"
        reachable = [n for n in nodes if n.reachable]
        reporter.stage1_result(reachable)

        # Save cache
        if save_cache_path:
            self._save_cache(nodes, save_cache_path)
            reporter.info(f"Cache saved: {save_cache_path}")

        # Stage 2: bandwidth test on top nodes
        if stage >= 2 and reachable:
            top = self._pick_top(reachable)
            reporter.info(f"Stage 2: testing {len(top)} nodes for bandwidth")
            self._run_bandwidth_sync(mihomo, group, top, reporter)

        # Output
        if output_path:
            self._export(nodes, output_path, output_format)
            reporter.info(f"Exported: {output_path}")

    def run_stage2_from_cache(self, cache_path: Path, reporter,
                               save_cache_path: str = "", node_filter: str = "",
                               output_path: str = "", output_format: str = ""):
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
        nodes = [Node(**item) for item in data.get("nodes", [])]
        reporter.info(f"Loaded {len(nodes)} nodes from cache")

        # Filter by index
        if node_filter:
            indices = self._parse_indices(node_filter)
            nodes = [n for i, n in enumerate(nodes) if i in indices]
            reporter.info(f"Filtered to {len(nodes)} nodes")

        group = self._cfg.group_name or ""
        top = [n for n in nodes if n.reachable]
        if not top:
            reporter.error("No reachable nodes")
            return

        self._cfg.top_max = len(top)
        top = self._pick_top(top)

        with MihomoClient(self._cfg) as mihomo:
            if not group:
                groups = mihomo.list_groups()
                group = self._auto_pick_group(groups)
            self._run_bandwidth_sync(mihomo, group, top, reporter)

        if output_path:
            self._export(nodes, output_path, output_format)

    def _run_bandwidth_sync(self, mihomo, group: str, nodes: list[Node], reporter):
        tester = CloudflareSpeedTest(self._cfg.proxy_url, timeout=self._cfg.bandwidth_timeout)
        for node in nodes:
            reporter.progress(f"  Testing {node.name}...")
            try:
                mihomo.switch_and_reset(node.name, group_name=group, wait=self._cfg.switch_wait)
            except Exception as e:
                reporter.error(f"  Switch failed: {e}")
                continue

            trace = tester.fetch_trace()
            reporter.trace(node.name, trace)

            dl = tester.run_download(total_bytes=self._cfg.download_bytes)
            ul = tester.run_upload(total_bytes=self._cfg.upload_bytes)
            node.download = dl.mbps
            node.upload = ul.mbps
            reporter.bandwidth_result(node)

        # Restore best
        best = max(nodes, key=lambda n: (n.download or 0) + (n.upload or 0))
        try:
            mihomo.switch_and_reset(best.name, group_name=group)
            reporter.info(f"Best node: {best.name}")
        except Exception:
            pass

    def _pick_top(self, nodes: list[Node]) -> list[Node]:
        sorted_nodes = sorted([n for n in nodes if n.reachable],
                              key=lambda n: n.latency or 9999)
        n = len(sorted_nodes)
        count = max(self._cfg.top_min, min(self._cfg.top_max, max(2, int(n * self._cfg.top_ratio))))
        return sorted_nodes[:count]

    @staticmethod
    def _auto_pick_group(groups: list[dict]) -> str:
        candidates = [g for g in groups if g["name"] != "GLOBAL"]
        if not candidates:
            return "Select"
        for g in candidates:
            if g["type"] == "Selector":
                return g["name"]
        return candidates[0]["name"]

    @staticmethod
    def _parse_indices(s: str) -> set[int]:
        result = set()
        for part in s.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-", 1)
                result.update(range(int(a) - 1, int(b)))
            else:
                result.add(int(part) - 1)
        return result

    def _save_cache(self, nodes: list[Node], path: str):
        data = {
            "nodes": [{"name": n.name, "protocol": n.protocol, "latency": n.latency,
                        "reachable": n.reachable, "download": n.download,
                        "upload": n.upload, "error": n.error} for n in nodes],
            "timestamp": time.time()
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _export(self, nodes: list[Node], path: str, fmt: str):
        from nodebench.reporter import Reporter
        r = Reporter()
        r.export(nodes, path, fmt)

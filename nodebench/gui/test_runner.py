from __future__ import annotations
import queue
import threading
from nodebench.mihomo_client import MihomoClient
from nodebench.models import TestConfig, Node
from nodebench.speedtest import CloudflareSpeedTest

class TestRunner(threading.Thread):
    def __init__(self, config: dict, mode: str = "stage2", selected_nodes: list[Node] | None = None):
        super().__init__(daemon=True)
        self._cfg_dict = config
        self._mode = mode
        self._selected = selected_nodes
        self._msg_queue: queue.Queue = queue.Queue()
        self._cancel = threading.Event()

    @property
    def messages(self) -> queue.Queue:
        return self._msg_queue

    def cancel(self):
        self._cancel.set()

    def _post(self, msg_type: str, **kwargs):
        if not self._cancel.is_set():
            kwargs["type"] = msg_type
            self._msg_queue.put(kwargs)

    def run(self):
        try:
            if self._mode == "stage1": self._run_stage1()
            elif self._mode == "stage2": self._run_stage2()
        except Exception as e:
            self._post("error", message=str(e))

    def _run_stage1(self):
        cfg = self._make_cfg()
        self._post("stage", stage=1, status="connecting")
        with MihomoClient(cfg) as mihomo:
            if not mihomo.healthcheck():
                self._post("error", message="Cannot reach mihomo API.")
                return
            if not cfg.group_name:
                cfg.group_name = self._auto_group(mihomo)
            groups = mihomo.list_groups()
            group_names = [g["name"] for g in groups if g["name"] != "GLOBAL"]
            nodes = mihomo.get_node_list(group_name=cfg.group_name)
            for n in nodes:
                n.reachable = n.latency is not None
                if not n.reachable:
                    n.error = "no mihomo latency"
            reachable = sum(1 for n in nodes if n.reachable)
            self._post("stage1_done", nodes=nodes, reachable=reachable, total=len(nodes),
                       groups=group_names, current_group=cfg.group_name)

    def _run_stage2(self):
        if not self._selected:
            self._post("error", message="No nodes selected.")
            return
        cfg = self._make_cfg()
        self._post("stage", stage=2, status="connecting", count=len(self._selected))
        with MihomoClient(cfg) as mihomo:
            if not mihomo.healthcheck():
                self._post("error", message="Cannot reach mihomo API.")
                return
            if not cfg.group_name:
                cfg.group_name = self._auto_group(mihomo)
            tester = CloudflareSpeedTest(cfg.proxy_url, timeout=cfg.bandwidth_timeout)
            for i, node in enumerate(self._selected):
                if self._cancel.is_set():
                    self._post("cancelled")
                    return
                self._post("node_start", index=i, name=node.name, group=cfg.group_name)
                try:
                    mihomo.switch_and_reset(node.name, group_name=cfg.group_name, wait=cfg.switch_wait)
                except Exception as e:
                    self._post("node_error", index=i, error=f"switch failed: {e}")
                    continue
                trace = tester.fetch_trace()
                self._post("trace", index=i, country=trace.country, colo=trace.colo, ip=trace.ip,
                           group=cfg.group_name, name=node.name)

                def dl_cb(done, total, speed):
                    if not self._cancel.is_set():
                        self._post("dl_progress", index=i, done=done, total=total, speed=speed)
                try:
                    dl = tester.run_download(total_bytes=cfg.download_bytes, on_progress=dl_cb)
                    node.download = dl.mbps
                    if dl.mbps == 0 and dl.error:
                        self._post("node_error", index=i, error=f"download: {dl.error} ({cfg.download_bytes // 1_000_000} MB)")
                except Exception as e:
                    self._post("node_error", index=i, error=f"download: {e}")
                    node.download = 0.0

                if self._cancel.is_set():
                    self._post("cancelled")
                    return

                def ul_cb(done, total, speed):
                    if not self._cancel.is_set():
                        self._post("ul_progress", index=i, done=done, total=total, speed=speed)
                try:
                    ul = tester.run_upload(total_bytes=cfg.upload_bytes, on_progress=ul_cb)
                    node.upload = ul.mbps
                except Exception as e:
                    self._post("node_error", index=i, error=f"upload: {e}")
                    node.upload = 0.0

                self._post("node_done", index=i, name=node.name, download=node.download, upload=node.upload)

            # Best node
            best = max(self._selected, key=lambda n: (n.download or 0) + (n.upload or 0), default=None)
            if best is not None and best.download is not None:
                try:
                    with MihomoClient(cfg) as fresh:
                        fresh.switch_and_reset(best.name, group_name=cfg.group_name, wait=1.0)
                    self._post("best_node", name=best.name, group=cfg.group_name,
                               download=(best.download or 0), upload=(best.upload or 0))
                except Exception as e:
                    self._post("node_error", index=-1, error=f"Failed to set best node: {e}")

        self._post("done", count=len(self._selected))

    def _make_cfg(self) -> TestConfig:
        d = self._cfg_dict
        return TestConfig(
            api_url=d.get("api", "http://127.0.0.1:9090"), secret=d.get("secret", ""),
            proxy_url=d.get("proxy", "socks5://127.0.0.1:7890"), group_name=d.get("group", ""),
            download_bytes=int(d.get("download_bytes", 25_000_000)),
            upload_bytes=int(d.get("upload_bytes", 25_000_000)),
            bandwidth_timeout=float(d.get("bandwidth_timeout", 20.0)),
            switch_wait=float(d.get("switch_wait", 0.5)),
            use_mihomo_latency=True,
        )

    @staticmethod
    def _auto_group(mihomo) -> str:
        groups = [g for g in mihomo.list_groups() if g["name"] != "GLOBAL"]
        if not groups:
            return "Select"
        selectors = [g for g in groups if g["type"] == "Selector"]
        return selectors[0]["name"] if selectors else groups[0]["name"]

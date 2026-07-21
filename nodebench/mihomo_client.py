from __future__ import annotations
import time
import httpx
from nodebench.models import TestConfig, Node

class MihomoError(Exception):
    pass

class MihomoClient:
    def __init__(self, config: TestConfig):
        self._cfg = config
        headers = {"Content-Type": "application/json"}
        if config.secret:
            headers["Authorization"] = f"Bearer {config.secret}"
        self._client = httpx.Client(
            base_url=config.api_url,
            headers=headers,
            timeout=config.connect_timeout
        )
        self._proxies_cache: dict | None = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self._client.close()

    def healthcheck(self) -> bool:
        try:
            r = self._client.get("/version", timeout=5.0)
            return r.status_code == 200
        except Exception:
            return False

    def _get(self, path: str, params=None) -> dict:
        r = self._client.get(path, params=params)
        if r.status_code == 401:
            raise MihomoError("Unauthorized - check secret")
        if r.status_code != 200:
            raise MihomoError(f"HTTP {r.status_code} from {path}")
        data = r.json()
        if isinstance(data, dict):
            return data
        return {"data": data}

    def _put(self, path: str, body: dict) -> dict:
        r = self._client.put(path, json=body)
        if r.status_code != 204 and r.status_code != 200:
            raise MihomoError(f"HTTP {r.status_code}")
        return {}

    def _delete(self, path: str):
        r = self._client.delete(path)
        if r.status_code not in (204, 200, 404):
            raise MihomoError(f"HTTP {r.status_code}")

    def _fetch_proxies(self) -> dict:
        """Lazy-load and cache the /proxies response."""
        if self._proxies_cache is None:
            self._proxies_cache = self._get("/proxies").get("proxies", {})
        return self._proxies_cache

    def list_groups(self) -> list[dict]:
        all_proxies = self._fetch_proxies()
        groups = []
        for name, info in all_proxies.items():
            if info.get("type") in ("Selector", "URLTest", "Fallback", "LoadBalance"):
                groups.append({
                    "name": name,
                    "type": info.get("type", ""),
                    "now": info.get("now", "")
                })
        return groups

    def get_node_list(self, group_name: str = "Select") -> list[Node]:
        """Fetch leaf-node proxies directly under a group, using history-based latency."""
        all_proxies = self._fetch_proxies()
        group = all_proxies.get(group_name)
        if not group:
            raise MihomoError(f"Group '{group_name}' not found")

        nodes = []
        skip_set = {"DIRECT", "REJECT", "REJECT-DROP"}
        group_types = {"Selector", "URLTest", "Fallback", "LoadBalance"}
        for name in group.get("all", []):
            if name in skip_set:
                continue
            proxy = all_proxies.get(name, {})
            if proxy.get("type") in group_types:
                continue
            latency = self._extract_delay(proxy)
            node = Node(name=name, latency=latency)
            if latency is None:
                node.reachable = False
                node.error = "no delay history (node may need URL-test)"
            nodes.append(node)
        return nodes

    @staticmethod
    def _extract_delay(proxy: dict) -> float | None:
        """Extract latest delay from proxy history. Returns None if no valid delay."""
        history = proxy.get("history", [])
        if not history:
            return None
        delay = history[-1].get("delay", None)
        if delay is None or delay == 0:
            return None
        return float(delay)

    def switch_node(self, node_name: str, group_name: str = "Select"):
        self._put(f"/proxies/{group_name}", {"name": node_name})

    def close_all_connections(self):
        data = self._get("/connections")
        for c in data.get("connections", []):
            cid = c.get("id")
            if cid:
                try:
                    self._delete("/connections/" + cid)
                except MihomoError:
                    pass

    def switch_and_reset(self, node_name: str, group_name: str = "Select", wait: float = 0.5):
        self.switch_node(node_name, group_name)
        try:
            self.close_all_connections()
        except Exception:
            pass
        if wait > 0:
            time.sleep(wait)

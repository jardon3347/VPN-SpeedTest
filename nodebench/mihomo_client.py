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
            raise MihomoError(f"HTTP {r.status_code}")
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

    def list_groups(self) -> list[dict]:
        data = self._get("/proxies")
        groups = []
        for name, info in data.get("proxies", {}).items():
            if info.get("type") in ("Selector", "URLTest", "Fallback", "LoadBalance"):
                groups.append({
                    "name": name,
                    "type": info.get("type", ""),
                    "now": info.get("now", "")
                })
        return groups

    def get_node_list(self, group_name: str = "Select") -> list[Node]:
        data = self._get(f"/proxies/{group_name}")
        nodes = []
        delay_map = self._get_delays(group_name)
        for name in data.get("all", []):
            if name in ("DIRECT", "REJECT", "REJECT-DROP"):
                continue
            provider = data.get("provider", {})
            protocol = ""
            for pname, pinfo in provider.items():
                if name in pinfo.get("proxies", []):
                    protocol = pname
                    break
            latency = delay_map.get(name)
            node = Node(name=name, protocol=protocol, latency=latency)
            nodes.append(node)
        return nodes

    def _get_delays(self, group_name: str) -> dict[str, float]:
        try:
            data = self._get(f"/group/{group_name}/delay")
            result = {}
            for entry in data.get("data", data.get("delay", [])):
                result[entry.get("name", "")] = entry.get("delay", None)
            return result
        except Exception:
            return {}

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

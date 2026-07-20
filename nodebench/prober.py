from __future__ import annotations
import asyncio
import time
from aiohttp import ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector

PROBE_URL = "https://speed.cloudflare.com/cdn-cgi/trace"

class Prober:
    def __init__(self, proxy_url: str = "", attempts: int = 3, timeout: float = 3.0):
        self.proxy_url = proxy_url
        self.attempts = attempts
        self.timeout = timeout

    def probe(self) -> bool:
        try:
            return asyncio.run(self._akit_probe(self.attempts))
        except Exception:
            return False

    async def _akit_probe(self, required: int) -> bool:
        successes = 0
        connector = ProxyConnector.from_url(self.proxy_url) if self.proxy_url else None
        t = ClientTimeout(total=self.timeout, connect=3.0)
        async with ClientSession(connector=connector, timeout=t) as session:
            for _ in range(self.attempts):
                try:
                    async with session.get(PROBE_URL) as resp:
                        if resp.status == 200:
                            successes += 1
                            if successes >= required:
                                return True
                except Exception:
                    pass
        return False

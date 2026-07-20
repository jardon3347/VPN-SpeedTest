from __future__ import annotations
import asyncio
import io
import time
from dataclasses import dataclass
from statistics import mean, stdev
from typing import Optional
import aiohttp
from aiohttp import ClientTimeout, ClientSession
from aiohttp_socks import ProxyConnector

CF_DOWN = "https://speed.cloudflare.com/__down"
CF_UP = "https://speed.cloudflare.com/__up"
CF_TRACE = "https://speed.cloudflare.com/cdn-cgi/trace"
CF_PING = "https://speed.cloudflare.com"
CHUNK = 25_000_000

@dataclass
class TraceInfo:
    country: str = ""
    colo: str = ""
    ip: str = ""

@dataclass
class PingResult:
    rtts: list[float]
    min_ms: float
    max_ms: float
    jitter_ms: float
    loss: float

@dataclass
class BandwidthResult:
    mbps: float
    error: str = ""

class CloudflareSpeedTest:
    def __init__(self, proxy_url: str = "", timeout: float = 20.0):
        self.proxy_url = proxy_url
        self.timeout = timeout

    def fetch_trace(self) -> TraceInfo:
        try:
            return asyncio.run(self._akit_trace())
        except Exception:
            return TraceInfo()

    async def _akit_trace(self) -> TraceInfo:
        connector = ProxyConnector.from_url(self.proxy_url) if self.proxy_url else None
        async with ClientSession(connector=connector) as session:
            async with session.get(CF_TRACE, timeout=ClientTimeout(total=10)) as resp:
                text = await resp.text()
        info = {}
        for line in text.strip().split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                info[k.strip()] = v.strip()
        return TraceInfo(
            country=info.get("loc", ""),
            colo=info.get("colo", ""),
            ip=info.get("ip", "")
        )

    def measure_latency_async(self, count: int = 10, timeout: float = 5.0) -> PingResult:
        try:
            return asyncio.run(self._akit_latency(count, timeout))
        except Exception:
            return PingResult([], 0, 0, 0, 100.0)

    async def _akit_latency(self, count: int, timeout: float) -> PingResult:
        connector = ProxyConnector.from_url(self.proxy_url) if self.proxy_url else None
        t = ClientTimeout(total=timeout, connect=5.0)
        rtts = []
        async with ClientSession(connector=connector, timeout=t) as session:
            for _ in range(count):
                try:
                    t0 = time.perf_counter()
                    async with session.head(CF_PING) as resp:
                        await resp.read()
                    rtts.append((time.perf_counter() - t0) * 1000)
                except Exception:
                    pass
        if not rtts:
            return PingResult([], 0, 0, 0, 100.0)
        rtts.sort()
        return PingResult(
            rtts=rtts,
            min_ms=min(rtts),
            max_ms=max(rtts),
            jitter_ms=stdev(rtts) if len(rtts) > 1 else 0.0,
            loss=(count - len(rtts)) / count * 100
        )

    def run_download(self, total_bytes: int = 25_000_000, on_progress=None) -> BandwidthResult:
        try:
            return asyncio.run(self._akit_download(total_bytes, on_progress))
        except Exception as e:
            return BandwidthResult(mbps=0.0, error=type(e).__name__)

    async def _akit_download(self, total_bytes: int, on_progress=None) -> BandwidthResult:
        t0 = time.perf_counter()
        total = 0
        last_update = t0
        last_bytes = 0
        remaining = total_bytes
        error_reason = ""

        connector = ProxyConnector.from_url(self.proxy_url) if self.proxy_url else None
        req_timeout = ClientTimeout(total=self.timeout, connect=10.0, sock_read=15.0)

        async with ClientSession(connector=connector) as session:
            while remaining > 0:
                if time.perf_counter() - t0 > self.timeout:
                    error_reason = "total timeout"
                    break
                size = min(remaining, CHUNK)
                url = f"{CF_DOWN}?bytes={size}"
                try:
                    async with session.get(url, timeout=req_timeout) as resp:
                        if resp.status != 200:
                            error_reason = f"HTTP {resp.status}"
                            break
                        if on_progress:
                            on_progress(0, total_bytes, 0)
                        async for chunk in resp.content.iter_any():
                            total += len(chunk)
                            remaining -= len(chunk)
                            now = time.perf_counter()
                            if on_progress and now - last_update > 0.15:
                                speed = (total - last_bytes) / (now - last_update) / 1_000_000 * 8
                                on_progress(total, total_bytes, speed)
                                last_update = now
                                last_bytes = total
                except asyncio.TimeoutError:
                    error_reason = "timeout"
                    break
                except Exception as e:
                    error_reason = type(e).__name__
                    break
            elapsed = max(time.perf_counter() - t0, 0.001)
            mbps = total * 8.0 / elapsed / 1_000_000.0
        return BandwidthResult(mbps=max(mbps, 0.0), error=error_reason)

    def run_upload(self, total_bytes: int = 25_000_000, on_progress=None) -> BandwidthResult:
        try:
            return asyncio.run(self._akit_upload(total_bytes, on_progress))
        except Exception as e:
            return BandwidthResult(mbps=0.0, error=type(e).__name__)

    async def _akit_upload(self, total_bytes: int, on_progress=None) -> BandwidthResult:
        t0 = time.perf_counter()
        total = 0
        last_update = t0
        last_bytes = 0
        error_reason = ""
        connector = ProxyConnector.from_url(self.proxy_url) if self.proxy_url else None
        async with ClientSession(connector=connector) as session:
            data = io.BytesIO(b"0" * CHUNK)
            while total < total_bytes:
                if time.perf_counter() - t0 > self.timeout:
                    error_reason = "total timeout"
                    break
                chunk = data.read(min(CHUNK, total_bytes - len(data.getvalue())))
                if not chunk:
                    data.seek(0)
                    chunk = data.read(min(CHUNK, total_bytes - total))
                try:
                    async with session.post(CF_UP, data=chunk,
                                            timeout=ClientTimeout(total=self.timeout)) as resp:
                        total += len(chunk)
                        now = time.perf_counter()
                        if on_progress and now - last_update > 0.15:
                            speed = (total - last_bytes) / (now - last_update) / 1_000_000 * 8
                            on_progress(total, total_bytes, speed)
                            last_update = now
                            last_bytes = total
                except Exception as e:
                    error_reason = type(e).__name__
                    break
            elapsed = max(time.perf_counter() - t0, 0.001)
            mbps = total * 8.0 / elapsed / 1_000_000.0
        return BandwidthResult(mbps=max(mbps, 0.0), error=error_reason)

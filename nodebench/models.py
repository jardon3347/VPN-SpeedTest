from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Node:
    name: str
    protocol: str = ""
    latency: float | None = None
    jitter: float = 0.0
    packet_loss: float = 0.0
    download: float | None = None
    upload: float | None = None
    reachable: bool = True
    error: str = ""

    @property
    def download_label(self) -> str:
        return f"{self.download / 8:.1f} MB/s" if self.download else "-"

    @property
    def upload_label(self) -> str:
        return f"{self.upload / 8:.1f} MB/s" if self.upload else "-"

@dataclass
class TestConfig:
    api_url: str = "http://127.0.0.1:9090"
    secret: str = ""
    proxy_url: str = "socks5://127.0.0.1:7890"
    group_name: str = ""
    stage: int = 2
    top_ratio: float = 0.1
    top_min: int = 5
    top_max: int = 7
    ping_samples: int = 10
    ping_timeout: float = 5.0
    download_bytes: int = 25_000_000
    upload_bytes: int = 25_000_000
    bandwidth_timeout: float = 20.0
    connect_timeout: float = 15.0
    switch_wait: float = 0.5
    probe_attempts: int = 3
    probe_timeout: float = 3.0
    probe_success_required: int = 1
    output_path: str = ""
    output_format: str = ""
    verbose: bool = False
    demo_mode: bool = False
    save_cache: str = ""
    load_cache: str = ""
    use_mihomo_latency: bool = True
    selected_nodes: str = ""

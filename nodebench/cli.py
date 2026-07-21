from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

from nodebench.models import TestConfig
from nodebench.mihomo_client import MihomoClient
from nodebench.speedtest import CloudflareSpeedTest
from nodebench.scheduler import Scheduler
from nodebench.reporter import Reporter
from nodebench.demo import run_demo

CONFIG_PATH = Path(__file__).parent.parent / "nodebench_config.json"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"

def _load_json_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def build_parser():
    jcfg = _load_json_config()
    p = argparse.ArgumentParser("nodebench", description="NodeBench - VPN node speed tester")
    p.add_argument("--version", action="version", version="NodeBench 1.0")
    p.add_argument("--api", default=jcfg.get("api", "http://127.0.0.1:9090"))
    p.add_argument("--secret", default=jcfg.get("secret", ""))
    p.add_argument("--proxy", default=jcfg.get("proxy", "socks5://127.0.0.1:7890"))
    p.add_argument("--group", default=jcfg.get("group", ""))
    p.add_argument("--stage", type=int, choices=[1, 2], default=2)
    p.add_argument("--top-ratio", type=float, default=jcfg.get("top_ratio", 0.1))
    p.add_argument("--top-min", type=int, default=jcfg.get("top_min", 5))
    p.add_argument("--top-max", type=int, default=jcfg.get("top_max", 7))
    p.add_argument("--download-bytes", type=int, default=jcfg.get("download_bytes", 25_000_000))
    p.add_argument("--upload-bytes", type=int, default=jcfg.get("upload_bytes", 25_000_000))
    p.add_argument("--bandwidth-timeout", type=float, default=jcfg.get("bandwidth_timeout", 20.0))
    p.add_argument("--connect-timeout", type=float, default=15.0)
    p.add_argument("--switch-wait", type=float, default=jcfg.get("switch_wait", 0.5))
    p.add_argument("--output", default="")
    p.add_argument("--format", choices=["csv", "json"], default="")
    p.add_argument("--list-groups", action="store_true")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--save-cache", default="")
    p.add_argument("--load-cache", default="")
    p.add_argument("--no-mihomo-latency", action="store_true")
    p.add_argument("--nodes", default="")
    return p

def main(args=None):
    p = build_parser()
    args = p.parse_args(args)

    if args.demo:
        run_demo()
        return 0

    cfg = TestConfig(
        api_url=args.api, secret=args.secret, proxy_url=args.proxy,
        group_name=args.group, stage=args.stage, top_ratio=args.top_ratio,
        top_min=args.top_min, top_max=args.top_max,
        download_bytes=args.download_bytes, upload_bytes=args.upload_bytes,
        bandwidth_timeout=args.bandwidth_timeout, connect_timeout=args.connect_timeout,
        switch_wait=args.switch_wait, output_path=args.output or "",
        output_format=args.format, verbose=args.verbose,
        save_cache=args.save_cache, load_cache=args.load_cache,
        use_mihomo_latency=not args.no_mihomo_latency,
        selected_nodes=args.nodes
    )

    # --list-groups
    if args.list_groups:
        with MihomoClient(cfg) as mihomo:
            groups = mihomo.list_groups()
            for g in groups:
                print(f"  {g['name']} ({g['type']}) -> {g.get('now', '?')}")
        return 0

    reporter = Reporter()
    scheduler = Scheduler(cfg)

    # --load-cache: use cached results
    if cfg.load_cache:
        cache_path = Path(cfg.load_cache)
        if not cache_path.exists():
            print(f"Cache not found: {cfg.load_cache}")
            return 1
        print(f"Loading cache: {cfg.load_cache}")
        scheduler.run_stage2_from_cache(
            cache_path, reporter,
            save_cache_path=cfg.save_cache,
            node_filter=cfg.selected_nodes,
            output_path=cfg.output_path,
            output_format=cfg.output_format
        )
        return 0

    # Full run
    scheduler.run_full(
        reporter,
        stage=cfg.stage,
        save_cache_path=cfg.save_cache,
        output_path=cfg.output_path,
        output_format=cfg.output_format
    )

    return 0

from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
CONFIG_FILE = ROOT / "nodebench_config.json"
OUTPUT_DIR = ROOT / "outputs"

DEFAULTS = {
    "api": "http://127.0.0.1:9090",
    "secret": "",
    "proxy": "socks5://127.0.0.1:7890",
    "group": "",
    "top_ratio": 0.2,
    "top_min": 5,
    "top_max": 20,
    "download_bytes": 25_000_000,
    "upload_bytes": 25_000_000,
    "bandwidth_timeout": 20.0,
    "switch_wait": 0.5,
    "output": str(OUTPUT_DIR / "result.csv"),
}

def load_config() -> dict:
    cfg = dict(DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg

def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def prompt(label: str, default: str, mask=False) -> str:
    display = "(set)" if mask and default else default
    val = input(f"{label} [{display}]: ").strip()
    if mask and val == "":
        val = default
    return val if val else default

def edit_connection(cfg: dict):
    print("\n  === Connection ===")
    cfg["api"] = prompt("  Mihomo API URL", cfg["api"])
    cfg["secret"] = prompt("  API Secret", cfg["secret"], mask=True)
    cfg["proxy"] = prompt("  SOCKS5 Proxy", cfg["proxy"])
    cfg["group"] = prompt("  Group name (blank=auto)", cfg["group"])
    save_config(cfg)

def edit_test_params(cfg: dict):
    print("\n  === Test Parameters ===")
    cfg["top_ratio"] = float(prompt("  Top ratio for bandwidth", str(cfg["top_ratio"])))
    cfg["top_min"] = int(prompt("  Min nodes for bandwidth", str(cfg["top_min"])))
    cfg["top_max"] = int(prompt("  Max nodes for bandwidth", str(cfg["top_max"])))
    cfg["download_bytes"] = int(prompt("  Download test size (bytes)", str(cfg["download_bytes"])))
    cfg["upload_bytes"] = int(prompt("  Upload test size (bytes)", str(cfg["upload_bytes"])))
    cfg["bandwidth_timeout"] = float(prompt("  Bandwidth timeout (seconds)", str(cfg["bandwidth_timeout"])))
    cfg["switch_wait"] = float(prompt("  Switch wait (seconds)", str(cfg.get("switch_wait", 0.5))))
    save_config(cfg)

def edit_output(cfg: dict):
    print("\n  === Output ===")
    cfg["output"] = prompt("  Output file path", cfg["output"])
    save_config(cfg)

def show_config(cfg: dict):
    print(f"\n  === Current Config ===")
    print(f"  Mihomo API      : {cfg['api']}")
    print(f"  Proxy           : {cfg['proxy']}")
    print(f"  Group           : {cfg['group'] or '(auto)'}")
    print(f"  Top ratio       : {cfg['top_ratio']}")
    print(f"  Top min / max   : {cfg['top_min']} / {cfg['top_max']}")
    print(f"  Download size   : {cfg['download_bytes']:,} bytes")
    print(f"  Upload size     : {cfg['upload_bytes']:,} bytes")
    print(f"  Bandwidth to    : {cfg['bandwidth_timeout']}s")
    print(f"  Switch wait     : {cfg.get('switch_wait', 0.5)}s")
    print(f"  Output file     : {cfg['output']}")

def run_test(cfg: dict, stage: int, load_cache=False, selected_nodes=""):
    args = [
        sys.executable, "main.py",
        "--api", cfg["api"], "--secret", cfg["secret"], "--proxy", cfg["proxy"],
        "--stage", str(stage),
        "--top-ratio", str(cfg["top_ratio"]), "--top-min", str(cfg["top_min"]), "--top-max", str(cfg["top_max"]),
        "--download-bytes", str(cfg["download_bytes"]), "--upload-bytes", str(cfg["upload_bytes"]),
        "--bandwidth-timeout", str(cfg["bandwidth_timeout"]),
        "--switch-wait", str(cfg.get("switch_wait", 0.5)),
    ]
    if cfg["group"]:
        args += ["--group", cfg["group"]]
    if load_cache:
        args += ["--load-cache", "cache.json"]
    if selected_nodes:
        args += ["--nodes", selected_nodes]
    if cfg.get("use_mihomo_latency", True):
        args += ["--no-mihomo-latency"]
    subprocess.run(args)

def main():
    cfg = load_config()
    while True:
        print("\n" + "=" * 50)
        print("  NodeBench - VPN Node Speed Tester")
        print("=" * 50)
        print("  1. Edit Connection Settings")
        print("  2. Edit Test Parameters")
        print("  3. Edit Output Settings")
        print("  4. Show Current Config")
        print("  5. Stage 1: Latency Test")
        print("  6. Stage 2: Bandwidth Test (from cache)")
        print("  7. Full Test")
        print("  0. Exit")
        choice = input("\n  Choice: ").strip()
        if choice == "1":
            edit_connection(cfg)
        elif choice == "2":
            edit_test_params(cfg)
        elif choice == "3":
            edit_output(cfg)
        elif choice == "4":
            show_config(cfg)
        elif choice == "5":
            run_test(cfg, 1)
        elif choice == "6":
            subprocess.run([sys.executable, "main.py", "--load-cache", "cache.json", "--stage", "2"])
        elif choice == "7":
            run_test(cfg, 2)
        elif choice == "0":
            break

if __name__ == "__main__":
    main()

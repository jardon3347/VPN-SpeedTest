# NodeBench

VPN node batch speed tester using Cloudflare Speed Test via mihomo API.

---

## !! Install Dependencies First !!

```bash
pip install -r requirements.txt
```

**Or double-click `install.bat` for one-click install.**

---

## Quick Start

### Option 1: Desktop App (Recommended)

Double-click `NodeBench-GUI.exe` to launch the graphical interface.

### Option 2: Command Line

```bash
python menu.py           # Interactive menu
python main.py --demo    # Self-test
python main.py --help    # Full CLI help
```

## CLI Parameters

| Flag | Description | Default |
|------|-------------|---------|
| `--api` | mihomo API URL | `http://127.0.0.1:9090` |
| `--secret` | API secret | none |
| `--proxy` | SOCKS5 proxy | `socks5://127.0.0.1:7890` |
| `--group` | Group name | auto-detect |
| `--stage` | `1`=latency, `2`=latency+bandwidth | `2` |
| `--download-bytes` | Download test size (bytes) | 25000000 |
| `--upload-bytes` | Upload test size (bytes) | 25000000 |
| `--bandwidth-timeout` | Bandwidth timeout (seconds) | 20 |
| `--switch-wait` | Switch wait (seconds) | 0.5 |
| `--demo` | Self-test mode | — |
| `--output` | Export path (.csv/.json) | — |
| `--save-cache` / `--load-cache` | Cache management | — |
| `--nodes` | Node filter e.g. `1,3,5-7` | — |

## Build EXE

```bash
pip install pyinstaller
python build_exe.py
```
Output: `NodeBench-GUI.exe` (~25MB, standalone)

## Architecture

```
mihomo (SOCKS5:7890, API:9090)
    -> NodeBench
        Stage 1: Fetch nodes + mihomo latency
        Stage 2: Cloudflare download/upload test
```

## Files

| File | Role |
|------|------|
| `NodeBench-GUI.exe` | Packaged desktop app |
| `main.py` | Entry (no args=GUI, args=CLI) |
| `menu.py` | Interactive CLI menu |
| `nodebench/` | Core library |
| `nodebench/gui/` | GUI (customtkinter) |
| `install.bat` | One-click dependency install |
| `build_exe.py` | PyInstaller build script |
| `requirements.txt` | Python dependencies |

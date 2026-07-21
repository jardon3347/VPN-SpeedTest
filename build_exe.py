"""Build NodeBench GUI as a standalone Windows exe.
Requires: pip install pyinstaller
Run:     python build_exe.py
Output:  NodeBench-GUI.exe (project root)
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--name", "NodeBench-GUI",
    "--onefile", "--noconsole",
    "--distpath", "exe_dist", "--workpath", "exe_build",
    "--add-data", f"{ROOT / 'nodebench'};nodebench",
    "--add-data", f"{ROOT / 'nodebench_config.json'};.",
    "--hidden-import", "aiohttp_socks",
    "--collect-all", "customtkinter",
    "--collect-all", "aiohttp",
    str(ROOT / "main.py"),
]

print(">>> Building NodeBench-GUI.exe ...")
result = subprocess.run(cmd)
if result.returncode != 0:
    print(">>> PyInstaller failed with exit code", result.returncode)
    sys.exit(1)

print(">>> Moving exe to project root ...")
import shutil
exe_path = ROOT / "exe_dist" / "NodeBench-GUI.exe"
if not exe_path.exists():
    print(f">>> ERROR: {exe_path} not found — PyInstaller did not produce output")
    sys.exit(1)
shutil.copy(exe_path, ROOT / "NodeBench-GUI.exe")
print(">>> Done: NodeBench-GUI.exe")

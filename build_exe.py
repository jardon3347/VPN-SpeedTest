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
subprocess.run(cmd)
print(">>> Moving exe to project root ...")
import shutil
shutil.copy(ROOT / "exe_dist" / "NodeBench-GUI.exe", ROOT / "NodeBench-GUI.exe")
print(">>> Done: NodeBench-GUI.exe")

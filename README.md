# NodeBench

VPN 节点批量测速工具。调用 **Clash Mi / mihomo** 的 API 获取节点列表和延迟，通过 Cloudflare Speed Test 测速下载/上传带宽。

---

## 使用源码（需要 Python）

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

**或双击 `install.bat` 一键安装。**

### 2. 启动

**桌面应用（推荐）：**
```bash
python main.py
```
或双击 `NodeBench-GUI.exe`（已打包，无需 Python）。

**命令行：**
```bash
python menu.py              # 交互式菜单
python main.py --demo       # 自检模式
python main.py --help       # 完整帮助
```

---

## 前置条件

本工具仅测试过 **Clash Mi / mihomo** 客户端。需要：

1. 运行 Clash Mi / mihomo（如 Clash Verge、mihomo Party、FlClash 等）
2. 开启 **外部控制（External Controller）**（默认端口 `9090`）
3. 记录 **API Secret**（如设置过的话）
4. SOCKS5 代理端口（默认 `7890`）

### 配置参数在哪里找？

| 参数 | Clash Mi 核心设置中的位置 |
|------|---------------------------|
| `API 地址` | 核心设置 → 外部控制（External Controller），默认 `http://127.0.0.1:9090` |
| `Secret` | 核心设置 → API Secret（Bearer Token）。没设则为空 |
| `代理地址` | 核心设置 → SOCKS5 端口，默认 `socks5://127.0.0.1:7890` |
| `代理组` | 运行时自动检测，也可在界面下拉框中选择 |

> 💡 大部分 GUI 客户端（Clash Verge / mihomo Party）的 **设置 → 核心** 页面可以直接看到这些参数。

---

## CLI 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--api` | mihomo API 地址 | `http://127.0.0.1:9090` |
| `--secret` | API 密钥 | 空 |
| `--proxy` | SOCKS5 代理地址 | `socks5://127.0.0.1:7890` |
| `--group` | 代理组名 | 自动检测 |
| `--stage` | `1`=仅延迟, `2`=延迟+带宽 | `2` |
| `--download-bytes` | 下载测试大小（字节） | 25000000 |
| `--upload-bytes` | 上传测试大小（字节） | 25000000 |
| `--bandwidth-timeout` | 带宽测试超时（秒） | 20 |
| `--switch-wait` | 节点切换等待（秒） | 0.5 |
| `--demo` | 自检模式 | — |
| `--output` | 导出路径（.csv / .json） | — |
| `--save-cache` / `--load-cache` | 缓存管理 | — |
| `--nodes` | 节点筛选，如 `1,3,5-7` | — |

---

## 打包 EXE

```bash
pip install pyinstaller
python build_exe.py
```
输出：`NodeBench-GUI.exe`（约 25MB，单文件免安装）

---

## 架构

```
mihomo (SOCKS5:7890, API:9090)
    → NodeBench
        阶段1: 获取节点 + 读取 mihomo 历史延迟
        阶段2: Cloudflare 下载/上传带宽测试
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `NodeBench-GUI.exe` | 打包好的桌面应用（免 Python） |
| `main.py` | 入口（无参=GUI，有参=CLI） |
| `menu.py` | 交互式命令行菜单 |
| `nodebench/` | 核心逻辑 |
| `nodebench/gui/` | GUI 界面（customtkinter） |
| `nodebench/cli.py` | CLI 入口 |
| `install.bat` | 一键安装依赖 |
| `build_exe.py` | PyInstaller 打包脚本 |
| `requirements.txt` | Python 依赖清单 |

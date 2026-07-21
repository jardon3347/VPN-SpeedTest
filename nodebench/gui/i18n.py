"""Simple i18n module for NodeBench GUI. Supports en / zh-CN."""

LANGUAGES = {"en": "English", "zh": "中文简体"}

CURRENT_LANG = "zh"

_TR = {
    # === App ===
    "window_title":              {"en": "NodeBench GUI",                            "zh": "NodeBench 节点测速"},
    "btn_stage1":                {"en": "Stage 1  Fetch Nodes",                     "zh": "阶段1  获取节点"},
    "btn_stage2":                {"en": "Stage 2  Test Selected",                   "zh": "阶段2  测速选中"},
    "btn_select_all":            {"en": "Select All",                               "zh": "全选"},
    "btn_select_none":           {"en": "None",                                     "zh": "取消"},
    "btn_export":                {"en": "Export CSV",                               "zh": "导出CSV"},
    "search_placeholder":        {"en": "Search nodes...",                          "zh": "搜索节点..."},
    "lbl_hint":                  {"en": "Select nodes and click Stage 2.",          "zh": "选择节点后点击阶段2测速"},
    "lbl_dl":                    {"en": "DL",                                       "zh": "下载"},
    "lbl_ul":                    {"en": "UL",                                       "zh": "上传"},
    "lbl_default_speed":         {"en": "0/0 MB  0 Mbps",                          "zh": "0/0 MB  0 Mbps"},
    "msg_switch_to":             {"en": "Switching to [{group}] {name} ...",        "zh": "正在切换到 [{group}] {name} ..."},
    "msg_switched":              {"en": "  Switched -> {name}",                     "zh": "  已切换 -> {name}"},
    "msg_stage1_start":          {"en": "Stage 1: Fetching nodes from mihomo...",   "zh": "阶段1: 正在从 mihomo 获取节点..."},
    "msg_no_nodes_selected":     {"en": "No nodes selected!",                       "zh": "未选中任何节点！"},
    "msg_stage2_start":          {"en": "Stage 2: Testing {count} nodes...",        "zh": "阶段2: 正在测试 {count} 个节点..."},
    "msg_nothing_to_export":     {"en": "Nothing to export!",                       "zh": "没有可导出的数据！"},
    "msg_exported":              {"en": "Exported -> {name}",                       "zh": "已导出 -> {name}"},
    "msg_stage1_done":           {"en": "Stage 1 done: {reachable}/{total} nodes (mihomo latency)", "zh": "阶段1完成: {reachable}/{total} 节点可达"},
    "msg_node_done":             {"en": "{name:<42} DL={download:5.1f}  UL={upload:5.1f} Mbps", "zh": "{name:<42} DL={download:5.1f}  UL={upload:5.1f} Mbps"},
    "msg_best_log":              {"en": "Best -> [{group}] {name}  DL={download:.1f}  UL={upload:.1f} Mbps", "zh": "最佳 -> [{group}] {name}  DL={download:.1f}  UL={upload:.1f} Mbps"},
    "msg_best_lbl":              {"en": "Best: [{group}] {name}  DL={download:.1f}  UL={upload:.1f} Mbps", "zh": "最佳: [{group}] {name}  DL={download:.1f}  UL={upload:.1f} Mbps"},
    "msg_all_done":              {"en": "All {count} nodes tested. Done.",          "zh": "全部 {count} 个节点测试完成"},
    "msg_error_prefix":          {"en": "ERROR: {msg}",                             "zh": "错误: {msg}"},

    # === Config Panel ===
    "cfg_api":                   {"en": "API Address",                              "zh": "API 地址"},
    "cfg_secret":                {"en": "Secret",                                   "zh": "密钥"},
    "cfg_proxy":                 {"en": "Proxy URL",                                "zh": "代理地址"},
    "cfg_group":                 {"en": "Proxy Group",                              "zh": "代理组"},
    "cfg_download":              {"en": "Download (MB)",                            "zh": "下载量 (MB)"},
    "cfg_upload":                {"en": "Upload (MB)",                              "zh": "上传量 (MB)"},
    "cfg_bw_timeout":            {"en": "Bandwidth Timeout (s)",                    "zh": "带宽超时 (秒)"},
    "cfg_switch_wait":           {"en": "Switch Wait (s)",                          "zh": "切换等待 (秒)"},
    "cfg_auto_detect":           {"en": "(auto-detect)",                            "zh": "(自动检测)"},
    "cfg_save":                  {"en": "Save Config",                              "zh": "保存配置"},
    "cfg_saved":                 {"en": "Saved!",                                   "zh": "已保存!"},
    "cfg_language":              {"en": "Language",                                 "zh": "语言"},

    # === Node List ===
    "col_name":                  {"en": "Name",                                     "zh": "名称"},
    "col_latency":               {"en": "Latency",                                  "zh": "延迟"},
    "col_download":              {"en": "Download",                                 "zh": "下载"},
    "col_upload":                {"en": "Upload",                                   "zh": "上传"},
    "col_status":                {"en": "Status",                                   "zh": "状态"},
    "unit_ms":                   {"en": " ms",                                      "zh": " ms"},
    "na":                        {"en": "-",                                        "zh": "-"},

    # === Log Panel ===
    "log_title":                 {"en": "Log",                                      "zh": "日志"},

    # === Test Runner ===
    "err_cannot_reach_api":      {"en": "Cannot reach mihomo API.",                 "zh": "无法连接 mihomo API"},
    "err_no_latency":            {"en": "no mihomo latency",                        "zh": "无延迟数据"},
    "err_no_nodes":              {"en": "No nodes selected.",                       "zh": "未选择节点"},
    "err_switch_failed":         {"en": "switch failed: {e}",                       "zh": "节点切换失败: {e}"},
    "err_download":              {"en": "download: {error}",                        "zh": "下载: {error}"},
    "err_upload":                {"en": "upload: {error}",                          "zh": "上传: {error}"},
    "err_bandwidth":             {"en": "bandwidth test: {e}",                      "zh": "带宽测试: {e}"},
    "err_best_node":             {"en": "Failed to set best node: {e}",             "zh": "设置最佳节点失败: {e}"},
}

def t(key: str, **kwargs) -> str:
    """Get translation for key in current language. Supports format kwargs."""
    entry = _TR.get(key, {})
    text = entry.get(CURRENT_LANG, entry.get("en", key))
    if kwargs:
        text = text.format(**kwargs)
    return text

def set_language(lang: str):
    global CURRENT_LANG
    if lang in LANGUAGES:
        CURRENT_LANG = lang

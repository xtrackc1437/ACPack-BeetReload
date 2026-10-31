"""集中存放数据包的元信息、计分板名、队伍与文案常量。

原项目把这些字面量散落在 29 个 .mcfunction 里，同一事实往往出现在多处且互不一致
（版本号 1.0.8.1 / 1.0.8.3 / 1.21.11 等）。此处收敛为唯一真相源，见 MIGRATION.md 中
的 F6 条目。
"""

from __future__ import annotations

# --- 包元信息 ---------------------------------------------------------------

PACK_NAME = "ACPack"
PACK_VERSION = "1.0.8.4"
MC_TARGET = "26.3"
PACK_FORMAT = (121, 0)

PACK_DESCRIPTION = (
    f"Datapack designed for Areocraft Server, Version {PACK_VERSION}, "
    f"Targeting MC {MC_TARGET}."
)

# --- 外部链接 / 固定信息 -----------------------------------------------------

REPO_URL = "https://github.com/misividkoukou/ACPack"
ISSUES_URL = "https://github.com/misividkoukou/ACPack/issues"
SITE_URL = "https://areocraft.zhangrx.top"
DOCS_URL = "https://docsareocraft.zhangrx.top/zh/help"
AUDIT_GROUP = "176629694"
SERVER_SEED = "1861731603229431126"

# --- 计分板持有人 / 固定名字 --------------------------------------------------

SWEEPER_HOLDER = "#sweeper"
TOTAL_HOLDER = "total"
RANDOM_HOLDER = "#random"
CAROUSEL_HOLDER = "#stats_display"
CONST_HOUR = "#CONSTANT_hour"
CONST_20 = "#CONSTANT_20"
SPECIAL_PLAYER = "misivid_koukou"

# --- 计分板名 ---------------------------------------------------------------

OBJ_SWEEPER = "sweeper_countdown"
OBJ_GAMETIME = "stats.gametime"
OBJ_TIPS_RANDOM = "tips_random"
OBJ_FIRST_JOIN = "first_join"
OBJ_TRIGGER_INT = "trigger.int"
OBJ_TRIGGER = "trigger"
OBJ_TRIGGER_PARTICLE_INT = "trigger.particle.int"
OBJ_TRIGGER_PARTICLE = "trigger.particle"
OBJ_DISPLAY_MODE = "stats.display_mode"
OBJ_DISPLAY = "stats.display"
OBJ_DISPLAY_CAROUSEL = "stats.display"
OBJ_RECORDING = "stats.display_recording"

# --- trigger 编码 -----------------------------------------------------------
# 原实现用裸数字硬编码，且注释里写“10 到 35 预留给 display”，实际只用到 20。
# 这里把语义命名出来，取值保持与原文一致。

TRIG_PANEL = 1
TRIG_TIPS_ON = 2
TRIG_TIPS_OFF = 3
TRIG_SWEEPER_CANCEL = 4
TRIG_SWEEPER_START = 5
TRIG_DISPLAY_SETTINGS = 6
TRIG_SUICIDE = 7
TRIG_PARTICLE_MENU = 8
TRIG_PARTICLE_OFFSET = 9  # 未使用，仅占位说明
TRIG_MODE_BASE = 10
TRIG_MODE_END = 20

# --- 队伍 -------------------------------------------------------------------

TEAMS = [
    # (内部名, 显示名, 颜色, 前缀, 后缀)
    ("core", "[CORE]", "aqua", None, None),
    ("bots", "[假人]", "gray", None, None),
    ("s.total", "[total]", "light_purple", None, None),
    ("ops", "[ADMIN]", "red", None, None),
    ("special", "[SPECIAL]", "gold", "❤", "❤"),
]

TEAM_OPS = "ops"
TEAM_BOTS = "bots"
TEAM_SPECIAL = "special"

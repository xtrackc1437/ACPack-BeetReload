"""引导：ac:load 与 ac:info。

对应原文件：
  data/ac/function/load.mcfunction
  data/ac/function/info.mcfunction
  data/minecraft/tags/function/load.json
"""

from __future__ import annotations

from .. import commands as c
from ..components import open_url, plain, show_text, text
from ..constants import (
    AUDIT_GROUP,
    PACK_VERSION,
    REPO_URL,
    SITE_URL,
    TEAMS,
    TRIG_PANEL,
)
from ..builder import PackWriter


def build(pack: PackWriter) -> None:
    _info(pack)
    _load(pack)


def _info(pack: PackWriter) -> None:
    banner = pack.fn("ac:info")
    banner.add(
        c.tellraw(
            "@s",
            [
                text("ACPack 数据包已加载！", bold=True, color="green"),
                plain(" "),
                text(f"ACPack v{PACK_VERSION} 更新时间:2026.6.29", bold=False),
            ],
        ),
        c.tellraw(
            "@s",
            [
                text("开发: ", color="#FFAD33", bold=True),
                text(
                    "misivid_koukou，Mudkeepz",
                    color="#ffad33",
                    underlined=True,
                    hover=show_text("点击访问源代码仓库"),
                    click=open_url(REPO_URL),
                ),
                plain("   "),
                text(
                    "[关于AreoCraft]",
                    bold=True,
                    color="yellow",
                    hover=show_text(f"审核Q群：{AUDIT_GROUP}"),
                    click=open_url(SITE_URL),
                ),
            ],
        ),
        c.tellraw(
            "@s",
            [
                text(
                    "[打开控制面板]",
                    color="aqua",
                    bold=True,
                    hover=show_text("[打开控制面板]"),
                    click={"action": "run_command", "command": f"trigger trigger set {TRIG_PANEL}"},
                )
            ],
        ),
    )


def _load(pack: PackWriter) -> None:
    load = pack.fn("ac:load", tags=["minecraft:load"])

    # 加载告知
    load.add(c.execute(c.as_("@a"), c.call("ac:info")))

    # 计分板：扫地机倒计时
    load.add(c.obj_add("sweeper_countdown", "dummy"))
    pack.declare_objective("sweeper_countdown")
    load.add(c.sb_set("#sweeper", "sweeper_countdown", -1))

    # 计分板：游戏时长（原版统计）
    load.add(c.obj_add("stats.gametime", "minecraft.custom:play_time"))
    pack.declare_objective("stats.gametime", "minecraft.custom:play_time")

    # 计分板：小贴士随机数
    load.add(c.obj_remove("tips_random"))
    load.add(c.obj_add("tips_random", "dummy"))
    pack.declare_objective("tips_random")

    # 计分板：首次加入
    load.add(c.obj_add("first_join", "dummy", "首次加入"))
    pack.declare_objective("first_join")

    # 计分板：trigger 体系
    load.add(c.obj_add("trigger.int", "dummy"))
    pack.declare_objective("trigger.int")
    load.add(c.obj_remove("trigger"))
    load.add(c.obj_add("trigger", "trigger"))
    pack.declare_objective("trigger", "trigger")

    load.add(c.obj_add("trigger.particle.int", "dummy"))
    pack.declare_objective("trigger.particle.int")
    load.add(c.obj_remove("trigger.particle"))
    load.add(c.obj_add("trigger.particle", "trigger"))
    pack.declare_objective("trigger.particle", "trigger")

    # 计分板：显示模式
    load.add(c.obj_add("stats.display_mode", "dummy"))
    pack.declare_objective("stats.display_mode")

    # 队伍
    for name, display, color, prefix, suffix in TEAMS:
        load.add(c.team_add(name, display))
        load.add(f"team modify {name} color {color}")
        if prefix is not None:
            load.add(f"team modify {name} prefix {c.json_compact(text(prefix, color='red'))}")
        if suffix is not None:
            load.add(f"team modify {name} suffix {c.json_compact(text(suffix, color='red'))}")

    # 计时器启用
    load.add(
        # 原实现的四条首启调度全部是 1t（循环周期由各自函数内部重排）
        c.schedule("ac:ticks/300sec", "1t"),
        c.schedule("ac:ticks/1tick", "1t"),
        c.schedule("ac:ticks/2tick", "2t"),
        c.schedule("ac:ticks/1sec", "1t"),
    )

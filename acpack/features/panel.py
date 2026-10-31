"""控制面板：主面板、计分板显示设置面板、显示模式切换。

对应原文件：
  data/ac/function/display/bar.mcfunction
  data/ac/function/display/settings.mcfunction
  data/ac/function/display/set_mode.mcfunction

原实现里「有哪些显示模式」这一事实被复制了三份（面板按钮、set_mode 的三个分支、
图例文字），导致 trigger 20 的分支写错、图例漏掉 9/10 两项。这里用 MODE_OPTIONS
一张表同时生成三者，结构上消除该类偏差。
"""

from __future__ import annotations

from dataclasses import dataclass

from .. import commands as c
from ..builder import PackWriter
from ..components import Component, button, copy_button, gap, newline, text
from ..constants import (
    OBJ_DISPLAY_MODE,
    OBJ_TRIGGER,
    OBJ_TRIGGER_INT,
    SERVER_SEED,
    TEAM_OPS,
    TRIG_DISPLAY_SETTINGS,
    TRIG_PANEL,
)


@dataclass(frozen=True)
class ModeOption:
    trigger: int
    mode: int
    panel_label: str
    panel_hover: str
    panel_color: str
    feedback: str
    legend: str


# 顺序与原 set_mode.mcfunction 的判定顺序一致
MODE_OPTIONS: list[ModeOption] = [
    ModeOption(10, 1, "[普通轮播]", "普通轮播模式", "green", "计分板显示已切换为: 普通轮播", "轮播"),
    ModeOption(11, 0, "[关闭显示]", "关闭计分板显示", "red", "计分板显示已切换为: 隐藏", "关闭"),
    ModeOption(12, 2, "[固定:死亡量]", "固定显示死亡量", "aqua", "计分板显示已固定为: 死亡量", "死亡"),
    ModeOption(13, 3, "[固定:挖掘量]", "固定显示挖掘量", "aqua", "计分板显示已固定为: 挖掘量", "挖掘"),
    ModeOption(14, 4, "[固定:锄头量]", "固定显示锄头使用量", "aqua", "计分板显示已固定为: 锄头使用量", "锄头"),
    ModeOption(15, 5, "[固定:容器]", "固定显示容器打开次数", "aqua", "计分板显示已固定为: 容器打开次数", "容器"),
    ModeOption(16, 6, "[固定:交易]", "固定显示村民交易次数", "aqua", "计分板显示已固定为: 村民交易次数", "交易"),
    ModeOption(17, 7, "[固定:时长]", "固定显示游戏时长", "aqua", "计分板显示已固定为: 游戏时长", "时长"),
    ModeOption(19, 9, "[固定:加入次数]", "固定显示加入次数", "aqua", "计分板显示已固定为: 加入次数", "加入"),
    ModeOption(20, 10, "[固定:放置次数]", "固定显示放置次数", "aqua", "计分板显示已固定为: 放置次数", "放置"),
    ModeOption(18, 8, "[录屏模式]", "录屏模式:显示固定服务器信息", "light_purple", "计分板显示已切换为: 录屏模式", "录屏"),
]

MODE_BY_TRIGGER = {option.trigger: option for option in MODE_OPTIONS}

# 图例由模式表派生：新增模式时不会漏改说明文字
LEGEND = "(" + ",".join(
    f"{option.mode}={option.legend}" for option in sorted(MODE_OPTIONS, key=lambda item: item.mode)
) + ")"

# 面板按钮的分行布局（原 settings.mcfunction 的视觉排版）
# 第二项表示该行是否用数组包裹：原实现里只有「录屏模式」一行是裸对象
PANEL_ROWS: list[tuple[list[int], bool]] = [
    ([10, 11], True),
    ([12, 13], True),
    ([14, 15], True),
    ([16, 17], True),
    ([19], True),
    ([20], True),
    ([18], False),
]


def build(pack: PackWriter) -> None:
    _bar(pack)
    _settings(pack)
    _set_mode(pack)


def _switch(trigger: int) -> str:
    return f"trigger {OBJ_TRIGGER} set {trigger}"


def _bar(pack: PackWriter) -> None:
    bar = pack.fn("ac:display/bar")
    bar.add(
        # 记下最近一次操作，然后把 trigger 清零避免重复触发
        c.sb_set("@s", OBJ_TRIGGER_INT, TRIG_PANEL),
        c.sb_reset("@s", OBJ_TRIGGER),
        c.tellraw("@s", text("------------ACPack 功能控制面板--------------", color="red")),
        c.tellraw(
            "@s",
            [
                text("欢迎使用控制面板！", color="yellow"),
                text("你可以在这里操作一些数据包的功能。", color="red"),
                newline(),
                text("下一次想要打开面板请使用指令: ", color="red"),
                copy_button(
                    "/trigger trigger set 1",
                    "/trigger trigger set 1",
                    hover="复制到剪贴板",
                    color="gold",
                    bold=None,
                ),
            ],
        ),
        c.tellraw(
            "@s",
            [
                button("[打开Tips]", _switch(2), hover="打开Tips", color="green"),
                gap(),
                button("[关闭Tips]", _switch(3), hover="关闭Tips", color="green"),
                gap(),
                button("[清扫掉落物]", _switch(5), hover="启动扫地机", color="green"),
                gap(),
                button("[粒子菜单]", _switch(8), hover="打开粒子模式设置菜单", color="green", bold=None),
            ],
        ),
        c.tellraw(
            "@s",
            [
                button("[计分板显示设置]", _switch(6), hover="打开计分板显示设置菜单", color="aqua"),
                gap(),
                button("[自杀]", _switch(7), hover="<脱离卡死>", color="red"),
                gap(),
                copy_button("[服务器种子]", SERVER_SEED, hover="点击复制", color="green", bold=None),
            ],
        ),
        c.tellraw("@s", text("------------------------------------------", color="red")),
    )

    # 管理便利面板：仅 ops 队伍可见
    ops_target = f"@s[team={TEAM_OPS}]"
    bar.add(
        c.tellraw(
            ops_target,
            text("------------ACPack 管理便利面板--------------", color="red"),
        ),
        c.tellraw(ops_target, text("请不要随意使用这些命令", color="red")),
    )
    for particle_tag in ("particle_water", "particle_flame", "particle_note"):
        bar.add(
            c.tellraw(
                ops_target,
                copy_button(
                    particle_tag,
                    f"/tag @s add {particle_tag}",
                    hover="复制指令到剪贴板",
                    color="green",
                    bold=None,
                ),
            )
        )


def _settings(pack: PackWriter) -> None:
    settings = pack.fn("ac:display/settings")
    settings.add(
        c.sb_set("@s", OBJ_TRIGGER_INT, TRIG_DISPLAY_SETTINGS),
        c.sb_reset("@s", OBJ_TRIGGER),
        c.tellraw("@s", text("------------计分板显示设置--------------", color="red")),
        c.tellraw(
            "@s",
            [
                text("当前模式: ", color="yellow"),
                {"score": {"name": "@s", "objective": OBJ_DISPLAY_MODE}, "color": "gold"},
                text(f" {LEGEND}", color="gray"),
            ],
        ),
    )

    for triggers, wrapped in PANEL_ROWS:
        parts: list[Component] = []
        for index, trigger in enumerate(triggers):
            option = MODE_BY_TRIGGER[trigger]
            if index:
                parts.append(gap())
            parts.append(
                button(
                    option.panel_label,
                    _switch(trigger),
                    hover=option.panel_hover,
                    color=option.panel_color,
                )
            )
        settings.add(c.tellraw("@s", parts if wrapped else parts[0]))

    settings.add(c.tellraw("@s", text("-----------------------------------------------------", color="red")))


def _set_mode(pack: PackWriter) -> None:
    set_mode = pack.fn("ac:display/set_mode")

    for option in MODE_OPTIONS:
        condition = c.condition_score("@s", OBJ_TRIGGER, str(option.trigger))
        set_mode.add(
            c.execute(condition, c.sb_set("@s", OBJ_DISPLAY_MODE, option.mode)),
            c.execute(condition, c.sb_set("@s", OBJ_TRIGGER_INT, option.trigger)),
            c.execute(condition, c.tellraw("@s", text(option.feedback, color=option.panel_color))),
        )

    # 立即刷新侧边栏，然后清空 trigger
    set_mode.add(
        c.execute(c.as_("@s"), c.call("statistics:display/display_mode")),
        c.sb_reset("@s", OBJ_TRIGGER),
    )

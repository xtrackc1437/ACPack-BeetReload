"""侧边栏显示：模式切换、轮播、录屏板、假人清理联动。

对应原文件：
  statistics/display/display_mode.mcfunction
  statistics/display/display_sidebar.mcfunction
  statistics/display/random.mcfunction
  statistics/display/random_player.mcfunction
  statistics/display/update_recording.mcfunction

改动（见 MIGRATION.md F6）：录屏板上的版本行原为硬编码的 `版本：1.21.11`，与包实际
目标版本（26.3）不一致，现由 constants.MC_TARGET 生成。
"""

from __future__ import annotations

from ... import commands as c
from ...builder import PackWriter
from ...constants import CAROUSEL_HOLDER, MC_TARGET
from .names import (
    OBJ_CONTAINER_USE,
    OBJ_HOE,
    OBJ_JOIN_TOTAL,
    OBJ_MINE,
    OBJ_MODE,
    OBJ_PLACED,
    OBJ_PLAYER_DEATH,
    OBJ_PLAYER_TIME,
    OBJ_RECORDING,
    OBJ_TRADE,
    OBJ_WORLD_DISPLAY,
)

# 固定显示模式：stats.display_mode -> objective
FIXED_MODES: list[tuple[int, str]] = [
    (2, OBJ_PLAYER_DEATH),
    (3, OBJ_MINE),
    (4, OBJ_HOE),
    (5, OBJ_CONTAINER_USE),
    (6, OBJ_TRADE),
    (7, OBJ_PLAYER_TIME),
    (9, OBJ_JOIN_TOTAL),
    (10, OBJ_PLACED),
]

RECORDING_MODE = 8

# 轮播顺序：#stats_display 1..8
CAROUSEL_OBJECTIVES: list[str] = [
    OBJ_PLAYER_DEATH,
    OBJ_MINE,
    OBJ_HOE,
    OBJ_CONTAINER_USE,
    OBJ_TRADE,
    OBJ_PLAYER_TIME,
    OBJ_JOIN_TOTAL,
    OBJ_PLACED,
]


def build(pack: PackWriter) -> None:
    _display_mode(pack)
    _sidebar(pack)
    _random(pack)
    _random_player(pack)
    _recording_board(pack)


def _display_mode(pack: PackWriter) -> None:
    mode = pack.fn("statistics:display/display_mode")
    mode.add(
        c.if_score("@s", OBJ_MODE, "0", c.setdisplay("sidebar")),
        c.if_score("@s", OBJ_MODE, "1", c.call("statistics:display/display_sidebar")),
    )
    for value, objective in FIXED_MODES:
        mode.add(c.if_score("@s", OBJ_MODE, str(value), c.setdisplay("sidebar", objective)))
    mode.add(
        c.if_score("@s", OBJ_MODE, str(RECORDING_MODE), c.setdisplay("sidebar", OBJ_RECORDING)),
    )


def _sidebar(pack: PackWriter) -> None:
    sidebar = pack.fn("statistics:display/display_sidebar")
    for index, objective in enumerate(CAROUSEL_OBJECTIVES, start=1):
        sidebar.add(
            c.if_score(CAROUSEL_HOLDER, OBJ_WORLD_DISPLAY, str(index), c.setdisplay("sidebar", objective))
        )


def _random(pack: PackWriter) -> None:
    total = len(CAROUSEL_OBJECTIVES)
    pack.fn("statistics:display/random").add(
        # 1..N 循环
        c.if_score(CAROUSEL_HOLDER, OBJ_WORLD_DISPLAY, str(total), c.sb_set(CAROUSEL_HOLDER, OBJ_WORLD_DISPLAY, 0)),
        c.sb_add(CAROUSEL_HOLDER, OBJ_WORLD_DISPLAY, 1),
        c.call("statistics:display/update_recording"),
        c.call("statistics:display/random_player"),
    )


def _random_player(pack: PackWriter) -> None:
    # 轮播 / 关闭 / 固定+录屏，分别按各自设置刷新
    pack.fn("statistics:display/random_player").add(
        c.execute(
            c.as_(f"@a[scores={{{OBJ_MODE}=1}}]"),
            c.call("statistics:display/display_mode"),
        ),
        c.execute(
            c.as_(f"@a[scores={{{OBJ_MODE}=0}}]"),
            c.call("statistics:display/display_mode"),
        ),
        c.execute(
            c.as_(f"@a[scores={{{OBJ_MODE}=2..10}}]"),
            c.call("statistics:display/display_mode"),
        ),
    )


def _recording_board(pack: PackWriter) -> None:
    """录屏模式：用假玩家名充当多行文本，分数只用于排序。"""
    board = pack.fn("statistics:display/update_recording")
    lines = [
        ("AreoCraft_8.2", 4),
        ("纯公益原版生存服务器", 3),
        (f"版本：{MC_TARGET}", 2),
        ("审核群：176629694", 1),
    ]
    for holder, value in lines:
        board.add(c.sb_set(holder, OBJ_RECORDING, value))


__all__ = ["build", "CAROUSEL_OBJECTIVES", "FIXED_MODES", "RECORDING_MODE", "OBJ_WORLD_DISPLAY"]

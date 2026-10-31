"""假人清理：每 10 秒把 bots 队伍的统计清零。

对应原文件：statistics/function/fake_player_remove/fake_player_remove.mcfunction
"""

from __future__ import annotations

from ... import commands as c
from ...builder import PackWriter
from ...constants import TEAM_BOTS
from .names import (
    OBJ_CONTAINER_USE,
    OBJ_HOE,
    OBJ_JOIN_TOTAL,
    OBJ_MINE,
    OBJ_PLACED,
    OBJ_PLAYER_DEATH,
    OBJ_PLAYER_TIME,
    OBJ_TRADE,
)

BOT_OBJECTIVES = (
    OBJ_PLAYER_DEATH,
    OBJ_MINE,
    OBJ_CONTAINER_USE,
    OBJ_TRADE,
    OBJ_PLAYER_TIME,
    OBJ_JOIN_TOTAL,
    OBJ_HOE,
    OBJ_PLACED,
)


def build(pack: PackWriter) -> None:
    function = pack.fn("statistics:fake_player_remove/fake_player_remove")
    target = f"@a[team={TEAM_BOTS}]"
    for objective in BOT_OBJECTIVES:
        function.add(c.sb_reset(target, objective))

"""会话类统计：游戏时长与加入次数。

对应原文件：
  statistics/gametime/gametime_judge.mcfunction
  statistics/gametime/gametime_merge.mcfunction
  statistics/join_time/join_time_judge.mcfunction
  statistics/join_time/join_time_merge.mcfunction
"""

from __future__ import annotations

from ... import commands as c
from ...builder import PackWriter
from ...components import plain, score, text
from ...constants import CONST_20, CONST_HOUR
from .names import GAMETIME, OBJ_JOIN, OBJ_JOIN_TOTAL, OBJ_PLAYER_TIME

HOUR_TICKS = "72000"


def build(pack: PackWriter) -> None:
    _gametime(pack)
    _join_time(pack)


def _gametime(pack: PackWriter) -> None:
    pack.fn("statistics:gametime/gametime_judge").add(
        c.execute(
            c.as_(f"@a[scores={{{GAMETIME}={HOUR_TICKS}..}}]"),
            c.call("statistics:gametime/gametime_merge"),
        )
    )

    merge = pack.fn("statistics:gametime/gametime_merge")
    merge.add(
        # 刻 -> 秒 -> 小时
        c.sb_operation("@s", GAMETIME, "/=", CONST_20, GAMETIME),
        c.sb_operation("@s", GAMETIME, "/=", CONST_HOUR, GAMETIME),
        c.sb_operation("@s", OBJ_PLAYER_TIME, "+=", "@s", GAMETIME),
        # 重置基准值（原实现用 61 而非 0，保留该偏置）
        c.sb_set("@s", GAMETIME, 61),
        # 每小时约 3 秒的计时漂移，累计到 1 小时时补正
        c.if_score("@s", OBJ_PLAYER_TIME, "1201", c.sb_remove("@s", OBJ_PLAYER_TIME, 1)),
    )


def _join_time(pack: PackWriter) -> None:
    pack.fn("statistics:join_time/join_time_judge").add(
        c.execute(
            c.as_(f"@a[scores={{{OBJ_JOIN}=1..}}]"),
            c.call("statistics:join_time/join_time_merge"),
        )
    )

    merge = pack.fn("statistics:join_time/join_time_merge")
    merge.add(
        c.execute(
            c.as_("@s"),
            c.sb_operation("@s", OBJ_JOIN_TOTAL, "+=", "@s", OBJ_JOIN),
        ),
        c.sb_reset("@s", OBJ_JOIN),
        c.tellraw("@s", plain(" ")),
        c.tellraw(
            "@s",
            [
                text("这是你第 ", color="aqua"),
                score("@s", OBJ_JOIN_TOTAL, color="gold"),
                plain(" 次加入Areocraft服务器！"),
                text(" 你在服务器的总在线时间为 ", color="aqua"),
                score("@s", OBJ_PLAYER_TIME, color="gold"),
                text(" 小时！", color="aqua"),
            ],
        ),
        c.execute(c.as_("@s"), c.call("ac:info")),
        c.tellraw("@s", plain(" ")),
    )

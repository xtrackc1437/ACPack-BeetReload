"""计时器循环。

原实现是 4 个互相独立、各自 `schedule` 自己的 .mcfunction（ac:ticks/*），
外加 statistics 的 2 个。每个文件都是「先把自己排进队列，再调用业务函数」这一固定模式，
这里用一张表统一生成，避免周期/重排模式被写歪。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .. import commands as c
from ..builder import PackWriter


@dataclass(frozen=True)
class Loop:
    reference: str
    period: str
    body: list[str] = field(default_factory=list)


LOOPS: list[Loop] = [
    Loop(
        "ac:ticks/1tick",
        "1t",
        ["ac:first_join/player", "ac:trigger/player"],
    ),
    Loop(
        "ac:ticks/2tick",
        "2t",
        ["ac:particle/player"],
    ),
    Loop(
        "ac:ticks/1sec",
        "1s",
        ["ac:sweeper/1sec", "ac:sweeper/judge"],
    ),
    Loop(
        "ac:ticks/300sec",
        "300s",
        ["ac:tips/random"],
    ),
    Loop(
        "statistics:1tick",
        "1t",
        [
            "statistics:mine/mine_judge",
            "statistics:hoe/hoe_judge",
            "statistics:death/death_judge",
            "statistics:open_container/open_container_judge",
            "statistics:traded_with_villager/traded_with_villager_judge",
            "statistics:gametime/gametime_judge",
            "statistics:join_time/join_time_judge",
        ],
    ),
    Loop(
        "statistics:10sec",
        "10s",
        [
            "statistics:display/random",
            "statistics:fake_player_remove/fake_player_remove",
        ],
    ),
]


def build(pack: PackWriter) -> None:
    for loop in LOOPS:
        function = pack.fn(loop.reference)
        function.add(c.schedule(loop.reference, loop.period, "replace"))
        function.extend([c.call(target) for target in loop.body])

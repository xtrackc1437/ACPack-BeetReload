"""统计计数：判定 + 合并。

对应原文件：
  statistics/{mine,hoe,death,open_container,traded_with_villager}/*_judge.mcfunction
  statistics/{mine,hoe,death,open_container,traded_with_villager}/*_merge.mcfunction

原实现是 5 组 × 2 个、共 10 个高度雷同的文件，每组只是「准则计分板列表」不同。
这里用 CounterGroup 表统一生成。

改动（见 MIGRATION.md F3）：原 merge 一律执行 `scoreboard players add <显示计分板> 1`
再 reset 源准则，等于把同一 tick 内的多次同类事件压成 1 次。此处改为把源准则的
累计值 `+=` 上去后再 reset，计数与事件次数一致。由于 merge 先累加后清零，
被判据重复调用时后续调用累加的是 0，不会重复计数。
"""

from __future__ import annotations

from dataclasses import dataclass

from ... import commands as c
from ...builder import PackWriter
from .names import (
    OBJ_CONTAINER_USE,
    OBJ_DEATH,
    OBJ_HOE,
    OBJ_MINE,
    OBJ_PLAYER_DEATH,
    OBJ_TRADE,
    TOTAL,
)


@dataclass(frozen=True)
class CounterGroup:
    name: str
    display: str
    sources: tuple[str, ...]

    @property
    def judge(self) -> str:
        return f"statistics:{self.name}/{self.name}_judge"

    @property
    def merge(self) -> str:
        return f"statistics:{self.name}/{self.name}_merge"


COUNTER_GROUPS: list[CounterGroup] = [
    CounterGroup(
        "mine",
        OBJ_MINE,
        (
            "stats.netherite_shovel_used",
            "stats.netherite_pickaxe_used",
            "stats.netherite_axe_used",
            "stats.diamond_shovel",
            "stats.diamond_pickaxe_used",
            "stats.diamond_axe_used",
            "stats.shears",
        ),
    ),
    CounterGroup("hoe", OBJ_HOE, ("stats.diamond_hoe", "stats.netherite_hoe")),
    CounterGroup("death", OBJ_PLAYER_DEATH, (OBJ_DEATH,)),
    CounterGroup(
        "open_container",
        OBJ_CONTAINER_USE,
        ("stats.open_barrel", "stats.open_shulker_box", "stats.open_enderchest", "stats.open_chest"),
    ),
    CounterGroup("traded_with_villager", OBJ_TRADE, ("stats.traded_with_villager",)),
]


def build(pack: PackWriter) -> None:
    for group in COUNTER_GROUPS:
        judge = pack.fn(group.judge)
        for source in group.sources:
            judge.add(
                c.execute(
                    c.as_(f"@a[scores={{{source}=1..}}]"),
                    c.call(group.merge),
                )
            )

        merge = pack.fn(group.merge)
        for source in group.sources:
            merge.add(
                c.sb_operation("@s", group.display, "+=", "@s", source),
                c.sb_operation(TOTAL, group.display, "+=", "@s", source),
                c.sb_reset("@s", source),
            )

    _death_revert(pack)


def _death_revert(pack: PackWriter) -> None:
    """自杀时回退死亡计数（由 ac:kill/kill 调用）。"""
    pack.fn("statistics:death/death_del").add(
        c.sb_remove(TOTAL, OBJ_PLAYER_DEATH, 1),
        c.sb_remove("@s", OBJ_PLAYER_DEATH, 1),
        c.tellraw(
            "@s",
            {"text": "由于玩家本次为自杀，不计入统计数据", "color": "yellow", "bold": True},
        ),
    )

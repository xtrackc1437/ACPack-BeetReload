"""statistics:load —— 计分板声明。

对应原文件：data/statistics/function/load.mcfunction

改动（见 MIGRATION.md F5）：删除无实体上下文下的 `advancement revoke @s only statistics:place`。
该行在服务端上下文执行时必然报错，且 `statistics:block_place/place` 内部已逐玩家 revoke。
"""

from __future__ import annotations

from typing import Any

from ... import commands as c
from ...builder import PackWriter
from ...constants import CONST_20, CONST_HOUR
from .names import GAMETIME, OBJ_RECORDING, OBJ_WORLD_DISPLAY

Display = str | dict[str, Any] | None

# 声明顺序与原文件一致；`CONSTANTS_MARKER` 处插入时长换算常量
CONSTANTS_MARKER: tuple[str, str, Display] = ("__constants__", "", None)

OBJECTIVES: list[tuple[str, str, Display]] = [
    ("stats.death", "minecraft.custom:minecraft.deaths", "死亡次数"),
    ("stats.player_death", "dummy", {"text": "死亡量", "color": "red", "bold": True}),
    ("stats.netherite_shovel_used", "minecraft.used:netherite_shovel", "下界合金铲使用"),
    ("stats.netherite_pickaxe_used", "minecraft.used:netherite_pickaxe", "下界合金镐使用"),
    ("stats.netherite_axe_used", "minecraft.used:netherite_axe", "下界合金斧使用"),
    ("stats.diamond_shovel", "minecraft.used:diamond_shovel", "钻石铲使用"),
    ("stats.diamond_pickaxe_used", "minecraft.used:diamond_pickaxe", "钻石镐使用"),
    ("stats.diamond_axe_used", "minecraft.used:diamond_axe", "钻石斧使用"),
    ("stats.shears", "minecraft.used:shears", "剪刀使用"),
    ("stats.player_mine", "dummy", {"text": "挖掘量", "color": "yellow", "bold": True}),
    ("stats.netherite_hoe", "minecraft.used:netherite_hoe", "下界合金锄使用"),
    ("stats.diamond_hoe", "minecraft.used:diamond_hoe", "钻石锄使用"),
    ("stats.player_hoe", "dummy", {"text": "锄头使用量", "color": "green", "bold": True}),
    ("stats.open_barrel", "minecraft.custom:open_barrel", "木桶打开次数"),
    ("stats.open_shulker_box", "minecraft.custom:open_shulker_box", "潜影盒打开次数"),
    ("stats.open_enderchest", "minecraft.custom:open_enderchest", "末影箱打开次数"),
    ("stats.open_chest", "minecraft.custom:open_chest", "箱子打开次数"),
    ("stats.player_container_use", "dummy", {"text": "容器打开次数", "color": "#FFCC00", "bold": True}),
    ("stats.traded_with_villager", "minecraft.custom:traded_with_villager", "村民交易次数"),
    ("stats.player_traded_with_villager", "dummy", {"text": "村民交易次数", "color": "#33ffad", "bold": True}),
    CONSTANTS_MARKER,
    ("stats.player_gametime", "dummy", {"text": "游戏时长(h)", "color": "gold", "bold": True}),
    ("stats.join_time", "minecraft.custom:leave_game", "退出次数"),
    ("stats.total_join_time", "dummy", {"text": "加入次数", "color": "aqua", "bold": True}),
    ("stats.placed_count", "dummy", {"text": "放置数量", "color": "#63dade"}),
]


def build(pack: PackWriter) -> None:
    load = pack.fn("statistics:load", tags=["minecraft:load"])

    # 轮播用的临时计分板，每次 reload 重置
    load.add(c.obj_remove(OBJ_WORLD_DISPLAY), c.obj_add(OBJ_WORLD_DISPLAY, "dummy"))
    pack.declare_objective(OBJ_WORLD_DISPLAY)

    for name, criteria, display in OBJECTIVES:
        if (name, criteria, display) == CONSTANTS_MARKER:
            load.add(
                c.sb_set(CONST_HOUR, GAMETIME, 3600),
                c.sb_set(CONST_20, GAMETIME, 20),
            )
            continue
        load.add(c.obj_add(name, criteria, display))
        pack.declare_objective(name)

    load.add(c.obj_add(OBJ_RECORDING, "dummy", {"text": "Areocraft Server", "color": "aqua", "bold": True}))
    pack.declare_objective(OBJ_RECORDING)

    load.add(
        c.schedule("statistics:1tick", "1t"),
        c.schedule("statistics:10sec", "10s"),
    )

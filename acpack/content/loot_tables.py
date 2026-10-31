"""战利品表：覆写猪灵以物易物。

对应原文件：data/minecraft/loot_table/gameplay/piglin_bartering.json

条目顺序、权重、数量区间与原文件完全一致；只把重复的结构提成小函数，便于阅读。
（1.21.5+ 的条目字段名是 `modifier`，与原文件保持一致。）
"""

from __future__ import annotations

from typing import Any

from beet import LootTable

from ..builder import PackWriter

Entry = dict[str, Any]


def _uniform(low: float, high: float) -> dict[str, Any]:
    return {"type": "minecraft:uniform", "max": high, "min": low}


def _set_count(count: Any) -> dict[str, Any]:
    return {"type": "minecraft:set_count", "add": False, "count": count}


def _enchant(options: str) -> dict[str, Any]:
    return {"type": "minecraft:enchant_randomly", "options": options}


def _potion(effect: str) -> dict[str, Any]:
    return {"type": "minecraft:set_potion", "id": effect}


def _item(name: str, weight: int, modifier: dict[str, Any] | None = None) -> Entry:
    entry: Entry = {"type": "minecraft:item", "name": f"minecraft:{name}", "weight": weight}
    if modifier is not None:
        entry["modifier"] = modifier
    return entry


ENTRIES: list[Entry] = [
    _item("book", 5, _enchant("minecraft:soul_speed")),
    _item("book", 5, _enchant("minecraft:wind_burst")),
    _item("book", 5, _enchant("minecraft:swift_sneak")),
    _item("iron_boots", 8, _enchant("minecraft:soul_speed")),
    _item("potion", 8, _potion("minecraft:fire_resistance")),
    _item("splash_potion", 8, _potion("minecraft:fire_resistance")),
    _item("potion", 10, _potion("minecraft:water")),
    _item("iron_nugget", 10, _set_count(_uniform(10.0, 36.0))),
    _item("breeze_rod", 5, _set_count(_uniform(12.0, 24.0))),
    _item("heavy_core", 1, _set_count(_uniform(1, 2))),
    _item("ender_pearl", 10, _set_count(_uniform(2.0, 4.0))),
    _item("dried_ghast", 10, _set_count(1.0)),
    _item("string", 20, _set_count(_uniform(3.0, 9.0))),
    _item("quartz", 20, _set_count(_uniform(5.0, 12.0))),
    _item("obsidian", 40),
    _item("crying_obsidian", 40, _set_count(_uniform(1.0, 3.0))),
    _item("fire_charge", 40),
    _item("leather", 40, _set_count(_uniform(2.0, 4.0))),
    _item("soul_sand", 40, _set_count(_uniform(2.0, 8.0))),
    _item("nether_brick", 40, _set_count(_uniform(2.0, 8.0))),
    _item("spectral_arrow", 40, _set_count(_uniform(6.0, 12.0))),
    _item("gravel", 40, _set_count(_uniform(8.0, 16.0))),
    _item("blackstone", 40, _set_count(_uniform(8.0, 16.0))),
]

PIGLIN_BARTERING: dict[str, Any] = {
    "type": "minecraft:barter",
    "pools": [
        {
            "bonus_rolls": 0.0,
            "entries": ENTRIES,
            "rolls": 1.0,
        }
    ],
    "random_sequence": "minecraft:gameplay/piglin_bartering",
}


def build(pack: PackWriter) -> None:
    pack.ctx.data.loot_tables["minecraft:gameplay/piglin_bartering"] = LootTable(PIGLIN_BARTERING)

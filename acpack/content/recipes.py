"""配方修改。

对应原文件：data/ac/recipe/*.json（7 个）

原实现是 7 个独立 JSON；内容不变，改为 Python 字面量后由 beet 的 Recipe 资源写出。
"""

from __future__ import annotations

from typing import Any

from beet import Recipe

from ..builder import PackWriter

RECIPES: dict[str, dict[str, Any]] = {
    # 煤块烧钻石：600 tick（30 秒），经验 1
    "ac:diamond": {
        "type": "smelting",
        "category": "misc",
        "experience": 1,
        "cookingtime": 600,
        "ingredient": "coal_block",
        "result": {"id": "diamond"},
    },
    "ac:calcite": {
        "type": "crafting_shaped",
        "group": "building",
        "show_notification": True,
        "key": {"1": "cobblestone", "2": "bone_block"},
        "pattern": ["112", "  2", "   "],
        "result": {"id": "calcite", "count": 2},
    },
    "ac:cinnabar": {
        "type": "crafting_shaped",
        "group": "building",
        "show_notification": True,
        "key": {"1": "sand", "2": "red_sand"},
        "pattern": ["12 ", "21 ", "   "],
        "result": {"id": "cinnabar", "count": 2},
    },
    "ac:dead_bush": {
        "type": "crafting_shaped",
        "category": "misc",
        "show_notification": True,
        "key": {"1": "stick", "2": "netherite_ingot"},
        "pattern": [" 1 ", "121", "111"],
        "result": {"id": "dead_bush", "count": 1},
    },
    "ac:elytra": {
        "type": "crafting_shaped",
        "category": "equipment",
        "show_notification": True,
        "key": {"1": "phantom_membrane", "2": "stick"},
        "pattern": ["1 1", "121", "1 1"],
        "result": {"id": "elytra", "count": 1},
    },
    "ac:enchanted_golden_apple": {
        "type": "crafting_shaped",
        "category": "misc",
        "show_notification": True,
        "key": {"1": "gold_block", "2": "apple"},
        "pattern": ["111", "121", "111"],
        "result": {"id": "enchanted_golden_apple", "count": 1},
    },
    # 原文件没有 show_notification 字段，保持一致
    "ac:sponge": {
        "type": "crafting_shaped",
        "category": "building",
        "key": {"1": "yellow_wool"},
        "pattern": ["111", "111", "111"],
        "result": {"id": "sponge", "count": 1},
    },
}


def build(pack: PackWriter) -> None:
    for reference, data in RECIPES.items():
        pack.ctx.data.recipes[reference] = Recipe(data)

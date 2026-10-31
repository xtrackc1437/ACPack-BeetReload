"""放置数量统计：由 advancement 触发。

对应原文件：
  data/statistics/advancement/place.json
  data/statistics/function/block_place/place.mcfunction
"""

from __future__ import annotations

from beet import Advancement

from ... import commands as c
from ...builder import PackWriter
from .names import ADVANCEMENT_PLACE, OBJ_PLACED, TOTAL

PLACE_ADVANCEMENT: dict = {
    "criteria": {
        "place_block": {
            "trigger": "minecraft:placed_block",
            "conditions": {},
        }
    },
    "rewards": {
        "function": "statistics:block_place/place",
    },
}


def build(pack: PackWriter) -> None:
    pack.ctx.data.advancements[ADVANCEMENT_PLACE] = Advancement(PLACE_ADVANCEMENT)

    pack.fn("statistics:block_place/place").add(
        c.sb_add("@s", OBJ_PLACED, 1),
        c.sb_add(TOTAL, OBJ_PLACED, 1),
        # 撤销后才能在下次放置时再次触发
        c.advancement_revoke("@s", ADVANCEMENT_PLACE),
    )

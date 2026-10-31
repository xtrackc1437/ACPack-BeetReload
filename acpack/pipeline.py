"""beet 构建入口。

pipeline:
  1. build     —— 由 Python 生成全部函数 / 配方 / 战利品表 / 进度，并做构建期校验
  2. mecha     —— 解析并规范化所有 .mcfunction（语法错误在此阶段直接失败）
  3. finalize  —— 写回与原包逐字段一致的 pack.mcmeta
"""

from __future__ import annotations

from beet import Context

from .builder import PackWriter
from .constants import PACK_DESCRIPTION, PACK_FORMAT
from .content import loot_tables, recipes
from .features import (
    boot,
    dispatch,
    first_join,
    kill,
    panel,
    particles,
    statistics,
    sweeper,
    timers,
    tips,
)
from .validation import validate


def build(ctx: Context) -> None:
    pack = PackWriter(ctx)

    boot.build(pack)
    timers.build(pack)
    dispatch.build(pack)
    panel.build(pack)
    tips.build(pack)
    sweeper.build(pack)
    particles.build(pack)
    first_join.build(pack)
    kill.build(pack)
    statistics.build(pack)

    recipes.build(pack)
    loot_tables.build(pack)

    validate(
        {ref: builder.lines for ref, builder in pack.functions.items()},
        pack.objectives,
    )
    pack.flush()


def finalize(ctx: Context) -> None:
    data = ctx.data.mcmeta.data
    if isinstance(data, dict):
        data["pack"] = {
            "description": PACK_DESCRIPTION,
            "min_format": list(PACK_FORMAT),
            "max_format": list(PACK_FORMAT),
        }
    else:  # 兼容 beet 未来的模型化 mcmeta
        data.pack.description = PACK_DESCRIPTION
        data.pack.min_format = list(PACK_FORMAT)
        data.pack.max_format = list(PACK_FORMAT)

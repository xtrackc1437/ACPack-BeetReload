"""statistics 命名空间：玩家统计与侧边栏显示。"""

from __future__ import annotations

from ...builder import PackWriter
from . import counters, display, maintenance, objectives, placement, session


def build(pack: PackWriter) -> None:
    objectives.build(pack)
    counters.build(pack)
    session.build(pack)
    display.build(pack)
    placement.build(pack)
    maintenance.build(pack)

"""自助自杀（脱离卡死）。

对应原文件：
  data/ac/function/kill/kill.mcfunction
"""

from __future__ import annotations

from .. import commands as c
from ..builder import PackWriter
from ..constants import OBJ_TRIGGER, OBJ_TRIGGER_INT


def build(pack: PackWriter) -> None:
    pack.fn("ac:kill/kill").add(
        c.sb_set("@s", OBJ_TRIGGER_INT, 6),
        c.sb_reset("@s", OBJ_TRIGGER),
        c.kill("@s"),
        c.execute(c.as_("@s"), c.say("我自杀了,牛逼不?!")),
        # 自杀不计入死亡统计
        c.execute(c.as_("@s"), c.call("statistics:death/death_del")),
    )

"""首次加入引导。

对应原文件：
  data/ac/function/first_join/player.mcfunction
  data/ac/function/first_join/1tick.mcfunction
  data/ac/function/first_join/first_join.mcfunction
"""

from __future__ import annotations

from .. import commands as c
from ..builder import PackWriter
from ..components import copy_button, newline, plain, text


def build(pack: PackWriter) -> None:
    pack.fn("ac:first_join/player").add(
        c.execute(c.as_("@a"), c.call("ac:first_join/1tick")),
    )
    pack.fn("ac:first_join/1tick").add(
        c.execute(
            [c.as_("@a"), c.condition_unless_score("@s", "first_join", "1")],
            c.call("ac:first_join/first_join"),
        ),
    )

    join = pack.fn("ac:first_join/first_join")
    join.add(
        # 初始化玩家档案：时长基线、小贴士、显示模式、加入次数
        c.sb_set("@s", "stats.gametime", 61),
        c.sb_set("@s", "stats.player_gametime", 0),
        "tag @s add tips_on",
        c.sb_set("@s", "stats.display_mode", 1),
        c.sb_set("@s", "stats.total_join_time", 1),
        c.tellraw("@s", [plain(" ")]),
        c.tellraw(
            "@s",
            [
                text(
                    "欢迎您来到Areocraft服务器,这个教程将会让你更加了解服务器,但可惜的是",
                    color="green",
                ),
                newline(),
                text("koukou咕了 :(", color="gold"),
            ],
        ),
        c.tellraw("@s", plain(" ")),
        c.tellraw(
            "@s",
            [
                text("小提示已经自动开启,想要关闭请通过教程熟悉！", color="aqua"),
                plain("打开控制面板请用指令："),
                copy_button(
                    "/trigger trigger set 1",
                    "/trigger trigger set 1",
                    hover="复制到剪贴板",
                    color="gold",
                    bold=None,
                ),
            ],
        ),
        c.sb_set("@s", "first_join", 1),
        # 原实现在末尾又写了一次同样的两个值；保留以维持逐指令一致
        c.sb_set("@s", "stats.gametime", 61),
        c.sb_set("@s", "stats.player_gametime", 0),
    )

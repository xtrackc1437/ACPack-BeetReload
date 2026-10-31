"""trigger 分发。

对应原文件：
  data/ac/function/trigger/player.mcfunction
  data/ac/function/trigger/1tick.mcfunction

原实现每个 tick 给所有在线玩家 `enable trigger`，然后按 trigger 值分派到具体功能。
判定用一长串 `execute if score ... matches N run function ...`，值域是散落的魔法数字。
这里改成一张 (值域, 目标函数) 表，语义与原文一致（含 `..-1` 也能打开面板这一行为）。
"""

from __future__ import annotations

from .. import commands as c
from ..builder import PackWriter

# (trigger 值域, 目标函数)，顺序即判定顺序
DISPATCH_TABLE: list[tuple[str, str]] = [
    ("..-1", "ac:display/bar"),
    ("1", "ac:display/bar"),
    ("2", "ac:tips/_on"),
    ("3", "ac:tips/_off"),
    ("4", "ac:sweeper/break"),
    ("5", "ac:sweeper/announce"),
    ("6", "ac:display/settings"),
    ("7", "ac:kill/kill"),
    ("8", "ac:particle/particle_bar"),
    ("10..20", "ac:display/set_mode"),
]


def build(pack: PackWriter) -> None:
    player = pack.fn("ac:trigger/player")
    player.add(c.execute(c.as_("@a"), c.call("ac:trigger/1tick")))

    tick = pack.fn("ac:trigger/1tick")
    # 每 tick 重新授权，玩家用 /trigger 才能再次写入
    tick.add(c.sb_enable("@s", "trigger"))
    # 值域收窄，避免玩家用任意数字触发预留区
    tick.extend(
        [c.if_score("@s", "trigger", matches, c.call(target)) for matches, target in DISPATCH_TABLE]
    )

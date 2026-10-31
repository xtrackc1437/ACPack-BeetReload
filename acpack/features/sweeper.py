"""扫地机。

对应原文件：
  data/ac/function/sweeper/1sec.mcfunction
  data/ac/function/sweeper/announce.mcfunction
  data/ac/function/sweeper/break.mcfunction
  data/ac/function/sweeper/clean.mcfunction
  data/ac/function/sweeper/halt.mcfunction
  data/ac/function/sweeper/judge.mcfunction
  data/ac/function/sweeper/start.mcfunction

【冻结模块】按需求，扫地机行为完全保持原样，不做任何修改：
  * `#sweeper sweeper_countdown` 的状态语义（-1 待机 / 15 起步 / 每秒递减 / 0 清场）不变；
  * `kill @e[type=item]` 仍在服务器上下文执行，即只清理执行维度（主世界）的掉落物；
  * `announce` / `break` 通过 `schedule ... 1t` 延迟切换状态以规避判定竞态的做法不变；
  * `playsound entity.villager.ambient` 不带目标选择器，与原实现一致。
本文件只做指令的等价重写，任何逻辑调整都视为违规。
"""

from __future__ import annotations

from .. import commands as c
from ..builder import PackWriter
from ..components import Component, button, gap, text
from ..constants import OBJ_SWEEPER, OBJ_TRIGGER, OBJ_TRIGGER_INT, SWEEPER_HOLDER

HOLDER = SWEEPER_HOLDER
OBJ = OBJ_SWEEPER


def _countdown(matches: str, run: str) -> str:
    return c.if_score(HOLDER, OBJ, matches, run)


def build(pack: PackWriter) -> None:
    _start(pack)
    _tick(pack)
    _judge(pack)
    _clean(pack)
    _announce(pack)
    _cancel(pack)
    _halt(pack)


def _start(pack: PackWriter) -> None:
    pack.fn("ac:sweeper/start").add(
        _countdown("-1", c.sb_set(HOLDER, OBJ, 15)),
    )


def _tick(pack: PackWriter) -> None:
    pack.fn("ac:sweeper/1sec").add(
        _countdown("1..", c.sb_remove(HOLDER, OBJ, 1)),
    )


def _judge(pack: PackWriter) -> None:
    judge = pack.fn("ac:sweeper/judge")
    judge.add(_countdown("0", c.call("ac:sweeper/clean")))
    for seconds in (1, 2, 3, 4, 5, 10):
        judge.add(
            _countdown(
                str(seconds),
                # 原实现用单元素数组包一层，保持逐指令一致
                c.tellraw("@a", [text(f"[扫地机] 将在{seconds}秒后出动!", color="red")]),
            )
        )


def _clean(pack: PackWriter) -> None:
    pack.fn("ac:sweeper/clean").add(
        c.sb_set(HOLDER, OBJ, -1),
        c.playsound("entity.villager.ambient"),
        c.kill("@e[type=item]"),
        c.tellraw(
            "@a",
            text("[扫地机] 扫地鸡已完成任务,打道回府啦 :）", color="light_purple"),
        ),
    )


def _announce(pack: PackWriter) -> None:
    announce = pack.fn("ac:sweeper/announce")
    announce.add(
        c.sb_set("@s", OBJ_TRIGGER_INT, 5),
        c.sb_reset("@s", OBJ_TRIGGER),
        # 延迟 1t 再置位，避免与随后的状态判定互相干扰
        c.schedule("ac:sweeper/start", "1t", "replace"),
    )

    notice: list[Component] = [
        text("[扫地机] 扫地机即将在15s后出击,如要阻止请点击取消按钮！", color="red"),
        gap(),
        button("[取消]", "trigger trigger set 4", hover="阻止扫地机行动", color="yellow"),
    ]
    announce.add(
        _countdown("-1", c.tellraw("@a", notice)),
        _countdown("-1", c.me("启动了扫地机。")),
        _countdown("1..", c.tellraw("@s", text("[扫地机] 扫地机不在待机状态，无法启动！", color="red"))),
    )


def _cancel(pack: PackWriter) -> None:
    cancel = pack.fn("ac:sweeper/break")
    cancel.add(
        c.sb_set("@s", OBJ_TRIGGER_INT, 4),
        c.sb_reset("@s", OBJ_TRIGGER),
        c.schedule("ac:sweeper/halt", "1t", "replace"),
        _countdown(
            "1..",
            c.tellraw("@a", text("[扫地机] 因玩家要求,扫地鸡暂停出击！！", color="red")),
        ),
        _countdown("1..", c.me("中断了扫地机。")),
        c.unless_score(
            HOLDER,
            OBJ,
            "0..",
            c.tellraw("@s", text("[扫地机] 扫地机没有启动，无法取消！", color="red")),
        ),
    )


def _halt(pack: PackWriter) -> None:
    pack.fn("ac:sweeper/halt").add(
        _countdown("1..", c.sb_set(HOLDER, OBJ, -1)),
    )

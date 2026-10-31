"""粒子装饰系统。

对应原文件：
  data/ac/function/particle/player.mcfunction
  data/ac/function/particle/2tick.mcfunction
  data/ac/function/particle/merge.mcfunction
  data/ac/function/particle/particle.mcfunction
  data/ac/function/particle/particle_bar.mcfunction
  data/ac/function/particle/error.mcfunction

改动（见 MIGRATION.md F2）：原 `2tick` 里在已经是 `as @a` 的上下文中又写了一次
`execute as @a run function ac:particle/particle`，导致 N 名玩家时粒子指令被执行 N² 次、
视觉密度随人数放大。此处直接以当前玩家（@s）执行，恢复“每人一份粒子”的设计意图。

权限选择器按原文件逐条照抄（原文在 name/team 两种限制下参数顺序并不统一），
避免引入与行为无关的差异。
"""

from __future__ import annotations

from dataclasses import dataclass

from .. import commands as c
from ..builder import PackWriter
from ..components import Component, button, gap, newline, text
from ..constants import (
    OBJ_TRIGGER,
    OBJ_TRIGGER_INT,
    OBJ_TRIGGER_PARTICLE,
    OBJ_TRIGGER_PARTICLE_INT,
    SPECIAL_PLAYER,
    TEAM_OPS,
    TEAM_SPECIAL,
    TRIG_PARTICLE_MENU,
)


@dataclass(frozen=True)
class ParticleMode:
    code: int
    particle: str
    speed: str
    count: int
    allow: str
    deny: str


PARTICLE_MODES: list[ParticleMode] = [
    ParticleMode(
        code=1,
        particle="falling_water",
        speed="0.001",
        count=3,
        allow="@s[tag=particle_water,scores={trigger.particle.int=1}]",
        deny="@s[tag=!particle_water,scores={trigger.particle.int=1}]",
    ),
    ParticleMode(
        code=2,
        particle="small_flame",
        speed="0.001",
        count=2,
        allow="@s[tag=particle_flame,scores={trigger.particle.int=2}]",
        deny="@s[tag=!particle_flame,scores={trigger.particle.int=2}]",
    ),
    ParticleMode(
        code=3,
        particle="note",
        speed="0.8",
        count=1,
        allow="@s[tag=particle_note,scores={trigger.particle.int=3}]",
        deny="@s[tag=!particle_note,scores={trigger.particle.int=3}]",
    ),
    ParticleMode(
        code=100,
        particle="cherry_leaves",
        speed="1",
        count=1,
        allow=f"@s[name={SPECIAL_PLAYER},scores={{trigger.particle.int=100}}]",
        deny=f"@s[scores={{trigger.particle.int=100}},name=!{SPECIAL_PLAYER}]",
    ),
    ParticleMode(
        code=101,
        particle="heart",
        speed="0.001",
        count=1,
        allow=f"@s[team={TEAM_SPECIAL},scores={{trigger.particle.int=101}}]",
        deny=f"@s[team=!{TEAM_SPECIAL},scores={{trigger.particle.int=101}}]",
    ),
    ParticleMode(
        code=102,
        particle="copper_fire_flame",
        speed="0.001",
        count=2,
        allow=f"@s[team={TEAM_OPS},scores={{trigger.particle.int=102}}]",
        deny=f"@s[team=!{TEAM_OPS},scores={{trigger.particle.int=102}}]",
    ),
    ParticleMode(
        code=103,
        particle="heart",
        speed="0.001",
        count=1,
        allow=f"@s[name={SPECIAL_PLAYER},scores={{trigger.particle.int=103}}]",
        deny=f"@s[scores={{trigger.particle.int=103}},name=!{SPECIAL_PLAYER}]",
    ),
]


def build(pack: PackWriter) -> None:
    _player(pack)
    _tick(pack)
    _merge(pack)
    _apply(pack)
    _menu(pack)
    _error(pack)


def _player(pack: PackWriter) -> None:
    pack.fn("ac:particle/player").add(c.execute(c.as_("@a"), c.call("ac:particle/2tick")))


def _tick(pack: PackWriter) -> None:
    tick = pack.fn("ac:particle/2tick")
    tick.add(
        c.sb_enable("@s", OBJ_TRIGGER_PARTICLE),
        c.if_score("@s", OBJ_TRIGGER_PARTICLE, "1..", c.call("ac:particle/merge")),
        # 原为 `execute as @a run ...`，此处去掉内层选择器（F2）
        c.call("ac:particle/particle"),
    )


def _merge(pack: PackWriter) -> None:
    pack.fn("ac:particle/merge").add(
        c.sb_operation("@s", OBJ_TRIGGER_PARTICLE_INT, "=", "@s", OBJ_TRIGGER_PARTICLE),
        c.sb_reset("@s", OBJ_TRIGGER_PARTICLE),
    )


def _apply(pack: PackWriter) -> None:
    apply = pack.fn("ac:particle/particle")
    for mode in PARTICLE_MODES:
        apply.add(
            c.execute(
                [c.as_(mode.allow), c.at("@s")],
                c.particle(mode.particle, speed=mode.speed, count=mode.count),
            ),
            c.execute(c.as_(mode.deny), c.call("ac:particle/error")),
        )


def _menu(pack: PackWriter) -> None:
    menu = pack.fn("ac:particle/particle_bar")
    menu.add(
        c.sb_set("@s", OBJ_TRIGGER_INT, TRIG_PARTICLE_MENU),
        c.sb_reset("@s", OBJ_TRIGGER),
        c.tellraw("@s", text("------------ACPack 粒子控制面板--------------", color="red")),
        c.tellraw(
            "@s",
            [
                text("欢迎来到粒子模式设置菜单！", color="aqua"),
                text("你可以在这里选择一些粒子效果来装饰自己。", color="aqua"),
                newline(),
                text("使用方法: ", color="red"),
                text("点击下方按钮选择你想要的粒子效果，", color="aqua"),
            ],
        ),
    )

    common: list[Component] = [
        button("[水流]", "trigger trigger.particle set 1", hover="点击切换水流粒子效果", color="aqua"),
        gap(),
        button("[火焰]", "trigger trigger.particle set 2", hover="点击切换火焰粒子效果", color="red"),
        gap(),
        button("[音符]", "trigger trigger.particle set 3", hover="点击切换音符粒子效果", color="gold"),
    ]
    menu.add(c.tellraw("@s", common))

    # 特殊粒子按权限逐条显示
    special_rows = [
        (f"@s[name={SPECIAL_PLAYER}]", 100, "[樱花]", "点击切换樱花粒子效果"),
        (f"@s[team={TEAM_SPECIAL}]", 101, "[心形]", "点击切换心形粒子效果"),
        (f"@s[team={TEAM_OPS}]", 102, "[铜火]", "点击切换铜火粒子效果"),
        (f"@s[name={SPECIAL_PLAYER}]", 103, "[心形]", "点击切换心形粒子效果"),
    ]
    for target, code, label, hover in special_rows:
        menu.add(
            c.tellraw(
                target,
                [
                    button(
                        label,
                        f"trigger trigger.particle set {code}",
                        hover=hover,
                        color="green",
                    )
                ],
            )
        )

    menu.add(c.tellraw("@s", text("------------------------------------------", color="red")))


def _error(pack: PackWriter) -> None:
    pack.fn("ac:particle/error").add(
        c.tellraw("@s", text("你似乎没有拥有这个效果呢:(", color="red")),
        c.sb_reset("@s", OBJ_TRIGGER_PARTICLE_INT),
    )

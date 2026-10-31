"""指令字符串构造器。

迁移策略：指令文本仍由 Minecraft 语法构成，但每一条都在 Python 中被结构化地拼装出来，
不再以 .mcfunction 源文件形式存在。因此这里只做「无状态、可组合、纯字符串」的薄封装，
方便各 feature 模块以声明式的方式描述逻辑。
"""

from __future__ import annotations

import json
from typing import Any

# --- JSON 文本组件序列化 ------------------------------------------------------


def json_compact(value: Any) -> str:
    """把 Python 结构序列化成紧凑 JSON（保持中文原文，不转义）。"""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def json_display(value: str | dict[str, Any]) -> str:
    """objective 的显示名：字符串原样加引号，字典序列化成组件。"""
    if isinstance(value, str):
        return json_display_text(value)
    return json_compact(value)


def json_display_text(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


# --- scoreboard --------------------------------------------------------------


def obj_add(name: str, criteria: str, display: str | dict[str, Any] | None = None) -> str:
    line = f"scoreboard objectives add {name} {criteria}"
    if display is not None:
        line += f" {json_display(display)}"
    return line


def obj_remove(name: str) -> str:
    return f"scoreboard objectives remove {name}"


def setdisplay(slot: str = "sidebar", objective: str | None = None) -> str:
    line = f"scoreboard objectives setdisplay {slot}"
    if objective is not None:
        line += f" {objective}"
    return line


def sb_set(target: str, objective: str, value: int | str) -> str:
    return f"scoreboard players set {target} {objective} {value}"


def sb_get(target: str, objective: str) -> str:
    return f"scoreboard players get {target} {objective}"


def sb_add(target: str, objective: str, value: int | str) -> str:
    return f"scoreboard players add {target} {objective} {value}"


def sb_remove(target: str, objective: str, value: int | str) -> str:
    return f"scoreboard players remove {target} {objective} {value}"


def sb_reset(target: str, objective: str) -> str:
    return f"scoreboard players reset {target} {objective}"


def sb_enable(target: str, objective: str) -> str:
    return f"scoreboard players enable {target} {objective}"


def sb_operation(target: str, objective: str, op: str, source: str, source_objective: str) -> str:
    return (
        f"scoreboard players operation {target} {objective} "
        f"{op} {source} {source_objective}"
    )


def sb_store_result(target: str, objective: str, command: str) -> str:
    return f"execute store result score {target} {objective} run {command}"


# --- execute ----------------------------------------------------------------


def condition_score(target: str, objective: str, matches: str) -> str:
    return f"if score {target} {objective} matches {matches}"


def condition_unless_score(target: str, objective: str, matches: str) -> str:
    return f"unless score {target} {objective} matches {matches}"


def condition_entity(targets: str) -> str:
    return f"if entity {targets}"


def as_(targets: str) -> str:
    return f"as {targets}"


def at(targets: str) -> str:
    return f"at {targets}"


def execute(conditions: str | list[str], run: str) -> str:
    if isinstance(conditions, str):
        conditions = [conditions]
    return f"execute {' '.join(conditions)} run {run}"


def if_score(target: str, objective: str, matches: str, run: str) -> str:
    return execute(condition_score(target, objective, matches), run)


def unless_score(target: str, objective: str, matches: str, run: str) -> str:
    return execute(f"unless score {target} {objective} matches {matches}", run)


# --- 函数 / 调度 -------------------------------------------------------------


def call(reference: str) -> str:
    return f"function {reference}"


def schedule(reference: str, delay: str, mode: str = "replace") -> str:
    return f"schedule function {reference} {delay} {mode}"


# --- 输出 -------------------------------------------------------------------


def tellraw(target: str, component: Any) -> str:
    return f"tellraw {target} {json_compact(component)}"


def say(message: str) -> str:
    return f"say {message}"


def me(message: str) -> str:
    return f"me {message}"


def playsound(sound: str, targets: str | None = None) -> str:
    line = f"playsound {sound}"
    if targets is not None:
        line += f" {targets}"
    return line


def particle(
    name: str,
    position: str = "~ ~ ~",
    delta: str = "0 0 0",
    speed: str | float = "0",
    count: int | str = 1,
) -> str:
    return f"particle {name} {position} {delta} {speed} {count}"


def team_add(name: str, display: str) -> str:
    return f"team add {name} {json_display_text(display)}"


def team_modify(name: str, option: str, value: str) -> str:
    return f"team modify {name} {option} {value}"


def advancement_revoke(target: str, only: str | None = None) -> str:
    line = f"advancement revoke {target}"
    if only is not None:
        line += f" only {only}"
    return line


def random_value(value_range: str) -> str:
    return f"random value {value_range}"


def kill(targets: str) -> str:
    return f"kill {targets}"

"""构建期校验：悬空函数引用、未声明的计分板、失效的 schedule 目标。

原项目没有任何校验，凡是路径写错、计分板名拼错都要进游戏后才暴露（且往往静默失败）。
这里在构建阶段就把它变成硬错误。
"""

from __future__ import annotations

import re
from collections.abc import Mapping

FUNCTION_REF = re.compile(r"^function ([a-z0-9_.-]+:[a-z0-9_./-]+)$")
SCHEDULE_REF = re.compile(r"^schedule function ([a-z0-9_.-]+:[a-z0-9_./-]+) ")
SCORE_CONDITION = re.compile(r"\b(?:if|unless) score \S+ ([A-Za-z0-9_.]+) matches")
SCORE_PLAYERS = re.compile(
    r"scoreboard players (?:set|add|remove|reset|enable|get) \S+ ([A-Za-z0-9_.]+)"
)
SCORE_OPERATION = re.compile(r"scoreboard players operation \S+ ([A-Za-z0-9_.]+) ")
SCORE_STORE = re.compile(r"execute store (?:result|success) score \S+ ([A-Za-z0-9_.]+) ")
SETDISPLAY = re.compile(r"scoreboard objectives setdisplay \w+(?: ([A-Za-z0-9_.]+))?")
OBJECTIVE_ADD = re.compile(r"scoreboard objectives add ([A-Za-z0-9_.]+) ")


class ValidationError(Exception):
    pass


def validate(
    functions: Mapping[str, list[str]],
    objectives: Mapping[str, str],
) -> None:
    problems: list[str] = []
    known = set(functions)
    declared = set(objectives)

    for reference, lines in functions.items():
        for index, raw in enumerate(lines, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            where = f"{reference}:{index}"

            match = FUNCTION_REF.match(line)
            if match and match.group(1) not in known:
                problems.append(f"{where}: 调用了不存在的函数 {match.group(1)}")

            match = SCHEDULE_REF.match(line)
            if match and match.group(1) not in known:
                problems.append(f"{where}: schedule 指向不存在的函数 {match.group(1)}")

            for pattern in (
                SCORE_CONDITION,
                SCORE_PLAYERS,
                SCORE_OPERATION,
                SCORE_STORE,
            ):
                for objective in pattern.findall(line):
                    if objective not in declared:
                        problems.append(f"{where}: 引用了未声明的计分板 {objective}")

            match = SETDISPLAY.search(line)
            if match and match.group(1) and match.group(1) not in declared:
                problems.append(f"{where}: setdisplay 引用了未声明的计分板 {match.group(1)}")

            for objective in OBJECTIVE_ADD.findall(line):
                if objective not in declared:
                    problems.append(f"{where}: 声明了未登记的计分板 {objective}")

    if problems:
        raise ValidationError("数据包校验失败：\n  " + "\n  ".join(problems))

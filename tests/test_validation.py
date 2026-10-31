"""构建期校验的单元测试：确认护栏真的会拦住写错的引用。"""

from __future__ import annotations

import pytest

from acpack.validation import ValidationError, validate


def test_missing_function_reference() -> None:
    functions = {"ac:a": ["function ac:does_not_exist"]}
    with pytest.raises(ValidationError, match="不存在的函数"):
        validate(functions, {})


def test_missing_schedule_target() -> None:
    functions = {"ac:a": ["schedule function ac:ghost 1t replace"]}
    with pytest.raises(ValidationError, match="schedule 指向不存在的函数"):
        validate(functions, {})


def test_undeclared_objective() -> None:
    functions = {"ac:a": ["scoreboard players set @s typo_obj 1"]}
    with pytest.raises(ValidationError, match="未声明的计分板"):
        validate(functions, {})


def test_valid_pack_passes() -> None:
    functions = {
        "ac:a": ["scoreboard players set @s ok 1", "function ac:b"],
        "ac:b": ["tellraw @s {text: \"hi\"}"],
    }
    validate(functions, {"ok": "dummy"})

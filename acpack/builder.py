"""函数装配器：把各 feature 模块产出的指令行收集成 beet 的 Function 资源。"""

from __future__ import annotations

from dataclasses import dataclass, field

from beet import Context, Function


@dataclass
class FunctionBuilder:
    """单个函数的指令累积器。"""

    reference: str
    tags: tuple[str, ...] = ()
    lines: list[str] = field(default_factory=list)

    def add(self, *lines: str | None) -> "FunctionBuilder":
        for line in lines:
            if line is None:
                continue
            if line == "":
                self.lines.append("")
            else:
                self.lines.extend(line.splitlines())
        return self

    def extend(self, lines: list[str]) -> "FunctionBuilder":
        self.lines.extend(lines)
        return self

    def comment(self, text: str) -> "FunctionBuilder":
        self.lines.append(f"# {text}")
        return self

    def blank(self) -> "FunctionBuilder":
        self.lines.append("")
        return self


class PackWriter:
    """数据包写入器：持有 beet Context，负责函数登记与目标定稿。"""

    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx
        self._functions: dict[str, FunctionBuilder] = {}
        self.objectives: dict[str, str] = {}

    # --- 函数 ---------------------------------------------------------------

    def fn(self, reference: str, *, tags: tuple[str, ...] | list[str] = ()) -> FunctionBuilder:
        if reference in self._functions:
            builder = self._functions[reference]
            if tags:
                builder.tags = tuple(dict.fromkeys([*builder.tags, *tags]))
            return builder
        builder = FunctionBuilder(reference=reference, tags=tuple(tags))
        self._functions[reference] = builder
        return builder

    @property
    def functions(self) -> dict[str, FunctionBuilder]:
        return dict(self._functions)

    # --- 计分板 -------------------------------------------------------------

    def declare_objective(self, name: str, criteria: str = "dummy") -> None:
        self.objectives[name] = criteria

    # --- 定稿 ---------------------------------------------------------------

    def flush(self) -> None:
        for builder in self._functions.values():
            self.ctx.data[builder.reference] = Function(
                builder.lines,
                tags=list(builder.tags),
            )

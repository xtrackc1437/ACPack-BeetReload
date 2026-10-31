"""聊天文本组件（tellraw 的 JSON）构造器。

原项目里每个面板/提示都是一行几百字符的手写 JSON，键名有的加引号有的不加，
字段顺序随机。这里用函数式构造把它变成可读代码，输出语义与原实现逐字段一致。
"""

from __future__ import annotations

from typing import Any

Component = dict[str, Any]
Message = Component | list[Component]


# --- 事件 -------------------------------------------------------------------


def show_text(value: str) -> dict[str, str]:
    return {"action": "show_text", "value": value}


def run_command(command: str) -> dict[str, str]:
    return {"action": "run_command", "command": command}


def copy_to_clipboard(value: str) -> dict[str, str]:
    return {"action": "copy_to_clipboard", "value": value}


def open_url(url: str) -> dict[str, str]:
    return {"action": "open_url", "url": url}


# --- 组件 -------------------------------------------------------------------


def text(
    value: str,
    *,
    color: str | None = None,
    bold: bool | None = None,
    underlined: bool | None = None,
    italic: bool | None = None,
    obfuscated: bool | None = None,
    strikethrough: bool | None = None,
    hover: dict[str, str] | None = None,
    click: dict[str, str] | None = None,
) -> Component:
    component: Component = {"text": value}
    if color is not None:
        component["color"] = color
    if bold is not None:
        component["bold"] = bold
    if underlined is not None:
        component["underlined"] = underlined
    if italic is not None:
        component["italic"] = italic
    if obfuscated is not None:
        component["obfuscated"] = obfuscated
    if strikethrough is not None:
        component["strikethrough"] = strikethrough
    if hover is not None:
        component["hover_event"] = hover
    if click is not None:
        component["click_event"] = click
    return component


def score(target: str, objective: str, *, color: str | None = None) -> Component:
    component: Component = {"score": {"name": target, "objective": objective}}
    if color is not None:
        component["color"] = color
    return component


def button(
    label: str,
    command: str,
    *,
    hover: str,
    color: str,
    bold: bool | None = True,
) -> Component:
    """面板上的可点击按钮：点击执行指令，悬停显示说明。"""
    return text(
        label,
        color=color,
        bold=bold,
        click=run_command(command),
        hover=show_text(hover),
    )


def copy_button(
    label: str,
    value: str,
    *,
    hover: str,
    color: str,
    bold: bool | None = True,
) -> Component:
    """可点击复制的文本（用于复制指令、种子等）。"""
    return text(
        label,
        color=color,
        bold=bold,
        click=copy_to_clipboard(value),
        hover=show_text(hover),
    )


def gap(width: int = 3) -> Component:
    return {"text": " " * width}


def newline() -> Component:
    return {"text": "\n"}


def plain(value: str) -> Component:
    """无任何格式的文本组件（原实现中大量 `{text:" "}` 的等价写法）。"""
    return {"text": value}

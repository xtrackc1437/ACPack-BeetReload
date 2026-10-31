"""对拍工具：比较「原数据包目录」与「beet 构建产物」。

用法：
    python tools/parity.py                     # 原包默认取仓库根目录
    python tools/parity.py --original ../      # 指定原包根目录
    python tools/parity.py --built build       # 指定构建产物
    python tools/parity.py --json out.json     # 输出机器可读的差异

比较口径：
  * 函数：逐行去注释、去空行，再用 mecha 把每条指令解析成 AST 后重新序列化，
    消除空白/引号/JSON 键序差异；比较的是「指令序列」而非字节。
  * JSON（配方 / 战利品表 / 进度）：解析后做结构化深比较。
  * 文件集合：两边的函数与 JSON 文件路径集合必须一致（缺文件/多文件都算差异）。
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any

try:  # mecha 随 beet 安装
    from mecha import Mecha

    MECHA = Mecha()
except Exception:  # pragma: no cover - 仅在对拍环境缺依赖时降级
    MECHA = None

WHITESPACE = re.compile(r"\s+")

FUNCTION_DIRS = ("function", "functions")
JSON_DIRS = ("recipe", "recipes", "advancement", "advancements", "loot_table", "loot_tables")


# --- 读取 -------------------------------------------------------------------


def collect(root: Path) -> tuple[dict[str, Path], dict[str, Path]]:
    """返回 (函数文件, JSON 文件)，键为 `命名空间:相对路径`。"""
    functions: dict[str, Path] = {}
    documents: dict[str, Path] = {}
    data = root / "data"
    if not data.is_dir():
        raise SystemExit(f"找不到数据包目录：{data}")

    for namespace in sorted(p for p in data.iterdir() if p.is_dir()):
        for directory in namespace.iterdir():
            if not directory.is_dir():
                continue
            if directory.name in FUNCTION_DIRS:
                for file in directory.rglob("*.mcfunction"):
                    relative = file.relative_to(directory).with_suffix("").as_posix()
                    key = f"{namespace.name}:{relative}"
                    functions[key] = file
            elif directory.name in JSON_DIRS:
                for file in directory.rglob("*.json"):
                    key = f"{namespace.name}:{file.relative_to(directory).as_posix()}"
                    documents[key] = file
    return functions, documents


# --- 规范化 -----------------------------------------------------------------


def normalize_command(command: str) -> str:
    normalized = command
    if MECHA is not None:
        try:
            normalized = MECHA.serialize(MECHA.parse(command))
        except Exception:
            normalized = WHITESPACE.sub(" ", command).strip()
    else:
        normalized = WHITESPACE.sub(" ", command).strip()
    return canonicalize_payload(normalized)


def _strict_json(text: str) -> str:
    """把 Minecraft 的宽松 JSON（键名可不加引号）转成标准 JSON。"""
    out: list[str] = []
    index = 0
    in_string = False
    escaped = False
    expect_key = False

    while index < len(text):
        char = text[index]
        if in_string:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        else:
            if char == '"':
                in_string = True
                expect_key = False
                out.append(char)
            elif char in "{,":
                expect_key = True
                out.append(char)
            elif char == ":":
                expect_key = False
                out.append(char)
            elif expect_key and (char.isalpha() or char == "_"):
                end = index
                while end < len(text) and (text[end].isalnum() or text[end] == "_"):
                    end += 1
                out.append(f'"{text[index:end]}"')
                index = end - 1
                expect_key = False
            else:
                out.append(char)
        index += 1

    return "".join(out)


def canonicalize_payload(command: str) -> str:
    """把指令里的 JSON 文本组件规范化（键排序、紧凑分隔符）。

    文字组件的键顺序不影响语义（`{text,color}` 与 `{color,text}` 等价），
    但对拍时需要剔除这种噪声，才能暴露真正的内容差异。
    """
    # JSON 组件从「空格 + { 或 [」处开始且一直延伸到行尾；从左往右试第一个能完整解析的位置
    for match in re.finditer(r"[{\[]", command):
        index = match.start()
        if index == 0 or command[index - 1] != " ":
            continue
        payload = command[index:]
        try:
            parsed = json.loads(_strict_json(payload))
        except json.JSONDecodeError:
            continue
        canonical = json.dumps(parsed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return command[:index] + canonical
    return command


def normalize_function(path: Path) -> list[str]:
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(normalize_command(line))
    return lines


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


# --- 比较 -------------------------------------------------------------------


def compare(original: Path, built: Path) -> dict[str, Any]:
    src_funcs, src_docs = collect(original)
    dst_funcs, dst_docs = collect(built)

    report: dict[str, Any] = {
        "missing_functions": sorted(set(src_funcs) - set(dst_funcs)),
        "extra_functions": sorted(set(dst_funcs) - set(src_funcs)),
        "missing_documents": sorted(set(src_docs) - set(dst_docs)),
        "extra_documents": sorted(set(dst_docs) - set(src_docs)),
        "changed_functions": {},
        "changed_documents": {},
    }

    for key in sorted(set(src_funcs) & set(dst_funcs)):
        before = normalize_function(src_funcs[key])
        after = normalize_function(dst_funcs[key])
        if before != after:
            diff = list(
                difflib.unified_diff(
                    before,
                    after,
                    fromfile=f"original/{key}",
                    tofile=f"built/{key}",
                    lineterm="",
                    n=2,
                )
            )
            report["changed_functions"][key] = {
                "lines_before": len(before),
                "lines_after": len(after),
                "diff": diff,
            }

    for key in sorted(set(src_docs) & set(dst_docs)):
        before = load_json(src_docs[key])
        after = load_json(dst_docs[key])
        if before != after:
            report["changed_documents"][key] = {
                "before": before,
                "after": after,
            }

    return report


def summarize(report: dict[str, Any]) -> str:
    lines: list[str] = []
    for field in ("missing_functions", "extra_functions", "missing_documents", "extra_documents"):
        items = report[field]
        if items:
            lines.append(f"{field}: {len(items)}")
            lines.extend(f"  - {item}" for item in items)

    changed_functions = report["changed_functions"]
    lines.append(f"changed_functions: {len(changed_functions)}")
    for key, detail in changed_functions.items():
        lines.append(f"  - {key} ({detail['lines_before']} -> {detail['lines_after']} 行)")

    changed_documents = report["changed_documents"]
    lines.append(f"changed_documents: {len(changed_documents)}")
    for key in changed_documents:
        lines.append(f"  - {key}")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ACPack 原包与构建产物对拍")
    parser.add_argument("--original", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument(
        "--built",
        default=str(Path(__file__).resolve().parents[1] / "build" / "ACPack"),
    )
    parser.add_argument("--json", dest="json_out", default=None)
    parser.add_argument("--diff", action="store_true", help="打印逐行差异")
    args = parser.parse_args(argv)

    report = compare(Path(args.original), Path(args.built))
    print(summarize(report))

    if args.diff:
        for key, detail in report["changed_functions"].items():
            print()
            print("\n".join(detail["diff"]))

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return 0 if not any(
        report[field]
        for field in ("missing_functions", "extra_functions", "missing_documents", "extra_documents")
    ) else 1


if __name__ == "__main__":
    sys.exit(main())

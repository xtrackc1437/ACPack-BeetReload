"""对拍工具：比较「原始数据包」与「beet 构建产物」。

原包默认取**仓库根目录下的 `original.zip`**（标准 Minecraft 数据包压缩包，
根内含 `pack.mcmeta` 与 `data/`）；也接受解包后的目录，便于本地调试。

用法：
    python tools/parity.py                          # 默认：仓库根 original.zip
    python tools/parity.py --original path/to.zip   # 指定压缩包
    python tools/parity.py --original path/to/dir   # 指定解包目录
    python tools/parity.py --built build/ACPack     # 指定构建产物
    python tools/parity.py --json out.json          # 输出机器可读的差异
    python tools/parity.py --diff                   # 打印逐行差异

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
import os
import re
import sys
import zipfile
from collections import Counter
from dataclasses import dataclass, field
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

ORIGINAL_ZIP_NAME = "original.zip"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent


# --- 基准包定位 --------------------------------------------------------------


def candidate_origins() -> list[Path]:
    """默认候选：仓库根目录的 original.zip（再退一步找工程目录下的同名文件）。"""
    return [REPO_ROOT / ORIGINAL_ZIP_NAME, PROJECT_ROOT / ORIGINAL_ZIP_NAME]


def resolve_original(explicit: str | None = None) -> Path | None:
    """确定原包位置：显式参数 > 环境变量 ACPACK_ORIGINAL > 默认候选。"""
    if explicit:
        return Path(explicit)
    from_env = os.environ.get("ACPACK_ORIGINAL")
    if from_env:
        return Path(from_env)
    for candidate in candidate_origins():
        if candidate.is_file():
            return candidate
    return None


# --- 读取 -------------------------------------------------------------------


@dataclass
class PackContents:
    """一份数据包的内容：函数源码文本 + 已解析的 JSON。"""

    origin: str
    functions: dict[str, str] = field(default_factory=dict)
    documents: dict[str, Any] = field(default_factory=dict)


def classify(relative: str) -> tuple[str, str] | None:
    """把 `data/<ns>/<folder>/<rest>` 归类成 (function|document, key)。"""
    parts = relative.split("/")
    if len(parts) < 4 or parts[0] != "data":
        return None
    namespace, directory, rest = parts[1], parts[2], "/".join(parts[3:])

    if directory in FUNCTION_DIRS and rest.endswith(".mcfunction"):
        return "function", f"{namespace}:{rest[: -len('.mcfunction')]}"
    if directory in JSON_DIRS and rest.endswith(".json"):
        return "document", f"{namespace}:{rest}"
    return None


def load_pack(source: Path) -> PackContents:
    """读取数据包：支持 .zip 压缩包与解包后的目录。"""
    if not source.exists():
        raise SystemExit(f"找不到原始数据包：{source}")

    if source.is_file():
        if source.suffix.lower() != ".zip":
            raise SystemExit(f"只支持 .zip 或目录：{source}")
        return _load_zip(source)
    return _load_directory(source)


def _load_directory(root: Path) -> PackContents:
    data = root / "data"
    if not data.is_dir():
        raise SystemExit(f"目录里没有 data/：{root}")

    contents = PackContents(origin=str(root))
    for path in sorted(data.rglob("*")):
        if not path.is_file():
            continue
        relative = f"data/{path.relative_to(data).as_posix()}"
        kind = classify(relative)
        if kind is None:
            continue
        name, key = kind
        if name == "function":
            contents.functions[key] = path.read_text(encoding="utf-8")
        else:
            contents.documents[key] = json.loads(path.read_text(encoding="utf-8"))
    return contents


def _load_zip(path: Path) -> PackContents:
    contents = PackContents(origin=str(path))
    with zipfile.ZipFile(path) as archive:
        names = [
            name
            for name in archive.namelist()
            if not name.endswith("/") and "__MACOSX" not in name
        ]
        prefix = _content_prefix(names)
        for name in names:
            relative = name[len(prefix) :].replace("\\", "/")
            kind = classify(relative)
            if kind is None:
                continue
            kind_name, key = kind
            raw = archive.read(name).decode("utf-8")
            if kind_name == "function":
                contents.functions[key] = raw
            else:
                contents.documents[key] = json.loads(raw)
    return contents


def _content_prefix(names: list[str]) -> str:
    """压缩包可能把整个数据包套在一层目录里，找出 `data/` 之前的前缀。"""
    prefixes = Counter()
    for name in names:
        normalized = name.replace("\\", "/")
        index = normalized.find("data/")
        if index == -1:
            continue
        prefix = normalized[:index]
        if prefix and not prefix.endswith("/"):
            continue
        prefixes[prefix] += 1
    if not prefixes:
        raise SystemExit("压缩包里没有找到 data/ 目录，可能不是数据包")
    return prefixes.most_common(1)[0][0]


def read_mcmeta(source: Path) -> dict[str, Any]:
    """读取数据包的 pack.mcmeta（支持 .zip 与目录）。"""
    if source.is_file():
        with zipfile.ZipFile(source) as archive:
            for name in archive.namelist():
                if name.replace("\\", "/").endswith("pack.mcmeta"):
                    return json.loads(archive.read(name).decode("utf-8"))
        raise SystemExit(f"压缩包里没有 pack.mcmeta：{source}")

    path = source / "pack.mcmeta"
    if not path.is_file():
        raise SystemExit(f"目录里没有 pack.mcmeta：{source}")
    return json.loads(path.read_text(encoding="utf-8"))


# --- 规范化 -----------------------------------------------------------------


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


def normalize_command(command: str) -> str:
    if MECHA is not None:
        try:
            normalized = MECHA.serialize(MECHA.parse(command))
        except Exception:
            normalized = WHITESPACE.sub(" ", command).strip()
    else:
        normalized = WHITESPACE.sub(" ", command).strip()
    return canonicalize_payload(normalized)


def normalize_function(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(normalize_command(line))
    return lines


# --- 比较 -------------------------------------------------------------------


def compare(original: Path, built: Path) -> dict[str, Any]:
    src = load_pack(original)
    dst = load_pack(built)

    report: dict[str, Any] = {
        "original": src.origin,
        "built": dst.origin,
        "missing_functions": sorted(set(src.functions) - set(dst.functions)),
        "extra_functions": sorted(set(dst.functions) - set(src.functions)),
        "missing_documents": sorted(set(src.documents) - set(dst.documents)),
        "extra_documents": sorted(set(dst.documents) - set(src.documents)),
        "changed_functions": {},
        "changed_documents": {},
    }

    for key in sorted(set(src.functions) & set(dst.functions)):
        before = normalize_function(src.functions[key])
        after = normalize_function(dst.functions[key])
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

    for key in sorted(set(src.documents) & set(dst.documents)):
        before = src.documents[key]
        after = dst.documents[key]
        if before != after:
            report["changed_documents"][key] = {"before": before, "after": after}

    return report


def summarize(report: dict[str, Any]) -> str:
    lines = [f"original: {report['original']}", f"built: {report['built']}"]
    for bucket in ("missing_functions", "extra_functions", "missing_documents", "extra_documents"):
        items = report[bucket]
        if items:
            lines.append(f"{bucket}: {len(items)}")
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
    parser.add_argument(
        "--original",
        default=None,
        help="原始数据包：.zip 或解包目录（默认取仓库根目录的 original.zip）",
    )
    parser.add_argument("--built", default=str(PROJECT_ROOT / "build" / "ACPack"))
    parser.add_argument("--json", dest="json_out", default=None)
    parser.add_argument("--diff", action="store_true", help="打印逐行差异")
    args = parser.parse_args(argv)

    original = resolve_original(args.original)
    if original is None or not original.exists():
        candidates = "、".join(str(path) for path in candidate_origins())
        print(
            f"未找到原始数据包（当前指向 {original}）。\n"
            f"请把标准数据包（根内含 pack.mcmeta 与 data/）放到：{candidates}",
            file=sys.stderr,
        )
        return 2

    report = compare(original, Path(args.built))
    print(summarize(report))

    if args.diff:
        for detail in report["changed_functions"].values():
            print()
            print("\n".join(detail["diff"]))

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return (
        0
        if not any(
            report[field]
            for field in (
                "missing_functions",
                "extra_functions",
                "missing_documents",
                "extra_documents",
            )
        )
        else 1
    )


if __name__ == "__main__":
    sys.exit(main())

"""对拍测试：构建产物必须与原数据包「除已知修正外」完全一致。

这个测试是本次迁移的验收闸门：
  * 文件集合必须一致；
  * 未列入 EXPECTED_CHANGED 的函数，指令序列必须逐条相同；
  * 实际发生差异的函数集合必须恰好等于 EXPECTED_CHANGED（多一个、少一个都失败）。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import parity  # noqa: E402

# 基准包默认取仓库根目录的 original.zip（标准数据包压缩包）。
# 也可用 --original 之外的 ACPACK_ORIGINAL 指定 zip 或解包目录；
# 独立仓库 / CI 环境下若没有放入基准包，本文件整体跳过。
ORIGINAL = parity.resolve_original()
if ORIGINAL is None or not ORIGINAL.exists():
    candidates = "、".join(str(path) for path in parity.candidate_origins())
    pytest.skip(
        f"未找到原始数据包（当前指向 {ORIGINAL}），跳过对拍测试；"
        f"请把标准数据包放到：{candidates}",
        allow_module_level=True,
    )

# 迁移中有意修正的函数（详见 MIGRATION.md）
EXPECTED_CHANGED = {
    "ac:info",  # F6 版本号统一
    "ac:display/set_mode",  # F1 trigger 20 分支写错
    "ac:display/settings",  # F7 图例缺 9/10
    "ac:particle/2tick",  # F2 嵌套 as @a
    "statistics:load",  # F5 无实体上下文 revoke
    "statistics:display/update_recording",  # F6 录屏板版本行
    "statistics:mine/mine_merge",  # F3 计数取累计值
    "statistics:hoe/hoe_merge",  # F3
    "statistics:death/death_merge",  # F3
    "statistics:open_container/open_container_merge",  # F3
}


def _beet() -> str:
    candidate = Path(sys.executable).with_name("beet.exe")
    return str(candidate) if candidate.exists() else "beet"


@pytest.fixture(scope="session")
def built() -> Path:
    subprocess.run([_beet(), "build"], cwd=ROOT, check=True)
    output = ROOT / "build" / "ACPack"
    assert (output / "pack.mcmeta").is_file(), "构建产物缺少 pack.mcmeta"
    return output


@pytest.fixture(scope="session")
def report(built: Path) -> dict:
    return parity.compare(ORIGINAL, built)


def test_file_sets_match(report: dict) -> None:
    assert not report["missing_functions"], f"缺少函数：{report['missing_functions']}"
    assert not report["extra_functions"], f"多余函数：{report['extra_functions']}"
    assert not report["missing_documents"], f"缺少数据文件：{report['missing_documents']}"
    assert not report["extra_documents"], f"多余数据文件：{report['extra_documents']}"


def test_only_expected_functions_changed(report: dict) -> None:
    changed = set(report["changed_functions"])
    assert changed == EXPECTED_CHANGED, (
        f"意外的差异集合\n  多出: {sorted(changed - EXPECTED_CHANGED)}\n"
        f"  缺失: {sorted(EXPECTED_CHANGED - changed)}"
    )


def test_content_documents_identical(report: dict) -> None:
    assert report["changed_documents"] == {}, (
        f"配方/战利品表/进度出现差异：{sorted(report['changed_documents'])}"
    )


def test_pack_mcmeta(built: Path) -> None:
    original = parity.read_mcmeta(ORIGINAL)["pack"]
    current = parity.read_mcmeta(built)["pack"]

    assert current["min_format"] == original["min_format"]
    assert current["max_format"] == original["max_format"]
    # 描述里的版本号按 F6 统一到 1.0.8.4
    assert "1.0.8.4" in current["description"]
    assert "26.3" in current["description"]

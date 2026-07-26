"""誕生ゲート台帳 §A（常駐面ベースライン）の機械検査。

設計: docs/artifacts/clause-gate-routing-design-2026-07-26.md v0.3 §4.3 #1
台帳: docs/artifacts/clause-gate-ledger.md

役割は「出口の不動点」である。ゲートを経ずに常駐条項が追加された場合、
台帳 §A の実測値と乖離するためテストが落ちる。編集主体（L1 / subagent）と
セッション内の編集回数を問わずに発火する点が、散文の契機（PM 級事前宣言義務）
より強い（設計 §4.2）。

検査は ID 照合と数値突合のみで、意味解釈を含まない（設計 §1.1 の R3 要件）。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
LEDGER = REPO_ROOT / "docs" / "artifacts" / "clause-gate-ledger.md"

# 台帳 §A が定義する指令カウントのパターン（変更は PM 級 / 台帳 §A と同一）。
# 長いキーワードを先に置き、"MUST NOT" が "MUST" に食われないようにする。
_DIRECTIVE_RE = re.compile(
    r"MUST NOT|MUST|SHOULD NOT|SHOULD|禁止|必須|してはならない"
)

# hard ceiling（外部定数 / arXiv:2607.19257 / 設計 §3.3）
HARD_CEILING = 80

# 台帳 §A の行: | # | `path` | 数 |
_ROW_RE = re.compile(r"^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*$")
_TOTAL_RE = re.compile(r"^\*\*TOTAL:\s*(\d+)\*\*\s*$", re.MULTILINE)


def _count_directives(path: Path) -> int:
    """ファイル内の指令キーワードの出現回数を数える（行数ではない）。"""
    text = path.read_text(encoding="utf-8")
    return len(_DIRECTIVE_RE.findall(text))


def _is_resident(path: Path) -> bool:
    """`paths:` frontmatter を持たない = 無条件ロード = R1。"""
    with path.open(encoding="utf-8") as fh:
        head = [next(fh, "") for _ in range(3)]
    return not any(line.startswith("paths:") for line in head)


def _live_resident_files() -> "dict[str, int]":
    """実際の R1 集合（相対パス → 指令数）を実測する。"""
    candidates = [REPO_ROOT / "CLAUDE.md"]
    candidates += sorted((REPO_ROOT / ".claude" / "rules").rglob("*.md"))
    result = {}
    for path in candidates:
        if not path.is_file() or not _is_resident(path):
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        result[rel] = _count_directives(path)
    return result


def _ledger_section_a() -> "dict[str, int]":
    """台帳 §A の表を読み、相対パス → 指令数 を返す。"""
    text = LEDGER.read_text(encoding="utf-8")
    section = text.split("## §A ")[1].split("## §B ")[0]
    rows = {}
    for line in section.splitlines():
        match = _ROW_RE.match(line.strip())
        if match:
            rows[match.group(1)] = int(match.group(2))
    return rows


def _ledger_total() -> int:
    match = _TOTAL_RE.search(LEDGER.read_text(encoding="utf-8"))
    assert match is not None, "台帳 §A に `**TOTAL: N**` 行がない"
    return int(match.group(1))


def test_ledger_exists():
    assert LEDGER.is_file(), "誕生ゲート台帳が存在しない: {0}".format(LEDGER)


def test_resident_file_set_matches_ledger():
    """R1 ファイル集合の一致。

    新規 rules ファイルの追加 / 既存ファイルの `paths:` 付与（R2 降格）が
    台帳に反映されていない場合に落ちる。
    """
    live = set(_live_resident_files())
    ledger = set(_ledger_section_a())
    missing = sorted(live - ledger)
    stale = sorted(ledger - live)
    assert not missing, (
        "常駐ファイルが台帳 §A に未登録（誕生ゲート未通過の疑い）: {0}".format(missing)
    )
    assert not stale, "台帳 §A に実在しない行がある: {0}".format(stale)


@pytest.mark.parametrize("rel", sorted(_live_resident_files()))
def test_directive_count_matches_ledger(rel):
    """ファイル別の指令数の一致（常駐面の canary）。

    常駐条項を増減させると落ちる。落ちた場合は、設計 §2 の routing を通し、
    §B 条項取引簿に 1 行を記録してから §A の数値を更新すること。
    """
    ledger = _ledger_section_a()
    assert rel in ledger, "台帳 §A に未登録: {0}".format(rel)
    live = _count_directives(REPO_ROOT / rel)
    assert live == ledger[rel], (
        "{0}: 実測 {1} / 台帳 {2}。誕生ゲートを通し §B に記録してから "
        "§A を更新せよ（設計 §2 / §3.2）".format(rel, live, ledger[rel])
    )


def test_ledger_total_is_consistent():
    """§A の TOTAL が行の合計と一致する（算術整合）。"""
    rows = _ledger_section_a()
    assert _ledger_total() == sum(rows.values())


def test_exchange_rate_matches_ceiling_state():
    """天井超過時に net-negative が台帳に明記されていること（設計 §3.5）。

    超過しているのに 1 対 1 のままだと、是正の合法手段が存在しない状態
    （HGA #19 WC-2）に戻るため、台帳の記載自体を検査対象にする。
    """
    total = _ledger_total()
    text = LEDGER.read_text(encoding="utf-8")
    if total > HARD_CEILING:
        assert "net-negative" in text, (
            "指令数 {0} が天井 {1} を超過しているが、台帳に net-negative の "
            "記載がない（設計 §3.5）".format(total, HARD_CEILING)
        )
    else:
        assert "net-negative（1 行追加 = 2 行退出）** ← 設計 §3.5 が発動中" not in text, (
            "指令数 {0} は天井 {1} 以下だが net-negative が発動中と記載されている"
            "（1 対 1 に復帰させること）".format(total, HARD_CEILING)
        )

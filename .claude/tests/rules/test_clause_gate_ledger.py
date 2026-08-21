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


# --- 機構 #9: 未払い債務の決済検査（台帳 §B §未払い債務 / HGA #26 / 2026-08-21）---
#
# 「入場は実行したが交換相手が未確定」という状態を台帳が持てるようにした代償として、
# 最も蓋然性の高い失敗形が「未決済のまま忘れられる」ことになった。人手の記録義務だけに
# 頼らず、次の入場が債務を踏み越えようとした瞬間に落ちるようにする。
#
# 検査は文字列の在否と行順のみで、意味解釈を含まない（設計 §1.1 の R3 要件）。

_TX_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*\d{4}-\d{2}-\d{2}\s*\|(.*)$")
_DEBT_MARKER = "未払い債務"
_SETTLED_MARKER = "債務決済済"
_ENTRY_OP = "入場"
# 操作列の先頭の強調キーワード（`**入場**` / `**退出**` / `**更正**`）を取る。
_EMPHASIS_RE = re.compile(r"\*\*([^*]+)\*\*")


def _transaction_rows(text: str) -> "list[tuple[int, str]]":
    """§B の取引行を (取引番号, 残りの列) で返す。"""
    rows = []
    for line in text.splitlines():
        match = _TX_ROW_RE.match(line)
        if match:
            rows.append((int(match.group(1)), match.group(2)))
    return rows


def _open_debt(rows: "list[tuple[int, str]]") -> "int | None":
    """未払い債務マーカーを持つ取引番号を返す（なければ None）。"""
    for number, rest in rows:
        if _DEBT_MARKER in rest and _SETTLED_MARKER not in rest:
            return number
    return None


def _entries_after(rows: "list[tuple[int, str]]", after: int) -> "list[int]":
    """`after` より後の「入場」操作の取引番号を返す。

    判定は**操作列の先頭の強調キーワードとの完全一致**による。部分一致で見ると、
    操作列や根拠列に「入場」の語を含む別カテゴリの行を誤検出する —— 実際、取引 #17 の
    操作列は「**更正**（記録面の瑕疵の是正 / **入場**でも退出でもない第三カテゴリ）」
    であり、部分一致では入場と誤判定された（2026-08-21 の実測）。
    """
    result = []
    for number, rest in rows:
        if number <= after:
            continue
        emphasis = _EMPHASIS_RE.search(rest.split("|")[0])
        if emphasis is not None and emphasis.group(1) == _ENTRY_OP:
            result.append(number)
    return result


def test_unpaid_debt_blocks_new_entry():
    """未払い債務が開いている間に新規入場が記録されていないこと。

    決済するときは、退出 2 件（自分の分 + 債務分）を §B に記録したうえで
    債務行に "債務決済済" を追記する。根拠は元本の繰越であり、§3.5 の
    net-negative レート（天井超過時の混雑価格）ではない。
    """
    rows = _transaction_rows(LEDGER.read_text(encoding="utf-8"))
    debt = _open_debt(rows)
    if debt is None:
        return
    violating = _entries_after(rows, debt)
    assert not violating, (
        "取引 #{0} の未払い債務が未決済のまま、後続の入場 {1} が記録されている。"
        "入場には 2 件の真正な退出（自分の分 + 債務分）が要る"
        "（台帳 §B §未払い債務 / 設計 §3.2）".format(debt, violating)
    )


def test_debt_detector_fires_on_violation():
    """陰性対照: 検出器が実際に発火することを確かめる。

    実台帳が緑であることは「違反がない」とも「検出器が死んでいる」とも読める。
    偽データで発火を確認しない限り、この検査は無言の空振りと区別できない。
    """
    fake = "\n".join([
        "| 16 | 2026-08-21 | **入場** | 条項 X | 出典 | R1 | **未払い債務 1 件** | 根拠 |",
        "| 17 | 2026-08-22 | **入場** | 条項 Y | 出典 | R1 | #99 | 根拠 |",
    ])
    rows = _transaction_rows(fake)
    debt = _open_debt(rows)
    assert debt == 16, "債務マーカーを検出できていない"
    assert _entries_after(rows, debt) == [17], "債務後の入場を検出できていない"


def test_debt_detector_accepts_settlement():
    """決済済みマーカーがあれば後続の入場を妨げない（決済経路が存在すること）。"""
    fake = "\n".join([
        "| 16 | 2026-08-21 | **入場** | 条項 X | 出典 | R1 | **未払い債務 1 件**（債務決済済 #20・#21） | 根拠 |",
        "| 20 | 2026-08-22 | **入場** | 条項 Y | 出典 | R1 | #21・#22 | 根拠 |",
    ])
    rows = _transaction_rows(fake)
    assert _open_debt(rows) is None, "決済済みマーカーが効いていない"

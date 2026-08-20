"""計器隔離ガード（rootdir conftest / 台帳 §D 在庫 #4 の機構化）

## これは何か

テストセッションの前後で **hook の計器実体**を突き合わせ、変化していたらセッションを
落とす。テストが実リポジトリの計器を汚したことを、その場で名指しで報告する。

## なぜ要るか

`docs/artifacts/retro-2026-08-17.md` P1 の実測: 1 セッションで計器に 3 回触れて
**2 回壊した**。うち 1 件は hook のスモーク実行時に環境変数名を取り違え
（`CLAUDE_PROJECT_DIR` / 正しくは `LAM_PROJECT_ROOT`）、発火時刻に偽の値を上書き
したもの。もう 1 件は復元不能だった。

台帳 §D 在庫 #4 は「計器に書き込みうる検証は隔離の実効を先に確認する」という
**規律**として登録されていたが、規律は忘れられる。検出機構に変換すれば忘れない。

## なぜ rootdir に置くか

`pyproject.toml` の `testpaths` は `.claude/tests` と `.claude/hooks/tests` の
2 ツリーであり、両方を 1 箇所で覆えるのは rootdir の conftest だけである。

## 設計上の制約 — 維持リストを持たない

監視対象は `.claude/hooks/*.py` のソースから導出する。ハードコードした一覧は、
新しい計器が hook に足されたときに**静かに漏れる**。台帳 §C 機構 #7 が同じ理由で
同じ手を採っている（推論をやめて実体から導く）。

テストは `.claude/tests/hooks/test_instrument_isolation.py`。
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

# --------------------------------------------------------------------------
# 除外 — 監視しないものは、必ず理由とセットで書く
# --------------------------------------------------------------------------

EXCLUDED_FROM_WATCH: dict[str, str] = {
    ".claude/test-results.xml": (
        "pytest 自身が pyproject.toml の addopts (--junitxml) で毎回正当に更新する。"
        "監視対象にするとガードが常時落ち、やがて無視されるようになる —— "
        "それは計器を殺すのと同じ結果になる（retro-2026-08-17 P2 の型）。"
    ),
    ".claude": (
        "ディレクトリ（hook が mkdir する）。ファイルではないため内容比較の対象外。"
    ),
    ".claude/rules": (
        "ディレクトリ（条件ロード規範の置き場）。hook は読むだけで書かない。"
    ),
    ".claude/logs": (
        "ディレクトリ（hook のログ置き場）。個々のログファイルは導出側が拾う。"
    ),
}

# --------------------------------------------------------------------------
# 導出
# --------------------------------------------------------------------------

_PATH_EXPR = re.compile(
    r'project_root\s*/\s*((?:"[^"]+"|\w+)(?:\s*/\s*(?:"[^"]+"|\w+))*)'
)
_CONST_DEF = re.compile(r'^(\w+)\s*=\s*"([^"]+)"\s*$', re.MULTILINE)


def _resolve_segments(raw: str, constants: dict[str, str]) -> str | None:
    """`"a" / "b" / IDENT` を `a/b/<IDENT の値>` に解決する。

    解決できない要素（関数呼び出し・引数など動的に決まるもの）が 1 つでも
    あれば None を返す。当て推量で監視対象を作らない。
    """
    segments: list[str] = []
    for seg in raw.split("/"):
        seg = seg.strip()
        if len(seg) >= 2 and seg.startswith('"') and seg.endswith('"'):
            segments.append(seg[1:-1])
        elif seg in constants:
            segments.append(constants[seg])
        else:
            return None
    return "/".join(segments) if segments else None


def derive_instrument_paths(repo_root: Path | str) -> set[str]:
    """`.claude/hooks/*.py` のソースから、hook が触れるリポジトリ相対パスを導出する。

    除外表に載っているものは返さない。
    """
    hooks_dir = Path(repo_root) / ".claude" / "hooks"
    if not hooks_dir.is_dir():
        return set()

    derived: set[str] = set()
    for hook in sorted(hooks_dir.glob("*.py")):
        try:
            text = hook.read_text(encoding="utf-8")
        except OSError:
            continue
        constants = dict(_CONST_DEF.findall(text))
        for raw in _PATH_EXPR.findall(text):
            rel = _resolve_segments(raw, constants)
            if rel and rel not in EXCLUDED_FROM_WATCH:
                derived.add(rel)
    return derived


# --------------------------------------------------------------------------
# スナップショットと差分
# --------------------------------------------------------------------------


def snapshot_instruments(root: Path | str, rel_paths: set[str]) -> dict[str, str | None]:
    """各パスの内容ハッシュを取る。存在しない / ファイルでないものは None。"""
    base = Path(root)
    snap: dict[str, str | None] = {}
    for rel in sorted(rel_paths):
        target = base / rel
        try:
            if target.is_file():
                snap[rel] = hashlib.sha256(target.read_bytes()).hexdigest()
            else:
                snap[rel] = None
        except OSError:
            snap[rel] = None
    return snap


def diff_snapshots(
    before: dict[str, str | None], after: dict[str, str | None]
) -> list[str]:
    """変化したパスをソート済みで返す（作成・削除・内容変更のいずれも変化とみなす）。"""
    return sorted(
        key
        for key in set(before) | set(after)
        if before.get(key) != after.get(key)
    )


def format_violation(changed: list[str]) -> str:
    """違反メッセージを組む。変わったパスを必ず名指しする。

    「何かが変わった」だけでは、後から汚染と正当な更新を区別できない
    （曝露ログを append-only にした判断と同じ理由 / retro-2026-08-17 K3）。
    """
    listing = "\n".join(f"  - {path}" for path in changed)
    return (
        "計器隔離ガード: テストがリポジトリ実体の計器を書き換えた。\n"
        f"{listing}\n\n"
        "hook を実行・import するテストは、書込先を tmp へ向けること。\n"
        "環境変数は LAM_PROJECT_ROOT（CLAUDE_PROJECT_DIR ではない）。\n"
        "参考: .claude/hooks/tests/conftest.py の project_root fixture。\n"
        "変更が意図的なら、変えた計器を手で元に戻してから再実行すること。"
    )


# --------------------------------------------------------------------------
# ガード本体
# --------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def lam_instrument_isolation_guard():
    """セッション前後で計器を突き合わせる。opt-out スイッチは意図的に持たない。"""
    repo_root = Path(__file__).resolve().parent
    watched = derive_instrument_paths(repo_root)
    before = snapshot_instruments(repo_root, watched)

    yield

    after = snapshot_instruments(repo_root, watched)
    changed = diff_snapshots(before, after)
    if changed:
        pytest.fail(format_violation(changed), pytrace=False)

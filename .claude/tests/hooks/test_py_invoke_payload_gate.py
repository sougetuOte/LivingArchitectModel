r"""`py_invoke.sh -c` のペイロード判定 TDD（/full-review 2026-09-05 iter0 の C-1）.

## 問題

`.claude/settings.json` の allow に `Bash(bash .claude/scripts/py_invoke.sh *)` があり、
末尾ワイルドカードが**任意の引数**にマッチする。Python は `subprocess` / `os.system` /
`shutil` で `rm` / `mv` / `chmod` / `git push --force` 相当を全て代替できるため、
`settings.json` の deny リストは**この経路からは一切当たらない**。

実測（2026-09-05）: `/full-review` の監査セッション自身が、この形で任意 Python を
承認なしに 6 回実行した。攻撃を実演するまでもなく、通常運用がそのまま実証だった。

## 前提の確認（upstream-first）

「allow マッチ時に hook がスキップされる」なら hook 側の分岐は空振りする。これは
`pre-tool-use.py` 自身のコメントが述べていた懸念だが、**成立しない**ことを確認した。

- 上流ドキュメントで「allow ルールで事前承認されたものには呼ばれない」と明記されているのは
  **`CanUseTool`**（SDK の権限コールバック）であって PreToolUse hook ではない。hook 側は
  「exit 0 で出力なし = 通常の権限フローに委ねる」= **権限評価より前に走る**構造
- 実測: `.claude/logs/permission.log` に、allow 規則へ厳密一致する
  `bash .claude/scripts/py_invoke.sh ...` の記録が **418 件**。毎回発火している

## 採った形と、採らなかった形

`-c` を一律 PM にすると `/full-review` `/ship` など LAM 自身の動線で承認ダイアログが
常時鳴り、「常時鳴る計器は殺される」型に直行する（`docs/internal/` を PM 級にした際に
`docs/artifacts/` を除外したのと同じ判断）。よって**ペイロードを見て昇格**する。

これは `_determine_by_command` が AUDITING の PG コマンドに対して既に行っている
「shell メタ文字 + ブラックリスト引数」判定と**同じ形**である。

ADR-0008 の反面教師制約 **D1（deny 単独で守らない / allow と対で運用する）**への対応:
本判定の allow 対は「**該当トークンを含まない `-c` は SE のまま自動許可**」であり、
`security-commands.md` §コマンド許可マトリクスにその対で記載する。

## 射程の限界（意図的に守らないもの）

- **`-m` 経路**は対象外。任意モジュールの実行には importable なモジュールが要り、
  任意コードには結局ファイルが要るため、`-c` より 1 段遠い。残件として記録する
- **一般のファイル書込**（`Path.write_text` 等）は対象外。`-c` から PM 級パスへ書けるのは
  事実だが、これは `Bash("cat > ...")` と同じ「Bash 経路はパス判定に到達しない」既知の限界であり、
  本件（deny リストの迂回）とは別の穴である
- **難読化**（`getattr(__import__('os'), 'system')`）は `__import__` を検出対象に含めることで
  一部拾うが、完全ではない。ただし**その形で書かれること自体が異常信号**である
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))


def _load_pre_tool_use():
    spec = importlib.util.spec_from_file_location(
        "ptu_py_invoke_gate", _HOOKS_DIR / "pre-tool-use.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def phase_file(tmp_path):
    p = tmp_path / "current-phase.md"
    p.write_text("**BUILDING**", encoding="utf-8")
    return p


_PREFIX = "bash .claude/scripts/py_invoke.sh"

# deny リスト（rm / mv / chmod / git push --force 等）を Python で代替する形。
#
# 注: 以下の `os.system(...)` / `eval(...)` / `shutil.rmtree(...)` は**判定器に食わせる
# 文字列リテラル**であり、このテストが実行するコードではない（`_determine_by_command` は
# コマンド文字列を受け取って等級を返す純関数で、コマンドを実行しない）。検出対象の
# 見本そのものを置く必要があるため、ここに書くのが正しい。
_RISKY = [
    f"""{_PREFIX} -c "import subprocess; subprocess.run(['git','push','--force'])" """,
    f"""{_PREFIX} -c "import shutil; shutil.rmtree('.claude/logs')" """,
    f"""{_PREFIX} -c "import os; os.system('whoami')" """,
    f"""{_PREFIX} -c "from pathlib import Path; Path('x').unlink()" """,
    f"""{_PREFIX} -c "import os; os.remove('x')" """,
    f"""{_PREFIX} -c "import os; os.chmod('x', 0o777)" """,
    f"""{_PREFIX} -c "import shutil; shutil.move('a','b')" """,
    f"""{_PREFIX} -c "import os; os.rename('a','b')" """,
    f"""{_PREFIX} -c "getattr(__import__('os'),'system')('whoami')" """,
    f"""{_PREFIX} -c "exec(open('payload.txt').read())" """,
    f"""{_PREFIX} -c "eval('1+1')" """,
    # hook 形式（絶対パス）でも同じ判定になること
    'bash "$CLAUDE_PROJECT_DIR/.claude/scripts/py_invoke.sh" -c "import subprocess"',
]

# 本セッションで実際に使った形を含む、判定を変えてはならないもの。
_BENIGN = [
    f"""{_PREFIX} -m pytest .claude/tests .claude/hooks/tests -q""",
    f"""{_PREFIX} .claude/scripts/derive_project_copies.py --check""",
    f"""{_PREFIX} -c "import json; print(json.dumps({{}}))" """,
    f"""{_PREFIX} -c "import sys; sys.path.insert(0, '.claude/hooks'); from analyzers.run_pipeline import run_phase0" """,
    # 陰性対照: exec_module は exec( ではない（誤爆すると本セッションの実作業が全て PM になる）
    f"""{_PREFIX} -c "import importlib.util; spec.loader.exec_module(m)" """,
]


def test_risky_payload_is_escalated_to_pm(phase_file):
    """破壊系トークンを含む `-c` は PM（ask）に昇格する。"""
    ptu = _load_pre_tool_use()
    for command in _RISKY:
        level, reason = ptu._determine_by_command(command, phase_file)
        assert level == "PM", f"PM に昇格していない: {command!r} -> ({level}, {reason})"


def test_benign_payload_stays_se(phase_file):
    """該当トークンを含まない呼び出しは SE のまま（D1 の allow 対）。"""
    ptu = _load_pre_tool_use()
    for command in _BENIGN:
        level, _reason = ptu._determine_by_command(command, phase_file)
        assert level == "SE", f"誤って昇格している: {command!r} -> {level}"


def test_non_py_invoke_commands_are_unaffected(phase_file):
    """py_invoke 以外のコマンドの判定を変えない（射程を広げない）。"""
    ptu = _load_pre_tool_use()
    for command in [
        "echo hello",
        "git status --porcelain",
        # 文字列として subprocess を含むだけの無関係コマンドを巻き込まない
        "grep -rn subprocess .claude/hooks",
    ]:
        level, _reason = ptu._determine_by_command(command, phase_file)
        assert level == "SE", f"射程外のコマンドを昇格させている: {command!r} -> {level}"


def test_escalation_reason_names_the_matched_token(phase_file):
    """理由文字列が「何に当たったか」を含む（ログから追えること）。"""
    ptu = _load_pre_tool_use()
    _level, reason = ptu._determine_by_command(
        f"""{_PREFIX} -c "import shutil; shutil.rmtree('x')" """, phase_file
    )
    assert "shutil" in reason, f"理由に一致トークンが含まれていない: {reason!r}"

"""条件ロード規範の compaction 曝露検出（R3 機構 / 段 3）の TDD.

## 何を検出するのか（「違反」ではなく「曝露」）

段 1 の実測（`docs/artifacts/upstream-intake-survey-2026-08-13.md` §B.4）で、
**条件ロード（R2）で注入された規範は compaction を生き残らない**ことが確認された。
圧縮後に残るのは無条件常駐 13 件のみで、引き金となった `.py` 本体すら脱落する。
**失火は無音**であり、L1 は「消えた」ことに気づけない。

本機構が記録するのは **曝露（exposure）** —— すなわち「compaction が、条件ロード済み
規範の生存中に発生した」という**事象**である。規範に違反したかどうかは意味判断であり、
本機構は判定しない（clause-gate Step 1 (c) を通すための境界）。

## HGA #25 が課した実装条件 2 つ（`hga-summon-log.md` §25 詳細 ④）

1. **検査対象集合を機構自身が基質から導出すること**。維持されたリストを持った瞬間、
   対象の増減ごとに同時更新義務が生じ、設計 §1.1 違反 = `rule-002` 型の恒常税に退化する。
   → `test_no_maintained_list_of_rule_files_in_source` が執行歯
2. **検出のみ・注入なし**。→ `test_main_does_not_inject` が執行歯

## 射程の限界（過大評価しないこと）

- **`.claude/rules/` のみ**を見る。skills 側 frontmatter は今回の対象外
- transcript の `file_path` のみを見る。**Bash 経由でファイルに触れた場合は捕捉しない**
  （`pre-tool-use.py` の `_determine_by_command` と同じ穴 / 対処は別レイヤ）
- 「条件ロードが実際に注入されたか」ではなく「**注入される条件が満たされていたか**」を見る。
  Claude Code 側の注入実装が変われば乖離しうる近似である
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))


def _load_pre_compact():
    spec = importlib.util.spec_from_file_location(
        "pre_compact_for_exposure_test", _HOOKS_DIR / "pre-compact.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def pc():
    return _load_pre_compact()


# --- 条件① 基質からの導出 -------------------------------------------------


def test_conditional_load_rules_derived_from_substrate(pc):
    """`.claude/rules/**/*.md` の frontmatter から `paths:` を実際に読み出す。"""
    rules = pc.load_conditional_load_rules(_REPO_ROOT / ".claude" / "rules")

    # 2026-08-17 時点の実在する条件ロード規範（frontmatter に paths: を持つ）
    assert ".claude/rules/test-result-output.md" in rules
    assert ".claude/rules/subprocess-encoding-convention.md" in rules
    assert ".claude/rules/auto-generated/rule-002.md" in rules

    # 無条件常駐（paths: を持たない）は含まれない
    assert ".claude/rules/phase-rules.md" not in rules
    assert ".claude/rules/core-identity.md" not in rules

    # パターンが実体として読めている
    assert ".claude/**/*.py" in rules[".claude/rules/subprocess-encoding-convention.md"]


def test_no_maintained_list_of_rule_files_in_source(pc):
    """条件①の執行歯: 対象ファイル名をソースに列挙してはならない。

    列挙した瞬間、条件ロード規範の増減ごとに本ファイルの更新義務が生じ、
    設計 §1.1「同時更新義務 = 有の機構は R3 に置けない」に違反する。
    """
    source = (_HOOKS_DIR / "pre-compact.py").read_text(encoding="utf-8")
    for forbidden in (
        "test-result-output",
        "subprocess-encoding-convention",
        "rule-002",
        "model-delegation-prompting",
        "planning-quality-guideline",
    ):
        assert forbidden not in source, (
            f"維持リストの疑い: {forbidden!r} がソースに直書きされている。"
            "検査対象は基質（frontmatter）から導出すること（HGA #25 実装条件 1）"
        )


# --- glob 照合 -------------------------------------------------------------


@pytest.mark.parametrize(
    "pattern,path,expected",
    [
        (".claude/**/*.py", ".claude/hooks/pre-compact.py", True),
        (".claude/**/*.py", ".claude/scripts/dashboard/builder.py", True),
        (".claude/**/*.py", ".claude/rules/phase-rules.md", False),
        (".claude/agents/*.md", ".claude/agents/gabriel.md", True),
        # * は区切りを跨がない
        (".claude/agents/*.md", ".claude/agents/sub/nested.md", False),
        ("docs/specs/**/*.md", "docs/specs/m-1/design.md", True),
        ("docs/adr/*.md", "docs/adr/0009-hga-fable-summoning.md", True),
        ("docs/adr/*.md", "docs/specs/x.md", False),
        ("pyproject.toml", "pyproject.toml", True),
        ("pyproject.toml", "sub/pyproject.toml", False),
        # 先頭 **/ は 0 階層にもマッチする
        ("**/jest.config*", "jest.config.js", True),
        ("**/jest.config*", "web/app/jest.config.ts", True),
    ],
)
def test_glob_match(pc, pattern, path, expected):
    assert pc.glob_match(pattern, path) is expected


# --- transcript からの抽出 -------------------------------------------------


def _write_transcript(tmp_path: Path, entries) -> Path:
    p = tmp_path / "transcript.jsonl"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return p


def test_extract_touched_paths_from_transcript(pc, tmp_path):
    transcript = _write_transcript(
        tmp_path,
        [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Read",
                            "input": {"file_path": "/repo/.claude/hooks/pre-compact.py"},
                        }
                    ]
                },
            },
            {"type": "user", "message": {"content": "just text"}},
        ],
    )
    touched = pc.extract_touched_paths(transcript)
    assert "/repo/.claude/hooks/pre-compact.py" in touched


def test_extract_touched_paths_tolerates_malformed_lines(pc, tmp_path):
    """壊れた行があっても例外を投げず、読める行だけ返す。"""
    p = tmp_path / "transcript.jsonl"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("{ this is not json\n")
        f.write(
            json.dumps({"input": {"file_path": "/repo/a.py"}}, ensure_ascii=False) + "\n"
        )
    assert pc.extract_touched_paths(p) == {"/repo/a.py"}


# --- 曝露判定 ---------------------------------------------------------------


def test_detect_exposure_returns_live_rules(pc, tmp_path):
    rules = {".claude/rules/subprocess-encoding-convention.md": [".claude/**/*.py"]}
    touched = {str(tmp_path / ".claude" / "hooks" / "pre-compact.py")}
    exposed = pc.detect_exposure(rules, touched, tmp_path)
    assert exposed == [".claude/rules/subprocess-encoding-convention.md"]


def test_detect_exposure_empty_when_no_match(pc, tmp_path):
    rules = {".claude/rules/subprocess-encoding-convention.md": [".claude/**/*.py"]}
    touched = {str(tmp_path / "README.md")}
    assert pc.detect_exposure(rules, touched, tmp_path) == []


def test_detect_exposure_ignores_paths_outside_project(pc, tmp_path):
    """プロジェクト外の絶対パスは相対化できないため対象外。"""
    rules = {".claude/rules/subprocess-encoding-convention.md": [".claude/**/*.py"]}
    touched = {"/somewhere/else/.claude/hooks/x.py"}
    assert pc.detect_exposure(rules, touched, tmp_path) == []


# --- 記録 -------------------------------------------------------------------


def test_record_exposure_appends_jsonl(pc, tmp_path):
    pc.record_exposure(
        tmp_path, "2026-08-17T00:00:00Z", "manual", [".claude/rules/a.md"]
    )
    pc.record_exposure(
        tmp_path, "2026-08-17T01:00:00Z", "auto", [".claude/rules/b.md"]
    )

    log = tmp_path / ".claude" / "compaction-exposure.log"
    lines = log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    first = json.loads(lines[0])
    assert first["trigger"] == "manual"
    assert first["exposed"] == [".claude/rules/a.md"]
    assert first["timestamp"] == "2026-08-17T00:00:00Z"

    second = json.loads(lines[1])
    assert second["trigger"] == "auto"


def test_record_exposure_skips_when_nothing_exposed(pc, tmp_path):
    """曝露ゼロなら行を書かない（ログを無内容で膨らませない）。"""
    pc.record_exposure(tmp_path, "2026-08-17T00:00:00Z", "manual", [])
    assert not (tmp_path / ".claude" / "compaction-exposure.log").exists()


# --- 条件② 検出のみ・注入なし ---------------------------------------------


def test_main_does_not_inject(pc, tmp_path, monkeypatch, capsys):
    """条件②の執行歯: stdout に注入用 JSON を出さない。

    Claude Code は hook の stdout JSON（`hookSpecificOutput.additionalContext` 等）を
    context へ注入する。本機構は**検出のみ**であり、消えた規範を復元しない。
    """
    monkeypatch.setattr(pc, "get_project_root", lambda: tmp_path)
    monkeypatch.setattr(sys, "stdin", _FakeStdin(json.dumps({
        "hook_event_name": "PreCompact",
        "trigger": "manual",
        "transcript_path": str(tmp_path / "nonexistent.jsonl"),
    })))
    monkeypatch.setattr(pc, "safe_exit", lambda code: None)

    pc.main()

    out = capsys.readouterr().out
    assert "additionalContext" not in out
    assert "hookSpecificOutput" not in out


def test_main_survives_malformed_stdin(pc, tmp_path, monkeypatch):
    """壊れた stdin でも compaction をブロックしない（exit 0）。"""
    recorded = []
    monkeypatch.setattr(pc, "get_project_root", lambda: tmp_path)
    monkeypatch.setattr(sys, "stdin", _FakeStdin("{ not json"))
    monkeypatch.setattr(pc, "safe_exit", lambda code: recorded.append(code))

    pc.main()

    assert recorded == [0]


def test_main_preserves_existing_flag_behavior(pc, tmp_path, monkeypatch):
    """既存の発火フラグ記録を壊していないこと（回帰）。"""
    monkeypatch.setattr(pc, "get_project_root", lambda: tmp_path)
    monkeypatch.setattr(sys, "stdin", _FakeStdin("{ not json"))
    monkeypatch.setattr(pc, "safe_exit", lambda code: None)

    pc.main()

    assert (tmp_path / ".claude" / "pre-compact-fired").is_file()


class _FakeStdin:
    def __init__(self, payload: str) -> None:
        self._payload = payload

    def read(self) -> str:
        return self._payload

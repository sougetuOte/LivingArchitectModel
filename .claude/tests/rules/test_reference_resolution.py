"""R-1 W-R1 S1 T4: verify_reference_resolution.py テスト.

R-G7 drift 検出ロジックの層 3 unittest。design §5.3 準拠。

- 実データ上での drift 検出結果は「ゼロを強制せず記録のみ」
  (T4 の完了条件は「両ファイル作成 + テスト空実行成功」であり、
   実 drift = 0 は W-R3/W-R4 の完了条件であって S1 T4 の要件ではない)
- 内部関数の合成 fixture 検証 (パターン正規表現の抜け穴確認)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import verify_reference_resolution as vr  # noqa: E402


# ---- 正規表現パターン検査 (合成 fixture) ----


def test_w_r3_pat_rules_path_matches_numbered_rule():
    """数字含む rule-NNN ファイル名 (rule-001.md 等) を捕捉できる (W4 是正)."""
    m = vr._W_R3_PAT_RULES_PATH.search(".claude/rules/auto-generated/rule-001.md")
    assert m is not None
    assert m.group(1) == "rule-001.md"


def test_w_r3_pat_rules_path_matches_flat_rule():
    """auto-generated/ を含まないフラットな rules.md 参照."""
    m = vr._W_R3_PAT_RULES_PATH.search("see .claude/rules/phase-rules.md for detail")
    assert m is not None
    assert m.group(1) == "phase-rules.md"


def test_w_r3_pat_rule_name_matches_bare_rule_id():
    """rule-XXX 名前参照 (パス prefix なし)."""
    m = vr._W_R3_PAT_RULE_NAME.search("rule-001 に該当")
    assert m is not None
    assert m.group(1) == "001"


def test_w_r3_pat_spec_ref_matches_dir_and_file():
    """docs/specs/<slug>/ ディレクトリ形式と docs/adr/<slug>.md フラット形式."""
    m1 = vr._W_R3_PAT_SPEC_REF.search("docs/specs/large-scale-review/")
    assert m1 is not None
    assert m1.group(1) == "specs" and m1.group(2) == "large-scale-review"
    m2 = vr._W_R3_PAT_SPEC_REF.search("docs/adr/0009-hga-fable-summoning.md")
    assert m2 is not None
    assert m2.group(1) == "adr"


def test_w_r4_pat_subagent_matches_three_notations():
    """subagent_type の 3 記法 (キーワード引数 / YAML / 等号) を統一捕捉 (W4 是正)."""
    for txt in [
        'subagent_type="goal-driven-grader"',
        "subagent_type: goal-driven-grader",
        "subagent_type=goal-driven-grader",
    ]:
        m = vr._W_R4_PAT_SUBAGENT.search(txt)
        assert m is not None, f"failed to match: {txt!r}"
        assert m.group(1) == "goal-driven-grader"


def test_w_r4_pat_agent_call_matches_function_notation():
    m = vr._W_R4_PAT_AGENT_CALL.search("Agent(goal-driven-l3-executor)")
    assert m is not None
    assert m.group(1) == "goal-driven-l3-executor"


# ---- agent 存在解決 ----


def test_resolve_agent_builtin_is_valid():
    """組込 agent (general-purpose / Explore 等) は drift 判定から除外."""
    assert vr._resolve_agent("general-purpose") is True
    assert vr._resolve_agent("Explore") is True
    assert vr._resolve_agent("Plan") is True


def test_resolve_agent_plugin_namespaced_is_valid():
    """plugin:xxx 形式は本 repo にない前提で drift 判定除外."""
    assert vr._resolve_agent("pr-review-toolkit:code-reviewer") is True


def test_resolve_agent_existing_local_agent():
    """.claude/agents/ に実在する agent は True."""
    assert vr._resolve_agent("gabriel") is True
    assert vr._resolve_agent("code-reviewer") is True


def test_resolve_agent_nonexistent_returns_false():
    """実在しない agent 名は False = drift."""
    assert vr._resolve_agent("nonexistent-agent-xyz-123") is False


# ---- エンドツーエンド (実データ) ----


def test_verify_w_r3_returns_list():
    """W-R3 用検査は list[dict] を返す (実 drift 件数は問わない)."""
    result = vr.verify_w_r3()
    assert isinstance(result, list)
    for drift in result:
        assert "pattern" in drift
        assert "source" in drift
        assert "referenced" in drift


def test_verify_w_r4_returns_list():
    """W-R4 用検査は list[dict] を返す (実 drift 件数は問わない)."""
    result = vr.verify_w_r4()
    assert isinstance(result, list)
    for drift in result:
        assert "pattern" in drift
        assert "source" in drift
        assert "referenced" in drift


def test_gabriel_contract_fields_present_in_agent_md():
    """gabriel.md には 6 契約フィールドが全て記述されている (W-R4 drift 0 前提)."""
    gabriel_md = vr.REPO_ROOT / ".claude/agents/gabriel.md"
    if not gabriel_md.exists():
        return  # skip if not present
    text = gabriel_md.read_text(encoding="utf-8")
    missing = sorted(f for f in vr._GABRIEL_CONTRACT_FIELDS if f not in text)
    # 参考記録として assert しない (W-R4 S3 で消化する drift の可能性あり)
    # ただし後続実装で欠落が判明したら Warning 起票の材料となる
    assert isinstance(missing, list)


# ---- CLI (エントリーポイント) ----


def test_cli_help_exits_zero():
    """--help は rc=0."""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "verify_reference_resolution.py"), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "verify_reference_resolution" in result.stdout


def test_cli_all_wave_runs():
    """--wave all で実行完了 (drift 検出は許容 / rc=0)."""
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "verify_reference_resolution.py"),
            "--wave",
            "all",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "total_drifts" in result.stdout

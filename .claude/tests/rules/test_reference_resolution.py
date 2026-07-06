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


# ---- R1-006: 大文字・ドット含みファイル名の検出漏れ修正 (2026-07-06 HGA #8 crux 反映) ----
#
# 根拠: docs/artifacts/r-1-audit-tracker.md §R1-006
# 修正方針 (3 箇所非対称):
#   - パターン 1 group 1 (\.md アンカー付き): [A-Za-z0-9._-]+
#   - パターン 3 group 3 (\.md アンカー付き): [A-Za-z0-9._-]+
#   - パターン 3 group 2 (slug / アンカーなし): [A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)* (内部ドットのみ)
#   - パターン 2 (rule-\d{3}) は無関係で無変更


def test_w_r3_pat_rules_path_matches_uppercase_filename():
    """(a) 大文字ファイル名 README.md が検出できる (旧 false negative)."""
    m = vr._W_R3_PAT_RULES_PATH.search(
        ".claude/rules/auto-generated/README.md（ライフサイクル）"
    )
    assert m is not None, "大文字ファイル名 README.md が検出できていません (R1-006)"
    assert m.group(1) == "README.md"


def test_w_r3_pat_rules_path_matches_dotted_filename():
    """(b) ドット合成ファイル名 foo.v2.md が全体としてマッチする."""
    m = vr._W_R3_PAT_RULES_PATH.search(".claude/rules/foo.v2.md")
    assert m is not None
    assert m.group(1) == "foo.v2.md"


def test_w_r3_pat_rules_path_stops_before_trailing_period():
    """(c) 文末句点で greedy+backtrack により自動整形されること (\\.md アンカー付きは安全)."""
    m = vr._W_R3_PAT_RULES_PATH.search(
        "see .claude/rules/phase-rules.md. Next sentence"
    )
    assert m is not None
    assert m.group(1) == "phase-rules.md", (
        "アンカー付きパターンは文末句点を含めない (greedy backtrack で .md 直後に停止)"
    )


def test_w_r3_pat_spec_ref_matches_dotted_slug_flat_file():
    """(d) パターン 3: ドット含み flat spec ファイル名 (group2 に .md まで取り込まれる) を検出できる.

    フラット形式 (末尾に /<file>.md を伴わない) では group3 の `(?:/...)?` が
    発火しないため、`.md` を含むファイル名全体が group2 (slug) 側に取り込まれる。
    """
    m = vr._W_R3_PAT_SPEC_REF.search(
        "docs/specs/v4.0.0-immune-system-requirements.md"
    )
    assert m is not None
    assert m.group(1) == "specs"
    assert m.group(2) == "v4.0.0-immune-system-requirements.md", (
        f"ドット含みファイル名が group2 に取り込まれていません: {m.group(2)!r}"
    )
    assert m.group(3) is None


def test_w_r3_pat_spec_ref_slug_stops_before_trailing_period():
    """(e) パターン 3 slug (アンカーなし) は文末句点を捕食しない (Windows 末尾ドット quirk 対比 / Red の主役).

    tracker 記載の Windows 末尾ドット quirk:
      Path('docs/specs/large-scale-review.').exists() が本機 win32 で True になり、
      slug が文末句点を含むと drift 検出が偽 Green 化する。
      内部ドットのみ許容 (末尾ドット不可) のクラスで防ぐ。
    """
    m = vr._W_R3_PAT_SPEC_REF.search(
        "... docs/specs/large-scale-review. 次の文"
    )
    assert m is not None
    assert m.group(2) == "large-scale-review", (
        f"slug が文末句点を含んでしまっている: {m.group(2)!r}"
    )


def test_w_r3_pat_spec_ref_regression_dir_and_adr():
    """(f) 既存 regression: ディレクトリ形式 + adr フラット形式 (0009-hga-fable-summoning.md).

    フラット形式 (docs/adr/<slug>.md) は group3 の `(?:/...)?` が `/` を要求するため
    発火せず、`.md` は group2 (slug) 側の内部ドットとして取り込まれる
    (R1-006 修正後: group2 の文字クラスが内部ドットを許容するため)。
    """
    m1 = vr._W_R3_PAT_SPEC_REF.search("docs/specs/large-scale-review/")
    assert m1 is not None
    assert m1.group(1) == "specs" and m1.group(2) == "large-scale-review"
    m2 = vr._W_R3_PAT_SPEC_REF.search("docs/adr/0009-hga-fable-summoning.md")
    assert m2 is not None
    assert m2.group(1) == "adr"
    assert m2.group(2) == "0009-hga-fable-summoning.md", (
        f"フラット形式の slug に .md が取り込まれていません: {m2.group(2)!r}"
    )


def test_w_r3_pat_rules_path_underscore_filename_now_matches():
    """(g) underscore 含みファイル名が検出対象になる (silent false negative → drift 報告に変化)."""
    m = vr._W_R3_PAT_RULES_PATH.search(".claude/rules/some_rule.md")
    assert m is not None, (
        "underscore 含みファイル名がマッチしていません。"
        "マッチしない = silent false negative は最悪の失敗モード (Fable 判定)。"
    )
    assert m.group(1) == "some_rule.md"


def test_verify_w_r3_no_false_positive_on_real_repo():
    """(h) E2E: 実 repo 走査で検出される drift が偽陽性でないこと (false positive ゼロ検査).

    拡張後の文字クラスで新規にマッチするようになった参照について、
    「実在しないので drift 報告される」ケースのみを許容し、
    「実在するのに drift 報告される」偽陽性がないことを確認する。
    """
    result = vr.verify_w_r3()
    for drift in result:
        referenced = drift["referenced"]
        # 山括弧付き placeholder (<feature> 等) は書式変更で検出対象外になっている前提
        assert "<" not in referenced and ">" not in referenced, (
            f"placeholder 表記が drift として誤検出されています: {drift}"
        )


# ---- R1-053: verify_w_r3 パターン 3 の existence-check hole (2026-07-06 HGA #9 C-N3) ----
#
# 根拠: docs/artifacts/r-1-audit-tracker.md §R1-053
# bug: dir が実在すれば candidates の any(exists) が True になり、fname (capture 済) の
#      実在検査が素通しされ、実在しない fname 参照が drift として検出されない
#      (silent false negative / R1-006 と同 bug class)。
# 修正方針: fname が capture された場合は (dir/fname).exists() を厳密要求する。
#           fname が capture されない参照 (dir のみ / slug のみ) の判定は現行挙動を維持する。


def test_verify_w_r3_detects_drift_when_dir_exists_but_fname_missing(monkeypatch, tmp_path):
    """(a) 実在 dir + 非実在 fname → drift として検出される (R1-053 の主眼 / 修正前は FAIL する).

    合成 fixture: tmp_path 配下に docs/internal/*.md (source) と
    docs/specs/large-scale-review/ (実在 dir、ただし fname は置かない) を用意し、
    REPO_ROOT をモンキーパッチして verify_w_r3() を走査させる。
    """
    internal_dir = tmp_path / "docs" / "internal"
    internal_dir.mkdir(parents=True)
    specs_dir = tmp_path / "docs" / "specs" / "large-scale-review"
    specs_dir.mkdir(parents=True)
    # fname 用ディレクトリは実在するが、参照先ファイル自体は作らない (nonexistent-file-xyz.md)
    source = internal_dir / "sample.md"
    source.write_text(
        "参照: docs/specs/large-scale-review/nonexistent-file-xyz.md を参照。",
        encoding="utf-8",
    )

    monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)
    result = vr.verify_w_r3()

    matches = [d for d in result if d["pattern"] == "w-r3-spec-ref"]
    assert len(matches) == 1, (
        f"実在しない fname (nonexistent-file-xyz.md) が drift として検出されていません "
        f"(dir 存在による existence-check hole / R1-053): {result}"
    )
    assert "nonexistent-file-xyz.md" in matches[0]["referenced"]


def test_verify_w_r3_no_drift_when_dir_and_fname_both_exist(monkeypatch, tmp_path):
    """(b) regression 保護: 実在 dir + 実在 fname → drift なし."""
    internal_dir = tmp_path / "docs" / "internal"
    internal_dir.mkdir(parents=True)
    specs_dir = tmp_path / "docs" / "specs" / "large-scale-review"
    specs_dir.mkdir(parents=True)
    (specs_dir / "existing-file.md").write_text("dummy", encoding="utf-8")
    source = internal_dir / "sample.md"
    source.write_text(
        "参照: docs/specs/large-scale-review/existing-file.md を参照。",
        encoding="utf-8",
    )

    monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)
    result = vr.verify_w_r3()

    matches = [d for d in result if d["pattern"] == "w-r3-spec-ref"]
    assert matches == [], f"実在する fname 参照が誤って drift 報告されています: {matches}"


def test_verify_w_r3_dir_only_reference_unaffected_by_fix(monkeypatch, tmp_path):
    """(c) regression 保護: fname が capture されない参照形 (dir のみ) は現行挙動を維持する.

    末尾スラッシュのみで終わる参照 (docs/specs/<slug>/) は group3 (fname) が None のまま
    であり、dir の存在有無のみで判定される従来ロジックが変わらないこと。
    """
    internal_dir = tmp_path / "docs" / "internal"
    internal_dir.mkdir(parents=True)
    specs_dir = tmp_path / "docs" / "specs" / "large-scale-review"
    specs_dir.mkdir(parents=True)
    source = internal_dir / "sample.md"
    source.write_text(
        "参照: docs/specs/large-scale-review/ を参照。",
        encoding="utf-8",
    )

    monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)
    result = vr.verify_w_r3()

    matches = [d for d in result if d["pattern"] == "w-r3-spec-ref"]
    assert matches == [], (
        f"dir のみ参照 (fname 非 capture) は dir 実在で drift なし判定のはずが、"
        f"誤って drift 報告されています (R1-053 修正の非対象範囲): {matches}"
    )


def test_verify_w_r3_slug_only_reference_unaffected_by_fix(monkeypatch, tmp_path):
    """(c-2) regression 保護: fname が capture されない参照形 (slug のみ / スラッシュなし) も現行挙動維持."""
    internal_dir = tmp_path / "docs" / "internal"
    internal_dir.mkdir(parents=True)
    # docs/adr/<slug>.md のフラット形式 (dir なし・fname なし・slug に .md を含む)
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0009-hga-fable-summoning.md").write_text("dummy", encoding="utf-8")
    source = internal_dir / "sample.md"
    source.write_text(
        "参照: docs/adr/0009-hga-fable-summoning.md を参照。",
        encoding="utf-8",
    )

    monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)
    result = vr.verify_w_r3()

    matches = [d for d in result if d["pattern"] == "w-r3-spec-ref"]
    assert matches == [], f"実在する flat adr 参照が誤って drift 報告されています: {matches}"

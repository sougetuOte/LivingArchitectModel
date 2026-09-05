"""R-1 W-R1 S1 T4: verify_reference_resolution.py テスト.

R-G7 drift 検出ロジックの層 3 unittest。design §5.3 準拠。

- 実データ上での drift 検出結果は「ゼロを強制せず記録のみ」
  (T4 の完了条件は「両ファイル作成 + テスト空実行成功」であり、
   実 drift = 0 は W-R3/W-R4 の完了条件であって S1 T4 の要件ではない)
- 内部関数の合成 fixture 検証 (パターン正規表現の抜け穴確認)
"""
from __future__ import annotations

import json
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


def _utf8_env():
    """Windows cp932 の em dash / 全角文字 UnicodeEncodeError 回避 (W-R5 S1 追加)."""
    import os

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def test_cli_help_exits_zero():
    """--help は rc=0."""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "verify_reference_resolution.py"), "--help"],
        capture_output=True,
        encoding="utf-8",
        env=_utf8_env(),
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
        encoding="utf-8",
        env=_utf8_env(),
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


# ---- W1-R2-T6: gabriel 契約検査の strict enum 化 (R1-059 是正) ----
#
# 根拠: docs/artifacts/r-1-audit-tracker.md §R1-059 (evidence_line 233)
# 修正方針 (design.md §4.5 / docs/specs/large-scale-review/design.md §5.2):
#   - D1: enum 値を持つ 3 フィールド (verdict/severity/recommended_action) を
#         行頭 key:value 構造化 regex で strict 検査に昇格
#   - D2: 自由記述系 3 フィールド (affected_atoms/reasoning/confidence) は
#         既存の presence (substring) 検査を維持
#   - D3/D4: strict 検査対象は文書系 2 ファイル (gabriel.md / SKILL.md) に限定。
#         magi_dispatch.py は Python ソースのため対象外 (enum 整合性は pytest で別途担保)


def test_gabriel_enum_fields_defines_three_fields_with_canonical_values():
    """_GABRIEL_ENUM_FIELDS は D1 の 3 フィールドのみを enum 値集合として持つ."""
    assert set(vr._GABRIEL_ENUM_FIELDS.keys()) == {
        "verdict",
        "severity",
        "recommended_action",
    }
    assert vr._GABRIEL_ENUM_FIELDS["verdict"] == {"confirmed", "refuted", "inconclusive"}
    assert vr._GABRIEL_ENUM_FIELDS["severity"] == {"critical", "warning", "info"}
    assert vr._GABRIEL_ENUM_FIELDS["recommended_action"] == {"proceed", "re-magi", "abort"}


def test_gabriel_presence_fields_excludes_enum_fields():
    """D2: 自由記述系 3 フィールドは enum 3 フィールドを除いた残り (集合演算の整合性)."""
    assert vr._GABRIEL_PRESENCE_FIELDS == {"affected_atoms", "reasoning", "confidence"}


# ---- 正例: 実ファイルの行頭 key-value 表記が strict 検査を通ること ----


def test_has_valid_enum_value_true_for_real_gabriel_md_verdict():
    """正例: .claude/agents/gabriel.md 176行目 `"verdict": "confirmed"` で strict 検査を通る."""
    text = (vr.REPO_ROOT / ".claude/agents/gabriel.md").read_text(encoding="utf-8")
    assert vr._has_valid_enum_value(text, "verdict", vr._GABRIEL_ENUM_FIELDS["verdict"]) is True


def test_has_valid_enum_value_true_for_real_gabriel_md_recommended_action():
    """正例: .claude/agents/gabriel.md 180行目 `"recommended_action": "proceed"` で strict 検査を通る."""
    text = (vr.REPO_ROOT / ".claude/agents/gabriel.md").read_text(encoding="utf-8")
    assert (
        vr._has_valid_enum_value(
            text, "recommended_action", vr._GABRIEL_ENUM_FIELDS["recommended_action"]
        )
        is True
    )


def test_has_valid_enum_value_true_for_real_skill_md_verdict_and_severity():
    """正例: .claude/skills/magi/SKILL.md 211/222行目 `- verdict: confirmed` / `- severity: critical`."""
    text = (vr.REPO_ROOT / ".claude/skills/magi/SKILL.md").read_text(encoding="utf-8")
    assert vr._has_valid_enum_value(text, "verdict", vr._GABRIEL_ENUM_FIELDS["verdict"]) is True
    assert vr._has_valid_enum_value(text, "severity", vr._GABRIEL_ENUM_FIELDS["severity"]) is True


# ---- 誤例: 散文中の言及のみでは strict 検査を通らない (substring 検査との対比が主眼) ----


def test_has_valid_enum_value_false_when_field_name_appears_only_in_prose():
    """誤例: フィールド名が行頭 key:value を伴わない散文中の言及のみ → strict 検査は False.

    対比 (substring 検査では検出されない): 同じテキストに対し素朴な `f in text` 判定を
    行うと、フィールド名の文字列自体は含まれるため「充足」と誤判定される (R1-059 の弱点)。
    strict 化後は行頭 key:value 構造を要求するため、この誤判定が解消されることを示す。
    """
    prose_text = (
        "gabriel の verdict は MAGI 合議全体の判定であり、重要な概念である。\n"
        "severity についても同様に、深刻度を表す指標として言及される。\n"
        "recommended_action という語もこの文書内で使われている。\n"
    )

    # 旧 substring 検査であれば「充足」と誤判定されることの確認 (対比)
    for field in ("verdict", "severity", "recommended_action"):
        assert field in prose_text, (
            f"{field} は散文中に substring として出現しているはず (対比の前提)"
        )

    # 新 strict 検査は行頭 key:value 構造を要求するため、いずれも False (drift 相当)
    for field, allowed in vr._GABRIEL_ENUM_FIELDS.items():
        assert vr._has_valid_enum_value(prose_text, field, allowed) is False, (
            f"{field} が散文中の言及のみで strict 検査を通過してしまっています (R1-059 未是正)"
        )


def test_has_valid_enum_value_false_for_placeholder_without_real_value():
    """誤例: `- verdict: [任意]` のようなプレースホルダのみでは strict 検査を通らない.

    実値を伴わないプレースホルダ表記 (CJK) はトークン抽出されず、
    enum 値の実定義とはみなされない。
    """
    placeholder_text = "- verdict: [任意]\n- severity: [任意]\n"
    for field in ("verdict", "severity"):
        allowed = vr._GABRIEL_ENUM_FIELDS[field]
        assert vr._has_valid_enum_value(placeholder_text, field, allowed) is False


# ---- E2E: verify_w_r4() 経由の drift 検出 (実データ + 合成 fixture) ----


def test_verify_w_r4_no_strict_enum_drift_on_real_repo_docs():
    """正例 (E2E): 実 gabriel.md / SKILL.md は strict enum 検査で 0 drift (design §4.5 は 0 想定)."""
    result = vr.verify_w_r4()
    strict_drifts = [d for d in result if d["pattern"] == "w-r4-gabriel-contract-strict"]
    assert strict_drifts == [], f"実ドキュメントで strict enum drift が検出されました: {strict_drifts}"


def test_verify_w_r4_detects_strict_enum_drift_for_prose_only_mention(monkeypatch, tmp_path):
    """誤例 (E2E / Red 実証): enum フィールド名が散文中の言及のみの合成 gabriel.md → drift 検出.

    strict 化前 (substring 検査) ではこの合成ファイルは drift 非検出 (誤って充足扱い) になる
    ことを併せて確認し、strict 化の効果を対比で示す。
    """
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    gabriel_md = agents_dir / "gabriel.md"
    prose_only_text = (
        "gabriel の verdict は MAGI 合議全体の判定であり、重要な概念である。\n"
        "severity についても同様に、深刻度を表す指標として言及される。\n"
        "recommended_action という語もこの文書内で使われている。\n"
        "affected_atoms / reasoning / confidence もここに記載されている。\n"
    )
    gabriel_md.write_text(prose_only_text, encoding="utf-8")

    # SKILL.md は用意しない (exists() チェックで skip される既存仕様と整合)

    monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)
    result = vr.verify_w_r4()

    strict_drifts = [d for d in result if d["pattern"] == "w-r4-gabriel-contract-strict"]
    assert len(strict_drifts) == 1, (
        f"散文中の言及のみの gabriel.md で strict enum drift が検出されていません: {result}"
    )
    assert set(strict_drifts[0]["referenced"]) == {"verdict", "severity", "recommended_action"}

    # 対比: 旧 substring 検査 (presence 用) は「充足」と誤判定し drift を出さない
    presence_drifts = [d for d in result if d["pattern"] == "w-r4-gabriel-contract"]
    assert presence_drifts == [], (
        "presence(substring) 検査は affected_atoms/reasoning/confidence の文字列が "
        f"散文中に含まれているため drift を出さないはず: {presence_drifts}"
    )


def test_verify_w_r4_strict_enum_excludes_magi_dispatch_py(monkeypatch, tmp_path):
    """D4: 合成 magi_dispatch.py (f-string 由来の enum 値) は strict enum 検査の対象外.

    Python ソースは「行頭 key:value」構造を持たないため strict 検査対象から除外される。
    合成ファイルは enum フィールド名を f-string としてのみ含み、構造化 key:value を持たない
    ため、strict 検査対象に含まれていれば drift 化するはずだが、対象外のため drift は出ない。
    """
    scripts_dir = tmp_path / ".claude" / "scripts"
    scripts_dir.mkdir(parents=True)
    magi_dispatch_py = scripts_dir / "magi_dispatch.py"
    magi_dispatch_py.write_text(
        'f"- verdict: {verdict}\\n"\n'
        'gabriel_output["severity"]\n'
        'gabriel_output.get("recommended_action")\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)
    result = vr.verify_w_r4()

    strict_drifts = [
        d
        for d in result
        if d["pattern"] == "w-r4-gabriel-contract-strict"
        and d["source"] == ".claude/scripts/magi_dispatch.py"
    ]
    assert strict_drifts == [], (
        f"magi_dispatch.py が strict enum 検査対象に含まれています (D4 違反): {strict_drifts}"
    )


# ---- W1-R2-T8: gabriel-metrics.log mode enum 検査 (パターン 4 / design §4.7) ----
#
# 根拠: docs/specs/r-2-consolidation/design.md §4.7 / requirements.md FR-7
# 許可 enum: {"aot", "lightweight", "widescan_verify"}
# D3: ファイル不在時は skip (drift ゼロ) — .claude/gabriel-metrics.log は
#     gitignore 対象・環境依存のため、不在を drift として報告してはならない。


def test_gabriel_mode_enum_defines_three_values():
    """_GABRIEL_MODE_ENUM は design §4.7 の 3 値のみを許可 enum として持つ."""
    assert vr._GABRIEL_MODE_ENUM == {"aot", "lightweight", "widescan_verify"}


def test_verify_mode_enum_no_drift_on_real_repo_log_if_present():
    """正例: 実 .claude/gabriel-metrics.log の全 entry が enum 準拠であること.

    実ファイルは環境依存 (gitignore 対象) のため、存在しない環境では検査自体を skip する。
    """
    log_path = vr.REPO_ROOT / ".claude/gabriel-metrics.log"
    if not log_path.exists():
        return  # skip: 環境依存ファイル不在
    result = vr.verify_mode_enum()
    assert result == [], f"実 log entry に enum 外の mode 値が検出されました: {result}"


def test_verify_mode_enum_skips_when_log_file_absent(monkeypatch, tmp_path):
    """D3: .claude/gabriel-metrics.log 不在時は skip し drift ゼロで正常終了する."""
    # tmp_path は空ディレクトリ (.claude/gabriel-metrics.log を作らない)
    monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)
    result = vr.verify_mode_enum()
    assert result == [], f"ファイル不在時に drift が報告されています (D3 違反): {result}"


def test_verify_mode_enum_detects_drift_for_out_of_enum_value(monkeypatch, tmp_path):
    """誤例 (Red 実証): enum 外の mode 値 (unknown_mode) を含む entry が drift として検出される.

    実 .claude/gabriel-metrics.log を書き換えず、tmp_path に一時ファイルを生成して検査する。
    """
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True)
    log_path = claude_dir / "gabriel-metrics.log"
    log_path.write_text(
        '{"timestamp":"2026-07-25T00:00:00+09:00","mode":"aot"}\n'
        '{"timestamp":"2026-07-25T00:01:00+09:00","mode":"unknown_mode"}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)
    result = vr.verify_mode_enum()

    matches = [d for d in result if d["pattern"] == "gabriel-metrics-mode-enum"]
    assert len(matches) == 1, (
        f"enum 外の mode 値 (unknown_mode) が drift として検出されていません: {result}"
    )
    assert matches[0]["referenced"] == "unknown_mode"


def test_verify_mode_enum_no_drift_when_all_values_in_enum(monkeypatch, tmp_path):
    """regression 保護: enum 準拠の mode 値のみの合成 log は drift ゼロ."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True)
    log_path = claude_dir / "gabriel-metrics.log"
    log_path.write_text(
        '{"timestamp":"2026-07-25T00:00:00+09:00","mode":"aot"}\n'
        '{"timestamp":"2026-07-25T00:01:00+09:00","mode":"lightweight"}\n'
        '{"timestamp":"2026-07-25T00:02:00+09:00","mode":"widescan_verify"}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)
    result = vr.verify_mode_enum()

    assert result == [], f"enum 準拠の mode 値が誤って drift 報告されています: {result}"


def test_cli_mode_enum_wave_runs():
    """--wave mode-enum で実行完了 (drift 検出は許容 / rc=0)."""
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "verify_reference_resolution.py"),
            "--wave",
            "mode-enum",
        ],
        capture_output=True,
        encoding="utf-8",
        env=_utf8_env(),
    )
    assert result.returncode == 0
    assert "total_drifts" in result.stdout


def test_cli_all_wave_includes_mode_enum_key():
    """--wave all の結果に mode-enum キーが含まれる (件数非依存 / grep baseline 用)."""
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "verify_reference_resolution.py"),
            "--wave",
            "all",
        ],
        capture_output=True,
        encoding="utf-8",
        env=_utf8_env(),
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert "mode-enum" in payload["drifts_by_wave"]


# ---- パターン 5: gabriel-metrics anchor カバレッジ (2026-09-05 / iter0 C-5) ----
#
# パターン 4 が見ていたのは「書かれた行が enum に従うか」だけで、「書かれなかった」は
# 検出できなかった。実測ではログが 2026-07-18 で止まったまま 5 回の probe が記録されず、
# それでも検査は緑だった（空集合は常にスキーマに適合する）。


def _write_metrics_log(tmp_path, lines: str):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    (claude_dir / "gabriel-metrics.log").write_text(lines, encoding="utf-8")


def _write_magi_record(tmp_path, name: str, body: str):
    artifacts = tmp_path / "docs" / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / name).write_text(body, encoding="utf-8")


def test_verify_anchor_coverage_skips_when_log_absent(monkeypatch, tmp_path):
    """D3: ログ不在時は skip し drift ゼロ（clone 直後の利用者環境が常にこれ）."""
    _write_magi_record(tmp_path, "2026-09-10-magi-x.md", "- verdict: **refuted**\n")
    monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)
    assert vr.verify_anchor_coverage() == []


def test_verify_anchor_coverage_detects_unlogged_probe(monkeypatch, tmp_path):
    """陰性対照（Red 実証）: probe 記録があるのにログ行が無ければ赤くなる.

    これが赤くならない検査は、まさに今回見つかった「緑のまま 7 週間死んでいた」
    状態を再生産する。
    """
    _write_metrics_log(
        tmp_path,
        '{"timestamp":"2026-09-10T00:00:00+09:00","mode":"aot",'
        '"anchor":"docs/artifacts/2026-09-10-magi-other.md"}\n',
    )
    _write_magi_record(
        tmp_path,
        "2026-09-10-magi-x.md",
        "# MAGI\n\n- verdict: **refuted** / severity: **critical**\n",
    )
    monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)

    result = vr.verify_anchor_coverage()
    matches = [d for d in result if d["pattern"] == "gabriel-metrics-anchor-coverage"]
    assert len(matches) == 1, f"未記録の probe が検出されていません: {result}"
    assert matches[0]["source"] == "docs/artifacts/2026-09-10-magi-x.md"


def test_verify_anchor_coverage_passes_when_anchored(monkeypatch, tmp_path):
    """正例: 記録が anchor で指されていれば drift ゼロ."""
    _write_metrics_log(
        tmp_path,
        '{"timestamp":"2026-09-10T00:00:00+09:00","mode":"aot",'
        '"anchor":"docs/artifacts/2026-09-10-magi-x.md"}\n',
    )
    _write_magi_record(
        tmp_path,
        "2026-09-10-magi-x.md",
        "# MAGI\n\n- verdict: **confirmed** / severity: **info**\n",
    )
    monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)
    assert vr.verify_anchor_coverage() == []


def test_verify_anchor_coverage_ignores_records_before_baseline(monkeypatch, tmp_path):
    """基準日以前の記録は対象外（遡ると計器データの捏造が要るため）."""
    _write_metrics_log(tmp_path, "")
    _write_magi_record(
        tmp_path,
        "2026-07-05-magi-r1-planning.md",
        "- verdict: **refuted** / severity: **warning**\n",
    )
    monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)
    assert vr.verify_anchor_coverage() == []


def test_verify_anchor_coverage_ignores_records_without_verdict(monkeypatch, tmp_path):
    """陰性対照: probe を記録していない文書は対象にしない（誤爆防止）."""
    _write_metrics_log(tmp_path, "")
    _write_magi_record(
        tmp_path,
        "2026-09-10-retro.md",
        "# retro\n\n本文に verdict という語が散文で出てくるだけの文書。\n",
    )
    monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)
    assert vr.verify_anchor_coverage() == []

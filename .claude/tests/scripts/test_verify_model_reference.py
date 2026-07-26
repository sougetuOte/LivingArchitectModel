"""M-1 W2-M1-T4: verify_model_reference.py テスト.

design.md §6.2（3 分岐擬似コード）/ requirements.md FR-12, NFR-4, NFR-5 準拠。
tasks.md W2-M1-T4 の完了条件（10 項目）を検証する。

2026-07-26 追加: (a) cp932 コンソールでの stdout UnicodeEncodeError 回避、
(b) `_is_layer_assignment` の精度改善（false positive 削減）の回帰テスト。
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import verify_model_reference  # noqa: E402
from verify_model_reference import (  # noqa: E402
    _MODEL_NAME_PAT,
    _is_layer_assignment,
    _is_time_stamped_source,
    classify,
    main,
    scan,
)

SCRIPT_PATH = SCRIPTS_DIR / "verify_model_reference.py"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---- 検出パターン ----


def test_pattern_matches_versioned_model_name_with_space():
    assert _MODEL_NAME_PAT.search("Opus 5")


def test_pattern_matches_versioned_model_name_with_hyphen():
    assert _MODEL_NAME_PAT.search("Sonnet-4.6")


def test_pattern_matches_claude_api_id():
    assert _MODEL_NAME_PAT.search("claude-opus-5-20260101")


def test_pattern_is_case_insensitive():
    assert _MODEL_NAME_PAT.search("opus 5")


def test_pattern_does_not_match_unrelated_word_with_shared_prefix():
    assert not _MODEL_NAME_PAT.search("opusculent art collection")


def test_pattern_matches_bare_parenthetical_mention():
    """FR-12 受け入れ条件 2 の誤例: バージョン数字を伴わない括弧書き言及も検出する.

    design.md §6.2 擬似コードの正規表現（バージョン数字必須）だけでは
    `.claude/agents/gabriel.md` の「同一モデル（Opus）の別ペルソナ」を検出できないため、
    括弧で囲まれた無版数言及の検出を追加している（実装ノート参照）。
    """
    assert _MODEL_NAME_PAT.search("同一モデル（Opus）の別ペルソナ")


def test_pattern_does_not_match_fable_alembic_compound_noun():
    """「Fable-Alembic」はモデル名の言及ではなくプロジェクト名の複合語のため誤検出しない."""
    assert not _MODEL_NAME_PAT.search("D:/work7/Fable-Alembic/knowledge/")


# ---- classify() 3 分岐（判定順序: layer_assignment → point_in_time_record → 既定）----


def test_classify_layer_assignment_table_row():
    assert classify("| L1 | Opus 5 |", "CLAUDE.md") == "layer_assignment"


def test_classify_layer_assignment_inline_equals():
    assert classify("L1=Opus / L2=Sonnet / L3=Haiku", "CLAUDE.md") == "layer_assignment"


def test_classify_layer_assignment_japanese_tantou():
    assert classify("L3 の担当は Haiku 4.5", "CLAUDE.md") == "layer_assignment"


def test_classify_point_in_time_record_by_artifacts_path():
    assert classify("Opus 5 を使用した", "docs/artifacts/retro-2026.md") == "point_in_time_record"


def test_classify_point_in_time_record_by_adr_path():
    assert classify("Opus 5 を採用した", "docs/adr/0011-x.md") == "point_in_time_record"


def test_classify_point_in_time_record_by_log_filename():
    assert classify("Opus 5 実測", "some/path/foo.log") == "point_in_time_record"


def test_classify_point_in_time_record_by_session_state():
    assert classify("Opus 5", "SESSION_STATE.md") == "point_in_time_record"


def test_classify_default_design_property_description():
    assert (
        classify("同一モデル（Opus）の別ペルソナであり盲点が相関する", ".claude/agents/gabriel.md")
        == "design_property_description"
    )


def test_classify_order_layer_assignment_beats_time_stamped_path():
    """FR-12 受け入れ条件 3: 例外登録はファイルパス単位ではなく記述の性質単位.

    docs/artifacts/ 配下であっても、層への割当表現であれば layer_assignment を優先する
    （point_in_time_record ではない）。判定順序 1→2 がこの MUST の実体。
    """
    assert classify("| L1 | Opus 5 |", "docs/artifacts/some-retro.md") == "layer_assignment"


# ---- _is_layer_assignment / _is_time_stamped_source 単体 ----


def test_is_layer_assignment_false_without_layer_token():
    assert _is_layer_assignment("Opus 5 は速い") is False


def test_is_layer_assignment_false_without_assignment_symbol():
    assert _is_layer_assignment("L1 について Opus 5 が使われている") is False


# ---- (b) _is_layer_assignment 精度改善 (2026-07-26 / false positive 削減) ----


def test_is_layer_assignment_false_for_inline_code_span_colon():
    """inline code span 内の `:` を割当指標として誤検出しないこと."""
    text = (
        "Fable 5 の judgment heuristics を継承する "
        "`D:\\work7\\Fable-Alembic\\` を、レベル **L3** で参照する。"
    )
    assert _is_layer_assignment(text) is False


def test_is_layer_assignment_false_for_table_row_same_cell_fable_l1():
    """層トークンとモデル名が同一セル内にしか無い表行は False（別セルではない）."""
    text = "| 2026-07-02 | Living Architect (Fable 5 L1) | 追補 |"
    assert _is_layer_assignment(text) is False


def test_is_layer_assignment_false_for_table_row_same_cell_opus_l1():
    text = "| **2** | かつ Opus 5 の結論に L1 自身が確信を持てない | 事後条件 |"
    assert _is_layer_assignment(text) is False


def test_is_layer_assignment_true_for_bracket_form():
    """`L2 (Sonnet)` 形式（層トークン直後の括弧書きモデル名）は True."""
    text = "**対象**: 3.5 層委譲モデル の L2 (Sonnet) / L3 (Haiku) 委譲プロンプト全般"
    assert _is_layer_assignment(text) is True


def test_is_layer_assignment_true_for_hga_equals_fable():
    assert _is_layer_assignment("§1（HGA = Fable 5 の割当）") is True


def test_is_layer_assignment_true_regression_table_row():
    assert _is_layer_assignment("| L1 | Opus 5 |") is True


def test_is_layer_assignment_true_regression_inline_equals():
    assert _is_layer_assignment("L1=Opus / L2=Sonnet / L3=Haiku") is True


def test_is_layer_assignment_true_regression_japanese_tantou():
    assert _is_layer_assignment("L3 の担当は Haiku 4.5") is True


def test_is_time_stamped_source_true_for_artifacts():
    assert _is_time_stamped_source("docs/artifacts/x.md") is True


def test_is_time_stamped_source_true_for_adr():
    assert _is_time_stamped_source("docs/adr/0001-x.md") is True


def test_is_time_stamped_source_true_for_log_suffix():
    assert _is_time_stamped_source("foo/bar-log.md") is True


def test_is_time_stamped_source_false_for_rules():
    assert _is_time_stamped_source(".claude/rules/foo.md") is False


# ---- scan() 統合テスト（tmp_path で合成リポジトリ）----


def test_scan_excludes_model_roster_md(tmp_path):
    _write(tmp_path / ".claude/rules/model-roster.md", "| L1 | Opus 5 |\n")
    _write(tmp_path / "CLAUDE.md", "普通の文書。\n")
    result = scan(root=tmp_path)
    sources = {d["source"] for d in result["drifts"]}
    assert ".claude/rules/model-roster.md" not in sources


def test_scan_reports_layer_assignment_drift(tmp_path):
    _write(tmp_path / "CLAUDE.md", "| L1 | Opus 5 |\n")
    result = scan(root=tmp_path)
    assert result["total_drifts"] == 1
    assert result["drifts"][0]["classification"] == "layer_assignment"
    assert result["drifts"][0]["referenced"] == "Opus 5"


def test_scan_reports_design_property_description_drift(tmp_path):
    _write(tmp_path / ".claude/agents/foo.md", "同一モデル（Opus）の別ペルソナ\n")
    result = scan(root=tmp_path)
    assert result["total_drifts"] == 1
    assert result["drifts"][0]["classification"] == "design_property_description"
    assert result["drifts"][0]["referenced"] == "Opus"


def test_scan_counts_point_in_time_record_as_exempt_not_drift(tmp_path):
    _write(tmp_path / "docs/adr/0001-x.md", "Opus 5 を採用した。\n")
    result = scan(root=tmp_path)
    assert result["total_drifts"] == 0
    assert result["exempt_count"] == 1
    assert result["drifts"] == []


def test_scan_skips_frontmatter_block(tmp_path):
    content = "---\nmodel: sonnet\n---\n本文には Opus 5 が出てくる。\n"
    _write(tmp_path / ".claude/agents/foo.md", content)
    result = scan(root=tmp_path)
    assert result["total_drifts"] == 1
    assert "line 4" in result["drifts"][0]["match"]


def test_scan_line_numbers_are_1_indexed_and_reference_full_line(tmp_path):
    _write(tmp_path / "CLAUDE.md", "1 行目\n2 行目\n| L1 | Opus 5 |\n")
    result = scan(root=tmp_path)
    assert result["drifts"][0]["match"].startswith("line 3:")


# ---- 出力形式（design.md §6.2 JSON 形状 準拠）----


def test_scan_output_has_required_keys(tmp_path):
    _write(tmp_path / "CLAUDE.md", "| L1 | Opus 5 |\n")
    result = scan(root=tmp_path)
    assert set(result.keys()) == {"total_drifts", "drifts", "exempt_count"}
    for entry in result["drifts"]:
        assert set(entry.keys()) == {"pattern", "source", "referenced", "match", "classification"}
        assert entry["pattern"] == "model-name-literal"


def test_total_drifts_equals_len_drifts(tmp_path):
    _write(tmp_path / "CLAUDE.md", "| L1 | Opus 5 |\n| L2 | Sonnet 5 |\n")
    result = scan(root=tmp_path)
    assert result["total_drifts"] == len(result["drifts"])


# ---- CLI (main) ----


def test_main_output_writes_json_file(tmp_path):
    out = tmp_path / "result.json"
    rc = main(["--output", str(out)])
    assert rc == 0
    assert out.is_file()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "total_drifts" in data
    assert "exempt_count" in data


def test_main_exit_zero_by_default():
    rc = main([])
    assert rc == 0


def test_main_exit_nonzero_on_drift_flag_does_not_raise():
    rc = main(["--exit-nonzero-on-drift"])
    assert rc in (0, 1)


# ---- (a) cp932 コンソールでの stdout UnicodeEncodeError 回避 (2026-07-26) ----


class _StdoutWithoutReconfigure:
    """`reconfigure` 属性を持たない stdout 代替（TextIOWrapper 以外の代替実装を模す）."""

    def __init__(self):
        self._chunks = []

    def write(self, s):
        self._chunks.append(s)
        return len(s)

    def flush(self):
        pass


def test_main_stdout_json_survives_cp932_console_encoding(monkeypatch):
    """--output 無しの stdout 経路が cp932 コンソール上で UnicodeEncodeError を起こさないこと.

    cp932 の文字集合に含まれない文字（絵文字）を drift の match フィールドに含む
    payload を返す scan() をスタブし、sys.stdout を cp932 encoding の TextIOWrapper に
    差し替えて main() が例外なく完走することを検証する。
    """
    fake_payload = {
        "total_drifts": 1,
        "drifts": [
            {
                "pattern": "model-name-literal",
                "source": "x.md",
                "referenced": "Opus 5",
                "match": "line 1: \U0001f600 Opus 5 の説明",
                "classification": "design_property_description",
            }
        ],
        "exempt_count": 0,
    }
    monkeypatch.setattr(verify_model_reference, "scan", lambda *a, **k: fake_payload)

    buffer = io.BytesIO()
    fake_stdout = io.TextIOWrapper(buffer, encoding="cp932", errors="strict")
    monkeypatch.setattr(sys, "stdout", fake_stdout)

    rc = main([])

    assert rc == 0


def test_main_stdout_json_does_not_require_reconfigure_attribute(monkeypatch):
    """sys.stdout に `reconfigure` 属性が無くても AttributeError を出さないこと."""
    fake_stdout = _StdoutWithoutReconfigure()
    assert not hasattr(fake_stdout, "reconfigure")
    monkeypatch.setattr(sys, "stdout", fake_stdout)

    rc = main([])

    assert rc == 0


# ---- 実リポジトリに対する誤例実測（FR-12 受け入れ条件 2 / tasks.md 完了条件）----


def test_gabriel_md_bare_opus_mention_classified_as_design_property_description():
    result = scan()
    gabriel_drifts = [d for d in result["drifts"] if d["source"] == ".claude/agents/gabriel.md"]
    assert gabriel_drifts, "gabriel.md 内のモデル名言及 (Opus) が検出されていない"
    assert any(
        d["classification"] == "design_property_description" and d["referenced"] == "Opus"
        for d in gabriel_drifts
    )


def test_model_roster_md_excluded_in_real_repo_scan():
    result = scan()
    sources = {d["source"] for d in result["drifts"]}
    assert ".claude/rules/model-roster.md" not in sources


# ---- NFR-4: Python 3.8 互換性 ----


def test_nfr4_future_annotations_import_present():
    src = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "from __future__ import annotations" in src


def test_nfr4_no_py310_only_syntax():
    src = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "except*" not in src
    assert ".removesuffix(" not in src
    assert not re.search(r"^\s*match\s+\S.*:\s*$", src, re.MULTILINE)


# ---- NFR-5: subprocess を使う場合は encoding 指定必須（本スクリプトは subprocess 不使用）----


def test_nfr5_no_subprocess_run_without_encoding():
    src = SCRIPT_PATH.read_text(encoding="utf-8")
    if "subprocess.run(" in src:
        assert 'encoding="utf-8"' in src and 'errors="replace"' in src


# ---- ADR-0011 決定 2 の機構化（2026-07-26 / 誕生ゲート台帳 §C 機構 #4）----


def test_no_layer_assignment_drift_in_real_repo():
    """層 → モデルの束縛は `model-roster.md` 1 枚のみ（`layer_assignment` は 0 件）。

    `design_property_description`（設計上の性質記述）は許容カテゴリなので 0 を求めない。
    時点記録（retro / 日付つき観測）は `point_in_time_record` として exempt される。

    落ちた場合の直し方: 層名が既にある箇所のモデル名を落とす（`L2 (Sonnet)` → `L2`）。
    その層にどのモデルが割り当たっているかは `model-roster.md` §1 が唯一の正本である。
    """
    result = scan()
    offenders = [
        "{0}: {1}".format(d["source"], d["match"])
        for d in result["drifts"]
        if d["classification"] == "layer_assignment"
    ]
    assert not offenders, (
        "層 → モデルの束縛が roster 外に {0} 件ある（ADR-0011 決定 2 / "
        "model-roster.md §0）:\n  {1}".format(len(offenders), "\n  ".join(offenders))
    )

"""test_parser_generation_tracking.py - parser 世代追随 pytest 群（R-2 W1-R2-T4）.

対応:
    - .claude/rules/auto-generated/rule-002.md（機構実体）
    - docs/specs/r-2-consolidation/design.md §4.3
    - docs/specs/r-2-consolidation/tasks.md W1-R2-T4
    - docs/artifacts/r-1-audit-tracker.md R1-054 / R1-055 / R1-056 / R1-057 / R1-058 / R1-061

目的:
    Milestone/Task 命名体系の進化に parser regex が追随できているかを機構的に検証する
    (rule-001.md の SessionStateParser fallback と同型の "parser drift" 予防)。

構成:
    (a) GitHistoryParser の Task ID 抽出 regex (`_TASK_PATTERN`) が現行世代記法を
        捕捉することの回帰保護 + 拡張前 (旧) regex がそれを捕捉できないことの誤例実証。
    (b) verify_reference_resolution.py 系 (R1-055/056/057/058) および
        dashboard/builder.py (R1-054) の現状挙動を固定する characterization test。
        R1-054〜058 は 2026-07-15 W-R5 S1 で deferred 裁定済みのため、本テスト群は
        「直す」のではなく「意図しない挙動変化を検出可能にする」ことが目的。

注記 (R1-054 の所在について):
    design.md §4.3 は R1-054/055 系を一括して「verify_reference_resolution.py 系」と
    表記するが、r-1-audit-tracker.md の実測では R1-054 の evidence_file は
    `.claude/scripts/dashboard/builder.py` (`_resolve_task_status`) であり、
    verify_reference_resolution.py ではない。本ファイルでは実 evidence_file に
    従って builder.py から直接 import する。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from dashboard.builder import DashboardBuilder  # noqa: E402
from dashboard.models import DashboardData  # noqa: E402
from dashboard.parsers.git_history import _TASK_PATTERN  # noqa: E402

import verify_reference_resolution as vr  # noqa: E402


# ============================================================
# (a) GitHistoryParser Task ID regex
#     現行世代記法の回帰保護 + 拡張前 (旧) regex の誤例実証
# ============================================================

# R1-061 拡張前 (2026-07-10 commit 6b836e5 以前) の旧 _TASK_PATTERN。
# 根拠: `git show 61d6e27:.claude/scripts/dashboard/parsers/git_history.py` L27 実測。
_OLD_TASK_PATTERN = re.compile(r"\b(W\d+-(?:[A-Z][0-9]+-)?T\d+[a-z]?)\b")


class TestCurrentGenerationTaskIdRegex:
    """現行 `_TASK_PATTERN` が現行世代 Milestone/Task 記法を捕捉すること (回帰保護).

    R1-061 は 2026-07-10 commit 6b836e5 で regex 汎化により恒久解済み
    (rule-001 の `B-\\d+` -> `[A-Z]-\\d+` 拡張と同型パターン)。
    本テストはその hotfix 済み挙動を pin し、将来の regex 変更で
    再度捕捉漏れが起きないことを保護する。
    """

    @pytest.mark.parametrize(
        "task_id",
        [
            "W-R1-S1-T6",
            "W1-R2-T4",
            "W1-R2-T4a",
            "W-R2-S2-T3",
            "W7-B4-T9",
        ],
    )
    def test_matches_current_generation_notation(self, task_id):
        m = _TASK_PATTERN.fullmatch(task_id)
        assert m is not None, f"現行世代記法が捕捉できていない: {task_id!r}"
        assert m.group(1) == task_id

    def test_matches_real_git_log_wc_notation(self):
        """実 git log (直近 100 コミット) に実在する `WC-B5-T1` 記法
        (Milestone 短縮形) が現行 regex で捕捉できること
        (2026-07-25 baseline 実測: git log --oneline -100 中 1 件ヒット確認済み)。
        """
        m = _TASK_PATTERN.search("Wave C Stage 1 Spike 完了 - WC-B5-T1/T2 Green")
        assert m is not None
        assert m.group(1) == "WC-B5-T1"


class TestOldTaskIdRegexFailsOnCurrentGenerationNotation:
    """誤例 (Red 実証): 拡張前 (2026-07-10 以前) の旧 `_TASK_PATTERN` は
    R-1 期以降のハイフン Milestone 記法を捕捉できない。旧 regex をリテラルで
    テスト内に保持し、「規則 (rule-002) を守らないとテストが落ちる」ことを
    機構的に担保する。
    """

    @pytest.mark.parametrize(
        "task_id",
        [
            "W-R1-S1-T6",  # 実際に R1-061 で drift が発生した記法 (2026-07-10 実測)
            "W-S3-T7",  # design.md §4.3 / tasks.md 記載の架空次世代記法の例
        ],
    )
    def test_old_pattern_does_not_match(self, task_id):
        m = _OLD_TASK_PATTERN.fullmatch(task_id)
        assert m is None, (
            f"旧 regex が現行世代記法 {task_id!r} を捕捉してしまっている "
            f"(誤例が誤例として機能していない)"
        )

    def test_old_pattern_still_matches_legacy_notation(self):
        """対比: 旧 regex は旧世代記法 (`W2-B5-T7`) は問題なく捕捉できていた
        (regex 自体が壊れているのではなく、Milestone 命名体系の進化に
        追随できていなかっただけであることの確認)。
        """
        m = _OLD_TASK_PATTERN.fullmatch("W2-B5-T7")
        assert m is not None
        assert m.group(1) == "W2-B5-T7"


# ============================================================
# (b) verify_reference_resolution.py 系 + builder.py characterization tests
#     R1-054〜058 は 2026-07-15 W-R5 S1 で deferred 裁定済み。
#     本テスト群は「直す」のではなく「現状の挙動を pin する」ことが目的。
# ============================================================


def _make_builder(completed=None, in_progress=None, blocked=None) -> DashboardBuilder:
    """R1-054 pin test 専用の最小 DashboardBuilder 構築ヘルパー。

    `.claude/tests/dashboard/test_r1_001_task_status_token_boundary.py` の
    同名ヘルパーと同型だが、本ファイルはそれに依存せず自己完結させる。
    """
    data = DashboardData(
        milestones=[],
        waves=[],
        tasks=[],
        current_phase="BUILDING",
        completed=completed or [],
        in_progress=in_progress or [],
        blocked=blocked or [],
        parser_errors=[],
    )
    return DashboardBuilder(data)


class TestR1054UnderscoreBoundaryCharacterization:
    """R1-054 (HGA #9 verdict C-N1): `_resolve_task_status`
    (.claude/scripts/dashboard/builder.py) の lookbehind/lookahead は
    underscore を境界文字として扱わない。

    status=deferred (2026-07-15 W-R5 S1)。本テストは
    「未文書化の false-positive surface」という現状挙動を pin する (修正はしない)。
    """

    def test_task_id_embedded_in_snake_case_token_is_false_positive_matched(self):
        """`W1-B5-T1_note: done` のような snake_case 埋め込みでも
        `_resolve_task_status("W1-B5-T1", ...)` は completed と誤判定する
        (underscore が境界文字扱いされないため / HGA #9 probe と同一挙動)。
        """
        builder = _make_builder(completed=["W1-B5-T1_note: done"])
        result = builder._resolve_task_status("W1-B5-T1", "not-started")
        assert result == "completed", (
            "R1-054 の現状挙動 (underscore 非境界扱いによる false positive) が"
            f"変化している。現状は 'completed' を返すはずが {result!r} だった。"
        )


class TestR1055Win32CaseInsensitivityCharacterization:
    """R1-055 (HGA #9 verdict C-N4): win32 (NTFS 既定) では `Path.exists()` が
    大文字小文字を区別しないため、大文字化された参照 (`PHASE-RULES.md` 等) も
    「実在する」と誤判定される portability residual。

    status=deferred (2026-07-15 W-R5 S1 / live corpus 0 実例)。本テストは
    win32 環境限定で現状挙動を pin する (POSIX 環境では skip する)。
    """

    @pytest.mark.skipif(
        sys.platform != "win32",
        reason="R1-055 は win32 (NTFS) 固有の case-insensitive 挙動",
    )
    def test_uppercase_filename_reference_resolves_as_existing_on_win32(self):
        p = vr.REPO_ROOT / ".claude/rules/PHASE-RULES.md"
        assert p.exists(), (
            "R1-055 の現状挙動 (win32 case-insensitive による偽 Green) が"
            "変化している。実ファイルは phase-rules.md (小文字) のはず。"
        )


class TestR1056MultiLevelReferenceDegradationCharacterization:
    r"""R1-056 (HGA #10 verdict 軸 B): `_W_R3_PAT_SPEC_REF` の group3
    (`[A-Za-z0-9._-]+\.md`) は `/` を含まないため、多階層参照
    (`docs/specs/<slug>/<sub>/<file>.md`) では fname を捕捉できず None に退化する。

    status=deferred (2026-07-15 W-R5 S1 / live corpus 0 実例)。
    """

    def test_multi_level_reference_fname_group_degrades_to_none(self):
        m = vr._W_R3_PAT_SPEC_REF.search(
            "docs/specs/large-scale-review/research/foo-notes.md"
        )
        assert m is not None
        assert m.group(2) == "large-scale-review"
        assert m.group(3) is None, (
            "R1-056 の現状挙動 (多階層参照が fname 非捕捉に退化する) が変化している。"
        )

    def test_multi_level_nonexistent_fname_is_not_flagged_as_drift(
        self, monkeypatch, tmp_path
    ):
        """実在しない多階層 fname (`research/nonexistent-notes.md`) を参照しても、
        中間ディレクトリ (`large-scale-review/`) さえ実在すれば drift として
        検出されない (silent false negative の現状を pin する)。
        """
        internal_dir = tmp_path / "docs" / "internal"
        internal_dir.mkdir(parents=True)
        specs_dir = tmp_path / "docs" / "specs" / "large-scale-review"
        specs_dir.mkdir(parents=True)
        source = internal_dir / "sample.md"
        source.write_text(
            "参照: docs/specs/large-scale-review/research/nonexistent-notes.md を参照。",
            encoding="utf-8",
        )

        monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)
        result = vr.verify_w_r3()

        matches = [d for d in result if d["pattern"] == "w-r3-spec-ref"]
        assert matches == [], (
            "R1-056 の現状挙動 (多階層 fname 非実在が drift として検出されない) が"
            f"変化している (matches={matches})。"
        )


class TestR1057RegexDegradationThreeAspectsCharacterization:
    """R1-057 (HGA #10 verdict 軸 B/C 付随): パターン 3 regex の非捕捉退化 3 態様
    (非 .md 拡張子 / 大文字 .MD / file-as-dir 擬似通過)。

    status=deferred (2026-07-15 W-R5 S1)。
    """

    def test_non_md_extension_fname_group_degrades_to_none(self):
        """(i) 非 .md 拡張子 (`.png` 等) は fname 非捕捉で dir-only 判定に退化する。"""
        m = vr._W_R3_PAT_SPEC_REF.search("docs/specs/large-scale-review/image.png")
        assert m is not None
        assert m.group(3) is None

    def test_uppercase_md_extension_fname_group_degrades_to_none(self):
        """(ii) 大文字拡張子 (`.MD`) は IGNORECASE 未指定のため fname 非捕捉に退化する。"""
        m = vr._W_R3_PAT_SPEC_REF.search("docs/specs/large-scale-review/DESIGN.MD")
        assert m is not None
        assert m.group(3) is None

    def test_flat_file_with_trailing_slash_pseudo_passes_as_existing_dir(
        self, monkeypatch, tmp_path
    ):
        """(iii) `docs/specs/foo.md/` (flat ファイル + trailing slash typo) が、
        else 分岐の candidate 1 (`.exists()` はファイルにも True を返す) により
        「dir 実在」扱いで drift 報告されずに素通りする現状挙動を pin する。
        """
        internal_dir = tmp_path / "docs" / "internal"
        internal_dir.mkdir(parents=True)
        specs_dir = tmp_path / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "foo.md").write_text("dummy", encoding="utf-8")
        source = internal_dir / "sample.md"
        source.write_text("参照: docs/specs/foo.md/ を参照。", encoding="utf-8")

        monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)
        result = vr.verify_w_r3()

        matches = [d for d in result if d["pattern"] == "w-r3-spec-ref"]
        assert matches == [], (
            f"R1-057(iii) の現状挙動 (file-as-dir 擬似通過) が変化している (matches={matches})。"
        )


class TestR1058ScopeLimitedToDocsInternalCharacterization:
    """R1-058 (HGA #10 verdict meta): パターン 3 の走査対象は `docs/internal/*.md` のみ。
    `.claude/rules/*.md` 内の spec 参照は存在検査の圏外 (design §5.1 の scope 定義通り)。

    status=deferred (2026-07-15 W-R5 S1 / scope 拡張要否は spec_ambiguity)。
    """

    def test_rules_directory_spec_reference_is_not_scanned_by_pattern3(
        self, monkeypatch, tmp_path
    ):
        (tmp_path / "docs" / "internal").mkdir(parents=True)
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "some-rule.md").write_text(
            "参照: docs/specs/nonexistent-xyz-issue/ を参照。",
            encoding="utf-8",
        )

        monkeypatch.setattr(vr, "REPO_ROOT", tmp_path)
        result = vr.verify_w_r3()

        matches = [d for d in result if d["pattern"] == "w-r3-spec-ref"]
        assert matches == [], (
            "R1-058 の現状挙動 (.claude/rules/ 内の spec 参照はパターン 3 の走査対象外) "
            f"が変化している (matches={matches})。"
        )

"""
test_pre_tool_use.py - pre-tool-use.py の TDD テスト

W2-T2: Red フェーズ（テストファースト）
対応仕様: docs/design/hooks-python-migration-design.md H1（pre-tool-use）
"""
import json
from pathlib import Path

import pytest

# テスト対象フックのパス
HOOK_PATH = Path(__file__).resolve().parent.parent / "pre-tool-use.py"


def _write_input(tool_name: str, file_path: str) -> dict:
    """Edit/Write 用の tool_input を組み立てる。"""
    if tool_name == "Write":
        return {"file_path": file_path, "content": "x"}
    return {"file_path": file_path, "old_string": "old", "new_string": "new"}


def write_phase(project_root: Path, phase: str) -> None:
    """current-phase.md を作成して指定フェーズに設定する。"""
    phase_file = project_root / ".claude" / "current-phase.md"
    phase_file.parent.mkdir(parents=True, exist_ok=True)
    phase_file.write_text(f"**{phase}**\n", encoding="utf-8")


class TestPreToolUse:
    """pre-tool-use.py の権限等級判定テスト"""

    def test_read_tool_pg_allow(self, hook_runner):
        """Read ツールは PG 級として許可される（exit 0、stdout 空）"""
        input_json = {
            "tool_name": "Read",
            "tool_input": {
                "file_path": "src/main.py",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        # PG 許可: stdout は空（hookSpecificOutput を出力しない）
        assert result.stdout.strip() == "", f"PG 許可時は stdout が空であるべき。got: {result.stdout!r}"

    def test_edit_specs_pm_ask(self, hook_runner):
        """Edit で docs/specs/*.md を編集すると PM ask が返る"""
        input_json = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "docs/specs/test.md",
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, "PM ask 時は stdout に JSON が出力されるべき"
        data = json.loads(stdout)
        assert "hookSpecificOutput" in data
        hook_output = data["hookSpecificOutput"]
        assert hook_output["permissionDecision"] == "ask"
        assert isinstance(hook_output["permissionDecisionReason"], str)
        assert len(hook_output["permissionDecisionReason"]) > 0

    def test_edit_rules_auto_generated_pm_ask(self, hook_runner):
        """Edit で .claude/rules/auto-generated/ 配下のファイルを編集すると PM ask が返る"""
        input_json = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": ".claude/rules/auto-generated/rule.md",
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, "PM ask 時は stdout に JSON が出力されるべき"
        data = json.loads(stdout)
        assert "hookSpecificOutput" in data
        hook_output = data["hookSpecificOutput"]
        assert hook_output["permissionDecision"] == "ask"
        assert isinstance(hook_output["permissionDecisionReason"], str)
        assert len(hook_output["permissionDecisionReason"]) > 0

    def test_absolute_path_normalization(self, hook_runner, project_root):
        """絶対パスが project_root からの相対パスに正規化されて SE 判定される"""
        abs_path = str(project_root / "src" / "main.py")
        input_json = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": abs_path,
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        # SE 級: stdout は空（ask/deny を出力しない）
        assert result.stdout.strip() == "", f"SE 許可時は stdout が空であるべき。got: {result.stdout!r}"

    def test_edit_src_se_allow(self, hook_runner):
        """Edit で src/main.py を編集すると SE 許可（exit 0、stdout 空）"""
        input_json = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "src/main.py",
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        # SE 許可: stdout は空
        assert result.stdout.strip() == "", f"SE 許可時は stdout が空であるべき。got: {result.stdout!r}"

    def test_log_truncation(self, hook_runner, project_root):
        """ログのターゲットフィールドが 100 文字でトランケートされる"""
        # 150 文字のパスを生成
        long_path = "src/" + "a" * 150 + ".py"
        input_json = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": long_path,
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        # ログファイルを確認
        log_file = project_root / ".claude" / "logs" / "permission.log"
        assert log_file.exists(), "ログファイルが作成されるべき"
        log_content = log_file.read_text(encoding="utf-8")
        # ログの各フィールドを確認: timestamp, level, tool_name, target(100文字)
        lines = [line for line in log_content.strip().split("\n") if "Edit" in line and "aaa" in line]
        assert lines, "Edit のログが記録されるべき"
        last_line = lines[-1]
        fields = last_line.split("\t")
        # target フィールドは 4番目（0-indexed: 3）
        assert len(fields) >= 4, f"ログフィールドが4つ以上あるべき。got: {len(fields)} fields"
        target = fields[3]
        # trunc 後は 100 文字以内
        assert len(target) <= 100, f"target が 100 文字を超えている: {len(target)}"

    def test_log_sanitizes_control_and_bidi_chars(self, hook_runner, project_root):
        """ログ target の Unicode 双方向制御文字（Cf）と C0 制御文字（Cc）が
        半角スペースへ置換される（Trojan Source 型パス偽装対策・iter4 W4-6）"""
        # U+202E = RIGHT-TO-LEFT OVERRIDE（Cf）、\x01 = C0 制御文字（Cc）
        # ソースに生の双方向制御文字を埋め込まない（Trojan Source 対策）
        rlo = chr(0x202E)
        tricky_path = f"src/evil{rlo}py.cod\x01e.py"
        input_json = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": tricky_path,
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        log_file = project_root / ".claude" / "logs" / "permission.log"
        assert log_file.exists(), "ログファイルが作成されるべき"
        lines = [
            line
            for line in log_file.read_text(encoding="utf-8").strip().split("\n")
            if "evil" in line
        ]
        assert lines, "Edit のログが記録されるべき"
        target = lines[-1].split("\t")[3]
        assert rlo not in target, "U+202E (RLO) はスペースに置換されるべき"
        assert "\x01" not in target, "C0 制御文字はスペースに置換されるべき"
        assert "src/evil py.cod e.py" == target, f"制御文字のみが置換されるべき。got: {target!r}"

    def test_glob_tool_pg_allow(self, hook_runner):
        """Glob ツールは PG 級として許可される（exit 0、stdout 空）"""
        input_json = {
            "tool_name": "Glob",
            "tool_input": {
                "pattern": "**/*.py",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        assert result.stdout.strip() == "", f"PG 許可時は stdout が空であるべき。got: {result.stdout!r}"

    def test_grep_tool_pg_allow(self, hook_runner):
        """Grep ツールは PG 級として許可される（exit 0、stdout 空）"""
        input_json = {
            "tool_name": "Grep",
            "tool_input": {
                "pattern": "def main",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        assert result.stdout.strip() == "", f"PG 許可時は stdout が空であるべき。got: {result.stdout!r}"

    @pytest.mark.parametrize("blacklisted_arg", [
        "--config",
        "--settings",
        "--ruleset",
        "--rule-dir",
        "--rulesdir",
        "--plugin",
        "--resolve-plugins-relative-to",
        "--stdin-filename",
        "--ignore-path",
        "--ext",
    ])
    def test_auditing_pg_command_with_blacklisted_arg_pm(self, hook_runner, project_root, blacklisted_arg):
        """AUDITING フェーズで PG コマンドにブラックリスト引数があると PM に昇格する"""
        phase_file = project_root / ".claude" / "current-phase.md"
        phase_file.parent.mkdir(parents=True, exist_ok=True)
        phase_file.write_text("**AUDITING**\n", encoding="utf-8")

        input_json = {
            "tool_name": "Bash",
            "tool_input": {
                "command": f"ruff check --fix {blacklisted_arg} /etc/evil.toml src/",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, f"ブラックリスト引数 {blacklisted_arg} 付き PG コマンドは PM ask を返すべき"
        data = json.loads(stdout)
        assert data["hookSpecificOutput"]["permissionDecision"] == "ask"

    def test_auditing_pg_command_normal_args_allowed(self, hook_runner, project_root):
        """AUDITING フェーズで PG コマンドに正常な引数は PG 許可される"""
        phase_file = project_root / ".claude" / "current-phase.md"
        phase_file.parent.mkdir(parents=True, exist_ok=True)
        phase_file.write_text("**AUDITING**\n", encoding="utf-8")

        input_json = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "ruff check --fix src/main.py",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        assert result.stdout.strip() == "", f"正常引数の PG コマンドは許可されるべき。got: {result.stdout!r}"

    def test_non_auditing_pg_command_se(self, hook_runner, project_root):
        """非 AUDITING フェーズでは PG コマンドも SE として扱われる"""
        # フェーズファイルを作成しない（非 AUDITING）
        input_json = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "ruff check --fix src/main.py",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        assert result.stdout.strip() == "", f"非 AUDITING では SE 許可されるべき。got: {result.stdout!r}"


class TestFR9SelfGovernance:
    """FR-9 自己統治の不可侵: AUTONOMOUS フェーズでの統治ファイル書込 deny テスト

    対応仕様: docs/specs/autonomous-mode/{requirements,design}.md FR-9.1 / design D5。
    層2（PreToolUse hook・プロンプティング層）の phase-conditional deny を検証する。
    層1（permissions.deny 決定的層）は T1-5 後に autonomous 専用 settings で別途実装する。
    """

    @pytest.mark.parametrize("tool_name,file_path", [
        ("Edit", ".claude/rules/core-identity.md"),
        ("Write", ".claude/rules/auto-generated/draft-001.md"),
        ("Write", "docs/adr/0006-new-decision.md"),
        ("Edit", ".claude/settings.json"),
        ("Edit", ".claude/settings.local.json"),
        ("Edit", ".claude/hooks/pre-tool-use.py"),          # 自己防衛（hook 自身）
        ("Write", ".claude/hooks/checkers/check_g2_lint.py"),
        ("Write", ".claude/skills/autonomous/SKILL.md"),    # モード自身の定義
    ])
    def test_autonomous_denies_governance_files(self, hook_runner, project_root, tool_name, file_path):
        """AUTONOMOUS フェーズでは FR9_PATTERNS への書込が deny される（自己破壊的再帰防止）"""
        write_phase(project_root, "AUTONOMOUS")
        input_json = {"tool_name": tool_name, "tool_input": _write_input(tool_name, file_path)}
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, f"deny 時は stdout に JSON が出力されるべき。got: {result.stdout!r}"
        data = json.loads(stdout)
        hook_output = data["hookSpecificOutput"]
        assert hook_output["hookEventName"] == "PreToolUse"
        assert hook_output["permissionDecision"] == "deny", \
            f"{file_path} は AUTONOMOUS で deny されるべき。got: {hook_output['permissionDecision']}"
        assert isinstance(hook_output["permissionDecisionReason"], str)
        assert len(hook_output["permissionDecisionReason"]) > 0

    @pytest.mark.parametrize("tool_name,file_path", [
        ("Edit", "src/main.py"),            # 通常コード → SE（deny でない）
    ])
    def test_autonomous_allows_non_governance_paths(self, hook_runner, project_root, tool_name, file_path):
        """AUTONOMOUS でも統治ファイル/spec いずれにも非該当のパス（src 等）は deny されない

        注: docs/specs/ は FR-9 統治ファイルではないが FR-3.4 spec freeze で別途 deny される
        （TestFR34SpecFreeze 参照）。本テストは FR-9/FR-3.4 いずれの対象でもない src 等を検証する。
        """
        write_phase(project_root, "AUTONOMOUS")
        input_json = {"tool_name": tool_name, "tool_input": _write_input(tool_name, file_path)}
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        if stdout:
            data = json.loads(stdout)
            assert data["hookSpecificOutput"]["permissionDecision"] != "deny", \
                f"{file_path} は AUTONOMOUS でも deny されるべきでない"

    @pytest.mark.parametrize("tool_name,file_path", [
        ("Edit", ".claude/rules/core-identity.md"),
        ("Edit", ".claude/hooks/pre-tool-use.py"),
        ("Edit", ".claude/settings.json"),
        ("Write", ".claude/skills/autonomous/SKILL.md"),
    ])
    def test_non_autonomous_does_not_deny_governance(self, hook_runner, project_root, tool_name, file_path):
        """非 AUTONOMOUS（BUILDING）では FR9_PATTERNS への書込が deny されない（回帰防止）"""
        write_phase(project_root, "BUILDING")
        input_json = {"tool_name": tool_name, "tool_input": _write_input(tool_name, file_path)}
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        if stdout:
            data = json.loads(stdout)
            assert data["hookSpecificOutput"]["permissionDecision"] != "deny", \
                f"非 AUTONOMOUS では {file_path} は deny されるべきでない（PM ask か SE）"


class TestFR34SpecFreeze:
    """FR-3.4 spec freeze: AUTONOMOUS フェーズでの docs/specs/ 書込 deny テスト

    対応仕様: requirements.md FR-3.4（MUST・不可逆 C 操作の即時ハードストップに
    「spec 書換」を明示列挙）/ design.md D2(§4)・D7 層1（FR-3.4 C層の強制点）。
    spec は FR-9 の統治ファイル（自己統治の強制点）ではなく「成果物」だが、FR-3.4 が
    spec 書換の即時ハードストップを MUST とするため、FR-9 とは別系統で deny する
    （成果物と統治ファイルの混同を避ける）。本クラスは層2（PreToolUse hook）の
    phase-conditional deny を検証する。層1（permissions.deny 決定的層）は
    test_settings_autonomous.py が検証する（二重防御）。
    """

    @pytest.mark.parametrize("tool_name,file_path", [
        ("Edit", "docs/specs/autonomous-mode/requirements.md"),
        ("Write", "docs/specs/autonomous-mode/design.md"),
        ("Edit", "docs/specs/green-state-definition.md"),
        ("Write", "docs/specs/new-feature/tasks.md"),
    ])
    def test_autonomous_denies_spec_files(self, hook_runner, project_root, tool_name, file_path):
        """AUTONOMOUS フェーズでは docs/specs/ への書込が deny される（FR-3.4 spec freeze）"""
        write_phase(project_root, "AUTONOMOUS")
        input_json = {"tool_name": tool_name, "tool_input": _write_input(tool_name, file_path)}
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, f"deny 時は stdout に JSON が出力されるべき。got: {result.stdout!r}"
        data = json.loads(stdout)
        hook_output = data["hookSpecificOutput"]
        assert hook_output["hookEventName"] == "PreToolUse"
        assert hook_output["permissionDecision"] == "deny", \
            f"{file_path} は AUTONOMOUS で deny されるべき。got: {hook_output['permissionDecision']}"
        assert isinstance(hook_output["permissionDecisionReason"], str)
        assert len(hook_output["permissionDecisionReason"]) > 0

    @pytest.mark.parametrize("tool_name,file_path", [
        ("Edit", "docs/specs/autonomous-mode/requirements.md"),
        ("Write", "docs/specs/foo/design.md"),
    ])
    def test_non_autonomous_does_not_deny_spec(self, hook_runner, project_root, tool_name, file_path):
        """非 AUTONOMOUS（BUILDING）では docs/specs/ は deny されない（PM ask のまま・回帰防止）"""
        write_phase(project_root, "BUILDING")
        input_json = {"tool_name": tool_name, "tool_input": _write_input(tool_name, file_path)}
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, "PM ask 時は stdout に JSON が出力されるべき（spec は PM パターン該当）"
        data = json.loads(stdout)
        hook_output = data["hookSpecificOutput"]
        assert hook_output["permissionDecision"] == "ask", \
            f"非 AUTONOMOUS では {file_path} は PM ask であるべき（deny でない）。got: {hook_output['permissionDecision']}"


class TestPMSessionDowngrade:
    """セッションスコープ PM 級降格テスト（2026-06-29 / 案 A）

    pre-tool-use.py が `.claude/.session-pm-edit-cache.json` を参照して、
    同一セッション内 2 回目以降の同一 PM 級パス Edit を SE 級に降格することを検証する。
    """

    def _write_cache(self, project_root: Path, session_id: str, approved_paths: list[str]) -> Path:
        """テスト用のキャッシュファイルを書き込む。"""
        cache_file = project_root / ".claude" / ".session-pm-edit-cache.json"
        cache_file.write_text(
            json.dumps({"session_id": session_id, "approved_paths": approved_paths}),
            encoding="utf-8",
        )
        return cache_file

    def test_pm_with_matching_cache_downgrades_to_se(self, hook_runner, project_root):
        """キャッシュに同 session_id + 同パスがある場合、PM が SE に降格される（stdout 空）"""
        self._write_cache(project_root, "sess-1", ["docs/specs/test.md"])
        input_json = {
            "session_id": "sess-1",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "docs/specs/test.md",
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        # SE 降格時は stdout 空（permissionDecision を出力しない = ask ダイアログが出ない）
        assert result.stdout.strip() == "", \
            f"SE 降格時は stdout が空であるべき。got: {result.stdout!r}"

    def test_pm_with_different_session_keeps_ask(self, hook_runner, project_root):
        """キャッシュの session_id が異なる場合は PM ask を維持する（境界失効）"""
        self._write_cache(project_root, "sess-OLD", ["docs/specs/test.md"])
        input_json = {
            "session_id": "sess-NEW",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "docs/specs/test.md",
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, "別 session_id の場合は PM ask が出力されるべき"
        data = json.loads(stdout)
        assert data["hookSpecificOutput"]["permissionDecision"] == "ask"

    def test_pm_without_cache_keeps_ask(self, hook_runner, project_root):
        """キャッシュファイルがない場合は通常通り PM ask（回帰防止）"""
        input_json = {
            "session_id": "sess-1",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "docs/specs/test.md",
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, "キャッシュ無し時は PM ask が出力されるべき"
        data = json.loads(stdout)
        assert data["hookSpecificOutput"]["permissionDecision"] == "ask"

    def test_pm_with_cache_different_path_keeps_ask(self, hook_runner, project_root):
        """キャッシュに別パスのみの場合は、対象パスは PM ask を維持する"""
        self._write_cache(project_root, "sess-1", ["docs/specs/other.md"])
        input_json = {
            "session_id": "sess-1",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "docs/specs/test.md",
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, "別パスがキャッシュされていても対象パスは PM ask"
        data = json.loads(stdout)
        assert data["hookSpecificOutput"]["permissionDecision"] == "ask"

    def test_autonomous_fr34_deny_unchanged_by_cache(self, hook_runner, project_root):
        """AUTONOMOUS フェーズの FR-3.4 spec freeze (deny) はキャッシュの影響を受けない"""
        write_phase(project_root, "AUTONOMOUS")
        self._write_cache(project_root, "sess-1", ["docs/specs/test.md"])
        input_json = {
            "session_id": "sess-1",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "docs/specs/test.md",
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, "AUTONOMOUS では deny が出力されるべき"
        data = json.loads(stdout)
        # FR-3.4 deny は PM 判定の前段で行われるため、キャッシュ降格の対象外
        assert data["hookSpecificOutput"]["permissionDecision"] == "deny"

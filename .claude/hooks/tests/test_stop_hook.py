"""
test_stop_hook.py - lam-stop-hook.py の TDD テスト

W4-T1: Red フェーズ（テストファースト）
対応仕様: docs/design/hooks-python-migration-design.md H3（lam-stop-hook）
"""
import datetime
import json
import re
from pathlib import Path

# テスト対象フックのパス
HOOK_PATH = Path(__file__).resolve().parent.parent / "lam-stop-hook.py"

# 状態ファイルのデフォルト構造
DEFAULT_STATE = {
    "active": True,
    "iteration": 0,
    "max_iterations": 5,
    "command": "test_command",
    "target": "test_target",
    "started_at": "2026-03-10T00:00:00Z",
    "log": [],
}


def _write_state(project_root: Path, state: dict) -> Path:
    """lam-loop-state.json を書き込む。"""
    state_file = project_root / ".claude" / "lam-loop-state.json"
    state_file.write_text(json.dumps(state), encoding="utf-8")
    return state_file


class TestStopHook:
    """lam-stop-hook.py の自律ループ収束判定テスト"""

    def test_no_state_file_stops(self, hook_runner, project_root):
        """状態ファイルが存在しない場合は停止許可する（exit 0、stdout 空）"""
        # 状態ファイルを作成しない
        state_file = project_root / ".claude" / "lam-loop-state.json"
        assert not state_file.exists()

        result = hook_runner(HOOK_PATH, {"session_id": "test-session"})

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"状態ファイルなし時は stdout が空であるべき。got: {result.stdout!r}"
        )

    def test_max_iterations_stops(self, hook_runner, project_root):
        """iteration >= max_iterations の場合、停止許可し状態ファイルを削除する"""
        state = {**DEFAULT_STATE, "iteration": 5, "max_iterations": 5}
        state_file = _write_state(project_root, state)
        assert state_file.exists()

        result = hook_runner(HOOK_PATH, {"session_id": "test-session"})

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"上限到達時は stdout が空であるべき。got: {result.stdout!r}"
        )
        # 状態ファイルが削除されていること
        assert not state_file.exists(), "上限到達時は状態ファイルが削除されるべき"

    def test_recursion_guard(self, hook_runner, project_root):
        """stop_hook_active=true の場合、再帰防止のため即座に停止する"""
        # 状態ファイルをアクティブ状態で作成
        _write_state(project_root, DEFAULT_STATE)

        result = hook_runner(HOOK_PATH, {"stop_hook_active": True})

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"再帰防止時は stdout が空であるべき。got: {result.stdout!r}"
        )

    def test_makefile_test_fail_blocks(self, hook_runner, project_root):
        """Makefile フォールバック: make test 失敗時は block JSON を出力して継続指示"""
        # アクティブな状態ファイルを作成（まだ上限に達していない）
        state = {**DEFAULT_STATE, "iteration": 0, "max_iterations": 5}
        _write_state(project_root, state)

        # Makefile の test ターゲットが失敗するよう設定（フォールバック検出テスト）
        makefile = project_root / "Makefile"
        makefile.write_text("test:\n\texit 1\n", encoding="utf-8")

        # cwd に project_root を渡す（テストフレームワーク検出のため）
        result = hook_runner(
            HOOK_PATH,
            {"session_id": "test-session", "cwd": str(project_root)},
        )

        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, (
            f"テスト失敗時は block JSON が出力されるべき。got: {stdout!r}"
        )
        data = json.loads(stdout)
        assert data.get("decision") == "block", (
            f"decision が 'block' であるべき。got: {data}"
        )
        assert "reason" in data, "reason フィールドが含まれるべき"

    def test_precompact_stops(self, hook_runner, project_root):
        """PreCompact 発火フラグが直近 10 分以内に存在する場合、停止許可する"""
        # アクティブな状態ファイルを作成
        state_file = _write_state(project_root, DEFAULT_STATE)

        # 直近のタイムスタンプで pre-compact-fired フラグを作成
        now_ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        pre_compact_flag = project_root / ".claude" / "pre-compact-fired"
        pre_compact_flag.write_text(now_ts, encoding="utf-8")

        result = hook_runner(HOOK_PATH, {"session_id": "test-session"})

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"PreCompact 発火直後は stdout が空であるべき。got: {result.stdout!r}"
        )
        # 状態ファイルが削除されていること
        assert not state_file.exists(), "PreCompact 発火時は状態ファイルが削除されるべき"

    def test_state_schema_valid(self, project_root):
        """lam-loop-state.json の必須フィールドが正しく書き込み・読み込みできる"""
        state = {
            "active": True,
            "iteration": 2,
            "max_iterations": 5,
            "command": "full-review",
            "target": "src/",
            "started_at": "2026-03-10T12:00:00Z",
            "log": [
                {
                    "iteration": 1,
                    "issues_found": 3,
                    "issues_fixed": 3,
                    "pg": 2,
                    "se": 1,
                    "pm": 0,
                    "test_count": 42,
                }
            ],
            "fullscan_pending": False,
        }
        state_file = _write_state(project_root, state)

        # 読み込んで検証
        loaded = json.loads(state_file.read_text(encoding="utf-8"))

        # 必須フィールドの存在確認
        assert loaded["active"] is True
        assert loaded["iteration"] == 2
        assert loaded["max_iterations"] == 5
        assert loaded["command"] == "full-review"
        assert loaded["target"] == "src/"
        assert isinstance(loaded["log"], list)
        assert len(loaded["log"]) == 1
        assert loaded["log"][0]["test_count"] == 42


class TestSecretPattern:
    """_SECRET_PATTERN のパターンマッチテスト

    注: テスト値には _SAFE_PATTERN キーワード（test, example 等）を含めて
    G5 シークレットスキャナーの誤検出を防止する。
    """

    # lam-stop-hook.py と同じパターンを使用
    _SECRET_PATTERN = re.compile(
        r'(password|secret|api_key|apikey|token|private_key)\s*[=:]\s*["\']([^"\']{8,})',
        re.IGNORECASE,
    )
    _SAFE_PATTERN = re.compile(
        r"(\btest\b|\bspec\b|\bmock\b|\bexample\b|\bplaceholder\b|\bxxx\b|\bchangeme\b)",
        re.IGNORECASE,
    )

    def test_equals_format_detected(self):
        """従来の等号形式 password="value" が検出される"""
        line = 'password="example_secret_value"'
        m = self._SECRET_PATTERN.search(line)
        assert m is not None, "等号形式が検出されるべき"
        assert m.group(1) == "password"

    def test_colon_format_detected(self):
        """YAML/JSON コロン形式 password: "value" が検出される"""
        line = 'password: "example_secret_value"'
        m = self._SECRET_PATTERN.search(line)
        assert m is not None, "コロン形式が検出されるべき"
        assert m.group(1) == "password"

    def test_colon_format_single_quotes(self):
        """コロン形式のシングルクォート api_key: 'value' が検出される"""
        line = "api_key: 'test_abcdefghij123456'"
        m = self._SECRET_PATTERN.search(line)
        assert m is not None, "コロン＋シングルクォート形式が検出されるべき"
        assert m.group(1) == "api_key"

    def test_safe_pattern_not_flagged(self):
        """テスト用の値（test, example 等）は safe として除外される"""
        line = 'password: "this is a test value"'
        m = self._SECRET_PATTERN.search(line)
        assert m is not None
        assert self._SAFE_PATTERN.search(m.group(2)), "test を含む値は safe であるべき"

    def test_short_values_ignored(self):
        """8文字未満の値は検出されない"""
        line = 'password: "short"'
        m = self._SECRET_PATTERN.search(line)
        assert m is None, "8文字未満の値は検出されないべき"

    def test_equals_still_works(self):
        """コロン対応後も等号形式が引き続き動作する"""
        line = 'secret = "placeholder_value_123"'
        m = self._SECRET_PATTERN.search(line)
        assert m is not None, "等号形式が引き続き検出されるべき"


class TestScanExtensions:
    """シークレットスキャンの対象拡張子テスト（統合テスト）

    注: 統合テスト内の秘密値は意図的に _SAFE_PATTERN 非対象値を使用している。
    これらの値は tmp_path 内のファイルに書き込まれ、フックのスキャン検出を検証する。
    テストソースファイル自体（test_stop_hook.py）はスキャン対象の check_dir（tmp_path）外に
    あるため、G5 シークレットスキャナーの誤検出は発生しない。
    """

    def test_md_secret_detected_integration(self, hook_runner, project_root):
        """.md ファイル内のシークレットが検出される"""
        _write_state(project_root, DEFAULT_STATE)
        readme = project_root / "README.md"
        readme.write_text('api_key: "sk_live_abcdefghijklmnop1234"\n', encoding="utf-8")

        result = hook_runner(HOOK_PATH, {"session_id": "test-session"})
        assert result.returncode == 0, f"フックが正常終了すべき。stderr: {result.stderr!r}"

        log_file = project_root / ".claude" / "logs" / "loop.log"
        assert log_file.exists(), "シークレット検出時は loop.log が生成されるべき"
        log_content = log_file.read_text(encoding="utf-8")
        assert "potential secret" in log_content, "README.md 内のシークレットがログに記録されるべき"

    def test_txt_secret_detected_integration(self, hook_runner, project_root):
        """.txt ファイル内のシークレットが検出される"""
        _write_state(project_root, DEFAULT_STATE)
        secret_file = project_root / "config.txt"
        secret_file.write_text('token = "ghp_abcdefghijklmnop1234567890"\n', encoding="utf-8")

        result = hook_runner(HOOK_PATH, {"session_id": "test-session"})
        assert result.returncode == 0, f"フックが正常終了すべき。stderr: {result.stderr!r}"

        log_file = project_root / ".claude" / "logs" / "loop.log"
        assert log_file.exists(), "シークレット検出時は loop.log が生成されるべき"
        log_content = log_file.read_text(encoding="utf-8")
        assert "potential secret" in log_content, "config.txt 内のシークレットがログに記録されるべき"

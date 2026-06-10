"""
test_hook_utils.py - _hook_utils.py のユニットテスト

W1-T2a: test_hook_utils.py（共通ユーティリティのユニットテスト）
対応仕様: design.md Section 2
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest


class TestGetProjectRoot:
    def test_get_project_root_default(self, hook_utils, monkeypatch):
        """__file__ ベースの PROJECT_ROOT 取得（環境非依存）"""
        monkeypatch.delenv("LAM_PROJECT_ROOT", raising=False)
        root = hook_utils.get_project_root()
        assert isinstance(root, Path)
        assert root.is_dir()

    def test_get_project_root_env_override(self, hook_utils, tmp_path, monkeypatch):
        """LAM_PROJECT_ROOT 環境変数でのオーバーライド"""
        monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
        root = hook_utils.get_project_root()
        assert root == tmp_path


class TestReadStdinJson:
    def test_read_stdin_json_valid(self, hook_utils, monkeypatch):
        """正常な JSON 入力"""
        input_data = {"tool_name": "Read", "tool_input": {"file_path": "/home/user/test.txt"}}
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))
        result = hook_utils.read_stdin_json()
        assert result == input_data

    def test_read_stdin_json_invalid(self, hook_utils, monkeypatch):
        """不正入力 -> 空 dict を返す"""
        monkeypatch.setattr("sys.stdin", io.StringIO("this is not json!!!"))
        result = hook_utils.read_stdin_json()
        assert result == {}

    def test_read_stdin_json_empty(self, hook_utils, monkeypatch):
        """空入力 -> 空 dict を返す"""
        monkeypatch.setattr("sys.stdin", io.StringIO(""))
        result = hook_utils.read_stdin_json()
        assert result == {}


class TestGetToolName:
    def test_get_tool_name_present(self, hook_utils):
        """tool_name が存在する場合"""
        data = {"tool_name": "Edit"}
        assert hook_utils.get_tool_name(data) == "Edit"

    def test_get_tool_name_missing(self, hook_utils):
        """tool_name が存在しない場合は空文字を返す"""
        assert hook_utils.get_tool_name({}) == ""


class TestGetToolInput:
    def test_get_tool_input_present(self, hook_utils):
        """tool_input のキーが存在する場合"""
        data = {"tool_input": {"file_path": "/home/user/foo.py"}}
        assert hook_utils.get_tool_input(data, "file_path") == "/home/user/foo.py"

    def test_get_tool_input_missing_key(self, hook_utils):
        """tool_input は存在するがキーがない場合は空文字"""
        data = {"tool_input": {}}
        assert hook_utils.get_tool_input(data, "file_path") == ""

    def test_get_tool_input_no_tool_input(self, hook_utils):
        """tool_input 自体がない場合は空文字"""
        assert hook_utils.get_tool_input({}, "file_path") == ""


class TestNormalizePath:
    def test_normalize_path_absolute(self, hook_utils, tmp_path):
        """絶対パス -> 相対パスに変換"""
        project_root = tmp_path
        abs_path = str(tmp_path / "src" / "main.py")
        result = hook_utils.normalize_path(abs_path, project_root)
        assert result == "src/main.py"

    def test_normalize_path_relative(self, hook_utils, tmp_path):
        """相対パスはそのまま返す"""
        project_root = tmp_path
        rel_path = "src/main.py"
        result = hook_utils.normalize_path(rel_path, project_root)
        assert result == "src/main.py"

    @pytest.mark.skipif(
        sys.platform != "win32",
        reason="バックスラッシュ区切りは Windows でのみ分離子として扱われる",
    )
    def test_normalize_path_relative_backslash(self, hook_utils, tmp_path):
        """相対パスのバックスラッシュは / に正規化する（Windows でのPM保護すり抜け防止）"""
        project_root = tmp_path
        result = hook_utils.normalize_path("docs\\specs\\x.md", project_root)
        assert result == "docs/specs/x.md"

    def test_normalize_path_project_root_itself(self, hook_utils, tmp_path):
        """プロジェクトルート自体の絶対パスは '.'"""
        project_root = tmp_path
        result = hook_utils.normalize_path(str(tmp_path), project_root)
        assert result == "."

    def test_normalize_path_out_of_root(self, hook_utils, tmp_path):
        """project_root 外の絶対パスは __out_of_root__ プレフィックス付きで返す"""
        project_root = tmp_path / "project"
        project_root.mkdir()
        external_path = "/etc/passwd"
        result = hook_utils.normalize_path(external_path, project_root)
        assert result.startswith("__out_of_root__/")
        assert "/etc/passwd" in result

    def test_normalize_path_symlink_escapes_root(self, hook_utils, tmp_path):
        """W-15: root 内 symlink が外部を指す絶対パスは out_of_root と判定される"""
        project_root = tmp_path / "project"
        project_root.mkdir()
        external = tmp_path / "external"
        external.mkdir()
        link = project_root / "link"
        try:
            link.symlink_to(external, target_is_directory=True)
        except OSError:
            # Windows の非特権ユーザー環境では [WinError 1314] で失敗する。
            # （Path.symlink_to は NotImplementedError を送出しないため OSError のみ）
            pytest.skip("symlink not permitted in this environment")
        # 文字列上は project_root 配下に見えるが、実体は external/secret.txt
        target_via_link = str(link / "secret.txt")
        result = hook_utils.normalize_path(target_via_link, project_root)
        assert result.startswith("__out_of_root__/")

    def test_normalize_path_nonexistent_within_root(self, hook_utils, tmp_path):
        """W-15 回帰防止: 未作成（Write 新規）の root 内絶対パスは相対化される"""
        project_root = tmp_path
        new_path = str(tmp_path / "newdir" / "new.py")
        result = hook_utils.normalize_path(new_path, project_root)
        assert result == "newdir/new.py"

    def test_normalize_path_relative_traversal_escapes(self, hook_utils, tmp_path):
        """W-16: 相対 .. が root を越境する場合は out_of_root と判定される"""
        result = hook_utils.normalize_path("../../etc/passwd", tmp_path)
        assert result.startswith("__out_of_root__/")
        assert "../../etc/passwd" in result

    def test_normalize_path_relative_benign_dotdot(self, hook_utils, tmp_path):
        """W-16: root 内に収まる良性の .. は誤検知せず正規化して返す"""
        result = hook_utils.normalize_path("docs/../specs/x.md", tmp_path)
        assert result == "specs/x.md"

    def test_normalize_path_relative_dotdot_to_root(self, hook_utils, tmp_path):
        """W-16: 相対 .. で root 自身に戻る場合は '.' を返す"""
        result = hook_utils.normalize_path("docs/..", tmp_path)
        assert result == "."

    def test_normalize_path_relative_no_dotdot_unchanged(self, hook_utils, tmp_path):
        """W-16 回帰防止: .. を含まない通常の相対パスは従来どおり不変"""
        result = hook_utils.normalize_path("docs/specs/x.md", tmp_path)
        assert result == "docs/specs/x.md"


class TestAtomicWriteJson:
    def test_atomic_write_json(self, hook_utils, tmp_path):
        """JSON のアトミック書き込み + 読み戻し検証"""
        target = tmp_path / "state.json"
        data = {"key": "value", "number": 42, "nested": {"a": 1}}
        hook_utils.atomic_write_json(target, data)

        assert target.exists()
        with open(target, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_atomic_write_json_overwrites(self, hook_utils, tmp_path):
        """既存ファイルを上書きする"""
        target = tmp_path / "state.json"
        hook_utils.atomic_write_json(target, {"old": True})
        hook_utils.atomic_write_json(target, {"new": True})

        with open(target, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == {"new": True}

    def test_atomic_write_json_creates_parent(self, hook_utils, tmp_path):
        """親ディレクトリが存在しない場合でも自動作成して書き込める"""
        target = tmp_path / "subdir" / "output.json"
        # subdir は意図的に未作成
        assert not target.parent.exists(), "前提: subdir が存在しないこと"
        hook_utils.atomic_write_json(target, {"x": 1})
        assert target.exists()


class TestLogEntry:
    def test_log_entry(self, hook_utils, tmp_path):
        """TSV ログ追記"""
        log_file = tmp_path / "test.log"
        hook_utils.log_entry(log_file, "INFO", "test_source", "test message")

        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        lines = content.strip().splitlines()
        assert len(lines) == 1

        fields = lines[0].split("\t")
        assert len(fields) == 4
        assert fields[1] == "INFO"
        assert fields[2] == "test_source"
        assert fields[3] == "test message"

    def test_log_entry_appends(self, hook_utils, tmp_path):
        """複数回呼び出すと追記される"""
        log_file = tmp_path / "test.log"
        hook_utils.log_entry(log_file, "INFO", "src", "first")
        hook_utils.log_entry(log_file, "WARN", "src", "second")

        content = log_file.read_text(encoding="utf-8")
        lines = content.strip().splitlines()
        assert len(lines) == 2
        assert "first" in lines[0]
        assert "second" in lines[1]

    def test_log_entry_timestamp_format(self, hook_utils, tmp_path):
        """タイムスタンプが ISO 8601 形式"""
        log_file = tmp_path / "test.log"
        hook_utils.log_entry(log_file, "INFO", "src", "msg")

        content = log_file.read_text(encoding="utf-8")
        timestamp = content.split("\t")[0]
        assert "T" in timestamp
        assert len(timestamp) >= 19


class TestSafeExit:
    def test_safe_exit_code_0(self, hook_utils):
        """exit code 0 で SystemExit が発生する"""
        with pytest.raises(SystemExit) as exc_info:
            hook_utils.safe_exit(0)
        assert exc_info.value.code == 0

    def test_safe_exit_code_1(self, hook_utils):
        """exit code 1 で SystemExit が発生する"""
        with pytest.raises(SystemExit) as exc_info:
            hook_utils.safe_exit(1)
        assert exc_info.value.code == 1

    def test_safe_exit_default(self, hook_utils):
        """デフォルト引数は 0"""
        with pytest.raises(SystemExit) as exc_info:
            hook_utils.safe_exit()
        assert exc_info.value.code == 0

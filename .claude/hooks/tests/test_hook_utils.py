"""
test_hook_utils.py - _hook_utils.py のユニットテスト

W1-T2a: test_hook_utils.py（共通ユーティリティのユニットテスト）
対応仕様: design.md Section 2
"""
import io
import json
import os
import sys
from pathlib import Path

import pytest

# import パス解決: _hook_utils.py は tests/ の一つ上のディレクトリに存在する
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import _hook_utils


class TestGetProjectRoot:
    def test_get_project_root_default(self):
        """__file__ ベースの PROJECT_ROOT 取得（環境非依存）"""
        env_backup = os.environ.pop("LAM_PROJECT_ROOT", None)
        try:
            root = _hook_utils.get_project_root()
            assert isinstance(root, Path)
            # __file__ から3階層上のディレクトリが返る
            assert root.is_dir()
        finally:
            if env_backup is not None:
                os.environ["LAM_PROJECT_ROOT"] = env_backup

    def test_get_project_root_env_override(self, tmp_path):
        """LAM_PROJECT_ROOT 環境変数でのオーバーライド"""
        os.environ["LAM_PROJECT_ROOT"] = str(tmp_path)
        try:
            root = _hook_utils.get_project_root()
            assert root == tmp_path
        finally:
            del os.environ["LAM_PROJECT_ROOT"]


class TestReadStdinJson:
    def test_read_stdin_json_valid(self, monkeypatch):
        """正常な JSON 入力"""
        input_data = {"tool_name": "Read", "tool_input": {"file_path": "/tmp/test.txt"}}
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))
        result = _hook_utils.read_stdin_json()
        assert result == input_data

    def test_read_stdin_json_invalid(self, monkeypatch):
        """不正入力 -> 空 dict を返す"""
        monkeypatch.setattr("sys.stdin", io.StringIO("this is not json!!!"))
        result = _hook_utils.read_stdin_json()
        assert result == {}

    def test_read_stdin_json_empty(self, monkeypatch):
        """空入力 -> 空 dict を返す"""
        monkeypatch.setattr("sys.stdin", io.StringIO(""))
        result = _hook_utils.read_stdin_json()
        assert result == {}


class TestGetToolName:
    def test_get_tool_name_present(self):
        """tool_name が存在する場合"""
        data = {"tool_name": "Edit"}
        assert _hook_utils.get_tool_name(data) == "Edit"

    def test_get_tool_name_missing(self):
        """tool_name が存在しない場合は空文字を返す"""
        assert _hook_utils.get_tool_name({}) == ""


class TestGetToolInput:
    def test_get_tool_input_present(self):
        """tool_input のキーが存在する場合"""
        data = {"tool_input": {"file_path": "/tmp/foo.py"}}
        assert _hook_utils.get_tool_input(data, "file_path") == "/tmp/foo.py"

    def test_get_tool_input_missing_key(self):
        """tool_input は存在するがキーがない場合は空文字"""
        data = {"tool_input": {}}
        assert _hook_utils.get_tool_input(data, "file_path") == ""

    def test_get_tool_input_no_tool_input(self):
        """tool_input 自体がない場合は空文字"""
        assert _hook_utils.get_tool_input({}, "file_path") == ""


class TestGetToolResponse:
    def test_get_tool_response_present(self):
        """tool_response のキーが存在する場合"""
        data = {"tool_response": {"exit_code": 0, "stdout": "ok"}}
        assert _hook_utils.get_tool_response(data, "exit_code", -1) == 0

    def test_get_tool_response_missing_key(self):
        """キーが存在しない場合は default を返す"""
        data = {"tool_response": {}}
        assert _hook_utils.get_tool_response(data, "exit_code", -1) == -1

    def test_get_tool_response_no_tool_response(self):
        """tool_response 自体がない場合は default を返す"""
        assert _hook_utils.get_tool_response({}, "exit_code", -1) == -1


class TestNormalizePath:
    def test_normalize_path_absolute(self, tmp_path):
        """絶対パス -> 相対パスに変換"""
        project_root = tmp_path
        abs_path = str(tmp_path / "src" / "main.py")
        result = _hook_utils.normalize_path(abs_path, project_root)
        assert result == "src/main.py"

    def test_normalize_path_relative(self, tmp_path):
        """相対パスはそのまま返す"""
        project_root = tmp_path
        rel_path = "src/main.py"
        result = _hook_utils.normalize_path(rel_path, project_root)
        assert result == "src/main.py"

    def test_normalize_path_project_root_itself(self, tmp_path):
        """プロジェクトルート自体の絶対パスは . または空文字"""
        project_root = tmp_path
        result = _hook_utils.normalize_path(str(tmp_path), project_root)
        # relative_to により "." になる
        assert result in (".", "")


class TestAtomicWriteJson:
    def test_atomic_write_json(self, tmp_path):
        """JSON のアトミック書き込み + 読み戻し検証"""
        target = tmp_path / "state.json"
        data = {"key": "value", "number": 42, "nested": {"a": 1}}
        _hook_utils.atomic_write_json(target, data)

        assert target.exists()
        with open(target, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_atomic_write_json_overwrites(self, tmp_path):
        """既存ファイルを上書きする"""
        target = tmp_path / "state.json"
        _hook_utils.atomic_write_json(target, {"old": True})
        _hook_utils.atomic_write_json(target, {"new": True})

        with open(target, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == {"new": True}

    def test_atomic_write_json_creates_parent(self, tmp_path):
        """親ディレクトリが存在する場合は書き込める"""
        # 親ディレクトリは tmp_path 自体であり存在する
        target = tmp_path / "output.json"
        _hook_utils.atomic_write_json(target, {"x": 1})
        assert target.exists()


class TestLogEntry:
    def test_log_entry(self, tmp_path):
        """TSV ログ追記"""
        log_file = tmp_path / "test.log"
        _hook_utils.log_entry(log_file, "INFO", "test_source", "test message")

        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        lines = content.strip().splitlines()
        assert len(lines) == 1

        fields = lines[0].split("\t")
        # TSV: timestamp, level, source, message
        assert len(fields) == 4
        assert fields[1] == "INFO"
        assert fields[2] == "test_source"
        assert fields[3] == "test message"

    def test_log_entry_appends(self, tmp_path):
        """複数回呼び出すと追記される"""
        log_file = tmp_path / "test.log"
        _hook_utils.log_entry(log_file, "INFO", "src", "first")
        _hook_utils.log_entry(log_file, "WARN", "src", "second")

        content = log_file.read_text(encoding="utf-8")
        lines = content.strip().splitlines()
        assert len(lines) == 2
        assert "first" in lines[0]
        assert "second" in lines[1]

    def test_log_entry_timestamp_format(self, tmp_path):
        """タイムスタンプが ISO 8601 形式"""
        log_file = tmp_path / "test.log"
        _hook_utils.log_entry(log_file, "INFO", "src", "msg")

        content = log_file.read_text(encoding="utf-8")
        timestamp = content.split("\t")[0]
        # ISO 8601: YYYY-MM-DDTHH:MM:SS... の形式
        assert "T" in timestamp
        assert len(timestamp) >= 19


class TestSafeExit:
    def test_safe_exit_code_0(self):
        """exit code 0 で SystemExit が発生する"""
        with pytest.raises(SystemExit) as exc_info:
            _hook_utils.safe_exit(0)
        assert exc_info.value.code == 0

    def test_safe_exit_code_1(self):
        """exit code 1 で SystemExit が発生する"""
        with pytest.raises(SystemExit) as exc_info:
            _hook_utils.safe_exit(1)
        assert exc_info.value.code == 1

    def test_safe_exit_default(self):
        """デフォルト引数は 0"""
        with pytest.raises(SystemExit) as exc_info:
            _hook_utils.safe_exit()
        assert exc_info.value.code == 0

"""test_check_g1_test.py - checkers/check_g1_test.py の TDD テスト

T1-2: checker スクリプト G1（test）
対応仕様: docs/specs/green-state-definition.md §3.1 / design.md D3 / FR-4.1a / FR-4.3
"""

from __future__ import annotations


class TestDetectTestCommand:
    """green-state §3.1 のテストFW自動検出（検出順序）。"""

    def test_pytest_detected_from_pyproject(self, hooks_on_syspath, tmp_path):
        from checkers.check_g1_test import detect_test_command

        (tmp_path / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\n", encoding="utf-8"
        )
        assert detect_test_command(tmp_path) == ["pytest"]

    def test_npm_test_detected_from_package_json(self, hooks_on_syspath, tmp_path):
        from checkers.check_g1_test import detect_test_command

        (tmp_path / "package.json").write_text(
            '{"scripts": {"test": "jest"}}', encoding="utf-8"
        )
        assert detect_test_command(tmp_path) == ["npm", "test"]

    def test_go_test_detected_from_go_mod(self, hooks_on_syspath, tmp_path):
        from checkers.check_g1_test import detect_test_command

        (tmp_path / "go.mod").write_text("module foo\n", encoding="utf-8")
        assert detect_test_command(tmp_path) == ["go", "test", "./..."]

    def test_make_test_detected_from_makefile(self, hooks_on_syspath, tmp_path):
        from checkers.check_g1_test import detect_test_command

        (tmp_path / "Makefile").write_text("test:\n\tpytest\n", encoding="utf-8")
        assert detect_test_command(tmp_path) == ["make", "test"]

    def test_no_framework_returns_none(self, hooks_on_syspath, tmp_path):
        from checkers.check_g1_test import detect_test_command

        assert detect_test_command(tmp_path) is None

    def test_detection_order_pyproject_before_package_json(
        self, hooks_on_syspath, tmp_path
    ):
        """検出順序1(pyproject) が 2(package.json) に優先する。"""
        from checkers.check_g1_test import detect_test_command

        (tmp_path / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\n", encoding="utf-8"
        )
        (tmp_path / "package.json").write_text(
            '{"scripts": {"test": "jest"}}', encoding="utf-8"
        )
        assert detect_test_command(tmp_path) == ["pytest"]


class TestRunCheck:
    """run_check の exit code 変換（findings B: PASS=0 / FAIL=2）。"""

    def test_passing_tests_exit_0(self, hooks_on_syspath, tmp_path):
        from checkers.check_g1_test import run_check

        (tmp_path / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\n", encoding="utf-8"
        )
        (tmp_path / "test_sample.py").write_text(
            "def test_ok():\n    assert True\n", encoding="utf-8"
        )
        code, _detail = run_check(tmp_path, timeout=60)
        assert code == 0

    def test_failing_tests_exit_2(self, hooks_on_syspath, tmp_path):
        from checkers.check_g1_test import run_check

        (tmp_path / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\n", encoding="utf-8"
        )
        (tmp_path / "test_sample.py").write_text(
            "def test_ng():\n    assert False\n", encoding="utf-8"
        )
        code, detail = run_check(tmp_path, timeout=60)
        assert code == 2
        assert detail  # 赤の詳細が空でない

    def test_no_framework_passes_skip(self, hooks_on_syspath, tmp_path):
        """テストFW なしは PASS-skip（exit 0）でループを阻害しない。"""
        from checkers.check_g1_test import run_check

        code, _detail = run_check(tmp_path)
        assert code == 0


class TestAllowlistedEnv:
    """W-16: subprocess.run に build_allowlisted_env() が適用されることを確認。"""

    def test_subprocess_run_receives_allowlisted_env(
        self, hooks_on_syspath, tmp_path, monkeypatch
    ):
        """run_check が subprocess.run を呼ぶとき env= が allowlist 済み dict で渡される。"""
        import subprocess
        import checkers.check_g1_test as mod

        (tmp_path / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\n", encoding="utf-8"
        )

        captured_kwargs: dict = {}

        def _capture_run(*args, **kwargs):
            captured_kwargs.update(kwargs)
            # テストが終わるように exit 0 相当の結果を返す
            return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="", stderr="")

        monkeypatch.setattr(mod.subprocess, "run", _capture_run)

        mod.run_check(tmp_path)

        assert "env" in captured_kwargs, "subprocess.run に env= が渡されていない"
        env = captured_kwargs["env"]
        # allowlist にある PATH は含まれる
        assert "PATH" in env
        # 機密変数が混入していないこと（存在しない変数名で確認）
        # allowlist 以外の OS 環境変数は継承されない
        import _hook_utils
        for key in env:
            assert key in _hook_utils.CHECKER_ENV_ALLOWLIST, (
                f"allowlist 外の環境変数 {key!r} が subprocess に継承されている"
            )


class TestOSErrorHandling:
    """W-3: pyproject.toml / Makefile の read_text OSError 耐性テスト。"""

    def test_pyproject_oserror_falls_through_to_next_detection(
        self, hooks_on_syspath, tmp_path, monkeypatch
    ):
        """pyproject.toml の read_text が OSError を送出しても次の検出候補へ進む。"""
        from pathlib import Path as _Path
        from checkers.check_g1_test import detect_test_command

        # pyproject.toml と package.json を配置
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.pytest.ini_options]\n", encoding="utf-8")
        (tmp_path / "package.json").write_text(
            '{"scripts": {"test": "jest"}}', encoding="utf-8"
        )

        # pyproject.toml の read_text だけ OSError にする
        original_read_text = _Path.read_text

        def _patched_read_text(self, *args, **kwargs):
            if self.name == "pyproject.toml":
                raise OSError("permission denied (test)")
            return original_read_text(self, *args, **kwargs)

        monkeypatch.setattr(_Path, "read_text", _patched_read_text)

        # pyproject が読めない → package.json に fallback して npm test を返す
        result = detect_test_command(tmp_path)
        assert result == ["npm", "test"]

    def test_makefile_oserror_returns_none(
        self, hooks_on_syspath, tmp_path, monkeypatch
    ):
        """Makefile の read_text が OSError を送出したら None（PASS-skip）を返す。"""
        from pathlib import Path as _Path
        from checkers.check_g1_test import detect_test_command

        (tmp_path / "Makefile").write_text("test:\n\tpytest\n", encoding="utf-8")

        original_read_text = _Path.read_text

        def _patched_read_text(self, *args, **kwargs):
            if self.name == "Makefile":
                raise OSError("permission denied (test)")
            return original_read_text(self, *args, **kwargs)

        monkeypatch.setattr(_Path, "read_text", _patched_read_text)

        result = detect_test_command(tmp_path)
        assert result is None


class TestEdgeCases:
    """W-9: エッジケーステスト。"""

    def test_to_exec_command_pytest_uses_sys_executable(self, hooks_on_syspath):
        """(a) pytest は [sys.executable, "-m", "pytest"] に変換される（PATH 非依存）。"""
        import sys as _sys
        from checkers.check_g1_test import _to_exec_command

        result = _to_exec_command(["pytest"])
        assert result == [_sys.executable, "-m", "pytest"]

    def test_run_check_timeout_returns_exit_2(self, hooks_on_syspath, tmp_path, monkeypatch):
        """(b) TimeoutExpired → exit 2 を返す。"""
        import subprocess
        from checkers.check_g1_test import run_check

        # pyproject.toml を置いて pytest を検出させる
        (tmp_path / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\n", encoding="utf-8"
        )

        # subprocess.run が TimeoutExpired を送出するようにモック
        def _raise_timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs.get("timeout", 1))

        import checkers.check_g1_test as mod
        monkeypatch.setattr(mod.subprocess, "run", _raise_timeout)

        code, detail = run_check(tmp_path, timeout=1)
        assert code == 2
        assert "timeout" in detail.lower()

    def test_run_check_file_not_found_returns_exit_0(self, hooks_on_syspath, tmp_path, monkeypatch):
        """(c) FileNotFoundError（コマンド未導入）→ PASS-skip（exit 0）。"""
        from checkers.check_g1_test import run_check

        # pyproject.toml を置いて pytest を検出させる
        (tmp_path / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\n", encoding="utf-8"
        )

        # subprocess.run が FileNotFoundError を送出するようにモック
        def _raise_fnf(*args, **kwargs):
            raise FileNotFoundError("No such file or directory: 'pytest'")

        import checkers.check_g1_test as mod
        monkeypatch.setattr(mod.subprocess, "run", _raise_fnf)

        code, detail = run_check(tmp_path)
        assert code == 0
        assert "not found" in detail.lower() or "pass-skip" in detail.lower()

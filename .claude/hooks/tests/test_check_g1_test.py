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

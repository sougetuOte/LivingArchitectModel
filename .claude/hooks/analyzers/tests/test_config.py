"""ReviewConfig のテスト。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from analyzers.config import ReviewConfig


class TestDefaultValues:
    """ReviewConfig のデフォルト値テスト。"""

    def test_default_exclude_languages(self) -> None:
        """デフォルトの除外言語リストは空であること。"""
        config = ReviewConfig()
        assert config.exclude_languages == []

    def test_default_exclude_dirs(self) -> None:
        """デフォルトの除外ディレクトリリストが正しいこと。"""
        config = ReviewConfig()
        assert config.exclude_dirs == ["node_modules", ".venv", "vendor", "dist"]

    def test_default_max_parallel_agents(self) -> None:
        """デフォルトの並列エージェント数は 4 であること。"""
        config = ReviewConfig()
        assert config.max_parallel_agents == 4

    def test_default_chunk_size_tokens(self) -> None:
        """デフォルトのチャンクサイズは 3000 トークンであること。"""
        config = ReviewConfig()
        assert config.chunk_size_tokens == 3000

    def test_default_overlap_ratio(self) -> None:
        """デフォルトのオーバーラップ比率は 0.2 であること。"""
        config = ReviewConfig()
        assert config.overlap_ratio == 0.2

    def test_default_auto_enable_threshold(self) -> None:
        """デフォルトの自動有効化閾値は 30000 行であること。"""
        config = ReviewConfig()
        assert config.auto_enable_threshold == 30000

    def test_default_agent_retry_count(self) -> None:
        """デフォルトのエージェントリトライ回数は 2 であること。"""
        config = ReviewConfig()
        assert config.agent_retry_count == 2

    def test_default_static_analysis_timeout_sec(self) -> None:
        """デフォルトの静的解析タイムアウトは 300 秒であること。"""
        config = ReviewConfig()
        assert config.static_analysis_timeout_sec == 300

    def test_default_file_size_limit_bytes(self) -> None:
        """デフォルトのファイルサイズ上限は 1000000 バイトであること。"""
        config = ReviewConfig()
        assert config.file_size_limit_bytes == 1000000

    def test_default_summary_max_tokens(self) -> None:
        """デフォルトのサマリー最大トークン数は 5000 であること。"""
        config = ReviewConfig()
        assert config.summary_max_tokens == 5000


class TestLoadFileNotFound:
    def test_returns_default_when_file_not_exists(self, project_root: Path) -> None:
        config = ReviewConfig.load(project_root)
        assert config == ReviewConfig()

    def test_default_exclude_dirs_not_shared(self, project_root: Path) -> None:
        c1 = ReviewConfig.load(project_root)
        c2 = ReviewConfig.load(project_root)
        c1.exclude_dirs.append("extra")
        assert "extra" not in c2.exclude_dirs


class TestLoadPartialOverride:
    def test_partial_override_respects_specified_values(self, project_root: Path) -> None:
        config_path = project_root / ".claude" / "review-config.json"
        config_path.write_text(json.dumps({"max_parallel_agents": 8}))

        config = ReviewConfig.load(project_root)
        assert config.max_parallel_agents == 8

    def test_partial_override_keeps_defaults_for_unspecified(self, project_root: Path) -> None:
        config_path = project_root / ".claude" / "review-config.json"
        config_path.write_text(json.dumps({"max_parallel_agents": 8}))

        config = ReviewConfig.load(project_root)
        assert config.chunk_size_tokens == 3000
        assert config.exclude_dirs == ["node_modules", ".venv", "vendor", "dist"]

    def test_partial_override_exclude_languages(self, project_root: Path) -> None:
        config_path = project_root / ".claude" / "review-config.json"
        config_path.write_text(json.dumps({"exclude_languages": ["go"]}))

        config = ReviewConfig.load(project_root)
        assert config.exclude_languages == ["go"]


class TestLoadAllFields:
    def test_all_fields_loaded_correctly(self, project_root: Path) -> None:
        data = {
            "exclude_languages": ["go", "rust"],
            "exclude_dirs": ["build", "out"],
            "max_parallel_agents": 2,
            "chunk_size_tokens": 1500,
            "overlap_ratio": 0.1,
            "auto_enable_threshold": 10000,
            "agent_retry_count": 3,
            "static_analysis_timeout_sec": 60,
            "file_size_limit_bytes": 500000,
            "summary_max_tokens": 2000,
        }
        config_path = project_root / ".claude" / "review-config.json"
        config_path.write_text(json.dumps(data))

        config = ReviewConfig.load(project_root)

        assert config.exclude_languages == ["go", "rust"]
        assert config.exclude_dirs == ["build", "out"]
        assert config.max_parallel_agents == 2
        assert config.chunk_size_tokens == 1500
        assert config.overlap_ratio == 0.1
        assert config.auto_enable_threshold == 10000
        assert config.agent_retry_count == 3
        assert config.static_analysis_timeout_sec == 60
        assert config.file_size_limit_bytes == 500000
        assert config.summary_max_tokens == 2000


class TestLoadInvalidJson:
    def test_invalid_json_raises_value_error(self, project_root: Path) -> None:
        config_path = project_root / ".claude" / "review-config.json"
        config_path.write_text("{ invalid json }")

        with pytest.raises(ValueError, match="review-config.json"):
            ReviewConfig.load(project_root)

    def test_non_dict_json_raises_value_error(self, project_root: Path) -> None:
        config_path = project_root / ".claude" / "review-config.json"
        config_path.write_text(json.dumps([1, 2, 3]))

        with pytest.raises(ValueError, match="review-config.json"):
            ReviewConfig.load(project_root)


class TestGitleaksEnabledValidation:
    """gitleaks_enabled の型バリデーションテスト（W-6 対応）。"""

    def test_gitleaks_enabled_default_true(self) -> None:
        """デフォルトは True であること。"""
        config = ReviewConfig()
        assert config.gitleaks_enabled is True

    def test_gitleaks_enabled_false(self, project_root: Path) -> None:
        """false を正しくパースすること。"""
        config_path = project_root / ".claude" / "review-config.json"
        config_path.write_text(json.dumps({"gitleaks_enabled": False}))
        config = ReviewConfig.load(project_root)
        assert config.gitleaks_enabled is False

    def test_gitleaks_enabled_string_raises(self, project_root: Path) -> None:
        """文字列 "false" を渡すと ValueError になること。"""
        config_path = project_root / ".claude" / "review-config.json"
        config_path.write_text(json.dumps({"gitleaks_enabled": "false"}))
        with pytest.raises(ValueError, match="gitleaks_enabled.*boolean"):
            ReviewConfig.load(project_root)

    def test_gitleaks_enabled_int_raises(self, project_root: Path) -> None:
        """整数 0 を渡すと ValueError になること。"""
        config_path = project_root / ".claude" / "review-config.json"
        config_path.write_text(json.dumps({"gitleaks_enabled": 0}))
        with pytest.raises(ValueError, match="gitleaks_enabled.*boolean"):
            ReviewConfig.load(project_root)

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ReviewConfig:
    exclude_languages: list[str] = field(default_factory=list)
    exclude_dirs: list[str] = field(
        default_factory=lambda: ["node_modules", ".venv", "vendor", "dist"]
    )
    max_parallel_agents: int = 4
    chunk_size_tokens: int = 3000
    overlap_ratio: float = 0.2
    auto_enable_threshold: int = 30000
    agent_retry_count: int = 2
    static_analysis_timeout_sec: int = 300
    file_size_limit_bytes: int = 1000000
    summary_max_tokens: int = 5000

    @classmethod
    def load(cls, project_root: Path) -> ReviewConfig:
        config_path = project_root / ".claude" / "review-config.json"
        if not config_path.exists():
            return cls()
        try:
            data = json.loads(config_path.read_text())
        except json.JSONDecodeError as e:
            raise ValueError(f"review-config.json: {e}") from e
        if not isinstance(data, dict):
            raise ValueError(
                f"review-config.json: expected object, got {type(data).__name__}"
            )
        defaults = cls()
        return cls(
            exclude_languages=data.get(
                "exclude_languages", defaults.exclude_languages
            ),
            exclude_dirs=data.get("exclude_dirs", defaults.exclude_dirs),
            max_parallel_agents=data.get(
                "max_parallel_agents", defaults.max_parallel_agents
            ),
            chunk_size_tokens=data.get("chunk_size_tokens", defaults.chunk_size_tokens),
            overlap_ratio=data.get("overlap_ratio", defaults.overlap_ratio),
            auto_enable_threshold=data.get(
                "auto_enable_threshold", defaults.auto_enable_threshold
            ),
            agent_retry_count=data.get("agent_retry_count", defaults.agent_retry_count),
            static_analysis_timeout_sec=data.get(
                "static_analysis_timeout_sec", defaults.static_analysis_timeout_sec
            ),
            file_size_limit_bytes=data.get(
                "file_size_limit_bytes", defaults.file_size_limit_bytes
            ),
            summary_max_tokens=data.get("summary_max_tokens", defaults.summary_max_tokens),
        )

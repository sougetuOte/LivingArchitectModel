"""loop_state_helpers.py - lam-loop-state.json テスト用共有ヘルパー (W2-6)

元は conftest.py に定義されていたが、`from conftest import ...` は
リポジトリ root からの統合 pytest 実行時に他 test root の conftest.py が
sys.modules['conftest'] を先取りして shadow するため (2026-07-20 T18 testpaths
導入時に実測)、一意な basename を持つ本モジュールへ移動した。
"""
from __future__ import annotations

import json
from pathlib import Path


def make_default_state(
    *,
    command: str = "test_command",
    target: str = "test_target",
    active: bool = True,
    iteration: int = 0,
    max_iterations: int = 5,
    started_at: str = "2026-03-10T00:00:00Z",
) -> dict:
    """テスト用 lam-loop-state.json のデフォルト構造を生成するファクトリ（W2-6）。

    共通フィールド（active/iteration/max_iterations/started_at/log）を集約し、
    テスト固有の command/target のみ呼び出し側で指定する。各テストファイルに
    重複していた DEFAULT_STATE 定義を一本化するための共有ヘルパー。
    """
    return {
        "active": active,
        "iteration": iteration,
        "max_iterations": max_iterations,
        "command": command,
        "target": target,
        "started_at": started_at,
        "log": [],
    }


def write_state(project_root: Path, state: dict) -> Path:
    """テスト用の lam-loop-state.json を書き込む共通ヘルパー。"""
    state_file = project_root / ".claude" / "lam-loop-state.json"
    state_file.write_text(json.dumps(state), encoding="utf-8")
    return state_file

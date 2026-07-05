"""R-1 W-R1 S1 T3: r1_cycle_detect.py テスト.

R-G8 (Python モジュール循環依存 = 0) 対応。
自作 AST + 自前 DFS の検出ロジック検証。
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import r1_cycle_detect  # noqa: E402
from r1_cycle_detect import (  # noqa: E402
    TARGET_MODULES,
    build_file_registry,
    build_graph,
    detect_cycles,
)


def test_target_modules_is_1_2_5():
    """tasks.md T3: 対象は module 1 / 2 / 5 (tests 除外)."""
    assert TARGET_MODULES == ["1", "2", "5"]


def test_detect_cycles_on_synthetic_2_node_cycle():
    """A → B → A の 2 ノード循環を検出."""
    graph = {"A.py": {"B.py"}, "B.py": {"A.py"}}
    cycles = detect_cycles(graph)
    assert len(cycles) >= 1
    # 循環に A と B の両方が含まれる
    flat = set(n for c in cycles for n in c)
    assert "A.py" in flat and "B.py" in flat


def test_detect_cycles_on_synthetic_3_node_cycle():
    """A → B → C → A の 3 ノード循環を検出."""
    graph = {
        "A.py": {"B.py"},
        "B.py": {"C.py"},
        "C.py": {"A.py"},
    }
    cycles = detect_cycles(graph)
    assert len(cycles) >= 1
    flat = set(n for c in cycles for n in c)
    assert {"A.py", "B.py", "C.py"}.issubset(flat)


def test_detect_cycles_no_cycle_in_dag():
    """A → B → C (DAG) では循環検出ゼロ."""
    graph = {
        "A.py": {"B.py"},
        "B.py": {"C.py"},
        "C.py": set(),
    }
    cycles = detect_cycles(graph)
    assert cycles == []


def test_detect_cycles_ignores_external_deps():
    """graph に存在しないノード (外部依存) は循環判定から除外される."""
    graph = {
        "A.py": {"external_lib", "B.py"},
        "B.py": {"os", "sys"},
    }
    cycles = detect_cycles(graph)
    assert cycles == []


def test_build_file_registry_maps_stem():
    """.py ファイルの basename が registry キーとして登録される."""
    fake_inv = {
        "1": {"python_ast": {".claude/scripts/dashboard/builder.py": {"imports": []}}},
        "2": {"python_ast": {".claude/scripts/build_dashboard.py": {"imports": []}}},
        "5": {"python_ast": {}},
    }
    reg = build_file_registry(fake_inv)
    assert "builder" in reg
    assert reg["builder"] == ".claude/scripts/dashboard/builder.py"
    assert "build_dashboard" in reg


def test_build_file_registry_dotted_path():
    """dashboard/builder.py が 'dashboard.builder' としても引ける."""
    fake_inv = {
        "1": {"python_ast": {".claude/scripts/dashboard/builder.py": {"imports": []}}},
        "2": {"python_ast": {}},
        "5": {"python_ast": {}},
    }
    reg = build_file_registry(fake_inv)
    assert "dashboard.builder" in reg


def test_build_graph_resolves_relative_import():
    """level=1 の from _foo import ... がローカル解決される."""
    fake_inv = {
        "1": {
            "python_ast": {
                ".claude/scripts/dashboard/builder.py": {
                    "imports": [],
                    "from_imports": [
                        {"module": "_radix_colors", "names": ["Color"], "level": 1}
                    ],
                },
                ".claude/scripts/dashboard/_radix_colors.py": {
                    "imports": [],
                    "from_imports": [],
                },
            }
        },
        "2": {"python_ast": {}},
        "5": {"python_ast": {}},
    }
    reg = build_file_registry(fake_inv)
    graph = build_graph(fake_inv, reg)
    assert ".claude/scripts/dashboard/builder.py" in graph
    deps = graph[".claude/scripts/dashboard/builder.py"]
    assert ".claude/scripts/dashboard/_radix_colors.py" in deps


def test_build_graph_resolves_absolute_dotted():
    """level=0 の from dashboard.builder import ... がローカル解決される."""
    fake_inv = {
        "1": {
            "python_ast": {
                ".claude/scripts/dashboard/builder.py": {
                    "imports": [],
                    "from_imports": [],
                }
            }
        },
        "2": {
            "python_ast": {
                ".claude/scripts/build_dashboard.py": {
                    "imports": [],
                    "from_imports": [
                        {"module": "dashboard.builder", "names": ["X"], "level": 0}
                    ],
                }
            }
        },
        "5": {"python_ast": {}},
    }
    reg = build_file_registry(fake_inv)
    graph = build_graph(fake_inv, reg)
    deps = graph[".claude/scripts/build_dashboard.py"]
    assert ".claude/scripts/dashboard/builder.py" in deps


def test_build_graph_ignores_stdlib():
    """os / sys / __future__ 等の標準ライブラリはエッジに含まれない."""
    fake_inv = {
        "1": {
            "python_ast": {
                ".claude/scripts/dashboard/x.py": {
                    "imports": ["os", "sys"],
                    "from_imports": [
                        {"module": "__future__", "names": [], "level": 0},
                        {"module": "pathlib", "names": ["Path"], "level": 0},
                    ],
                }
            }
        },
        "2": {"python_ast": {}},
        "5": {"python_ast": {}},
    }
    reg = build_file_registry(fake_inv)
    graph = build_graph(fake_inv, reg)
    assert graph[".claude/scripts/dashboard/x.py"] == set()

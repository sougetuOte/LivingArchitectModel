"""derive_project_copies.py テスト（2026-09-05 / セッション 32 / Action 3）.

複製相を「手で 2 部 + 恒等性検査」から「正本 1 部 + 変換つき生成」へ解体した
（ADR-0010 追補 2 / HGA #33）。本テストは生成器が

1. **実リポジトリで更新 0 件**である（= 正本と派生が整合している / 陽性対照）
2. **差分があれば検出し、書けば消える**（陰性対照）
3. **片側にしか無いエントリを勝手に作らない**（意図的な非対称を機械的に埋めない）

ことを固定する。変換規則そのものの検査は `test_verify_plugin_containment.py`
（`to_project_text` 群）が持つ —— **検査と生成が同一関数を使う**ため二重に書かない。
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import derive_project_copies as dpc  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]


def _repo(tmp_path: Path, *, plugin: dict, dev: dict, area: str = "agents") -> Path:
    """複製相 + manifest を持つ最小の偽リポジトリを作る。"""
    plugin_dir = tmp_path / "plugins" / "lam-harness"
    (plugin_dir / ".claude-plugin").mkdir(parents=True)
    (plugin_dir / ".claude-plugin" / "plugin.json").write_text(
        '{"name": "lam-harness"}', encoding="utf-8"
    )
    for rel, body in plugin.items():
        p = plugin_dir / area / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8", newline="\n")
    for rel, body in dev.items():
        p = tmp_path / ".claude" / area / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8", newline="\n")
    return tmp_path


def test_real_repo_needs_no_regeneration():
    """実リポジトリの派生は正本からの導出結果と一致している（陽性対照）。

    落ちた場合は `derive_project_copies.py --write` を実行して commit する。
    """
    pending = dpc.plan(REPO_ROOT)
    shown = "\n".join(str(p.relative_to(REPO_ROOT)) for p, _ in pending)
    assert pending == [], f"再生成が必要なファイルが残っている:\n{shown}"


def test_plan_is_not_vacuous():
    """比較対象が 0 件なら「常に更新 0 件」になるため、実対象の存在を要求する。"""
    matched = list(dpc._iter_mirror_matches(REPO_ROOT))
    assert len(matched) >= 20, f"複製相の一致エントリが少なすぎる（{len(matched)} 件）"


def test_plan_detects_untransformed_dev_side(tmp_path):
    """派生が正本の名前空間つき表記をそのまま持っていれば検出する（陰性対照）。"""
    repo = _repo(
        tmp_path,
        plugin={"gabriel.md": "use lam-harness:gabriel\n"},
        dev={"gabriel.md": "use lam-harness:gabriel\n"},
    )
    pending = dpc.plan(repo)
    assert len(pending) == 1
    path, expected = pending[0]
    assert path.name == "gabriel.md"
    assert expected == "use gabriel\n"


def test_write_makes_plan_empty(tmp_path):
    """書けば差分が消える（生成が実際に効くことの確認）。"""
    repo = _repo(
        tmp_path,
        plugin={"gabriel.md": "use lam-harness:gabriel\n"},
        dev={"gabriel.md": "stale\n"},
    )
    pending = dpc.plan(repo)
    assert len(pending) == 1
    for path, expected in pending:
        path.write_text(expected, encoding="utf-8", newline="\n")
    assert dpc.plan(repo) == []
    assert (repo / ".claude" / "agents" / "gabriel.md").read_text(encoding="utf-8") == (
        "use gabriel\n"
    )


def test_plan_does_not_create_missing_dev_files(tmp_path):
    """片側にしか無いファイルは生成しない（**意図的な非対称を機械的に埋めない**）。

    複製相の非対称は T3 が違反として報告する役割であり、生成器が黙って埋めると
    「plugin にだけ置いたつもりのファイル」が開発側に湧く。
    """
    repo = _repo(
        tmp_path,
        plugin={"gabriel.md": "x\n", "extra.md": "y\n"},
        dev={"gabriel.md": "x\n"},
    )
    assert dpc.plan(repo) == []
    assert not (repo / ".claude" / "agents" / "extra.md").exists()


def test_plan_ignores_line_ending_difference(tmp_path):
    """CRLF/LF の差だけでは再生成対象にしない（T1/T3 と同じ配慮）。"""
    repo = _repo(tmp_path, plugin={}, dev={})
    p = repo / "plugins" / "lam-harness" / "agents"
    p.mkdir(parents=True, exist_ok=True)
    (p / "gabriel.md").write_bytes(b"a\r\nb\r\n")
    d = repo / ".claude" / "agents"
    d.mkdir(parents=True, exist_ok=True)
    (d / "gabriel.md").write_bytes(b"a\nb\n")
    assert dpc.plan(repo) == []

"""incident-patterns.yaml の配布と、hook のパス解決（Action 4c-1 決定 C / 2026-09-08）.

**なぜ要るか**: 配布 hook `pre-tool-use.py` は動的 deny のパターンを
`<project_root>/docs/artifacts/incident-patterns.yaml` から読むが、**この実体は配布されて
いなかった**。`load_patterns` は不在時 `None` を返す設計（フェイルセーフ）なので、
**ADR-0008 の動的 deny は全利用者環境で沈黙したまま無効**だった —— 緑のまま機能が無い形である。
2026-09-07 の閉包導出で検出し、ADR-0010 追補 4 の「fail-open を黙認しない」に接続した。

**解法**: プロジェクト側を優先し、無ければ plugin 同梱の既定パターンへフォールバックする。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
DEV_YAML = REPO_ROOT / "docs" / "artifacts" / "incident-patterns.yaml"
DIST_YAML = REPO_ROOT / "plugins" / "lam-harness" / "hooks" / "incident-patterns.yaml"

sys.path.insert(0, str(HOOKS_DIR))


def _load_hook():
    """`pre-tool-use.py` はハイフンを含むので importlib で読む。"""
    spec = importlib.util.spec_from_file_location("_ptu", HOOKS_DIR / "pre-tool-use.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_patterns_are_distributed():
    """既定パターンが plugin に同梱されていること（**これが無いと機構が沈黙する**）。"""
    assert DIST_YAML.is_file(), "plugin に既定の incident-patterns.yaml が無い"


def test_distributed_copy_matches_the_development_source():
    """配布物と開発側の正本が一致すること（検査を伴わない複製を作らない）。"""
    assert DIST_YAML.read_text(encoding="utf-8").replace("\r\n", "\n") == DEV_YAML.read_text(
        encoding="utf-8"
    ).replace("\r\n", "\n")


def test_source_md_points_at_resolvable_locations():
    """`source_md` は**マッチ時に利用者へ提示される**。非配布のローカルパスを指さないこと。

    実測（2026-09-07）: 2 件が非配布の LAM retro を指していた。利用者環境では開けない。
    """
    text = DIST_YAML.read_text(encoding="utf-8")
    offenders = [
        line.strip()
        for line in text.split("\n")
        if "source_md:" in line and "http" not in line and line.split("source_md:")[1].strip()
    ]
    assert offenders == [], f"利用者環境で解決しない source_md: {offenders}"


def test_resolve_incident_yaml_prefers_the_project_copy(tmp_path, monkeypatch):
    """プロジェクト側があればそちらを使う（利用者自身の事故履歴が優先される）。"""
    hook = _load_hook()
    project = tmp_path / "proj"
    (project / "docs" / "artifacts").mkdir(parents=True)
    own = project / "docs" / "artifacts" / "incident-patterns.yaml"
    own.write_text("patterns: []\n", encoding="utf-8")
    plugin = tmp_path / "plugin"
    (plugin / "hooks").mkdir(parents=True)
    (plugin / "hooks" / "incident-patterns.yaml").write_text("patterns: []\n", encoding="utf-8")
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin))
    assert hook.resolve_incident_yaml(project) == own


def test_resolve_incident_yaml_falls_back_to_the_plugin_default(tmp_path, monkeypatch):
    """プロジェクト側が無ければ plugin 同梱へ落ちる（**沈黙させない**）。"""
    hook = _load_hook()
    project = tmp_path / "proj"
    project.mkdir()
    plugin = tmp_path / "plugin"
    (plugin / "hooks").mkdir(parents=True)
    shipped = plugin / "hooks" / "incident-patterns.yaml"
    shipped.write_text("patterns: []\n", encoding="utf-8")
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin))
    assert hook.resolve_incident_yaml(project) == shipped


def test_resolve_incident_yaml_returns_the_project_path_when_nothing_exists(tmp_path, monkeypatch):
    """どちらも無い場合はプロジェクト側のパスを返す（`load_patterns` が None を返す既存の道）。

    ここで例外を投げない —— hook が落ちると**全ツール呼び出しが止まる**。
    """
    hook = _load_hook()
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    assert hook.resolve_incident_yaml(project) == (
        project / "docs" / "artifacts" / "incident-patterns.yaml"
    )

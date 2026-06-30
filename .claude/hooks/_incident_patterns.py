"""
_incident_patterns.py - LAM 機械可読インシデント・パターンレジストリ読込/照合

ADR-0008 Phase B-2a (C2 動的 deny) の入力データ層。
docs/artifacts/incident-patterns.yaml を読み込み、PreToolUse hook 入力と照合して
パターンマッチ結果を返す純粋関数群。

設計方針:
  - fail-open: yaml 不在 / パース失敗 / 個別パターン失敗 でも hook はブロックしない
  - 副作用なし: ロード結果はキャッシュせず、毎回ファイル読込（テスト容易性 + 即時反映）
  - 標準 PyYAML のみ依存（既存環境に存在 / 6.0.3 確認済）

スキーマ仕様: docs/artifacts/incident-patterns.yaml ヘッダコメント参照
"""
from __future__ import annotations

import fnmatch
import sys
from pathlib import Path
from typing import NamedTuple

try:
    import yaml
except ImportError:
    yaml = None  # フェイルセーフ: 未インストール環境では機能無効化


# 許容される演算子
_TRIGGER_TYPES = frozenset({"path_glob", "command_literal", "tool_set"})

# 許容される action
_ACTIONS = frozenset({"deny", "ask", "log_only"})


class PatternMatch(NamedTuple):
    """パターンマッチ結果。

    incident_id: パターン ID（permission.log + additionalContext で参照）
    action: "deny" | "ask" | "log_only"
    severity: "low" | "mid" | "high" | "critical"
    description: 1-3 行説明
    source_md: 出典ドキュメント相対パス
    """
    incident_id: str
    action: str
    severity: str
    description: str
    source_md: str


def load_patterns(yaml_path: Path) -> list[dict] | None:
    """incident-patterns.yaml をロードし active なパターンのリストを返す。

    Returns:
        list[dict]: 有効パターンの配列（active=true のみ）
        None: yaml 不在 / パース失敗 / PyYAML 未インストール / 無効スキーマ
              （フェイルセーフ: 動的 deny を無効化して通常判定を継続）
    """
    if yaml is None:
        sys.stderr.write(
            "WARNING: _incident_patterns: PyYAML not available, "
            "dynamic deny disabled\n"
        )
        return None
    if not yaml_path.exists():
        return None
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError, ValueError) as e:
        sys.stderr.write(
            f"WARNING: _incident_patterns: failed to parse {yaml_path}: "
            f"{type(e).__name__}: {e}\n"
        )
        return None

    if not isinstance(raw, dict):
        return None
    patterns = raw.get("patterns")
    if not isinstance(patterns, list):
        return None

    valid: list[dict] = []
    for p in patterns:
        if not isinstance(p, dict):
            continue
        if not p.get("active", False):
            continue
        if p.get("trigger_type") not in _TRIGGER_TYPES:
            continue
        if p.get("action") not in _ACTIONS:
            continue
        if not isinstance(p.get("id"), str) or not p["id"]:
            continue
        if p.get("trigger_pattern") in (None, ""):
            continue
        valid.append(p)
    return valid


def _match_one(pattern: dict, tool_name: str, file_path: str, command: str) -> bool:
    """単一パターンを tool 入力に対して照合する。"""
    trigger_type = pattern["trigger_type"]
    trigger_pattern = pattern["trigger_pattern"]

    if trigger_type == "path_glob":
        if not file_path or not isinstance(trigger_pattern, str):
            return False
        # fnmatch は POSIX glob 風。pre-tool-use.py が file_path を
        # POSIX 形式に正規化していない場合に備えて両形式試行する。
        candidate = file_path.replace("\\", "/")
        return fnmatch.fnmatchcase(candidate, trigger_pattern)

    if trigger_type == "command_literal":
        if not command or not isinstance(trigger_pattern, str):
            return False
        return command == trigger_pattern

    if trigger_type == "tool_set":
        if not tool_name or not isinstance(trigger_pattern, list):
            return False
        return tool_name in trigger_pattern

    return False


def match_input(
    patterns: list[dict] | None,
    tool_name: str,
    file_path: str,
    command: str,
) -> PatternMatch | None:
    """tool 入力に対して最初にマッチした active パターンを返す。

    複数マッチした場合は yaml 内の最初のものを採用（明示的優先度なし / 1 ルール 1 パターン制約）。
    照合中の例外は当該パターンをスキップして継続（fail-open）。

    Returns:
        PatternMatch: マッチ成立
        None: マッチなし / patterns が None / 全パターン照合失敗
    """
    if not patterns:
        return None
    for p in patterns:
        try:
            if _match_one(p, tool_name, file_path, command):
                return PatternMatch(
                    incident_id=p["id"],
                    action=p["action"],
                    severity=p.get("severity", "low"),
                    description=p.get("description", "").strip(),
                    source_md=p.get("source_md", ""),
                )
        except Exception as e:
            sys.stderr.write(
                f"WARNING: _incident_patterns: match failed for "
                f"{p.get('id', '<unknown>')}: {type(e).__name__}: {e}\n"
            )
            continue
    return None

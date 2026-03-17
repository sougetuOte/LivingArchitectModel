"""gitleaks ラッパーモジュール — シークレットスキャンの統合基盤

gitleaks バイナリの呼び出しと結果変換を担当する。
LanguageAnalyzer プラグインではなく、独立したユーティリティとして機能する。

セキュリティ注意: Issue dataclass には gitleaks の Match/Secret フィールドを
格納しないこと。シークレット値がレポートやログに平文で永続化されるリスクを防ぐ。

対応仕様: docs/specs/gitleaks-integration-spec.md
対応設計: docs/design/gitleaks-integration-design.md Section 5.2, 5.3, 5.4a
"""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from .base import Issue

logger = logging.getLogger(__name__)

_SUGGESTION = "シークレットを環境変数または secret manager に移動してください"


def is_available() -> bool:
    """gitleaks バイナリが PATH に存在するか確認する。"""
    return shutil.which("gitleaks") is not None


def get_install_guide() -> str:
    """gitleaks のインストールガイドメッセージを返す（FR-4a）。"""
    return """\
gitleaks が未インストールのため、Green State G5（セキュリティ）が未達です。

【影響】
  gitleaks がインストールされるまで Green State を達成できません。
  /full-review はシークレットスキャン未実施を Critical Issue として扱い、
  何度再実行しても G5 が FAIL のままになります。
  インストール後に再実行すれば解消されます。
  gitleaks が不要な場合は review-config.json に "gitleaks_enabled": false を設定してください。
  （/ship ではシークレットスキャン未実施でも WARNING のみでコミットは許可されます）

【gitleaks とは】
  シークレット（API キー、パスワード等）がコードに紛れ込んでいないかを
  自動検出する業界標準ツールです。Go 製の単一バイナリで、
  Linux / macOS / Windows（Git Bash）で動作します。

【インストール方法】
  公式: https://github.com/gitleaks/gitleaks#installing

  # Linux / macOS（Homebrew）
  brew install gitleaks

  # Windows（Scoop）
  scoop install gitleaks

  # Go がある環境
  go install github.com/gitleaks/gitleaks/v8@latest

  # バイナリ直接ダウンロード
  https://github.com/gitleaks/gitleaks/releases から OS に合わせたバイナリを取得

【なぜ必要か】
  シークレット漏洩は「すり抜けたことに気づかない」性質を持ちます。
  推奨ツールとして文書化するだけでは防げないため、
  LAM はパイプラインに組み込んで自動検出します。

【無効化】
  gitleaks が不要な場合は .claude/review-config.json に以下を追加:
  {"gitleaks_enabled": false}"""


def run_detect(
    project_root: Path,
    config_path: Path | None = None,
    *,
    enabled: bool = True,
) -> list[Issue]:
    """gitleaks detect でリポジトリ全体をスキャンする。

    Args:
        project_root: スキャン対象のプロジェクトルート
        config_path: .gitleaks.toml のパス。None の場合は project_root から自動検出
        enabled: False の場合は明示的オプトアウト（空リスト + INFO ログ）

    Returns:
        検出された Issue のリスト。
        未インストール時は not-installed Issue、実行失敗時は scan-failed/scan-timeout Issue を返す。
    """
    if not enabled:
        logger.info("gitleaks は明示的に無効化されています (gitleaks_enabled=false)")
        return []

    if not is_available():
        guide = get_install_guide()
        logger.warning("gitleaks is not installed.\n%s", guide)
        return [
            Issue(
                file="",
                line=0,
                severity="critical",
                category="security",
                tool="gitleaks",
                message="gitleaks が未インストールです。シークレットスキャンを実行できません。",
                rule_id="gitleaks:not-installed",
                suggestion=guide,
            )
        ]

    config_path = _resolve_config(project_root, config_path)
    cmd = [
        "gitleaks", "detect",
        "--source", str(project_root),
        "--report-format", "json",
        "--no-git",
    ]
    if config_path is not None:
        cmd.extend(["--config", str(config_path)])

    return _run_gitleaks(cmd, timeout=120)


def run_protect_staged(
    project_root: Path | None = None,
    config_path: Path | None = None,
    *,
    enabled: bool = True,
) -> list[Issue]:
    """gitleaks protect --staged で staged changes をスキャンする。

    Args:
        project_root: .gitleaks.toml 自動検出用。None の場合は自動検出しない
        config_path: .gitleaks.toml のパス。None の場合は project_root から自動検出
        enabled: False の場合は明示的オプトアウト（空リスト + INFO ログ）

    Returns:
        検出された Issue のリスト。未インストール・無効化時は空リスト。
    """
    if not enabled:
        logger.info("gitleaks は明示的に無効化されています (gitleaks_enabled=false)")
        return []

    if not is_available():
        return []

    if project_root is not None:
        config_path = _resolve_config(project_root, config_path)
    cmd = [
        "gitleaks", "protect", "--staged",
        "--report-format", "json",
    ]
    if config_path is not None:
        cmd.extend(["--config", str(config_path)])

    return _run_gitleaks(cmd, timeout=60)


def _resolve_config(
    project_root: Path, config_path: Path | None,
) -> Path | None:
    """config_path が None の場合、project_root から .gitleaks.toml を自動検出する。"""
    if config_path is not None:
        return config_path
    candidate = project_root / ".gitleaks.toml"
    return candidate if candidate.exists() else None


def _run_gitleaks(cmd: list[str], timeout: int) -> list[Issue]:
    """gitleaks コマンドを実行し、結果を Issue リストに変換する共通ヘルパー。

    TimeoutExpired は scan-timeout、その他の例外は scan-failed として区別する。
    """
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        report_path = Path(tmp.name)

    cmd.extend(["--report-path", str(report_path)])

    try:
        # subprocess.run は TimeoutExpired 発生時に子プロセスを自動 kill する（Python 3.3+）
        result = subprocess.run(cmd, capture_output=True, timeout=timeout)
        logger.debug(
            "gitleaks: exit_code=%d stderr_len=%d",
            result.returncode,
            len(result.stderr),
        )
        return _parse_gitleaks_json(report_path)
    except subprocess.TimeoutExpired:
        logger.error("gitleaks timed out after %ds", timeout)
        return [
            Issue(
                file="",
                line=0,
                severity="critical",
                category="security",
                tool="gitleaks",
                message=f"gitleaks がタイムアウトしました (limit={timeout}s)",
                rule_id="gitleaks:scan-timeout",
                suggestion="大規模リポジトリの場合はタイムアウト値の調整を検討してください。",
            )
        ]
    except Exception as exc:
        logger.error("gitleaks failed: %s: %s", type(exc).__name__, exc)
        return [
            Issue(
                file="",
                line=0,
                severity="critical",
                category="security",
                tool="gitleaks",
                message=f"gitleaks の実行に失敗しました: {exc}",
                rule_id="gitleaks:scan-failed",
                suggestion="gitleaks がインストール済みか、PATH が通っているか確認してください。",
            )
        ]
    finally:
        report_path.unlink(missing_ok=True)


def _parse_gitleaks_json(json_path: Path) -> list[Issue]:
    """gitleaks JSON レポートを Issue dataclass に変換する。

    設計 5.3 のマッピングに準拠。
    Match/Secret フィールドは Issue に格納しない（シークレット値の露出防止）。
    """
    if not json_path.exists():
        return []
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("gitleaks report parse failed: %s", exc)
        return []

    issues: list[Issue] = []
    for finding in data:
        issues.append(
            Issue(
                file=finding.get("File", ""),
                line=finding.get("StartLine", 0),
                severity="critical",
                category="security",
                tool="gitleaks",
                message=finding.get("Description", ""),
                rule_id=f"gitleaks:{finding.get('RuleID', 'unknown')}",
                suggestion=_SUGGESTION,
            )
        )
    return issues

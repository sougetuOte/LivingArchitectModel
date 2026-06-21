"""build_dashboard.py - ダッシュボード生成オーケストレータ（W1-B5-T2）

対応仕様:
  - docs/specs/b4-dashboard/design.md §6「ビルドコマンド設計」
  - docs/specs/b4-dashboard/design.md §9「エラー耐障害性設計」

実行インターフェース:
  python .claude/scripts/build_dashboard.py [--output PATH] [--project-root PATH]

オプション:
  --output PATH        出力ファイルパス
                       (デフォルト: docs/artifacts/dashboard/dashboard.html)
  --project-root PATH  プロジェクトルート
                       (デフォルト: LAM_PROJECT_ROOT 環境変数 → __file__ 祖先推定)

終了コード:
  0: 成功（全パーサ正常）
  1: 部分失敗（警告あり・HTML 生成は完了）
  2: 致命的エラー（HTML 未生成）
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# パス解決（distill_lessons.py と同じパターン）
# ---------------------------------------------------------------------------


def get_project_root() -> Path:
    """プロジェクトルートを返す。

    LAM_PROJECT_ROOT 環境変数が設定されていればそれを使用する（P-3 対応）。
    未設定の場合は __file__ の祖先から推定する。
    .claude/scripts/build_dashboard.py → 2 階層上がプロジェクトルート。
    """
    env_root = os.environ.get("LAM_PROJECT_ROOT")
    if env_root:
        return Path(env_root)
    # .claude/scripts/build_dashboard.py → .claude/ → project_root
    return Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# scripts ディレクトリを sys.path に追加（dashboard パッケージを import 可能にする）
# ---------------------------------------------------------------------------


def _setup_import_path(project_root: Path) -> None:
    """dashboard パッケージを import 可能にするため sys.path を設定する。"""
    scripts_dir = str(project_root / ".claude" / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)


# ---------------------------------------------------------------------------
# パーサ結果のマージ
# ---------------------------------------------------------------------------


def _merge_into(data: object, parser_name: str, result_data: dict) -> None:
    """パーサ結果を DashboardData にマージする。

    各パーサが返す data キーの内容に応じてフィールドを更新する。
    未知のキーはスキップ（将来のパーサ追加に対して安全）。
    """
    if result_data is None:
        return

    # SessionStateParser: milestones, waves
    if "milestones" in result_data:
        data.milestones.extend(result_data["milestones"])
    if "waves" in result_data:
        data.waves.extend(result_data["waves"])

    # CurrentPhaseParser: phase
    if "phase" in result_data:
        data.current_phase = result_data["phase"]

    # TasksParser: tasks
    if "tasks" in result_data:
        data.tasks.extend(result_data["tasks"])

    # GitHistoryParser: completed_waves, completed_tasks（将来の補完用）
    # Wave 1 段階ではビュー未実装のため、データを受け取るのみ（マージは Wave 3 で実装）


# ---------------------------------------------------------------------------
# メインビルド関数（design.md §9 コードブロック準拠）
# ---------------------------------------------------------------------------


def _run_parsers(
    data: object, parsers: list[tuple[str, object]]
) -> None:
    """パーサリストを順に実行し、結果を data にマージする（design.md §9）。

    各パーサは try/except で保護される。例外が発生しても残りのパーサを継続する。
    失敗情報は data.parser_errors に追記される（NFR-6 MUST）。
    """
    for name, parser in parsers:
        try:
            result = parser.parse()
            if result["ok"]:
                _merge_into(data, name, result["data"])
            else:
                data.parser_errors.append(f"{name}: {result['error']}")
        except Exception as e:
            data.parser_errors.append(f"{name}: unexpected error: {e}")


def _write_html(data: object, output_path: Path) -> int:
    """DashboardData を HTML に変換してファイルに書き出す。

    Returns:
        int: 0=成功, 2=致命的エラー（HTML 未生成）
    """
    from dashboard.builder import DashboardBuilder

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        html = DashboardBuilder(data).render()
        output_path.write_text(html, encoding="utf-8")
    except Exception as e:
        print(f"[build_dashboard] FATAL: HTML 書き出し失敗: {e}", file=sys.stderr)
        return 2

    print(f"HTML generated at {output_path}")
    return 0


def build(project_root: Path, output_path: Path) -> int:
    """ダッシュボード HTML を生成する（design.md §9 コードブロック準拠）。

    Returns:
        int: 0=成功, 1=部分失敗（警告あり・HTML 生成は完了）, 2=致命的エラー（HTML 未生成）
    """
    _setup_import_path(project_root)

    from dashboard.models import DashboardData
    from dashboard.parsers.session_state import SessionStateParser
    from dashboard.parsers.current_phase import CurrentPhaseParser

    data = DashboardData(generated_at=datetime.now().isoformat())

    # Wave 2 で SessionStateParser / CurrentPhaseParser を追加（W2-B5-T11）。
    # Wave 3 で TasksParser / GitHistoryParser を追加する（T12, T13）。
    parsers: list[tuple[str, object]] = [
        ("SessionState", SessionStateParser(project_root)),
        ("CurrentPhase", CurrentPhaseParser(project_root)),
    ]

    _run_parsers(data, parsers)

    rc = _write_html(data, output_path)
    if rc != 0:
        return rc

    return 1 if data.parser_errors else 0


# ---------------------------------------------------------------------------
# CLI エントリポイント
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    """argparse パーサを構築して返す。"""
    parser = argparse.ArgumentParser(
        description="LAM ダッシュボード HTML 生成スクリプト（design.md §6）"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="出力ファイルパス（デフォルト: docs/artifacts/dashboard/dashboard.html）",
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="プロジェクトルートパス（デフォルト: LAM_PROJECT_ROOT 環境変数 → 自動推定）",
    )
    return parser


def main() -> int:
    """CLI エントリポイント。

    使用例:
      python .claude/scripts/build_dashboard.py
      python .claude/scripts/build_dashboard.py --project-root D:/work7/LivingArchitectModel
      python .claude/scripts/build_dashboard.py --output /tmp/dashboard.html
    """
    parser = build_arg_parser()
    args = parser.parse_args()

    # プロジェクトルートの解決
    if args.project_root is not None:
        project_root = Path(args.project_root)
    else:
        project_root = get_project_root()

    # 出力パスの解決
    if args.output is not None:
        output_path = Path(args.output)
    else:
        output_path = project_root / "docs" / "artifacts" / "dashboard" / "dashboard.html"

    return build(project_root=project_root, output_path=output_path)


if __name__ == "__main__":
    sys.exit(main())

"""distill-lessons.py - goal-driven メモリ蒸留スクリプト エントリポイント

SKILL.md フロー[8] からの呼び出し用エントリポイント。
実装本体は distill_lessons.py（Python モジュール命名規約に従いアンダースコア形式）。

使用例:
  python .claude/scripts/distill-lessons.py \\
    --task-id gd-20260613-001 \\
    --grader-log .claude/logs/gd/gd-20260613-001-loop*.json

  小タスクルート（design §9.1）:
  python .claude/scripts/distill-lessons.py \\
    --task-id gd-small-001 \\
    --grader-log .claude/logs/gd/gd-small-001-loop01-grader.json \\
    --small-task
"""

import sys
from pathlib import Path

# distill_lessons.py（実装本体）をインポート
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from distill_lessons import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

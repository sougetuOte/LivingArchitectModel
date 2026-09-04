#!/usr/bin/env bash
# check-runtime.sh — /lam-harness:init のランタイム前提を検査する。
#
# 目的（不可逆点 I4 / ユーザー確認済 2026-09-04）:
#   LAM のガードの実体は hooks（Python）である。Python が無い環境で init を完了させると、
#   利用者は「ハーネスが入った」と信じたままガードが一切効かない状態に置かれる。
#   これを防ぐため、init は本スクリプトが非零を返したら**完了を拒む**。
#
# なぜ hook 側の失敗に任せないか（上流実測 V4 / code.claude.com hooks reference）:
#   hook の exit 2 以外の非零終了は **非ブロッキング**（action proceeds）であり、
#   トランスクリプトに `<hook name> hook error` 通知と stderr 1 行目が出るだけである。
#   **インタプリタ不在の exit 127 も同じバケツ**に入る。つまり Python 不在を放置すると
#   「素通り（fail-open）」と「毎回のノイズ」が同時に起きる。init は「一度きり・利用者起動・
#   対話的」を満たす唯一の地点であり、ここで止めるのが最も安い。
#
# 前例: Anthropic 公式 plugin `security-guidance` も hooks/sg-python.sh で Python を
# 自力解決しており、Windows + Git Bash の Microsoft Store stub が exit 49 で黙って落ちる
# 問題まで文書化している。本スクリプトはその同型解である。
#
# 終了コード:
#   0 — 検査通過（Python が見つかり、実際に起動できた）
#   1 — Python が見つからない / 見つかったが起動できない
#
# 標準出力に人間向けの要約、標準エラーに失敗理由を書く。

set -u

FOUND=""

# py_invoke.sh と同じ探索順（venv-first → fallback chain）。
# 「存在するが起動不能」を弾くため、実際に 1 行実行してみる。
for candidate in \
    ".venv/Scripts/python.exe" \
    ".venv/bin/python" \
    "python3" \
    "python"
do
    case "$candidate" in
        .venv/*)
            [ -x "$candidate" ] || continue
            ;;
        *)
            command -v "$candidate" >/dev/null 2>&1 || continue
            ;;
    esac
    if "$candidate" -c 'import sys' >/dev/null 2>&1; then
        FOUND="$candidate"
        break
    fi
done

if [ -z "$FOUND" ]; then
    {
        echo "[lam-harness] ランタイム検査に失敗しました: 起動可能な Python が見つかりません。"
        echo ""
        echo "  LAM のガード（承認ゲート / 権限等級 / フェーズ規律）は .claude/hooks/ の"
        echo "  Python スクリプトが執行します。Python が無いと hook は exit 127 で落ちますが、"
        echo "  Claude Code はこれを非ブロッキングとして扱うため、操作はそのまま通ります。"
        echo "  つまり「ハーネスが入っているのにガードが効かない」状態になります。"
        echo ""
        echo "  探索した順序: .venv/Scripts/python.exe -> .venv/bin/python -> python3 -> python"
        echo ""
        echo "  対処: Python 3.8 以上をインストールし、PATH を通してから再実行してください。"
        echo "  Windows で Microsoft Store 版の stub がある場合、起動せずに落ちることがあります"
        echo "  （公式 plugin security-guidance も同じ問題を文書化しています）。"
        echo "  その場合は python.org 版か、プロジェクト直下の .venv を用意してください。"
    } >&2
    exit 1
fi

VERSION="$("$FOUND" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null)"
echo "[lam-harness] ランタイム検査 OK: $FOUND (Python ${VERSION:-unknown})"
exit 0

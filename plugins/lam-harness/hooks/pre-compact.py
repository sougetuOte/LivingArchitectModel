#!/usr/bin/env python3
"""
pre-compact.py - PreCompact hook: コンテキスト圧縮前の状態保存

bash 版 pre-compact.sh のパリティ実装。
設計書 H4（pre-compact）準拠。

NOTE: PreCompact は公式の正式 hook イベント（ブロック可能）。
LAM は状態保存のみが目的のため、エラー時も exit 0 を返し意図的に圧縮をブロックしない。
"""
from __future__ import annotations
import json
import os
import pathlib
import re
import shutil
import sys
import tempfile

_HOOKS_DIR = pathlib.Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))
from _hook_utils import get_project_root, now_utc_iso8601, safe_exit  # noqa: E402


def _atomic_write_text(path: pathlib.Path, content: str) -> None:
    """テキストをアトミックに書き込む（tempfile + os.replace）。

    部分書き込みによるファイル破損を防ぐ。
    OSError は呼び出し元に伝播させる。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except OSError:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def write_pre_compact_flag(project_root: pathlib.Path, timestamp: str) -> None:
    """PreCompact 発火フラグファイルにタイムスタンプを書き込む。

    update_session_state と同様にアトミック書込を用いる（iter2 SEC-2 対称化）。
    """
    flag_path = project_root / ".claude" / "pre-compact-fired"
    _atomic_write_text(flag_path, timestamp + "\n")


def update_session_state(session_state: pathlib.Path, timestamp: str) -> None:
    """
    SESSION_STATE.md に PreCompact 発火を記録する（冪等処理）。

    既存の「## PreCompact 発火」セクションがあれば時刻行を更新し、
    なければファイル末尾に新規追加する。
    I/O 失敗時は sys.stderr にエラーを記録して正常復帰する。
    """
    section_header = "## PreCompact 発火"

    try:
        content = session_state.read_text(encoding="utf-8")
    except OSError as e:
        sys.stderr.write(f"pre-compact: failed to read {session_state}: {e}\n")
        return

    if section_header in content:
        # PreCompact セクション内の時刻行のみを更新（セクション外の同パターンを誤置換しない）
        lines = content.splitlines(keepends=True)
        updated_lines = []
        in_section = False
        for line in lines:
            if line.rstrip() == section_header:
                in_section = True
            elif line.startswith("## ") and line.strip() != section_header:
                in_section = False
            if in_section and line.startswith("- 時刻: "):
                updated_lines.append(f"- 時刻: {timestamp}\n")
            else:
                updated_lines.append(line)
        try:
            _atomic_write_text(session_state, "".join(updated_lines))
        except OSError as e:
            sys.stderr.write(f"pre-compact: failed to write {session_state}: {e}\n")
    else:
        # セクションを末尾に追加
        suffix = (
            f"\n{section_header}\n"
            f"- 時刻: {timestamp}\n"
        )
        try:
            with open(session_state, "a", encoding="utf-8", newline="\n") as f:
                f.write(suffix)
        except OSError as e:
            sys.stderr.write(f"pre-compact: failed to append {session_state}: {e}\n")


def fallback_log(project_root: pathlib.Path, timestamp: str) -> None:
    """SESSION_STATE.md が存在しない場合に loop.log へフォールバック記録する。"""
    log_path = project_root / ".claude" / "logs" / "loop.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8", newline="\n") as f:
        f.write(f"{timestamp} PreCompact fired (no SESSION_STATE.md)\n")


def backup_loop_state(project_root: pathlib.Path) -> None:
    """lam-loop-state.json が存在すれば .bak にコピーする。"""
    loop_state = project_root / ".claude" / "lam-loop-state.json"
    if loop_state.exists():
        shutil.copy2(loop_state, loop_state.with_suffix(".json.bak"))


# --- 条件ロード規範の compaction 曝露検出（R3 機構 / 段 3 / HGA #25 要件 (ii)）-----
#
# 段 1 の実測（`docs/artifacts/upstream-intake-survey-2026-08-13.md` §B.4）で、条件ロード
# （R2）で注入された規範は compaction を生き残らないことが確認された。**失火は無音**である。
#
# 本機構が記録するのは「違反」ではなく **曝露** —— compaction が条件ロード済み規範の
# 生存中に発生したという**事象**である。意味判断を含まないため clause-gate Step 1 を通る。
#
# HGA #25 が課した実装条件 2 つ（`hga-summon-log.md` §25 詳細 ④）:
#   1. 検査対象集合は**基質から導出する**。維持リストを持つと対象の増減ごとに同時更新
#      義務が生じ、設計 §1.1 が R3 への設置を禁じた恒常税型の機構に退化する
#      （※ 該当する既存 rule の名を本ファイルに書けない。検査自身がそれを禁じているため）
#   2. **検出のみ・注入なし**（消えた規範を復元しない）
#
# 執行歯は `.claude/tests/hooks/test_compaction_exposure.py`。


def _pattern_to_regex(pattern: str) -> str:
    """frontmatter の glob パターンを正規表現へ変換する。

    `**` は 0 個以上の階層、`*` / `?` は区切り（`/`）を跨がない。
    """
    segments = pattern.split("/")
    parts = []
    for idx, seg in enumerate(segments):
        is_last = idx == len(segments) - 1
        if seg == "**":
            parts.append("(?:.*)" if is_last else "(?:[^/]+/)*")
            continue
        body = ""
        for ch in seg:
            if ch == "*":
                body += "[^/]*"
            elif ch == "?":
                body += "[^/]"
            else:
                body += re.escape(ch)
        parts.append(body)
        if not is_last:
            parts.append("/")
    return "^" + "".join(parts) + "$"


def glob_match(pattern: str, path: str) -> bool:
    """リポジトリ相対パスが glob パターンに一致するか判定する。"""
    return re.match(_pattern_to_regex(pattern), path) is not None


def _parse_paths_frontmatter(text: str) -> list:
    """markdown の YAML frontmatter から `paths:` の値を取り出す。

    外部依存（PyYAML）を持ち込まないため、必要な 1 キーのみを素朴に読む。
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    patterns = []
    in_paths = False
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped == "paths:":
            in_paths = True
            continue
        if in_paths:
            if stripped.startswith("- "):
                value = stripped[2:].strip().strip('"').strip("'")
                if value:
                    patterns.append(value)
            else:
                in_paths = False
    return patterns


def load_conditional_load_rules(rules_dir: pathlib.Path) -> dict:
    """条件ロード規範を**基質から導出**する（実装条件 1）。

    対象ファイル名を列挙せず、`paths:` frontmatter の有無だけで判定するため、
    条件ロード規範が増減しても本ファイルの更新義務が生じない。
    戻り値: {リポジトリ相対パス: [glob パターン]}
    """
    rules: dict = {}
    rules_dir = pathlib.Path(rules_dir)
    if not rules_dir.is_dir():
        return rules
    project_root = rules_dir.parent.parent
    for md in sorted(rules_dir.rglob("*.md")):
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        patterns = _parse_paths_frontmatter(text)
        if not patterns:
            continue
        try:
            key = md.relative_to(project_root).as_posix()
        except ValueError:
            key = md.as_posix()
        rules[key] = patterns
    return rules


def _collect_file_paths(node, acc: set) -> None:
    """任意の JSON 構造から `file_path` の値を再帰収集する。

    transcript のスキーマ変更に耐えるため、キー名のみを頼りに走査する。
    """
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "file_path" and isinstance(value, str) and value:
                acc.add(value)
            else:
                _collect_file_paths(value, acc)
    elif isinstance(node, list):
        for item in node:
            _collect_file_paths(item, acc)


def extract_touched_paths(transcript_path: pathlib.Path) -> set:
    """transcript JSONL から、当該セッションで触れたファイルパスを収集する。

    **射程の限界**: Bash 経由の書込は `file_path` を持たないため捕捉できない
    （`pre-tool-use.py` の `_determine_by_command` と同じ穴）。
    壊れた行・読めない transcript は黙って読み飛ばす（compaction を止めないため）。
    """
    paths: set = set()
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                _collect_file_paths(obj, paths)
    except OSError:
        return paths
    return paths


def detect_exposure(rules: dict, touched: set, project_root: pathlib.Path) -> list:
    """compaction 時点で live だった条件ロード規範を返す（検出のみ）。

    「条件ロードが実際に注入されたか」ではなく「**注入される条件が満たされていたか**」
    を見る近似である。Claude Code 側の注入実装が変われば乖離しうる。
    """
    root = pathlib.Path(project_root).resolve()
    relatives = set()
    for raw in touched:
        try:
            p = pathlib.Path(raw)
            if p.is_absolute():
                relatives.add(p.resolve().relative_to(root).as_posix())
            else:
                relatives.add(p.as_posix())
        except (ValueError, OSError):
            continue

    exposed = []
    for rule_path in sorted(rules):
        for pattern in rules[rule_path]:
            if any(glob_match(pattern, rel) for rel in relatives):
                exposed.append(rule_path)
                break
    return exposed


def record_exposure(
    project_root: pathlib.Path, timestamp: str, trigger: str, exposed: list
) -> None:
    """曝露イベントを JSONL に追記する。曝露ゼロなら書かない。"""
    if not exposed:
        return
    log_path = pathlib.Path(project_root) / ".claude" / "compaction-exposure.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": timestamp,
        "trigger": trigger,
        "exposed": exposed,
        "count": len(exposed),
    }
    try:
        with open(log_path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as e:
        sys.stderr.write(f"pre-compact: failed to append {log_path}: {e}\n")


def read_hook_input() -> dict:
    """stdin の hook 入力 JSON を読む。読めなければ空 dict を返す。"""
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    try:
        data = json.loads(raw)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def main() -> None:
    try:
        project_root = get_project_root()
        timestamp = now_utc_iso8601()

        # 1. PreCompact 発火フラグを記録
        write_pre_compact_flag(project_root, timestamp)

        # 2. SESSION_STATE.md に記録（冪等処理）
        session_state = project_root / "SESSION_STATE.md"
        if session_state.exists():
            update_session_state(session_state, timestamp)
        else:
            fallback_log(project_root, timestamp)

        # 3. lam-loop-state.json のバックアップ
        backup_loop_state(project_root)

        # 4. 条件ロード規範の compaction 曝露を検出（検出のみ・注入なし = 実装条件 2）
        hook_input = read_hook_input()
        transcript = hook_input.get("transcript_path")
        if transcript:
            rules = load_conditional_load_rules(project_root / ".claude" / "rules")
            touched = extract_touched_paths(pathlib.Path(transcript))
            record_exposure(
                project_root,
                timestamp,
                hook_input.get("trigger", "unknown"),
                detect_exposure(rules, touched, project_root),
            )

    except Exception:
        # 圧縮をブロックしないため常に正常終了
        pass

    safe_exit(0)


if __name__ == "__main__":
    main()

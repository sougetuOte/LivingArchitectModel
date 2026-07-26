#!/usr/bin/env python3
"""verify_model_reference.py — M-1 W2-M1-T4.

SSOT（`.claude/rules/model-roster.md`）外のファイルにおけるモデル名直書きを検出し、
記述の性質単位で 3 分岐に分類する（FR-12 / design.md §6.2 Red-4 の解決）。

3 分岐（design.md §6.2 擬似コード準拠）:
- layer_assignment: 層への割当表現（例:「L1 = Opus 5」「| L1 | Opus 5 |」）
  → SSOT（model-roster.md）へ退避
- point_in_time_record: 時点記録（docs/artifacts/ / docs/adr/ / 実測ログ）
  → 例外登録（変更しない）
- design_property_description: 既定
  → 圧縮対象（モデル名を落として意味が通れば落とす）

判定順序は layer_assignment → point_in_time_record → design_property_description の
固定順（入れ替え禁止）。例外登録は「ファイルパス単位」ではなく「記述の性質単位」で
行う（FR-12 受け入れ条件 3 / gabriel 指摘 1）ため、docs/artifacts/ 配下であっても
層への割当表現があれば layer_assignment を優先する。

実装ノート（design.md §6.2 擬似コードからの差分・self-report 対象）:
    design.md §6.2 の検出パターンはバージョン数字を必須とするが、FR-12 受け入れ条件 2 の
    誤例（`.claude/agents/gabriel.md` の「同一モデル（Opus）の別ペルソナ」）はバージョン
    数字を伴わない。単純にバージョン数字を任意化すると「Fable-Alembic」（別プロジェクト名
    の複合語）を Fable の言及として誤検出するため、括弧で囲まれた単独言及のみを追加の
    検出対象とした（下記 _MODEL_NAME_PAT 第 3 alternative）。

Usage:
    bash .claude/scripts/py_invoke.sh .claude/scripts/verify_model_reference.py \
        [--output PATH] [--exit-nonzero-on-drift]

Refs:
    docs/specs/m-1-opus5-migration/design.md §6.2
    docs/specs/m-1-opus5-migration/requirements.md FR-12, NFR-4, NFR-5
    docs/specs/m-1-opus5-migration/tasks.md W2-M1-T4
    .claude/scripts/verify_reference_resolution.py（出力形式の参照元）
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]

# 検出パターン（design.md §6.2 の擬似コードを基底とし、上記実装ノートの理由により
# 括弧書きの無版数言及を検出する第 3 alternative を追加している）。
_MODEL_NAME_PAT = re.compile(
    r"\b(Opus|Sonnet|Haiku|Fable)[\s-]?\d+(\.\d+)?\b"
    r"|claude-(opus|sonnet|haiku)-\d[\w.-]*"
    r"|[（(](Opus|Sonnet|Haiku|Fable)[）)]",
    re.IGNORECASE,
)

# 層トークン（層への割当表現の判定に使う / design.md §6.2 classify() 準拠）
_LAYER_TOKEN_PAT = re.compile(
    r"\bL1\.5\b|\bL1\b|\bL2\b|\bL3\b|\bHGA\b|\bhooks\b|\bsubagents?\b",
    re.IGNORECASE,
)

# 割当を表す記号・語（層トークンと同居した場合に layer_assignment と判定する）
_ASSIGNMENT_INDICATORS = ("=", ":", "|", "担当", "割当")

# 時点記録として扱うディレクトリ prefix
_TIME_STAMPED_DIR_PREFIXES = ("docs/artifacts/", "docs/adr/")

# 走査対象（既定 / 相対パス glob）
_DEFAULT_TARGET_GLOBS = [
    "CLAUDE.md",
    ".claude/rules/**/*.md",
    ".claude/agents/*.md",
    ".claude/skills/**/*.md",
    "docs/adr/*.md",
]

# model-roster.md はモデル名束縛の SSOT 本体であり、ここにモデル名があるのは正常
# （drift ではない）ため走査対象から除外する。
_EXCLUDED_FILES = frozenset({".claude/rules/model-roster.md"})

# referenced フィールドから括弧を除去するための変換表
_BRACKET_TRANSLATE = str.maketrans("", "", "（）()")


def _normalize(p: str) -> str:
    return p.replace("\\", "/")


def _iter_target_files(root: Path, target_globs: Optional[list] = None) -> list:
    """走査対象ファイルを glob で列挙し、除外対象を除いてソート済みリストで返す."""
    patterns = target_globs if target_globs is not None else _DEFAULT_TARGET_GLOBS
    files: set = set()
    for pat in patterns:
        for f in glob.glob(str(root / pat), recursive=True):
            rel = _normalize(os.path.relpath(f, root))
            if rel in _EXCLUDED_FILES:
                continue
            files.add(rel)
    return [root / f for f in sorted(files)]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _iter_scan_lines(text: str) -> list:
    """frontmatter（先頭 --- ... --- ブロック）を除いた行を (行番号, 行文字列) で返す.

    design.md §6.2 の誤例は「frontmatter 外のプローズ記述」を対象とするため、
    agents/skills frontmatter 内の `model: sonnet` 等は走査対象から除く。
    行番号は元ファイルの絶対行番号（1-indexed）を維持する。
    """
    raw_lines = text.splitlines()
    start = 0
    if raw_lines and raw_lines[0].strip() == "---":
        for idx in range(1, len(raw_lines)):
            if raw_lines[idx].strip() == "---":
                start = idx + 1
                break
    return [(i + 1, raw_lines[i]) for i in range(start, len(raw_lines))]


def _is_layer_assignment(match_context: str) -> bool:
    """マッチ行が層への割当表現かどうかを判定する（design.md §6.2 classify() 準拠）.

    例:「L1 = Opus」「| L1 | Opus 5 |」「L3 の担当は Haiku 4.5」
    """
    if not _LAYER_TOKEN_PAT.search(match_context):
        return False
    return any(indicator in match_context for indicator in _ASSIGNMENT_INDICATORS)


def _is_time_stamped_source(source_path: str) -> bool:
    """ソースパスが時点記録（docs/artifacts/ / docs/adr/ / 実測ログ）かどうかを判定する."""
    normalized = _normalize(source_path)
    if any(normalized.startswith(prefix) for prefix in _TIME_STAMPED_DIR_PREFIXES):
        return True
    filename = normalized.rsplit("/", 1)[-1]
    if filename.endswith(".log"):
        return True
    if filename.endswith("-log.md"):
        return True
    if filename == "SESSION_STATE.md":
        return True
    return False


def classify(match_context: str, source_path: str) -> str:
    """3 分岐判定（design.md §6.2 擬似コード準拠 / 判定順序は固定で入れ替え禁止）.

    順序: layer_assignment → point_in_time_record → design_property_description。
    例外登録はファイルパス単位ではなく記述の性質単位で行う（FR-12 受け入れ条件 3）ため、
    docs/artifacts/ 配下であっても層への割当表現があれば layer_assignment を優先する。
    """
    if _is_layer_assignment(match_context):
        return "layer_assignment"
    if _is_time_stamped_source(source_path):
        return "point_in_time_record"
    return "design_property_description"


def _extract_referenced(matched_text: str) -> str:
    """マッチした生テキストから括弧を除いた「参照されたモデル名」を取り出す."""
    return matched_text.translate(_BRACKET_TRANSLATE).strip()


def scan(root: Optional[Path] = None, target_globs: Optional[list] = None) -> dict:
    """走査対象ファイルからモデル名直書きを検出し、3 分岐で分類する.

    Returns:
        {"total_drifts": int, "drifts": [...], "exempt_count": int}
        drifts には layer_assignment / design_property_description のみを含める。
        point_in_time_record は exempt_count にのみ計上する（drifts に含めない）。
    """
    root = root if root is not None else REPO_ROOT
    drifts: list = []
    exempt_count = 0

    for path in _iter_target_files(root, target_globs):
        source = _normalize(str(path.relative_to(root)))
        text = _read(path)
        for lineno, line in _iter_scan_lines(text):
            for m in _MODEL_NAME_PAT.finditer(line):
                classification = classify(line, source)
                if classification == "point_in_time_record":
                    exempt_count += 1
                    continue
                drifts.append(
                    {
                        "pattern": "model-name-literal",
                        "source": source,
                        "referenced": _extract_referenced(m.group(0)),
                        "match": f"line {lineno}: {line.strip()}",
                        "classification": classification,
                    }
                )

    return {
        "total_drifts": len(drifts),
        "drifts": drifts,
        "exempt_count": exempt_count,
    }


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--output", type=str, help="drift 結果 JSON 出力先")
    parser.add_argument(
        "--exit-nonzero-on-drift",
        action="store_true",
        help="drift 検出時に exit code 1 で終了（CI 用 / 既定は 0）",
    )
    args = parser.parse_args(argv)

    payload = scan()

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"wrote {args.output} (total_drifts={payload['total_drifts']})")
    else:
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
        print()

    if args.exit_nonzero_on_drift and payload["total_drifts"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""verify_reference_resolution.py — R-1 W-R1 S1 T4.

R-G7 (drift = 0) 検証。層 1 (bash grep) の抜け穴を Python で埋め、
正規表現マッチ + 存在検査を 1 スクリプトで完結する。

対象パターン (design.md §5.1 / §5.2 準拠):
- W-R3 用: .claude/rules/ 内での他 rules.md 参照 / rule-XXX 名参照 / docs/(specs|adr)/ 参照
- W-R4 用: skills / agents frontmatter 内の subagent 名参照 / gabriel 契約フィールド名

各参照先を os.path.exists() で存在検査し、drift (実在しない参照) を JSON で出力。

Usage:
    python .claude/scripts/verify_reference_resolution.py [--wave {w-r3,w-r4,all}] [--output PATH] [--exit-nonzero-on-drift]

Refs:
    docs/specs/large-scale-review/design.md §5.1 / §5.2 / §5.3
    docs/specs/large-scale-review/requirements.md FR-F3 / R-G7
    docs/specs/large-scale-review/tasks.md W-R1 S1 T4
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

# ---- W-R3 用パターン (rules 相互参照 / internal → spec 参照) ----

# パターン 1: rules 内で他 rules.md をパス指定参照 (auto-generated サブディレクトリ対応 / 数字含む rule-NNN)
# R1-006 (2026-07-06 HGA #8 crux 反映): 大文字・ドット合成ファイル名の false negative 修正。
# \.md アンカーが後続するため greedy+backtrack で文末句点等を自動的に含めない (安全)。
_W_R3_PAT_RULES_PATH = re.compile(
    r"\.claude/rules/(?:auto-generated/)?([A-Za-z0-9._-]+\.md)"
)
# パターン 2: rules 内で "rule-XXX" 名前参照
_W_R3_PAT_RULE_NAME = re.compile(r"\brule-(\d{3})\b")
# パターン 3: internal 内で spec 参照 (末尾スラッシュ or ファイル)
# R1-006: group2 (slug / \.md アンカーなし) は内部ドットのみ許容し末尾ドットは不可とする。
# 一律 [A-Za-z0-9._-]+ を適用すると Windows 末尾ドット quirk
# (Path('...large-scale-review.').exists() が win32 で True) により文末句点を
# 捕食し偽 Green 化するため、group2 のみ非対称に "内部ドット限定" のクラスにする。
# group3 (\.md アンカー付き) はパターン 1 と同様に安全。
_W_R3_PAT_SPEC_REF = re.compile(
    r"docs/(specs|adr)/([A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*)(?:/([A-Za-z0-9._-]+\.md)?)?"
)

# ---- W-R4 用パターン (skills + agents frontmatter) ----

# subagent_type="xxx" / subagent_type: "xxx" / subagent_type=xxx を統一的に捕捉
_W_R4_PAT_SUBAGENT = re.compile(
    r"""subagent_type["'\s:=]+["']?([a-z0-9][a-z0-9-]*)"""
)
# Agent(name) 記法 (関数呼び出し)
_W_R4_PAT_AGENT_CALL = re.compile(r"\bAgent\(([a-z0-9-]+)\)")

# gabriel 契約 6 フィールド (design §5.2 パターン 3)
_GABRIEL_CONTRACT_FIELDS = {
    "verdict",
    "severity",
    "affected_atoms",
    "reasoning",
    "recommended_action",
    "confidence",
}

# enum 値を持つ 3 フィールド (design §5.2 strict enum 化 / r-2-consolidation design §4.5 D1)。
# 値は gabriel.md JSON schema (design §3) 準拠の enum そのもの。
_GABRIEL_ENUM_FIELDS: dict[str, set[str]] = {
    "verdict": {"confirmed", "refuted", "inconclusive"},
    "severity": {"critical", "warning", "info"},
    "recommended_action": {"proceed", "re-magi", "abort"},
}

# 自由記述系 3 フィールド (D2 / 既存の presence(substring) 検査を維持 = 構造化検査の対象外)
_GABRIEL_PRESENCE_FIELDS = _GABRIEL_CONTRACT_FIELDS - set(_GABRIEL_ENUM_FIELDS)

# 行頭 "- key: value" (Markdown 箇条書き) または "key": "value" (JSON) 形式を捕捉する。
# `"verdict": {` のようなスキーマ開始行は値部分に英字トークンを含まないため、
# _has_valid_enum_value() 側でトークン抽出結果が空集合になり自然に無効判定される。
_STRICT_ENUM_LINE_PAT = re.compile(
    r'^\s*[-*]?\s*"?(verdict|severity|recommended_action)"?\s*:\s*(.+?)\s*$',
    re.MULTILINE,
)
_ENUM_VALUE_TOKEN_PAT = re.compile(r"[A-Za-z][A-Za-z-]*")

# ---- パターン 4: gabriel-metrics mode enum 検査 (r-2-consolidation design §4.7) ----

# .claude/gabriel-metrics.log の mode フィールドが許可 enum に含まれるか検査。
# ファイル不在（gitignore 対象・環境依存）の場合は skip（T7 の設計通り log 本体は commit しない）。
_GABRIEL_MODE_ENUM = {"aot", "lightweight", "widescan_verify"}

# ---- パターン 5: gabriel-metrics anchor カバレッジ検査 (2026-09-05 / iter0 C-5) ----

#: この日付**より後**のファイル名日付を持つ MAGI 記録のみを検査対象にする。
#: 追記工程（skills/magi/SKILL.md §Step 4.1 の MUST）を入れたのが 2026-09-05 であり、
#: それ以前の記録を被覆させるには計器データの捏造が要る（やらない）。
_ANCHOR_COVERAGE_BASELINE = "2026-09-05"
#: MAGI 記録側で probe を記録している行（`- verdict: **refuted** / ...` 形式）。
_MAGI_RECORD_VERDICT_PAT = re.compile(r"^\s*[-*]\s*verdict:", re.MULTILINE)
_FILENAME_DATE_PAT = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _normalize(p: str) -> str:
    return p.replace("\\", "/")


def _iter_files(patterns: list[str]) -> list[Path]:
    files: set[str] = set()
    for pat in patterns:
        for f in glob.glob(str(REPO_ROOT / pat), recursive=True):
            files.add(_normalize(os.path.relpath(f, REPO_ROOT)))
    return [REPO_ROOT / f for f in sorted(files)]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def verify_w_r3() -> list[dict]:
    """W-R3 用 grep パターンを Python 側で再現し、drift を返す."""
    drifts: list[dict] = []

    # 対象: .claude/rules/*.md + .claude/rules/auto-generated/*.md + docs/internal/*.md
    rules_files = _iter_files([".claude/rules/*.md", ".claude/rules/auto-generated/*.md"])
    internal_files = _iter_files(["docs/internal/*.md"])

    # パターン 1: rules 内の rules.md パス参照
    for src in rules_files + internal_files:
        text = _read(src)
        for m in _W_R3_PAT_RULES_PATH.finditer(text):
            target_name = m.group(1)
            # 実在検査: .claude/rules/ 直下 or auto-generated/ のいずれかにあれば OK
            candidates = [
                REPO_ROOT / ".claude/rules" / target_name,
                REPO_ROOT / ".claude/rules/auto-generated" / target_name,
            ]
            if not any(c.exists() for c in candidates):
                drifts.append(
                    {
                        "pattern": "w-r3-rules-path",
                        "source": _normalize(str(src.relative_to(REPO_ROOT))),
                        "referenced": target_name,
                        "match": m.group(0),
                    }
                )

    # パターン 2: rules 内の rule-NNN 名前参照 (auto-generated/rule-NNN.md にマッピング)
    for src in rules_files:
        text = _read(src)
        for m in _W_R3_PAT_RULE_NAME.finditer(text):
            rule_num = m.group(1)
            target = REPO_ROOT / ".claude/rules/auto-generated" / f"rule-{rule_num}.md"
            if not target.exists():
                drifts.append(
                    {
                        "pattern": "w-r3-rule-name",
                        "source": _normalize(str(src.relative_to(REPO_ROOT))),
                        "referenced": f"rule-{rule_num}",
                        "match": m.group(0),
                    }
                )

    # パターン 3: internal 内の spec/adr 参照
    for src in internal_files:
        text = _read(src)
        for m in _W_R3_PAT_SPEC_REF.finditer(text):
            category = m.group(1)  # specs or adr
            slug = m.group(2)
            fname = m.group(3)
            # R1-053 (HGA #9 C-N3): fname が capture された場合、dir 実在だけで
            # any(exists) が True になり fname 自体の実在検査が素通しされる
            # existence-check hole があった (R1-006 と同 bug class)。
            # fname 捕捉時は dir/fname の実在のみを厳密に要求し、
            # fname 非捕捉時 (dir のみ / slug のみ参照) は従来通り any() 判定を維持する。
            if fname:
                is_drift = not (REPO_ROOT / f"docs/{category}" / slug / fname).exists()
            else:
                # docs/specs/<slug>/ (ディレクトリ) or docs/adr/<slug>.md (フラット) を許容
                candidates = [
                    REPO_ROOT / f"docs/{category}" / slug,
                    REPO_ROOT / f"docs/{category}" / f"{slug}.md",
                ]
                is_drift = not any(c.exists() for c in candidates)
            if is_drift:
                drifts.append(
                    {
                        "pattern": "w-r3-spec-ref",
                        "source": _normalize(str(src.relative_to(REPO_ROOT))),
                        "referenced": m.group(0),
                        "match": m.group(0),
                    }
                )

    return drifts


def _resolve_agent(name: str) -> bool:
    """agent 名 (goal-driven-grader 等) → .claude/agents/<name>.md 実在チェック.

    plugin-namespaced (pr-review-toolkit:code-reviewer) や built-in
    (general-purpose, Explore, Plan, claude) は drift 判定から除外。
    """
    # built-in / catch-all 判定 (Agent tool のデフォルト提供)
    _BUILTIN = {"general-purpose", "explore", "plan", "claude", "statusline-setup"}
    if name.lower() in _BUILTIN:
        return True
    # plugin-namespaced は本 repo の agents/ に無くて当然
    if ":" in name:
        return True
    return (REPO_ROOT / ".claude/agents" / f"{name}.md").exists()


def _has_valid_enum_value(text: str, field: str, allowed: set[str]) -> bool:
    """`field: value` 形式の行に allowed のいずれかの値が実際に出現するかを検査する.

    フィールド名が散文中に単独出現するだけでは充足しない (strict enum 化 / R1-059 是正)。
    """
    for m in _STRICT_ENUM_LINE_PAT.finditer(text):
        if m.group(1) != field:
            continue
        tokens = set(_ENUM_VALUE_TOKEN_PAT.findall(m.group(2)))
        if tokens & allowed:
            return True
    return False


def _check_gabriel_contract_drifts() -> list[dict]:
    """gabriel 契約 6 フィールドの検査 (パターン 3 / design §5.2).

    D1: enum 値を持つ 3 フィールド (verdict/severity/recommended_action) は
        文書系ファイル限定の strict 構造化検査。
    D2: 自由記述系 3 フィールド (affected_atoms/reasoning/confidence) は
        既存の presence (substring) 検査を維持する。
    D4: strict enum 検査は Python ソース (magi_dispatch.py) を対象外とする
        (f-string / dict アクセスで regex が未定義動作になるため)。
    """
    drifts: list[dict] = []

    presence_targets = [
        REPO_ROOT / ".claude/agents/gabriel.md",
        REPO_ROOT / ".claude/skills/magi/SKILL.md",
        REPO_ROOT / ".claude/scripts/magi_dispatch.py",
    ]
    for tgt in presence_targets:
        if not tgt.exists():
            # magi_dispatch.py は未実装の可能性あり (Wave C 起源) → 存在しない場合 skip
            continue
        text = _read(tgt)
        missing = sorted(f for f in _GABRIEL_PRESENCE_FIELDS if f not in text)
        if missing:
            drifts.append(
                {
                    "pattern": "w-r4-gabriel-contract",
                    "source": _normalize(str(tgt.relative_to(REPO_ROOT))),
                    "referenced": missing,
                    "match": f"missing_fields={missing}",
                }
            )

    # strict enum 検査は文書系 2 ファイルに限定 (D3/D4)
    strict_targets = [
        REPO_ROOT / ".claude/agents/gabriel.md",
        REPO_ROOT / ".claude/skills/magi/SKILL.md",
    ]
    for tgt in strict_targets:
        if not tgt.exists():
            continue
        text = _read(tgt)
        invalid = sorted(
            field
            for field, allowed in _GABRIEL_ENUM_FIELDS.items()
            if not _has_valid_enum_value(text, field, allowed)
        )
        if invalid:
            drifts.append(
                {
                    "pattern": "w-r4-gabriel-contract-strict",
                    "source": _normalize(str(tgt.relative_to(REPO_ROOT))),
                    "referenced": invalid,
                    "match": f"missing_or_invalid_enum_fields={invalid}",
                }
            )

    return drifts


def verify_w_r4() -> list[dict]:
    """W-R4 用 grep パターンを Python 側で再現し、drift を返す."""
    drifts: list[dict] = []

    # 対象: skills SKILL.md + agents md
    skill_files = _iter_files([".claude/skills/**/SKILL.md"])
    agent_files = _iter_files([".claude/agents/*.md"])
    rule_files = _iter_files([".claude/rules/*.md"])

    # パターン 1 + 2: subagent_type / Agent(name) 参照
    for src in skill_files + agent_files + rule_files:
        text = _read(src)
        for m in _W_R4_PAT_SUBAGENT.finditer(text):
            name = m.group(1)
            if not _resolve_agent(name):
                drifts.append(
                    {
                        "pattern": "w-r4-subagent-type",
                        "source": _normalize(str(src.relative_to(REPO_ROOT))),
                        "referenced": name,
                        "match": m.group(0),
                    }
                )
        for m in _W_R4_PAT_AGENT_CALL.finditer(text):
            name = m.group(1)
            if not _resolve_agent(name):
                drifts.append(
                    {
                        "pattern": "w-r4-agent-call",
                        "source": _normalize(str(src.relative_to(REPO_ROOT))),
                        "referenced": name,
                        "match": m.group(0),
                    }
                )

    # パターン 3: gabriel 契約 6 フィールド (D1: enum 3 フィールドは strict / D2: 残り 3 は presence)
    drifts.extend(_check_gabriel_contract_drifts())

    return drifts


def verify_mode_enum() -> list[dict]:
    """パターン 4: gabriel-metrics.log の mode フィールドが許可 enum に含まれるか検査する.

    r-2-consolidation design.md §4.7 準拠。`.claude/gabriel-metrics.log` は
    gitignore 対象・環境依存のため、ファイル不在時は skip し drift ゼロで正常終了する
    (D3: 不在を drift として報告してはならない)。
    """
    drifts: list[dict] = []
    log_path = REPO_ROOT / ".claude/gabriel-metrics.log"
    if not log_path.exists():
        return drifts

    source = _normalize(str(log_path.relative_to(REPO_ROOT)))
    for lineno, line in enumerate(_read(log_path).splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        mode = entry.get("mode")
        if mode is not None and mode not in _GABRIEL_MODE_ENUM:
            drifts.append(
                {
                    "pattern": "gabriel-metrics-mode-enum",
                    "source": source,
                    "referenced": mode,
                    "match": f"line {lineno}: mode={mode!r}",
                }
            )
    return drifts


def verify_anchor_coverage() -> list[dict]:
    """パターン 5: MAGI 記録に対する gabriel-metrics ログの被覆を検査する.

    2026-09-05 追加（/full-review iter0 C-5）。パターン 4 が検査していたのは
    「**書かれた行**が enum に従うか」だけであり、「**書かれなかった**」は
    検出できなかった。実測: ログは 4 行・最終更新 2026-07-18 で止まり、以後
    5 回走った probe が 1 行も記録されないまま検査は緑を返し続けていた
    （空集合は常にスキーマに適合する）。

    証人は MAGI 記録側の `- verdict:` 行と、ログ側の `anchor` フィールドである。
    記録に probe があるのに、その記録を anchor に持つログ行が 1 つも無ければ drift。

    **基準日より後のファイルのみを対象とする**（`_ANCHOR_COVERAGE_BASELINE`）。
    追記工程（`skills/magi/SKILL.md` §Step 4.1 の MUST）が存在しなかった時期の
    記録まで遡ると、埋めるには計器データを捏造するしかない。それは
    `security-commands.md` §計器への書き込みを伴う検証 が禁じる方向である。

    ログ不在時は skip し drift ゼロで正常終了する（パターン 4 と同じ D3 / ログは
    gitignore 対象のため、clone 直後の利用者環境では常に不在になる）。
    """
    drifts: list[dict] = []
    log_path = REPO_ROOT / ".claude/gabriel-metrics.log"
    if not log_path.exists():
        return drifts

    anchors: set[str] = set()
    for line in _read(log_path).splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        anchor = entry.get("anchor")
        if anchor:
            anchors.add(_normalize(str(anchor)))

    for path in _iter_files(["docs/artifacts/*.md"]):
        matched = _FILENAME_DATE_PAT.search(path.name)
        if not matched or matched.group(1) <= _ANCHOR_COVERAGE_BASELINE:
            continue
        if not _MAGI_RECORD_VERDICT_PAT.search(_read(path)):
            continue
        rel = _normalize(str(path.relative_to(REPO_ROOT)))
        if rel not in anchors:
            drifts.append(
                {
                    "pattern": "gabriel-metrics-anchor-coverage",
                    "source": rel,
                    "referenced": ".claude/gabriel-metrics.log",
                    "match": (
                        "probe 記録があるが、この記録を anchor に持つログ行が無い"
                        "（skills/magi/SKILL.md §Step 4.1 の追記 MUST を参照）"
                    ),
                }
            )
    return drifts


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--wave",
        choices=["w-r3", "w-r4", "mode-enum", "anchor-coverage", "all"],
        default="all",
        help="実行対象 Wave (既定: all)",
    )
    parser.add_argument("--output", type=str, help="drift 結果 JSON 出力先")
    parser.add_argument(
        "--exit-nonzero-on-drift",
        action="store_true",
        help="drift 検出時に exit code 1 で終了 (CI 用 / 既定は 0)",
    )
    args = parser.parse_args(argv)

    result: dict[str, list[dict]] = {}
    if args.wave in ("w-r3", "all"):
        result["w-r3"] = verify_w_r3()
    if args.wave in ("w-r4", "all"):
        result["w-r4"] = verify_w_r4()
    if args.wave in ("mode-enum", "all"):
        result["mode-enum"] = verify_mode_enum()
    if args.wave in ("anchor-coverage", "all"):
        result["anchor-coverage"] = verify_anchor_coverage()

    total = sum(len(v) for v in result.values())
    payload = {
        "wave": args.wave,
        "total_drifts": total,
        "drifts_by_wave": result,
    }

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"wrote {args.output} (total_drifts={total})")
    else:
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
        print()

    if args.exit_nonzero_on_drift and total > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Scalable Code Review Phase 2: バッチ並列オーケストレーション

Task B-2a: バッチ分割・プロンプト生成・結果収集

対応仕様: scalable-code-review-spec.md FR-2, FR-3
対応設計: scalable-code-review-design.md Section 3.3, 3.6, 3.8
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import PurePath
from typing import TYPE_CHECKING

from analyzers.base import Issue
from analyzers.chunker import Chunk

if TYPE_CHECKING:
    from analyzers.card_generator import ContractCard

_EXT_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
}


def _infer_language(file_path: str) -> str:
    """ファイル拡張子からコードブロック用の言語タグを推定する。"""
    return _EXT_TO_LANG.get(PurePath(file_path).suffix, "")


@dataclass
class ReviewResult:
    """1 チャンクのレビュー結果。

    issues は LLM レビュー出力を parse_llm_issues() で変換した list[Issue]。
    FR-7f: ReviewResult.issues が list[Issue] 型であること。
    """

    chunk_name: str
    file_path: str
    issues: list[Issue]
    success: bool
    error: str = ""


@dataclass
class BatchResult:
    """バッチ全体の集計結果。

    FR-7f: all_issues も list[Issue] に統一。
    """

    total: int = 0
    succeeded: int = 0
    failed: int = 0
    all_issues: list[Issue] = field(default_factory=list)
    failed_chunks: list[str] = field(default_factory=list)


def batch_chunks(chunks: list[Chunk], batch_size: int = 4) -> list[list[Chunk]]:
    """チャンクを batch_size 個ずつのバッチに分割する。

    設計書 Section 3.3: バッチ方式で並列制御。
    """
    if not chunks:
        return []
    return [chunks[i : i + batch_size] for i in range(0, len(chunks), batch_size)]


def build_review_prompt(chunk: Chunk) -> str:
    """チャンクからレビュー用の Agent プロンプトを生成する。

    設計書 Section 3.6: Agent にチャンクの内容を渡し、レビューを指示。
    """
    context = chunk.overlap_header + chunk.content + chunk.overlap_footer
    lang = _infer_language(chunk.file_path)

    return f"""\
以下のコードをレビューしてください。

## 対象ファイル: {chunk.file_path}
## チャンク: {chunk.node_name} ({chunk.level}, 行 {chunk.start_line}-{chunk.end_line})

```{lang}
{context}
```

## レビュー観点
- コード品質（命名、単一責任、エラーハンドリング）
- セキュリティ（インジェクション、認証、機密情報）
- パフォーマンス（不要なループ、メモリ使用）
- 保守性（可読性、テスト容易性）

Issue を発見した場合は以下の形式で報告してください:
- severity: critical / warning / info
- line: 行番号
- message: 問題の説明
- suggestion: 修正案"""


def parse_llm_issues(raw_text: str, file_path: str) -> list[Issue]:
    """LLM レビュー出力を Issue リストに変換する。

    build_review_prompt() が指示するフォーマットをパースする:
        - severity: critical / warning / info
        - line: 行番号
        - message: 問題の説明
        - suggestion: 修正案

    1 ブロック（severity〜suggestion の4行）を 1 Issue として生成する。
    フォーマットに合致しない自由文は severity=info の汎用 Issue として保持し、
    情報損失を防ぐ。空文字列は空リストを返す。
    """
    stripped = raw_text.strip()
    if not stripped:
        return []

    blocks = _split_into_blocks(stripped)
    issues: list[Issue] = []
    for block in blocks:
        parsed = _parse_block(block, file_path)
        if parsed is not None:
            issues.append(parsed)

    if not issues:
        issues.append(_make_fallback_issue(stripped, file_path))

    return issues


def _split_into_blocks(text: str) -> list[str]:
    """severity フィールドを先頭とするブロックに分割する。"""
    pattern = re.compile(r"(?=- severity:)", re.IGNORECASE)
    parts = pattern.split(text)
    return [p.strip() for p in parts if p.strip()]


def _parse_line_number(block: str) -> int:
    """ブロックから行番号を抽出する。取得できない場合は 0 を返す。"""
    value = _extract_field(block, "line")
    if value is not None and value.isdigit():
        return int(value)
    return 0


def _parse_block(block: str, file_path: str) -> Issue | None:
    """1 ブロックのテキストを Issue に変換する。

    severity が取得できない場合は None を返す。
    """
    severity = _extract_field(block, "severity")
    if not severity:
        return None

    return Issue(
        file=file_path,
        line=_parse_line_number(block),
        severity=severity.lower(),
        category="review",
        tool="llm",
        message=_extract_field(block, "message") or block,
        rule_id="",
        suggestion=_extract_field(block, "suggestion") or "",
    )


def _extract_field(text: str, field_name: str) -> str | None:
    """テキストから '- field_name: value' 形式の値を抽出する。"""
    pattern = re.compile(
        rf"^-\s*{re.escape(field_name)}\s*:\s*(.+)$",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def _make_fallback_issue(text: str, file_path: str) -> Issue:
    """フォーマット外のテキストを info Issue に変換する。"""
    return Issue(
        file=file_path,
        line=0,
        severity="info",
        category="review",
        tool="llm",
        message=text,
        rule_id="",
        suggestion="",
    )


def _collect_scc_group(
    scc_entry: str,
    scc_idx_to_members: dict[int, list[str]],
    node_to_file: dict[str, str],
    file_to_chunks: dict[str, list[Chunk]],
    used_files: set[str],
) -> list[Chunk]:
    """SCC スーパーノードに属するチャンクをまとめて返す。

    スーパーノード名（例: "scc_0"）からインデックスを解析し、
    SCC 内の全ファイルのチャンクを収集する。
    """
    idx_str = scc_entry[len("scc_"):]
    if not idx_str.isdigit():
        return []

    members = scc_idx_to_members.get(int(idx_str), [])
    group: list[Chunk] = []
    for member in members:
        file_path = node_to_file.get(member)
        if file_path is not None:
            group.extend(file_to_chunks.get(file_path, []))
            used_files.add(file_path)
    return group


def order_chunks_by_topo(
    chunks: list[Chunk],
    topo_order: list[str],
    node_to_file: dict[str, str],
    sccs: list[list[str]],
) -> list[list[Chunk]]:
    """topo_order に基づいてチャンクをグループ化・順序付けする。

    設計書 Section 5.2: トポロジカル順序でレビューを実施する。

    通常ノード: そのノードのファイルに属するチャンクを1グループ。
    SCC スーパーノード: SCC 内の全ファイルに属するチャンクを1グループ（バッチレビュー）。
    topo_order に含まれないファイルのチャンクは最後に追加する。
    """
    scc_idx_to_members: dict[int, list[str]] = dict(enumerate(sccs))
    file_to_chunks: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        file_to_chunks.setdefault(chunk.file_path, []).append(chunk)

    used_files: set[str] = set()
    groups: list[list[Chunk]] = []

    for entry in topo_order:
        if entry.startswith("scc_"):
            group = _collect_scc_group(
                entry, scc_idx_to_members, node_to_file, file_to_chunks, used_files
            )
        else:
            file_path = node_to_file.get(entry)
            if file_path is not None:
                group = list(file_to_chunks.get(file_path, []))
                used_files.add(file_path)
            else:
                group = []

        if group:
            groups.append(group)

    remaining = [
        chunk
        for file_path, file_chunks in file_to_chunks.items()
        if file_path not in used_files
        for chunk in file_chunks
    ]
    if remaining:
        groups.append(remaining)

    return groups


def build_review_prompt_with_contracts(
    chunk: Chunk,
    upstream_contracts: list[ContractCard],
) -> str:
    """上流契約カードをコンテキストに含むレビュープロンプトを生成する。

    設計書 Section 5.2: 下流モジュールの Agent プロンプトに上流の契約カードを注入する。
    upstream_contracts が空の場合は build_review_prompt() と同一出力を返す。
    """
    from analyzers.card_generator import format_contract_cards_for_prompt

    base_prompt = build_review_prompt(chunk)
    contracts_text = format_contract_cards_for_prompt(upstream_contracts)

    if not contracts_text:
        return base_prompt

    header = (
        "以下は上流モジュールの契約です。"
        "これらの前提条件・保証に違反する呼び出しがないか確認してください。\n\n"
        "【帰責判断ガイド】\n"
        "違反を発見した場合、以下の基準で帰責先を判定してください:\n"
        "1. 仕様書に定義がある場合 → 仕様と乖離している側が修正対象\n"
        "2. 仕様書に定義がない場合 → 仕様の欠落として PM級にエスカレーション\n"
        "3. 下流が上流の契約に違反している場合 → 下流が修正対象\n"
        "4. 上流の契約自体が不十分な場合 → 上流の契約更新が必要（PM級）\n\n"
        "帰責判断が必要な Issue には以下のマーカーで出力してください:\n"
        "---BLAME-HINT---\n"
        "issue: [Issue の要約]\n"
        "suspected_responsible: upstream | downstream | spec_ambiguity | unknown\n"
        "module: [帰責先モジュール名]\n"
        "reason: [判断理由の1行要約]\n"
        "---END-BLAME-HINT---\n\n"
        + contracts_text
        + "\n\n"
    )
    return header + base_prompt


def order_files_by_topo(
    file_paths: list[str],
    topo_order: list[str],
    node_to_file: dict[str, str],
) -> list[str]:
    """ファイルパスのリストをトポロジカル順にソートする。

    設計書 Section 5.2: Phase 4（修正順序）でも同じトポロジカル順を使用する。
    topo_order に含まれないファイルは最後に追加する。
    """
    # ノード名 → ファイルパスの逆引き
    file_to_topo_idx: dict[str, int] = {}
    for idx, entry in enumerate(topo_order):
        file_path = node_to_file.get(entry)
        if file_path is not None:
            file_to_topo_idx[file_path] = idx

    ordered: list[str] = []
    remaining: list[str] = []

    for fp in file_paths:
        if fp in file_to_topo_idx:
            ordered.append(fp)
        else:
            remaining.append(fp)

    ordered.sort(key=lambda fp: file_to_topo_idx[fp])
    return ordered + remaining


def collect_results(results: list[ReviewResult]) -> BatchResult:
    """複数の ReviewResult を BatchResult に集計する。"""
    batch = BatchResult()
    batch.total = len(results)

    for r in results:
        if r.success:
            batch.succeeded += 1
            batch.all_issues.extend(r.issues)
        else:
            batch.failed += 1
            batch.failed_chunks.append(r.chunk_name)

    return batch

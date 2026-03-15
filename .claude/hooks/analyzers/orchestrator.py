"""Scalable Code Review Phase 2: バッチ並列オーケストレーション

Task B-2a: バッチ分割・プロンプト生成・結果収集

対応仕様: scalable-code-review-spec.md FR-2, FR-3
対応設計: scalable-code-review-design.md Section 3.3, 3.6, 3.8
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import PurePath

from analyzers.base import Issue
from analyzers.chunker import Chunk

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

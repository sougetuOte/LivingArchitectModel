"""Scalable Code Review Phase 2: バッチ並列オーケストレーション

Task B-2a: バッチ分割・プロンプト生成・結果収集

対応仕様: scalable-code-review-spec.md FR-2, FR-3
対応設計: scalable-code-review-design.md Section 3.3, 3.6, 3.8
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePath

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

    issues は LLM Agent が返す自然言語テキストのリスト（list[str]）。
    静的解析の Issue 型（analyzers.base.Issue）とは意図的に分離している。
    Phase 3 で LLM 出力を Issue 型にパースする機構を実装する際に統一設計する。
    """

    chunk_name: str
    file_path: str
    # TODO: Phase 3 で LLM 出力を Issue 型にパースする機構を実装する際に list[Issue] に統一する（S-2）
    issues: list[str]
    success: bool
    error: str = ""


@dataclass
class BatchResult:
    """バッチ全体の集計結果。"""

    total: int = 0
    succeeded: int = 0
    failed: int = 0
    all_issues: list[str] = field(default_factory=list)
    failed_chunks: list[str] = field(default_factory=list)


def batch_chunks(chunks: list[Chunk], batch_size: int = 4) -> list[list[Chunk]]:
    """チャンクを batch_size 個ずつのバッチに分割する。

    設計書 Section 3.3: バッチ方式で並列制御。
    """
    if not chunks:
        return []
    return [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]


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

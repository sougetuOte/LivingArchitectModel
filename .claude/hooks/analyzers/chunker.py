"""Scalable Code Review Phase 2: AST チャンキングエンジン

Task B-1a: Chunk データモデル + トークンカウント

対応仕様: scalable-code-review-spec.md FR-2
対応設計: scalable-code-review-design.md Section 3.0, 3.1, 3.4, 3.5
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Chunk:
    """チャンキングエンジンが生成するレビュー単位。

    設計書 Section 3.4 に対応。各チャンクはソースコードの一部
    （関数/クラス/モジュール）と、周辺コンテキストを提供する
    のりしろ（overlap）で構成される。
    """

    file_path: str          # 対象ファイルの相対パス
    start_line: int         # チャンク本体の開始行
    end_line: int           # チャンク本体の終了行
    content: str            # チャンク本体のソースコード
    overlap_header: str     # のりしろ（ファイルヘッダー: import + 定数）
    overlap_footer: str     # のりしろ（シグネチャサマリー: 同一ファイル内 + 呼び出し先）
    token_count: int        # チャンク全体（本体 + のりしろ）の推定トークン数
    level: str              # "L1" | "L2" | "L3"（チャンク粒度）
    node_name: str          # 対象のクラス名/関数名（L3 の場合はファイル名）


def count_tokens(text: str) -> int:
    """テキストの推定トークン数を返す。

    len(text.split()) でワード数を近似トークン数として使用する。
    外部トークナイザ（tiktoken 等）への依存は NFR-3 により追加しない。
    """
    return len(text.split())

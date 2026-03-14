# ループログスキーマ定義書

**バージョン**: 1.0
**作成日**: 2026-03-08
**フェーズ**: BUILDING / Wave 0
**対応仕様**:
- 要件定義書: Section 5.0, P5-FR-5 (ループログの構造化出力)
- 設計書: Section 4.2 (ループログスキーマ)
- KPI定義書: `docs/specs/evaluation-kpi.md`

> **スキーマの正規参照**: `lam-loop-state.json`（実行時状態）のスキーマは本文書 Section 2 が SSOT である。
> `.claude/hooks/lam-stop-hook.py` および `.claude/hooks/post-tool-use.py` が実装上の参照先。
> 歴史的文書（`docs/design/v4.0.0-immune-system-design.md` 等）に記載のスキーマは設計時点のものであり、本文書が優先する。

---

## 1. 概要

ループ実行時に出力される構造化ログのスキーマを定義する。ループログは KPI 計測（K1〜K5）のデータソースであり、運用品質の可視化に不可欠である。

---

## 2. JSON スキーマ（完全実装）

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "LAM Loop Log",
  "type": "object",
  "required": ["command", "target", "started_at", "total_iterations", "convergence_reason"],
  "properties": {
    "command": {
      "type": "string",
      "description": "実行されたコマンド名",
      "examples": ["full-review"]
    },
    "target": {
      "type": "string",
      "description": "対象ファイル/ディレクトリ",
      "examples": ["src/", "src/main.py"]
    },
    "started_at": {
      "type": "string",
      "format": "date-time",
      "description": "ループ開始時刻（ISO 8601）"
    },
    "completed_at": {
      "type": "string",
      "format": "date-time",
      "description": "ループ完了時刻（ISO 8601）"
    },
    "total_iterations": {
      "type": "integer",
      "minimum": 1,
      "description": "総サイクル数"
    },
    "max_iterations": {
      "type": "integer",
      "default": 5,
      "description": "最大サイクル数上限"
    },
    "convergence_reason": {
      "type": "string",
      "enum": ["green_state", "max_iterations", "escalation", "context_exhaustion", "user_abort"],
      "description": "収束理由"
    },
    "convergence_detail": {
      "type": "string",
      "description": "収束理由の詳細説明（エスカレーション時の具体的内容等）"
    },
    "iterations": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/iteration"
      },
      "description": "各サイクルの詳細ログ"
    }
  },
  "$defs": {
    "iteration": {
      "type": "object",
      "required": ["number", "issues", "classification", "actions", "green_state"],
      "properties": {
        "number": {
          "type": "integer",
          "minimum": 1,
          "description": "サイクル番号"
        },
        "issues": {
          "type": "object",
          "properties": {
            "critical": { "type": "integer", "minimum": 0 },
            "warning": { "type": "integer", "minimum": 0 },
            "info": { "type": "integer", "minimum": 0 }
          },
          "description": "検出された問題の重要度別件数"
        },
        "classification": {
          "type": "object",
          "properties": {
            "pg": { "type": "integer", "minimum": 0 },
            "se": { "type": "integer", "minimum": 0 },
            "pm": { "type": "integer", "minimum": 0 }
          },
          "description": "権限等級別の件数"
        },
        "actions": {
          "type": "object",
          "properties": {
            "auto_fixed": { "type": "integer", "minimum": 0, "description": "PG級自動修正数" },
            "reported": { "type": "integer", "minimum": 0, "description": "SE級報告数" },
            "escalated": { "type": "integer", "minimum": 0, "description": "PM級エスカレーション数" },
            "deferred": { "type": "integer", "minimum": 0, "description": "理由付き保留数" }
          },
          "description": "実施されたアクション別件数"
        },
        "green_state": {
          "type": "object",
          "properties": {
            "test": { "type": "boolean", "description": "テスト全パス" },
            "lint": { "type": "boolean", "description": "lint全パス" },
            "issues_resolved": { "type": "boolean", "description": "対応可能Issue全解決（G3）" },
            "spec_sync": { "type": "boolean", "description": "仕様差分ゼロ（G4）" }
          },
          "description": "Green State 各条件の判定結果"
        },
        "deferred_items": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "issue": { "type": "string" },
              "reason": { "type": "string" },
              "level": { "type": "string", "enum": ["warning", "info"] }
            }
          },
          "description": "理由付き保留（deferred）の一覧"
        },
        "changed_files": {
          "type": "array",
          "items": { "type": "string" },
          "description": "このサイクルで変更されたファイル一覧"
        }
      }
    }
  }
}
```

---

## 3. MVP（テキスト形式）

Wave 2 の初期実装ではテキスト形式で出力する。完全実装で上記 JSON に移行する。

### 3.1 MVP テキストフォーマット

```
=== LAM Loop Log ===
Command: full-review
Target: src/
Started: 2026-03-08T10:00:00Z
Completed: 2026-03-08T10:15:00Z
Total Iterations: 3
Convergence: green_state

--- Iteration 1 ---
Issues: Critical=1, Warning=3, Info=2
Classification: PG=3, SE=2, PM=1
Actions: auto_fixed=3, reported=2, escalated=1
Green State: test=PASS, lint=FAIL

--- Iteration 2 ---
Issues: Critical=0, Warning=1, Info=1
Classification: PG=1, SE=1, PM=0
Actions: auto_fixed=1, reported=1, escalated=0
Green State: test=PASS, lint=PASS

--- Iteration 3 (Full Scan) ---
Issues: Critical=0, Warning=0, Info=0
Green State: test=PASS, lint=PASS
=== End ===
```

### 3.2 MVP と完全実装の差分

| 項目 | MVP | 完全実装 |
|------|-----|---------|
| フォーマット | テキスト（上記形式） | JSON（Section 2 スキーマ準拠） |
| ファイル名 | `.claude/logs/loop-YYYYMMDD-HHMMSS.txt` | `.claude/logs/loop-YYYYMMDD-HHMMSS.json` |
| Green State 条件 | G1(test) + G2(lint) のみ | G1〜G4 全条件 |
| deferred_items | 記録なし | 理由付き保留の詳細記録 |
| changed_files | 記録なし | サイクルごとの変更ファイル一覧 |

---

## 4. 各フィールドの詳細定義

### 4.1 convergence_reason

| 値 | 意味 | 条件 |
|----|------|------|
| `green_state` | Green State 達成で正常収束 | G1+G2（MVP）または G1〜G4（完全実装）が全て true |
| `max_iterations` | 最大サイクル数に到達 | iteration >= max_iterations |
| `escalation` | エスカレーション条件に該当 | 同一Issue再発、テスト数減少、PM級変更検出 |
| `context_exhaustion` | コンテキスト残量不足 | PreCompact 発火を検出 |
| `user_abort` | ユーザーによる手動停止 | ユーザーが明示的にループを中断 |

### 4.2 イテレーション内メタデータ

各イテレーション（サイクル）で以下のメタデータを記録する:

| フィールド | 必須 | 説明 |
|-----------|------|------|
| `issues` | Yes | 重要度別の検出問題数（critical/warning/info） |
| `classification` | Yes | 権限等級別の件数（pg/se/pm） |
| `actions` | Yes | アクション別の件数（auto_fixed/reported/escalated/deferred） |
| `green_state` | Yes | Green State 各条件の判定結果 |
| `deferred_items` | No | 理由付き保留の詳細（完全実装） |
| `changed_files` | No | 変更ファイル一覧（完全実装） |

---

## 5. ファイル管理

### 5.1 保存先

- ディレクトリ: `.claude/logs/`
- ファイル名: `loop-YYYYMMDD-HHMMSS.{txt|json}`
- 例: `loop-20260308-100000.txt`（MVP）

### 5.2 ライフサイクル

- **生成**: `/full-review` ループ完了時に Stop hook が状態ファイルの内容を元に生成
- **参照**: `/quick-save` の KPI 集計で走査
- **保持期間**: 無期限（git で追跡）
- **集計**: `evaluation-kpi.md` Section 5.2 の手順に従う

### 5.3 `/quick-save` との連携

`/quick-save` 実行時:
1. `.claude/logs/` 配下の未コミットのループログを記録に含める
2. git commit は `/ship` で行う

---

*本文書は BUILDING フェーズ Wave 0 にて作成されました。*
*更新日: 2026-03-08*

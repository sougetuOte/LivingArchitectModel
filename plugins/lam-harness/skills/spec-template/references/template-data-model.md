## テンプレート: データモデル仕様

```markdown
# データモデル仕様: [エンティティ名]

## 概要
[エンティティの役割と目的]

## ER図

```mermaid
erDiagram
    [Entity] {
        uuid id PK
        string field1
        timestamp created_at
    }
```

## フィールド定義

| フィールド | 型 | 制約 | 説明 |
|-----------|-----|------|------|
| id | UUID | PK, NOT NULL | 一意識別子 |
| field1 | VARCHAR(255) | NOT NULL | [説明] |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 作成日時 |

## インデックス
| 名前 | カラム | 種類 | 目的 |
|------|--------|------|------|
| idx_field1 | field1 | BTREE | 検索高速化 |

## 関連
- [関連エンティティへのリンク]
```


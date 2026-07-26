## テンプレート: API仕様書

```markdown
# API仕様書: [API名]

## メタ情報
| 項目 | 内容 |
|------|------|
| ベースURL | `/api/v1/[resource]` |
| 認証 | Bearer Token / API Key / None |
| 関連仕様 | [feat-*.md](./feat-*.md) |

## エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /resources | リソース一覧取得 |
| POST | /resources | リソース作成 |
| GET | /resources/:id | リソース詳細取得 |
| PUT | /resources/:id | リソース更新 |
| DELETE | /resources/:id | リソース削除 |

## 詳細仕様

### GET /resources

#### リクエスト
**パラメータ:**
| 名前 | 型 | 必須 | 説明 |
|------|-----|------|------|
| page | number | No | ページ番号（デフォルト: 1） |
| limit | number | No | 取得件数（デフォルト: 20） |

#### レスポンス
**成功時 (200):**
```json
{
  "data": [
    {
      "id": "string",
      "name": "string",
      "createdAt": "ISO8601"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100
  }
}
```

**エラー時 (4xx/5xx):**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}
```

## エラーコード一覧
| コード | HTTPステータス | 説明 |
|--------|---------------|------|
| RESOURCE_NOT_FOUND | 404 | リソースが見つからない |
| VALIDATION_ERROR | 400 | バリデーションエラー |
```


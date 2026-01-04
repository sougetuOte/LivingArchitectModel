# AUDITING フェーズ ガードレール

## Purpose

AUDITING フェーズにおいて、品質監査を体系的に実施するガードレール。

## Activation

- `.claude/current-phase.md` が `AUDITING` である
- `/auditing` コマンド実行後

## MUST（必須）

1. **体系的な監査**: チェックリストに基づく網羅的確認
2. **重要度分類**: Critical / Warning / Info
3. **3 Agents Model 適用**: 改善提案には3視点を適用
4. **根拠明示**: 問題の理由と具体的改善案を提示

## Checklists

### コード品質
- [ ] 命名が意図を表現している
- [ ] 単一責任原則を守っている
- [ ] エラーケースが網羅されている

### ドキュメント整合性
- [ ] 仕様と実装の差異がない
- [ ] ADR 決定事項が反映されている

### アーキテクチャ健全性
- [ ] 循環依存がない
- [ ] TODO/FIXME の棚卸し

## Report Template

```markdown
# 監査レポート
**対象**: [ファイル/ディレクトリ]

| 重要度 | 件数 |
|--------|------|
| Critical | X件 |
| Warning | X件 |
| Info | X件 |

**総合評価**: [A/B/C/D]
```

## References

- `docs/internal/03_QUALITY_STANDARDS.md`
- `docs/internal/06_DECISION_MAKING.md`

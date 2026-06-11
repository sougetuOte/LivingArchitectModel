---
name: project-b3-orchestration-requirements
description: B-3ゴール駆動オーケストレーション要件定義起草で確立したsanitize・構造化パターン
metadata:
  type: project
---

B-3「ゴール駆動オーケストレーション・スキル」の要件定義書を起草した（2026-06-11）。
成果物: `docs/specs/goal-driven-orchestration/requirements.md`

**Why:** 原本依頼書は gitignore（GitHub 公開リポジトリのため）。requirements.md が単独で SSOT になる必要がある。

**How to apply:** 同様の「非公開依頼書 → 公開仕様書」変換タスクでは以下の sanitize ルールを適用する:
1. 個人名 → 役職名（「PM」「プロジェクトオーナー」に置換。メモ自体にも実名を残さない）
2. 個人利用の実測逸話（「朝 X 時に制限が切れた」等） → 一般化した設計根拠のみ残す
3. 画像参照（img_*.png） → 元記事 URL に置き換える
4. Anthropic 公式の公開情報（価格・制限倍率等）は記載可

また、upstream-first 原則に従い未裏取りのプラットフォーム仕様（/goal のサブエージェント内動作等）は Open Questions に「未確認（要裏取り）」として明示した。

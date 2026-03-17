# gitleaks 統合 タスク定義

**対応仕様**: `docs/specs/gitleaks-integration-spec.md`
**対応設計**: `docs/design/gitleaks-integration-design.md`
**作成日**: 2026-03-17

---

## Wave 構成

依存関係に基づき 2 Wave で構成する。

```
Wave 1: 基盤（gitleaks_scanner.py + .gitleaks.toml + テスト）
  ↓
Wave 2: 統合（full-review Stage 1 + /ship Phase 1 + G5 更新 + ドキュメント）
```

---

## Wave 1: gitleaks ラッパー基盤

### Task 1-1: gitleaks_scanner.py 新規作成

**対応 FR**: FR-1, FR-2, FR-3, FR-4, FR-4a
**対応設計**: Section 5.2, 5.3, 5.4a
**種別**: feat
**権限等級**: SE

**完了条件**:
- [ ] `.claude/hooks/analyzers/gitleaks_scanner.py` が存在する
- [ ] `is_available()` が gitleaks バイナリの PATH 存在を判定できる
- [ ] `run_detect(project_root)` が gitleaks JSON → `list[Issue]` を返す
- [ ] `run_detect()` がプロジェクトルートの `.gitleaks.toml` を自動検出して `--config` に渡す
- [ ] `run_detect()` 未インストール時に `rule_id="gitleaks:not-installed"` の Critical Issue を返す
- [ ] `run_protect_staged()` が staged 差分の gitleaks JSON → `list[Issue]` を返す
- [ ] `run_protect_staged()` 未インストール時に空リストを返す
- [ ] `get_install_guide()` がインストールガイドメッセージを返す
- [ ] `_parse_gitleaks_json()` が全マッピング（設計 5.3）を正しく変換する
- [ ] 全 Issue の severity が `"critical"`、category が `"security"` である

### Task 1-2: .gitleaks.toml 新規作成

**対応 FR**: FR-5
**対応設計**: Section 5.7
**種別**: chore
**権限等級**: SE

**完了条件**:
- [ ] プロジェクトルートに `.gitleaks.toml` が存在する
- [ ] `.claude/hooks/analyzers/tests/fixtures/` が除外されている
- [ ] gitleaks デフォルトルールを継承している（`[extend]`）

### Task 1-3: ユニットテスト

**対応 FR**: 全 FR
**対応設計**: Section 6.1, 6.3
**種別**: test
**権限等級**: SE

**完了条件**:
- [ ] `tests/test_gitleaks_scanner.py` が存在する
- [ ] `test_is_available`（PATH あり/なし）
- [ ] `test_parse_gitleaks_json`（正常変換）
- [ ] `test_run_detect_not_installed`（not-installed Issue が返る）
- [ ] `test_run_detect_no_findings`（空リスト）
- [ ] `test_run_detect_with_findings`（Issue リスト）
- [ ] `test_run_protect_staged`（staged 差分）
- [ ] `test_issue_severity_is_critical`（全 Issue が Critical）
- [ ] `test_gitleaks_toml_allowlist`（除外パス）
- [ ] `test_get_install_guide`（URL・コマンド・G5 FAIL の影響説明が含まれる）
- [ ] subprocess.run をモック（gitleaks バイナリ不要）
- [ ] 全テスト PASS

---

## Wave 2: パイプライン統合

**実行順序**: 2-1 → 2-2 → 2-3 → 2-4（2-1 と 2-2 は同一ファイル full-review.md を変更するため順序を固定）

### Task 2-1: full-review Stage 1 統合

**対応 FR**: FR-1, FR-6
**対応設計**: Section 5.4
**種別**: feat
**権限等級**: SE（run_pipeline.py）+ PM（full-review.md）

**完了条件**:
- [ ] `run_phase0()` の末尾で `gitleaks_scanner.run_detect()` を呼び出す
- [ ] gitleaks の Issue が `Phase0Result.issues` に含まれる
- [ ] 未インストール時に not-installed Issue が含まれる（G5 FAIL を引き起こす）
- [ ] `full-review.md` の Stage 1 に Step 1.5（gitleaks）を追記
- [ ] 統合テスト: `test_run_phase0_includes_gitleaks` PASS
- [ ] 統合テスト: `test_run_phase0_without_gitleaks` PASS

### Task 2-2: full-review Stage 5 G5 更新

**対応 FR**: FR-4
**対応設計**: Section 5.6
**種別**: docs
**権限等級**: PM（full-review.md）

**完了条件**:
- [ ] `full-review.md` の G5 セキュリティチェック表からシークレット漏洩の `grep パターン` を `gitleaks` に置換
- [ ] gitleaks 未インストール時の G5 FAIL 動作が記述されている
- [ ] インストールガイド表示の指示が含まれている

### Task 2-3: /ship Phase 1 統合

**対応 FR**: FR-2, FR-4
**対応設計**: Section 5.5
**種別**: docs
**権限等級**: PM（ship.md）

**完了条件**:
- [ ] `ship.md` の Phase 1 に gitleaks protect --staged ステップを追記
- [ ] 検出時の警告表示 + ユーザー判断フローが記述されている
- [ ] 未インストール時の WARNING + コミット許可が記述されている

### Task 2-4: ドキュメント更新

**対応 FR**: FR-6
**対応設計**: Section 7
**種別**: docs
**権限等級**: PM（scalable-code-review-spec.md）

**完了条件**:
- [ ] `scalable-code-review-spec.md` FR-7e に gitleaks 統合への言及を追記
- [ ] `gitleaks-integration-spec.md` のステータスを approved に更新
- [ ] `gitleaks-integration-design.md` のステータスを approved に更新

---

## トレーサビリティ

| FR | Task |
|----|------|
| FR-1（full-review detect） | 1-1, 2-1 |
| FR-2（/ship protect） | 1-1, 2-3 |
| FR-3（クロスプラットフォーム） | 1-1（gitleaks 自体が対応） |
| FR-4（未インストール時） | 1-1, 2-1, 2-2, 2-3 |
| FR-4a（インストールガイド） | 1-1, 2-2 |
| FR-5（設定ファイル） | 1-2 |
| FR-6（FR-7e 統合） | 2-1, 2-4 |

| Task | FR |
|------|----|
| 1-1 | FR-1, FR-2, FR-3, FR-4, FR-4a |
| 1-2 | FR-5 |
| 1-3 | 全 FR（テスト） |
| 2-1 | FR-1, FR-4, FR-6 |
| 2-2 | FR-4 |
| 2-3 | FR-2, FR-4 |
| 2-4 | FR-6 |

孤児タスク: なし
未カバー FR: なし

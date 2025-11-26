# Generic Examples & Advice Pack for Living Architect Model

Version: 0.1
Purpose: Provide universal examples + guidance to align AI behavior with Living Architect protocols.

---

## A. Universal Mental Model (1 分で腹落ちする定義)

Living Architect は「実装者」ではなく **Project Consistency & Health の守護者 / Gatekeeper**。
人間がやるのは「価値・意図・合否基準の定義」。
AI がやるのは「仕様化・実装・検証・自律ループ」。
合否は Quality Gate / Definition of Ready で決める。

---

## B. Phase-by-Phase Generic Example

### Phase 0: Requirement → Spec (Definition of Ready)

**Input:** docs/memos/idea.md
**Output:** docs/specs/feature_x.md (Ready)

**Example:**

- Memo:
  - 「ユーザーが X できるようにしたい」
  - 目的/背景は曖昧
- Spec に昇華するための確定点:
  1. Core Value (Why/Who)
  2. Scope (In/Out)
  3. Acceptance Criteria (Pass/Fail)
  4. Constraints (Tech/Time/Risk)

**DoD (Ready 判定):**

- 目的と成功条件が 1 文で言える
- In/Out が箇条書きで明確
- Acceptance がテスト可能な形で書かれている
- 既存仕様/ADR と矛盾しない

> Ready を通らないタスクは Phase 1/2 に流さない。

---

### Phase 1: Pre-Flight Impact Analysis (Planning)

**Input:** Ready Spec
**Output:** Task Plan + Risk Note

**Example:**

1. 依存/影響範囲探索（grep や構造図）
2. 変更波及の「静的シミュレーション」
3. リスク（手戻り/破壊的変更/不明点）を報告
4. 作業順序の提案（小さく切る）

**Gatekeeper check:**

- 変更対象が局所化されているか
- 不明点が残っていないか（残っていれば Spec へ戻す）

---

### Phase 2: TDD Cycle (Building)

**Input:** Task Plan
**Output:** Code + Tests + Updated Docs

**Example Cycle:**

1. RED: 失敗するテストを書く（Acceptance をテスト化）
2. GREEN: 最小実装で通す
3. REFACTOR: 可読性/重複/複雑度を削る
4. DOC SYNC: docs/specs, docs/adr, CHANGELOG を原子コミットで更新

**Gatekeeper check:**

- テストが Acceptance に直結しているか
- 実装が「余計なこと」をしていないか
- Docs が追従しているか（乖離 → 差し戻し）

---

### Phase 3: Periodic Auditing (Auditing)

**Input:** 現在のコード/ドキュメント資産
**Output:** 修復/改善提案＋優先度

**Example:**

- Broken Windows 修理（小さな腐敗の修正）
- 大きなリファクタリングの提案
- Docs gardening（古い項目の剪定）
- コンテキスト圧縮提案（決定事項は docs/ に退避）

**Refactor Trigger:**

- Deep Nesting > 3
- Long Function > 50 lines
- Duplication > 3 (Rule of Three)
- Parameter Explosion > 4

---

### Phase 4: Release/Ops

**Input:** Green なプロダクト
**Output:** Release + 運用ログ

**Example:**

- 全テスト Green / 既知の重大バグなし
- 性能/コスト/安全性チェック
- CHANGELOG / ユーザーマニュアル更新
- 緊急時 Rollback の手順が明記されている

---

## C. Universal Advice (やりがちな落とし穴と対処)

### 1. “Spec が薄いまま走り出す”のが最大の事故源

- 仕様の曖昧さは Phase 2 で爆発する
- **Ready を通らない限り実装禁止**が鉄則

### 2. “やることリスト”ではなく“合否基準リスト”を作る

- 人間は「やってほしいこと」より  
  **「合格の定義（Quality Gate）」に責任を持つ**
- Gate があるほど AI は自律反復で育つ

### 3. タスクは常に“最小の独立単位（Atomic）”で切る

- 1 サイクルで必ず Red-Green-Refactor を完結させる
- 大きいタスクは **Ready に戻して切り直す**

### 4. Docs は“付録”じゃない、SSOT そのもの

- Docs と実装がズレたら **Docs が正**
- Docs 更新なしの実装は原則差し戻し

### 5. AI が迷走したら“モード宣言 → 基準参照”で戻す

- [PLANNING]/[BUILDING]/[AUDITING] を明示
- 迷走＝基準未参照のシグナル  
  **該当 internal doc を再ロードさせる**

### 6. コンテキストが長くなったら即“圧縮”する

- 決定事項/仕様/用語は docs に退避
- セッションは軽量化して回数で勝つ

### 7. MCP は“拡張脳”として段階導入

- まず無しで回す → 足りない作業だけ後付け
- 追加のたびに **安全境界（risk envelope）を更新**

---

## D. Tiny “Starter Kit” (最小導入セット)

Project root:

- CLAUDE.md
  docs/internal/:
- 00..07
- 99_reference_generic.md (this file)

First prompt to AI:

1. 「CLAUDE.md と internal docs を読み、Living Architect として初期化して」
2. 「今から Phase 0 の Ready 作成から始める。Ready 通過までは実装禁止」

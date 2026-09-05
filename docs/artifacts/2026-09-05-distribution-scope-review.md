# 配布範囲の全体レビュー（E2E 着手前 / セッション 32）

**実施日**: 2026-09-05（セッション 32 / ユーザー指示「範囲自体も見直しながら全体をレビューすべき」）
**対象**: `2026-09-05-magi-migration-sequence.md` §4「次セッションへの申し送り」の 4 項目
**方法**: 文書からではなく**基質から数える**。利用者環境（plugin コンポーネント + `/lam-harness:init` が敷くもの）を
テンプレートの実在から再現し、配布物の全参照がその環境で解決するかを機械的に突合した。
計測スクリプトは使い捨て（scratchpad / リポジトリに残していない）。

> **結論を先に**: 検査は**すべて緑**である（`verify_plugin_containment.py` = OK / `verify_distributable_claims.py` = OK）。
> その緑の下で、**利用者環境で解決しない参照が 86 件 / 182 箇所**存在する。
> `rule-001` 観測 #6 と同型（**緑のまま誤った状態を報告する**）であり、
> 記録にあった「60 件超」は **managed 規範 → `docs/artifacts/` のみ**を数えた部分集合だった。

---

## 1. 配布物の全数 × 検査の有無

配布物 = `plugins/lam-harness/` 配下の全 85 ファイル（実測）。

| 領域 | 件数 | 恒等性 | 閉包 (T2) | 存在主張 (#10) | 参照解決 |
|:--|--:|:--|:--|:--|:--|
| `templates/managed/` | 36 | **T1 ✓**（rules 14 / docs-internal 10 / scripts 12） | ✓ | docs-internal のみ間接的 | **なし** |
| `skills/` | 27（15 skill） | **T3 ✓ だが 14/15**（`init` は片側のみで対象外） | ✓ | **なし** | **なし** |
| `agents/` | 12 | **T3 ✓**（12/12） | ✓ | **なし** | **なし** |
| `templates/starter/` | 8 | **なし**（設計上の意図 = 利用者の資産） | ✓ | `*.md` 5 件のみ ✓ | **なし** |
| `scripts/check-runtime.sh` | 1 | **なし**（開発側に対応物を持たない） | ✓ | なし | **なし** |
| `.claude-plugin/plugin.json` | 1 | **なし** | ✓ | なし | — |
| `hooks/` | **0（未作成）** | — | — | — | — |

### 1-a. 見つかった穴

- **`_MIRROR_AREAS`（T3）は「両側に同名で存在するトップレベル」の積集合しか見ない**。
  片側だけのエントリは意図的な差分として黙って除外される（実装 docstring に明記）。
  結果、**「配布集合そのものが正しいか」は誰も検査していない** ——
  `.claude/skills/` 16 のうち配布 14、非配布 2（`build-dashboard` / `clause-gate`）、plugin 専用 1（`init`）
  という分割は、**どこにも宣言されておらず、新しい skill を作って複製し忘れても緑のまま**である。
- **機構 #10 の走査対象は 4 glob のみ** —— root `*.md` / `docs/slides/*.html` / `docs/internal/*.md` /
  `plugins/*/templates/starter/**/*.md`。**配布面の主役である skills 27 + agents 12 + managed rules 14 は走査外**。
- **`docs/artifacts/clause-gate-ledger.md` §C の機構 #11 の行が実装より古い**。
  トリガ欄は `templates/managed/{rules,docs-internal}/` のままで、2026-09-05 に加えた
  **`scripts`（T1）と複製相（T3 = skills/agents）が載っていない**。台帳と実装のドリフト。

---

## 2. dangling 参照の全数（定義を先に決めた）

**判定軸は「パスの形」でも「LAM 固有か」でもなく、「利用者環境に実体があるか」**とした。
利用者環境 = init が敷く 44 ファイル + 明示的に作る空ディレクトリ 5 + plugin skills 15 / agents 12。

除外は理由とセットで置いた（機構 #10 の `EXCLUDED_FROM_SCAN` と同じ思想）。

| 除外 | refs | sites | 理由 |
|:--|--:|--:|:--|
| placeholder | 18 | 28 | 命名パターンの提示（`retro-` / `<feature>` / `xxx.md`）であり特定の実体を指さない |
| runtime | 25 | 73 | 実行時生成物・出力先（`.claude/logs/` / `tdd-patterns.log` / `review-state/` 等） |
| write-dest | 4 | 8 | 書込先ディレクトリ（init が `docs/artifacts/` を作る / 中身は利用者が生む） |
| py-fixture | 2 | 2 | テストフィクスチャ内の文字列定数 |

### 残り = **86 参照 / 182 箇所**

| 分類 | refs | sites | 代表例（参照元 → 解決しない先） |
|:--|--:|--:|:--|
| `docs/specs/` | 22 | **53** | `goal-driven` と 3 agents → `goal-driven-orchestration/{design,config}.md`（19 箇所）/ `gabriel.md` → `magi-v2-gabriel/` |
| `NG-other` | 13 | 37 | `release` → `.claude/tests` `docs/slides/index.html` / `full-review` → `docs/memos/` |
| `.claude/skills` `.claude/agents` | 13 | **26** | `gabriel.md` → `.claude/skills/magi/SKILL.md`（8 箇所）—— **plugin 配布下ではこのパス形式自体が成立しない** |
| `docs/artifacts/` | 13 | 22 | `update-model` → `clause-gate-ledger.md`（6）/ `hga-summon-log.md`（2） |
| `.claude/tests/` | 10 | 13 | `phase-rules.md` / `security-commands.md` / `model-delegation-prompting.md` の**検証コマンドが利用者環境に無い** |
| `docs/adr/` | 5 | 13 | `autonomous` → ADR-0005・0006 / `gabriel.md` → ADR-0007 |
| `.claude/hooks/` | 6 | 11 | `permission-levels.md` → `post-tool-use.py`（**hooks 未配布**） |
| `.claude/rules/` | 2 | 4 | `06_DECISION_MAKING.md` → `hga-summoning.md`（**非配布**）/ `quick-save` → `rule-001.md`（**非配布**） |
| `.claude/scripts/` | 2 | 3 | `subprocess-encoding-convention.md` → `dashboard/parsers/git_history.py`（**配布 12 件に含まれない**） |

参照元の上位: `subprocess-encoding-convention.md`(18) / `update-model/SKILL.md`(14) /
`08_EXECUTION_DISCIPLINE.md`(14) / `magi/SKILL.md`(9) / `gabriel.md`(8) / `autonomous/SKILL.md`(8)。

### 2-a. 新しく判明した構造的な形（記録に無かったもの）

- **plugin 配布下では `.claude/skills/...` `.claude/agents/...` `.claude/hooks/...` という
  パス形式による自己参照が原理的に壊れる**（実体は plugin キャッシュに置かれる）。
  project ファイルだったときは解決していたため、**移行が参照を壊した**類型であり、
  「LAM 固有の実体か」という既存の切り分け基準では捕まらない。**26 + 11 = 37 箇所**。
- **managed 規範が、利用者環境に存在しないテストを検証手段として処方している**（13 箇所）。
  規範だけが届き、それを検査する歯は届かない。
- **外部依存が前提として書かれている**: `autonomous` / `goal-driven` は `/goal`（LAM 配布物ではない）を
  前提条件に置く（3 ファイル / 15 箇所）。#10 の走査を skills へ広げると**これが偽陽性になる**ため、
  理由つき除外の設計が先に要る。

---

## 3. 機構 #10 に陰性対照を与える方法

**現行の欠陥**: 実在判定の基準が **LAM リポジトリ**である。`.claude/skills/` 16 と plugin skills 15 の
和集合（実測 31）に対して照合するため、「LAM には在るが利用者環境には無い」が構造的に緑になる。

**採れる形**（本レビューで実証済 / 上記 §2 の計測がそのまま原型）:

1. 判定基準を **plugin のテンプレートから導出した利用者環境**に置き換える（維持リストを持たない = 機構 #7/#11 と同型）
2. 走査対象を `plugins/**` 全体へ広げる（skills / agents / managed rules を含める）
3. 除外は理由必須（placeholder / runtime 生成物 / 書込先 / 外部依存）
4. **陰性対照**: 偽の plugin ディレクトリに解決しない参照を仕込み、**ファイル名・行番号・参照先を名指しして落ちる**ことを実測する
   （機構 #10 の `test_detects_phantom_command` / 機構 #8 と同じ作り）

**注意**: いま 182 箇所が赤なので、**そのまま入れると常時赤 = 殺される計器**になる
（`security-commands.md` §計器 の警告/ `#12` が射程を意図的に狭めた理由と同じ）。
**先に実体を減らすか、初期状態を許容リストで凍結して増加分のみ赤にする**かの判断が要る（PM 級ではない / 設計判断）。

---

## 4. 確定版シナリオ（E1〜E6）の再検証

**骨格は妥当**（継ぎ目のみを検査する / observe-before-mutate / 陰性対照つき）。**壊れていない。**
一方、**証人が自分の主張より狭い箇所が 2 つ**あり、**射程外の失敗クラスが 1 つ**ある。

| # | 内容 | 判定 |
|:-:|:--|:--|
| 1 | **E2 の主張は「managed 36 + starter 8」だが、証人は managed 3 ディレクトリの件数のみ**。**starter 8 に証人が無い** | **要修正**（証人を 1 行足す） |
| 2 | **E6 の証人は `post-tool-use.py` 1 本**。`hooks.json` は複数エントリを持ち、**輸送はエントリ単位**である。1 本の緑は他 4 本の緑を意味しない | **要判断**（継ぎ目主義との折衷 / 最低限 `pre-tool-use` の deny 経路に 1 証人） |
| 3 | **参照解決の失敗クラスに証人が無い**。E4 は「skill 本文がロードされる」までしか見ず、**その skill が指す先が存在するか**は見ない。§2 の 182 箇所は E1〜E6 を全て緑で通過する | **要追加**（機構側 = §3 で扱うのが筋。E2E に足すと毎回赤になる） |

**E1（`enabled` の値）・E3・E5・陰性対照（ステップ 14）・#45542 対策・clone ライフタイム（ステップ 15）は妥当**。
gabriel 3 巡目の修正 3 件はいずれも骨格を保ったまま証人を精緻化しており、**再設計は不要**。

---

## 5. 帰結 —— 着手順への影響

| | 判断 |
|:--|:--|
| **確定版シナリオ** | **破棄しない**。§4 の 3 点を反映すれば E2E に進める |
| **P-1（hooks 複製）** | 変更なし。ただし **`_MIRROR_AREAS` に `hooks` を足す**のは P-1 の一部として明示する |
| **新規に必要** | (i) 配布集合そのものの宣言と検査 (ii) 参照解決の機構化（§3）(iii) 台帳 §C #11 行の是正 |
| **順序** | **(iii) は即時**（記録の瑕疵）/ **(i)(ii) は E2E の前か後かが判断ポイント** —— 182 箇所は
「配布物が利用者環境で動かない」ことを意味するため、**E2E が緑でも製品としては壊れている**。
ただし E2E は**輸送**を検査するものであり、両者は独立に進められる |

> **本レビューが「射程の見積りが小さかった」を 3 回目として繰り返していないかの自己点検**:
> 本レビューは維持リストを一切持たず、**配布物 85 ファイル全件**と**利用者環境 44 ファイル + 5 ディレクトリ**を
> 実在から導出して突合した。**取りこぼしうるのは抽出側**である ——
> 参照の抽出はバッククォート span と markdown リンクに限っており、**素の本文中に書かれたパスは拾っていない**。
> したがって **86 / 182 は下界**である。この限界を明記した上で下界として扱う。

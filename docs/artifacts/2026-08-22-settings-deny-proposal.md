# `settings.json` deny 追加の提案（ユーザー手動編集用）

**起草日**: 2026-08-22
**契機**: 列挙ドリフト掃き D-4 / D-5（`docs/artifacts/2026-08-22-enumeration-drift-sweep.md` §2）
**手順**: `.claude/settings.json` は **AI が編集できない**（auto-mode のハードブロック）。**案提示（本文書） → ユーザーが手動編集 → AI が検証**の 3 手順で進める。

---

## 1. 何が問題か

`.claude/rules/security-commands.md` §コマンド許可マトリクスは以下を **Deny（実行禁止）** 列に置いているが、**`.claude/settings.json` の deny 配列（実測 16 件）に該当エントリが存在しない**。

| 条文が Deny と宣言 | 実装の現状 |
|:---|:---|
| `git push --force` / `git reset --hard` | **不在**。`Bash(git push *)` が **ask** にあるため、prefix マッチで force push は ask に吸収される。`git reset --hard` は allow / ask / deny のいずれにも該当せず既定挙動に委ねられる |
| `curl \| bash` / `wget <不明ホスト>`（外部通信 + 実行の複合） | **不在**。`Bash(curl *)` `Bash(wget *)` が **ask** にあるのみ。pipe-to-shell は ask を承認すれば通る |

**条文が「二重」と注記している点**: D-4 の行には「AutoMode soft_deny と二重」とあり、Layer 1 単独での防御を前提していない可能性がある。**本提案は Layer 1 側の穴だけを塞ぐもの**であり、AutoMode 側の挙動は未検証（実害の有無はそちらに依存する）。

---

## 2. 提案する追加（`permissions.deny` 配列へ 8 行）

```jsonc
// .claude/settings.json の permissions.deny に追記（既存 16 件はそのまま）
  "Bash(git push --force*)",
  "Bash(git push -f *)",
  "Bash(git push * --force*)",
  "Bash(git push * -f *)",
  "Bash(git reset --hard*)",
  "Bash(curl * | bash*)",
  "Bash(curl * | sh*)",
  "Bash(wget * | bash*)"
```

### 各行の根拠

| 行 | 塞ぐもの | 備考 |
|:---|:---|:---|
| `git push --force*` | `git push --force` / `--force-with-lease` | `--force-with-lease` まで拒否される。**これを許したい場合は本行を `Bash(git push --force )` の形にできないため、ask 運用に戻す判断が要る**（下記 §4 の論点 1） |
| `git push -f *` | 短縮形 | |
| `git push * --force*` / `git push * -f *` | `git push origin --force` のように**リモート名が先に来る形** | 既存 deny の `Bash(find * -delete *)` と同じ「中間 `*`」の書式を踏襲 |
| `git reset --hard*` | 作業ツリーの破壊 | `git reset --hard HEAD~1` 等 |
| `curl * \| bash*` / `curl * \| sh*` / `wget * \| bash*` | pipe-to-shell | **`wget * \| sh*` を入れていない**のは §4 の論点 2 参照 |

---

## 3. 適用後の検証（AI が実施 / 手順）

ユーザーの手動編集後、以下を AI が実行して結果を報告する。

```bash
# 1. JSON として妥当か + deny の件数と内容
python -c "import json;d=json.load(open('.claude/settings.json',encoding='utf-8'));p=d['permissions'];print(len(p['deny']));[print(' ',x) for x in p['deny']]"

# 2. 条文（マトリクス）との突合が取れているか
grep -n "git push --force\|git reset --hard\|curl | bash" .claude/rules/security-commands.md

# 3. hook 経路の回帰（settings.json 変更で hook 定義を壊していないこと）
bash .claude/scripts/py_invoke.sh -m pytest .claude/tests/hooks/test_settings_hook_portability.py -q

# 4. 全数
bash .claude/scripts/py_invoke.sh -m pytest -q
```

**実挙動の確認は AI では完結しない** —— deny が実際に発火するかは、ユーザーが対話セッションで該当コマンドを 1 つ試すのが最も確実（例: `git reset --hard` と打って拒否されるか）。

---

## 4. 判断が要る論点（ユーザーに委ねる / 本提案では決めない）

1. **`--force-with-lease` まで巻き込むか**。`git push --force*` は前方一致なので `--force-with-lease` も拒否する。安全性を優先するなら現案のまま、実用を優先するなら `Bash(git push --force )`（末尾スペース）と `Bash(git push --force-with-lease*)` を allow / ask に分ける形が要る（**ただし前者は「`--force` の直後で終わる」形しか捕まえられず、実効が薄い**）
2. **`wget * | sh*` を入れていない理由**: 提案を最小に保つため。必要なら足す
3. **ワイルドカードの信頼性**: `security-commands.md` §D4 が「Claude Code 側のワイルドカード未尊重バグ（GH #27139 / #9924 / #13077）が未解決のため、明示列挙で運用する」と記している。**中間 `*` を使う本提案は、その方針と緊張関係にある**。既存 deny に `Bash(find * -delete *)` 等の同型が既にあるため踏襲したが、**§3 の実挙動確認は特に重要**
4. **条文側も直すか**。D-6（allow の lint / format / gitleaks / py_invoke 群 10 件がマトリクス表に不在）と D-3（`mv` が条文 Ask / 実装 Deny）は**条文側の更新で解消する**。`security-commands.md` は PM 級のため、本件とまとめて 1 承認で処理するのが効率的

---

## 5. 本提案が扱わないもの

- **`wget <不明ホスト>`**: 「不明ホスト」は prefix マッチで表現できない（意味論的条件）。ask のまま残す
- **`pytest`（引数明示 or 既知パス）/ `curl <既知 URL>`**: 同様に機構化不能。条文の記述精度の問題として別途扱う
- **AutoMode soft_deny の挙動**: 本掃きでは未検証。Layer 1 の穴を塞ぐことと、AutoMode 側の防御が効いているかは独立の問題

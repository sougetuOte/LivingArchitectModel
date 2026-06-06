# hook サブプロセスのセキュリティ堅牢化（CI 展開向け）

**起票日**: 2026-06-02
**起票元**: full-review iter1（`docs/artifacts/audit-reports/2026-06-02-iter1.md` W-14 / W-15）
**権限等級**: SE
**ステータス**: **W-14 完了**（2026-06-06）/ W-15 延期

## 概要

LAM はローカル個人開発が前提のため現状で実害はないが、CI／共有環境へ展開する場合に
顕在化する2件のセキュリティ堅牢化。性質が共通（環境変数・パスの信頼境界）のため1タスクに統合。

### W-14: サブプロセスへの環境変数全継承
- 箇所: `.claude/hooks/lam-stop-hook.py:269`（`_run_g1_checker`）
- 現状: `env={**os.environ, "LAM_PROJECT_ROOT": ...}` で全環境変数を G1 checker / pytest に継承。
  `AWS_SECRET_ACCESS_KEY` 等の機密が子プロセスに全量渡る。
- 方針: `conftest.py` の `_ENV_ALLOWLIST` 方式（必要変数のみ列挙）を本番コードにも適用。

### W-15: normalize_path の symlink 未展開
- 箇所: `.claude/hooks/_hook_utils.py:95-116`（`normalize_path`）
- 現状: `p.resolve()` を呼ばず文字列比較でプロジェクト境界を判定。symlink 経由で
  `__out_of_root__` マーカーなしに project_root 外パスが SE 判定に落ちる理論的余地。
- 方針: 境界判定時に `resolve()` でシンボリックリンクを展開してから比較。
  ただし resolve() がパフォーマンス・存在しないパスの扱いに影響しうるため要検証。

## なぜローカルで実害が小さいか

- W-14: ローカルの環境変数に機密が含まれる前提が薄く、子プロセスも信頼できる pytest/checker。
- W-15: symlink を意図的に張る攻撃者が同一マシンにいる前提が非現実的。

## 完了条件

- W-14: G1 checker 起動時の env が allowlist 化され、機密変数が継承されないテストが緑。**達成 (2026-06-06)**。
- W-15: symlink 経由のパスが境界判定で正しく project_root 外と判定されるテストが緑。

## 実装記録（W-14・2026-06-06）

- `_hook_utils.py` に公開定数 `CHECKER_ENV_ALLOWLIST` と公開ヘルパー `build_allowlisted_env(extra)` を追加（Windows 必須キー SYSTEMROOT / USERPROFILE / APPDATA / PATHEXT 等を含む）。
- `lam-stop-hook.py:_run_g1_checker` の `env={**os.environ, "LAM_PROJECT_ROOT": ...}` を `env=build_allowlisted_env({"LAM_PROJECT_ROOT": ...})` に差し替え。
- 新規テスト `tests/test_lam_stop_hook_env_allowlist.py`（5 件）: 機密 env 非伝播 / LAM_PROJECT_ROOT 伝播 / PATH 伝播 / 定数存在 / ヘルパー動作。
- 検証: 685 passed（既存 680 + 新規 5・e2e マーカー含む） / ruff clean / gitleaks no leaks。
- **未着手の DRY 統合**: `.claude/hooks/tests/conftest.py:_ENV_ALLOWLIST` と `.claude/hooks/analyzers/tests/test_e2e_review.py:_ENV_ALLOWLIST`（同内容）の `CHECKER_ENV_ALLOWLIST` への統一は別タスクで保留（test 用 allowlist に本番用 Windows キーを追加することの副作用を最小化するため）。

## 参照

- セキュリティレポート: `.claude/review-state/agent-security.md`
- 監査レポート: `docs/artifacts/audit-reports/2026-06-02-iter1.md`

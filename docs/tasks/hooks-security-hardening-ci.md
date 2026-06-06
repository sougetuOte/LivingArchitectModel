# hook サブプロセスのセキュリティ堅牢化（CI 展開向け）

**起票日**: 2026-06-02
**起票元**: full-review iter1（`docs/artifacts/audit-reports/2026-06-02-iter1.md` W-14 / W-15）
**権限等級**: SE
**ステータス**: **W-14 完了** / **W-15 完了**（2026-06-06）/ **W-16 新規起票**（2026-06-06・未着手）

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

### W-16: normalize_path の相対パス traversal 素通し
- 箇所: `.claude/hooks/_hook_utils.py:126-148`（`normalize_path` の相対パス分岐）
- 起票元: 2026-06-06 MAGI 合議（`docs/artifacts/2026-06-06-magi-w15-scope.md` Atom A3）。W-15（symlink）から脅威クラスが別のため分離起票。
- 現状: 相対パス（`is_absolute()=False` かつ `/` 始まりでない）は境界判定なしで `p.as_posix()` を即返す。
  `../../etc/passwd` のような traversal は PM/SE パターン未マッチで **default SE** に素通りする理論的余地。
- 脅威クラス: symlink（物理実体の偽装）とは別系統の「相対パス構文の越境」。
- 方針（要設計）: 相対パスの `..` 越境を out_of_root 相当として捕捉する。
  ただし **良性の `..`**（`docs/../specs/x.md` 等の正規な root 内パス）を誤検知しない設計が必須。
  単純な「`..` 含有で out_of_root」では誤検知するため、正規化後に root 内へ収まるかの判定が要る。
- 留意: W-15 で「相対分岐は不変」と決定済み（相対パス素通し契約への介入が Zero-Regression リスク）。
  W-16 は相対分岐に手を入れる以上、pre-tool-use の PM/SE 照合への影響を全数検証すること。

## なぜローカルで実害が小さいか

- W-14: ローカルの環境変数に機密が含まれる前提が薄く、子プロセスも信頼できる pytest/checker。
- W-15: symlink を意図的に張る攻撃者が同一マシンにいる前提が非現実的。
- W-16: 悪意ある相対 traversal パスを自分で打つ前提が非現実的。CI／エージェント自動実行で外部由来パスを扱う場合に顕在化。

## 完了条件

- W-14: G1 checker 起動時の env が allowlist 化され、機密変数が継承されないテストが緑。**達成 (2026-06-06)**。
- W-15: symlink 経由のパスが境界判定で正しく project_root 外と判定されるテストが緑。**達成 (2026-06-06)**。
- W-16: `../../etc/passwd` 等の相対 traversal が project_root 外と判定され、かつ良性の `..`（`docs/../specs/x.md`）が誤検知されないテストが両方緑。pre-tool-use の PM/SE 照合に退行がない。

## 実装記録（W-14・2026-06-06）

- `_hook_utils.py` に公開定数 `CHECKER_ENV_ALLOWLIST` と公開ヘルパー `build_allowlisted_env(extra)` を追加（Windows 必須キー SYSTEMROOT / USERPROFILE / APPDATA / PATHEXT 等を含む）。
- `lam-stop-hook.py:_run_g1_checker` の `env={**os.environ, "LAM_PROJECT_ROOT": ...}` を `env=build_allowlisted_env({"LAM_PROJECT_ROOT": ...})` に差し替え。
- 新規テスト `tests/test_lam_stop_hook_env_allowlist.py`（5 件）: 機密 env 非伝播 / LAM_PROJECT_ROOT 伝播 / PATH 伝播 / 定数存在 / ヘルパー動作。
- 検証: 685 passed（既存 680 + 新規 5・e2e マーカー含む） / ruff clean / gitleaks no leaks。
- **未着手の DRY 統合**: `.claude/hooks/tests/conftest.py:_ENV_ALLOWLIST` と `.claude/hooks/analyzers/tests/test_e2e_review.py:_ENV_ALLOWLIST`（同内容）の `CHECKER_ENV_ALLOWLIST` への統一は別タスクで保留（test 用 allowlist に本番用 Windows キーを追加することの副作用を最小化するため）。

## 実装記録（W-15・2026-06-06 / Opus 4.8 (1M)）

- 方針 SSOT: `docs/artifacts/2026-06-06-magi-w15-scope.md`（MAGI 合議）。
- `_hook_utils.py:normalize_path` の絶対パス分岐に `resolve()` を導入（両辺 resolve・`strict=False`）。out_of_root マーカーの表示は resolve 前の生 `file_path` を維持（既存テスト互換・ログ可読性）。**相対パス分岐は不変**（素通し契約保持）。
- resolve 失敗（循環 symlink 等の `OSError`/`RuntimeError`）時は生パスにフォールバックし `sys.stderr` に WARNING を出力（握りつぶし禁止・out_of_root の厳しい側に倒れる）。
- 新規テスト 2 件（`test_hook_utils.py`）: `test_normalize_path_symlink_escapes_root`（root 内 symlink が外部を指す絶対パスを out_of_root 判定。`os.symlink` 不可環境は `pytest.skip`）/ `test_normalize_path_nonexistent_within_root`（未作成 Write 新規パスの相対化・回帰防止）。
- 検証: **687 passed**（前 685 + 新規 2・e2e 含む）/ ruff clean / 既存5テスト非退行。本環境では symlink 作成可（開発者モード）で防御を実証。
- **残課題**: W-16（相対 path traversal）は別タスクとして起票済み・未着手。

## 参照

- セキュリティレポート: `.claude/review-state/agent-security.md`
- 監査レポート: `docs/artifacts/audit-reports/2026-06-02-iter1.md`

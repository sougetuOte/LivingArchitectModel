---
name: build-dashboard
description: "LAM ダッシュボード HTML を生成し、出力パスを表示する"
version: 1.0.0
disable-model-invocation: true
---

# ダッシュボード生成

LAM プロジェクトの作業状態を可視化した単一 HTML ファイルを生成する。
データソース（SESSION_STATE.md / current-phase.md / tasks.md / git log）を読み込み、
`docs/artifacts/dashboard/dashboard.html` に出力する。

## 1. ダッシュボードをビルドする

`build_dashboard.py` を実行してダッシュボードを生成する。

```bash
python .claude/scripts/build_dashboard.py --project-root <PROJECT_ROOT>
```

`<PROJECT_ROOT>` にはプロジェクトのルートディレクトリの絶対パスを指定する。
環境変数 `LAM_PROJECT_ROOT` が設定されている場合は省略可能。

## 2. 結果を確認する

スクリプトの終了コード（returncode）を確認する。

- **returncode = 0（成功）**: 全パーサが正常完了
- **returncode = 1（部分成功）**: 一部パーサが失敗したが HTML は生成済み
- **returncode = 2（致命的エラー）**: HTML 生成が失敗

## 3. 成功時

出力パスを表示する。

```
ダッシュボードを生成しました:
  docs/artifacts/dashboard/dashboard.html
```

ブラウザで `docs/artifacts/dashboard/dashboard.html` を開いて確認できる。

## 4. 失敗・警告時

エラーメッセージを表示する。スキル自体はエラー終了しない（returncode の値に関わらず処理を続行する）。

- **returncode = 1**: 「警告: 一部データソースが読み込めませんでした」を表示し、生成済み HTML のパスを案内する
- **returncode = 2**: 「エラー: ダッシュボードの生成に失敗しました」を表示する

いずれの場合もスキルとしての終了コードは 0 とし、呼び出し元（`/quick-save` 等）の処理を継続させる。

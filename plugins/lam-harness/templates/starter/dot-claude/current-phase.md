# Current Phase

**PLANNING**

_`/lam-harness:init` により設定。承認ゲート（requirements → design → tasks）を通過するまで
BUILDING へ進まない。BUILDING へ移るときは `/lam-harness:building` を実行するか、
本ファイルの `**PLANNING**` を `**BUILDING**` に書き換える。_

<!--
書式の制約（変更するとガードが黙って死ぬ）:

- フェーズ名は行頭の ** で囲み、大文字のみ（hook は ^\*\*([A-Z]+)\*\* にマッチさせる）
- ファイル名は current-phase.md。.json で置いてはならない —— hook が読まないため、
  「フェーズ状態が存在するように見えて、フェーズ依存のガードが一切効かない」状態になる
- 既存プロジェクトへ適用した場合、初期値 PLANNING は設定ファイル変更の deny を有効にする。
  進行中の作業が deny されうる点に注意（必要なら BUILDING に切り替える）
-->

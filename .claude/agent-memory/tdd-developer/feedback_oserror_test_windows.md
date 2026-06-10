---
name: oserror-test-windows
description: Windows で write_text の OSError を誘発するテスト手法 — 同名ディレクトリを作成して PermissionError を起こす
metadata:
  type: feedback
---

書き込みを阻害する OSError テストは、書き込み対象パスと同名のディレクトリを事前に作成する
（`path.mkdir()`）と Windows で `PermissionError: [Errno 13] Permission denied` が発生する。
これは `path.write_text()` が内部で `open()` を呼び出す際、ディレクトリに対してファイルモードで
開こうとして失敗するため。

**Why:** `/dev/full` 等の Unix 手法は Windows の Git Bash 環境では使えない。

**How to apply:** OSError ハンドリングのテストで `unittest.mock.patch` を使わずに
ファイルシステム上で誘発したい場合に使用する。

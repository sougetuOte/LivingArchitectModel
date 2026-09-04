"""verify_plugin_containment.py — plugin ディレクトリの 2 つの封じ込めを検査する。

R3 機構 #11 / #12（`docs/artifacts/2026-09-04-magi-distribution-form.md` §13.5-B / HGA #29）。

## なぜ要るか

`lam-harness` 1.0.0（2026-07-02 / 別リポジトリ配置）は skills 14 件のうち **9 件が現行 LAM に
存在しない**状態で 2 か月間放置された。K4「配布集合 ⊆ 開発ロード集合」は**原則としては
書かれていたが、検査が無かったため破れても誰も気づかなかった**。

本スクリプトは K4 を原則から**テスト**に変える。

## 2 つの検査

- **T1 包含（機構 #11）**: `plugins/<plugin>/templates/managed/` 配下の各ファイルは、
  開発側の対応物と**内容が一致する**こと。検査対象は「templates ディレクトリに実在するファイル」から
  導出するため、**維持リストを持たない**（R3 機構 #7 / #10 と同型）。
- **T2 閉包（機構 #12）**: `plugins/` 配下のファイルは、**作者環境の絶対パス**と
  **配布されないディレクトリ（`docs/private/`）への参照**を含まないこと。

## T2 の射程（v1 / 意図的に狭い）

managed に分類した規範から LAM 自身の記録（`docs/artifacts/` 等）への参照は **60 件超**存在する
（2026-09-04 実測）。これを一律に禁じると検査が最初から赤で埋まり、
`.claude/rules/security-commands.md` §計器への書き込みを伴う検証 が警告する
「常時落ちる計器は殺される」型に直行する。よって v1 の射程は

1. 作者環境の絶対パス（ドライブレター / `/home/<user>/` / `/Users/<name>/` / ユーザー名リテラル）
2. `docs/private/` への参照（配布されないことが確定しているディレクトリ）

に限定する。記録への dangling 参照は別枠の既知ギャップとして
`docs/artifacts/2026-09-04-distribution-layer-classification.md` §7 が持つ。

## 使い方

    bash .claude/scripts/py_invoke.sh .claude/scripts/verify_plugin_containment.py

exit 0 = 違反なし / exit 1 = 違反あり（内容を stdout に出す）。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable, List, NamedTuple

# templates/managed/<領域> → 開発側のディレクトリ
_MANAGED_AREAS = {
    "rules": Path(".claude") / "rules",
    "docs-internal": Path("docs") / "internal",
    # 2026-09-05 追加（P2 複製相）: 配布 skills が呼ぶ scripts は配布されねばならない。
    # 3 層分類 §5 は scripts を managed と分類していたが templates への実装が未了で、
    # 利用者が /lam-harness:ship を打つと存在しない py_invoke.sh を呼んで落ちた。
    "scripts": Path(".claude") / "scripts",
}

# 作者環境の絶対パス。ドライブレターは URL スキーム（http://）と衝突するため、
# 直前が英字でないことを要求する（"https://" の "s:" は 'p' が直前なので除外される）。
_ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]"),
    re.compile(r"/home/[A-Za-z0-9_.-]+/"),
    re.compile(r"/Users/[A-Za-z0-9_.-]+/"),
)

# 配布されないディレクトリへの参照
_NON_DISTRIBUTED_REFS = (re.compile(r"docs/private/"),)

_TEXT_SUFFIXES = {".md", ".json", ".py", ".sh", ".txt", ".yaml", ".yml", ".html"}


class Violation(NamedTuple):
    check: str
    path: str
    detail: str


def _iter_text_files(root: Path) -> Iterable[Path]:
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in _TEXT_SUFFIXES:
            yield p


def _read(path: Path) -> str:
    """改行コードを正規化して読む（Windows の CRLF 変換で偽陽性を出さないため）。"""
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def check_managed_identity(repo_root: Path) -> List[Violation]:
    """T1: templates/managed 配下と開発側の内容一致を検査する。

    検査対象は templates ディレクトリの実在ファイルから導出する（維持リスト不要）。
    """
    violations: List[Violation] = []
    for plugin_dir in sorted((repo_root / "plugins").glob("*/")):
        managed_root = plugin_dir / "templates" / "managed"
        if not managed_root.is_dir():
            continue
        for area, dev_dir in _MANAGED_AREAS.items():
            area_root = managed_root / area
            if not area_root.is_dir():
                continue
            for template in _iter_text_files(area_root):
                rel = template.relative_to(area_root)
                source = repo_root / dev_dir / rel
                shown = str(template.relative_to(repo_root)).replace("\\", "/")
                if not source.is_file():
                    violations.append(
                        Violation(
                            "T1",
                            shown,
                            f"開発側に対応物がない: {dev_dir.as_posix()}/{rel.as_posix()}",
                        )
                    )
                    continue
                if _read(template) != _read(source):
                    violations.append(
                        Violation(
                            "T1",
                            shown,
                            f"開発側と内容が異なる: {dev_dir.as_posix()}/{rel.as_posix()}",
                        )
                    )
    return violations


def check_reference_closure(repo_root: Path) -> List[Violation]:
    """T2: plugins/ 配下に作者環境の絶対パス・非配布ディレクトリ参照が無いことを検査する。"""
    violations: List[Violation] = []
    plugins_root = repo_root / "plugins"
    if not plugins_root.is_dir():
        return violations
    for path in _iter_text_files(plugins_root):
        shown = str(path.relative_to(repo_root)).replace("\\", "/")
        for lineno, line in enumerate(_read(path).split("\n"), start=1):
            for pattern in _ABSOLUTE_PATH_PATTERNS:
                m = pattern.search(line)
                if m:
                    violations.append(
                        Violation(
                            "T2",
                            f"{shown}:{lineno}",
                            f"作者環境の絶対パス: {line.strip()[:90]}",
                        )
                    )
                    break
            for pattern in _NON_DISTRIBUTED_REFS:
                if pattern.search(line):
                    violations.append(
                        Violation(
                            "T2",
                            f"{shown}:{lineno}",
                            f"配布されないディレクトリへの参照: {line.strip()[:90]}",
                        )
                    )
                    break
    return violations


def verify(repo_root: Path) -> List[Violation]:
    return check_managed_identity(repo_root) + check_reference_closure(repo_root)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    violations = verify(repo_root)

    managed = sum(
        1
        for plugin_dir in (repo_root / "plugins").glob("*/")
        for _ in _iter_text_files(plugin_dir / "templates" / "managed")
        if (plugin_dir / "templates" / "managed").is_dir()
    )
    print(f"managed テンプレート: {managed} 件 を検査した")

    if not violations:
        print("OK  plugin ディレクトリは包含（T1）と閉包（T2）を満たす")
        return 0

    print(f"NG  違反 {len(violations)} 件")
    for v in violations:
        print(f"  [{v.check}] {v.path}\n        {v.detail}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

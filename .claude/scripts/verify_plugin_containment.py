"""verify_plugin_containment.py — plugin ディレクトリの 4 つの封じ込めを検査する。

R3 機構 #11 / #12（`docs/artifacts/2026-09-04-magi-distribution-form.md` §13.5-B / HGA #29）。

## なぜ要るか

`lam-harness` 1.0.0（2026-07-02 / 別リポジトリ配置）は skills 14 件のうち **9 件が現行 LAM に
存在しない**状態で 2 か月間放置された。K4「配布集合 ⊆ 開発ロード集合」は**原則としては
書かれていたが、検査が無かったため破れても誰も気づかなかった**。

本スクリプトは K4 を原則から**テスト**に変える。

## 4 つの検査

- **T1 包含（機構 #11）**: `plugins/<plugin>/templates/managed/` 配下の各ファイルは、
  開発側の対応物と**内容が一致する**こと。検査対象は「templates ディレクトリに実在するファイル」から
  導出するため、**維持リストを持たない**（R3 機構 #7 / #10 と同型）。
- **T2 閉包（機構 #12）**: `plugins/` 配下のファイルは、**作者環境の絶対パス**と
  **配布されないディレクトリ（`docs/private/`）への参照**を含まないこと。
- **T3 複製相の恒等性（2026-09-05 追加）**: LAM は plugin 移行の途中にあり、
  `skills` と `agents` は開発側 (`.claude/skills/` `.claude/agents/`) と配布側
  (`plugins/<plugin>/skills/` `plugins/<plugin>/agents/`) の**両方に実体を持つ複製相**にある。
  将来 project 側を撤去するまで両者は一致していなければならない。検査対象は
  「**両側に同名で存在するトップレベルエントリ**（skill ディレクトリ / agent ファイル）」のみから
  導出する（維持リスト不要 / T1 と同型）。**片側にしか無いエントリは意図的な差分として無視する**
  （例: 開発側のみの `build-dashboard`（非配布）/ `clause-gate`（LAM 固有）、
  plugin 側のみの `init`（plugin 専用））。誤って片側のみの存在を違反として報告すると、
  意図的な非対称を毎回赤にする「常時落ちる計器」になり検査自体が殺されるため、
  この除外は本検査の核心である。**ただしこの除外は「配布集合そのものが正しいか」を
  検査できないことを意味する**（新しい skill を複製し忘れても緑のまま /
  `docs/artifacts/2026-09-05-distribution-scope-review.md` §1-a）。
- **T4 hook 宣言の実体検査（2026-09-05 追加 / P-1）**: `plugins/<plugin>/hooks/*.json` が
  `${CLAUDE_PLUGIN_ROOT}/…` の形で名指しする実体が、plugin 内に**実在する**こと。
  hook の輸送は **hooks.json のエントリ単位**で成立するため、宣言と実体のずれは
  「**そのイベントだけが黙って発火しない**」という形で現れる。E2E の証人は 5 イベント中 2 本しか
  無い（`2026-09-05-magi-migration-sequence.md` §(A) E6）ため、残り 3 本を守るのは本検査である。
  検査対象は hooks.json の実在から導出する（維持リスト不要 / T1・T3 と同型）。

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

import json
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

# plugins/<plugin>/<領域> ↔ 開発側のディレクトリ。
# T1 の _MANAGED_AREAS とは異なり、こちらは「テンプレートの派生元」ではなく
# 「両側に実体を持つ複製相」（将来 project 側撤去まで一致を要する）。
# ディレクトリ構造が異なる（managed は完全に一方向のテンプレート、
# こちらは両側が対等な複製）ため、_MANAGED_AREAS とは別定数・別関数で扱う。
# 将来 `plugins/lam-harness/hooks/` 等が新設された場合は、ここに 1 行足すだけで
# 検査対象を拡張できる（`_MANAGED_AREAS` と同じ思想）。
_MIRROR_AREAS = {
    "skills": Path(".claude") / "skills",
    "agents": Path(".claude") / "agents",
    # 2026-09-05 追加（P-1）: hooks は複製相に入った。開発側の analyzers / checkers /
    # tests は hook の import 閉包に含まれない（実測）ため配布せず、片側のみとして無視される。
    "hooks": Path(".claude") / "hooks",
}

# hooks.json 内で plugin 実体を名指しする形（上流の公式変数 / code.claude.com/docs/en/hooks）
_PLUGIN_ROOT_REF_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)")

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


def _relative_text_files(root: Path) -> dict:
    """root 配下の text suffix ファイルを、root からの相対パス → 絶対パスの辞書として返す。

    root がディレクトリなら再帰的に列挙する（skills）。root がファイルなら
    それ自身を `{Path(root.name): root}` として返す（agents）。この統一により
    「skill はディレクトリ、agent は単一ファイル」という構造差を吸収し、
    ディレクトリ/ファイルで検査ロジックを分岐させずに済む。
    """
    if root.is_file():
        if root.suffix.lower() not in _TEXT_SUFFIXES:
            return {}
        return {Path(root.name): root}
    return {t.relative_to(root): t for t in _iter_text_files(root)}


def _iter_mirror_matches(repo_root: Path):
    """plugins/<plugin>/<領域> と開発側で**同名のトップレベルエントリ**を列挙する。

    片側にしか無いエントリ（意図的な差分）はここで既に除外されるため、
    呼び出し側（check_mirror_identity / main）が別途フィルタする必要はない。
    """
    for plugin_dir in sorted((repo_root / "plugins").glob("*/")):
        for area, dev_dir in _MIRROR_AREAS.items():
            plugin_area_root = plugin_dir / area
            dev_area_root = repo_root / dev_dir
            if not plugin_area_root.is_dir() or not dev_area_root.is_dir():
                continue
            plugin_names = {p.name: p for p in plugin_area_root.iterdir()}
            dev_names = {p.name: p for p in dev_area_root.iterdir()}
            for name in sorted(set(plugin_names) & set(dev_names)):
                yield plugin_names[name], dev_names[name]


def _compare_mirror_entry(repo_root: Path, plugin_entry: Path, dev_entry: Path) -> List[Violation]:
    """同名の複製相エントリ（skill ディレクトリ or agent ファイル）を再帰的に比較する。"""
    violations: List[Violation] = []
    plugin_map = _relative_text_files(plugin_entry)
    dev_map = _relative_text_files(dev_entry)
    for rel in sorted(set(plugin_map) | set(dev_map)):
        if rel not in dev_map:
            shown = str(plugin_map[rel].relative_to(repo_root)).replace("\\", "/")
            violations.append(
                Violation("T3", shown, "開発側に対応物がない（複製相の非対称）")
            )
        elif rel not in plugin_map:
            shown = str(dev_map[rel].relative_to(repo_root)).replace("\\", "/")
            violations.append(
                Violation("T3", shown, "plugin 側に複製されていない（複製相の非対称）")
            )
        else:
            if _read(plugin_map[rel]) != _read(dev_map[rel]):
                shown = str(plugin_map[rel].relative_to(repo_root)).replace("\\", "/")
                dev_shown = str(dev_map[rel].relative_to(repo_root)).replace("\\", "/")
                violations.append(
                    Violation("T3", shown, f"開発側と内容が異なる: {dev_shown}")
                )
    return violations


def check_mirror_identity(repo_root: Path) -> List[Violation]:
    """T3: plugin 側の複製相（skills / agents）が開発側と内容一致することを検査する。

    検査対象は「両側に同名で存在するトップレベルエントリ」から導出する
    （維持リスト不要 / T1 と同型）。片側にしか無いエントリは意図的な差分として
    無視する（モジュール冒頭の docstring §3 つの検査 参照）。
    """
    violations: List[Violation] = []
    for plugin_entry, dev_entry in _iter_mirror_matches(repo_root):
        violations.extend(_compare_mirror_entry(repo_root, plugin_entry, dev_entry))
    return violations


def _iter_hook_commands(data: dict):
    """hooks.json の (イベント名, command 文字列) を列挙する。

    構造は上流の settings.json `hooks` と同一（イベント → グループ配列 → `hooks` 配列）。
    壊れた形は握りつぶさず、呼び出し側が違反として報告できるよう空を返すに留める。
    """
    events = data.get("hooks")
    if not isinstance(events, dict):
        return
    for event, groups in events.items():
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, dict):
                continue
            for entry in group.get("hooks") or []:
                if isinstance(entry, dict) and isinstance(entry.get("command"), str):
                    yield event, entry["command"]


def check_hook_declaration(repo_root: Path) -> List[Violation]:
    """T4: hooks.json が名指しする実体が plugin 内に実在することを検査する。

    検査対象は hooks.json の実在から導出する（維持リストを持たない / T1・T3 と同型）。
    """
    violations: List[Violation] = []
    for plugin_dir in sorted((repo_root / "plugins").glob("*/")):
        hooks_dir = plugin_dir / "hooks"
        if not hooks_dir.is_dir():
            continue
        for cfg in sorted(hooks_dir.glob("*.json")):
            shown = str(cfg.relative_to(repo_root)).replace("\\", "/")
            try:
                data = json.loads(_read(cfg))
            except json.JSONDecodeError as exc:
                violations.append(Violation("T4", shown, f"JSON として読めない: {exc}"))
                continue
            if not isinstance(data, dict) or not isinstance(data.get("hooks"), dict):
                violations.append(
                    Violation("T4", shown, "`hooks` オブジェクトを持たない（1 件も発火しない）")
                )
                continue
            declared = 0
            for event, command in _iter_hook_commands(data):
                for m in _PLUGIN_ROOT_REF_RE.finditer(command):
                    declared += 1
                    target = plugin_dir / m.group(1)
                    if not target.is_file():
                        violations.append(
                            Violation(
                                "T4",
                                shown,
                                f"{event} が名指しする実体が plugin 内に無い: {m.group(1)}",
                            )
                        )
            if declared == 0:
                violations.append(
                    Violation(
                        "T4",
                        shown,
                        "${CLAUDE_PLUGIN_ROOT} 参照が 1 件も無い"
                        "（plugin 外を指していれば install 先で解決しない）",
                    )
                )
    return violations


def verify(repo_root: Path) -> List[Violation]:
    return (
        check_managed_identity(repo_root)
        + check_reference_closure(repo_root)
        + check_mirror_identity(repo_root)
        + check_hook_declaration(repo_root)
    )


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

    mirror_matched = sum(1 for _ in _iter_mirror_matches(repo_root))
    print(f"複製相（skills/agents/hooks）: {mirror_matched} 件の一致エントリを検査した")

    hook_cfgs = sum(
        1
        for plugin_dir in (repo_root / "plugins").glob("*/")
        for _ in (plugin_dir / "hooks").glob("*.json")
    )
    print(f"hook 宣言: {hook_cfgs} 件の hooks.json を検査した")

    if not violations:
        print(
            "OK  plugin ディレクトリは包含（T1）・閉包（T2）・"
            "複製相の恒等性（T3）・hook 宣言の実体（T4）を満たす"
        )
        return 0

    print(f"NG  違反 {len(violations)} 件")
    for v in violations:
        print(f"  [{v.check}] {v.path}\n        {v.detail}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

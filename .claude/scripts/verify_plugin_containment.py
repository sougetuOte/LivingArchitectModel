"""verify_plugin_containment.py — plugin ディレクトリの 5 つの封じ込めを検査する。

R3 機構 #11 / #12（`docs/artifacts/2026-09-04-magi-distribution-form.md` §13.5-B / HGA #29）。

## なぜ要るか

`lam-harness` 1.0.0（2026-07-02 / 別リポジトリ配置）は skills 14 件のうち **9 件が現行 LAM に
存在しない**状態で 2 か月間放置された。K4「配布集合 ⊆ 開発ロード集合」は**原則としては
書かれていたが、検査が無かったため破れても誰も気づかなかった**。

本スクリプトは K4 を原則から**テスト**に変える。

## 5 つの検査

- **T1 包含（機構 #11）**: `plugins/<plugin>/templates/managed/` 配下の各ファイルは、
  開発側の対応物と**内容が一致する**こと。検査対象は「templates ディレクトリに実在するファイル」から
  導出するため、**維持リストを持たない**（R3 機構 #7 / #10 と同型）。
- **T2 閉包（機構 #12）**: `plugins/` 配下のファイルは、**作者環境の絶対パス**と
  **配布されないディレクトリ（`docs/private/`）への参照**を含まないこと。
- **T3 複製相の導出一致（2026-09-05 追加 / 同日「恒等性」から改訂）**: LAM は plugin 移行の途中にあり、
  `skills` と `agents` は開発側 (`.claude/skills/` `.claude/agents/`) と配布側
  (`plugins/<plugin>/skills/` `plugins/<plugin>/agents/`) の**両方に実体を持つ複製相**にある。
  将来 project 側を撤去するまで両者は対応していなければならない。
  **判定はバイト恒等ではなく「開発側 == 導出(正本)」である**（ADR-0010 追補 2 /
  正本 = `plugins/` 側、開発側は名前空間 prefix を除去した導出物）。検査対象は
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
- **T5 正本の名前空間化（2026-09-06 追加 / Action 4a）**: 正本
  （`plugins/<plugin>/{skills,agents}` の Markdown）に **bare な agent 名参照が残っていない**こと。
  bare 参照は利用者環境で解決しない —— そして `test-runner` のように**組み込みと同名のものは、
  止まらずに別 agent が黙って動く**（2026-09-05 実測）。判定は「規則 R-A による変換が
  恒等写像であること」で表され、**codemod と検査が同一関数 `to_namespaced_agent_text` を共有する**。
  併せて「除外 (T) のフェンス内にハーネス呼び出し構文が無い」ことも検査し、除外の前提を
  主張ではなく不変条件にする。設計は `docs/artifacts/2026-09-06-magi-action4-reference-model.md`。

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

# 名前の直後に続いてよくない文字（`gabriel` が `gabriel-x` に部分一致するのを防ぐ）
_NAME_BOUNDARY = r"(?![A-Za-z0-9_-])"

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
        namespace = plugin_namespace(plugin_dir)
        agents = agent_names(plugin_dir)
        skills = skill_names(plugin_dir)
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
                expected = derive_managed_text(
                    rel, _read(source), namespace, agents, skills
                )
                if _read(template) != expected:
                    violations.append(
                        Violation(
                            "T1",
                            shown,
                            f"開発側からの導出結果と一致しない: {dev_dir.as_posix()}/{rel.as_posix()}"
                            "（`derive_managed_templates.py --write` で再生成する）",
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


def plugin_namespace(plugin_dir: Path) -> str:
    """plugin の名前空間 prefix（例 ``lam-harness:``）を manifest から導出する。

    リテラルで持たない（基質から導出する / 機構 #7・#11 と同型）。manifest が読めない場合は
    空文字を返し、変換を恒等写像に落とす —— **推測で prefix を作らない**。
    """
    manifest = plugin_dir / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        return ""
    try:
        name = json.loads(_read(manifest)).get("name")
    except json.JSONDecodeError:
        return ""
    return f"{name}:" if isinstance(name, str) and name else ""


def component_names(plugin_dir: Path) -> set:
    """名前空間が付きうるコンポーネント名の集合を、plugin の実在から導出する。

    agents はファイル名の stem、skills はディレクトリ名。**維持リストを持たない**ため、
    コンポーネントが増減しても本関数の更新義務が生じない。
    """
    names = set()
    agents_dir = plugin_dir / "agents"
    if agents_dir.is_dir():
        names |= {p.stem for p in agents_dir.glob("*.md")}
    skills_dir = plugin_dir / "skills"
    if skills_dir.is_dir():
        names |= {p.name for p in skills_dir.iterdir() if p.is_dir()}
    return names


def to_project_text(text: str, namespace: str, names: set) -> str:
    """正本（plugin 側）のテキストを、開発側（project）の形へ導出する。

    名前空間 prefix を、**基質から導出した名前集合に前置されている場合にのみ**除去する
    （`lam-harness:gabriel` → `gabriel` / `/lam-harness:ship` → `/ship`）。

    向きの根拠は ADR-0010 追補 2「**正本は、第 2 段の後に生き残る側**」。prefix 除去は
    固定文字列の削除であり**無損失**である一方、逆向き（付与）は「実行指示か概念の言及か」の
    分類を要し、**分類は導出ではない**（HGA #33 裁定 1）。
    """
    if not namespace or not names:
        return text
    # 長い名前を先に試す（`goal-driven-l2-foreman` が `goal-driven-l2` に食われないため）
    alternation = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    pattern = re.compile(re.escape(namespace) + f"({alternation})" + _NAME_BOUNDARY)
    return pattern.sub(r"\1", text)


# --- T5: 正本の agent 名の名前空間化（規則 R-A / 2026-09-06 追加）--------------------
#
# 設計は `docs/artifacts/2026-09-06-magi-action4-reference-model.md`（MAGI 2 巡 + HGA #34）。
# 要点だけ再掲する（複製しない）:
#
#   「実行参照か散文か」を判定するのをやめ、**kind と構文位置だけで決まる規則**にした。
#   agent 名は固有名詞なので**全出現を ns 化**し、除外は構文的に判定できる 3 位置のみとする。
#   読者は LLM であり、無マークの散文（`agents/quality-auditor.md` の description 内
#   「code-reviewer を使うこと」）からも tool call を組み立てるため、「マーク無し = 散文」は
#   地図を書き換えただけで領土は変わらない（HGA #34 裁定 1）。
#
# skills（一般語）は本規則の対象外。`phase="building"` / `"command": "full-review"` /
# `"mode": "autonomous"` のように**別名前空間の値**と衝突するため一律 ns 化は壊す。
# slash 形だけを T3 側で ns 化すると T1 チェーン（`.claude/rules/` 55 箇所）と配布物の中で
# 分裂するため、独立した設計判断を要する（Action 4b / 同アンカー §発見 B）。

# 除外 (T): 出力テンプレート・スキーマを格納するフェンスの情報文字列。
# 実測（2026-09-06 / フェンス内 agent 名 40 件を全数目視 = markdown 32 / json 2 / タグ無し 6）。
# **既定は ns 化**であり、新しいタグのフェンスは自動的に対象になる（安全側 = 過剰に付く方に
# 倒れ diff に出る）。ここを ns 化すると、T1 チェーンの `.claude/rules/decision-making.md`
# §Output Format と `.claude/scripts/magi_dispatch.py` の emit 文字列（**順変換が存在しない**）と
# 3 者不一致になる。
_TEMPLATE_FENCE_LANGS = {"markdown", "json"}

_FENCE_RE = re.compile(r"^\s*(?:```|~~~)\s*([A-Za-z0-9_+.-]*)")

# 除外 (D): frontmatter の `name:` は宣言であって参照ではない。ns 化すると
# `lam-harness:lam-harness:gabriel` になる（ハーネスが plugin 名を前置して登録するため）。
_NAME_DECL_RE = re.compile(r"^name:\s")

# ハーネス呼び出し構文。除外 (T) の内側にこれが現れたら、除外の前提（出力テンプレートしか
# 入っていない）が破れている。gabriel 2 巡目が「フェンスタグは実際の不変量の**代理指標**であり、
# 将来 markdown フェンス内に真の実行指示が混入すれば検出できない」と指摘したため、
# 代理を検査可能な不変条件に変えるための対。
_HARNESS_CALL_RE = re.compile(r"Agent\s*\(|subagent_type\s*=|agent\s*=\s*[\"']")


def agent_names(plugin_dir: Path) -> set:
    """agent 名の集合を plugin の実在から導出する（維持リストを持たない / T1・T3 と同型）。"""
    agents_dir = plugin_dir / "agents"
    if not agents_dir.is_dir():
        return set()
    return {p.stem for p in agents_dir.glob("*.md")}


def _frontmatter_end(lines: List[str]) -> int:
    if not lines or lines[0].strip() != "---":
        return -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return i
    return -1


_TOKEN_DELIMITERS = " \t`"


def _enclosing_token(line: str, index: int) -> str:
    """`index` を含むトークンを返す（区切りは空白とバッククォートのみ）。

    除外 (P) の判定に使う —— **その語がファイルを指しているかは、その語を含むトークンが
    パスの形をしているか（`/` を含むか）で決まる**。

    区切りにカンマを含めないのが要点である。`` `.claude/agents/{a,b,c}.md` `` のような
    **ブレース展開のパス列挙**では、カンマはパスの内側にある —— カンマを区切りにすると
    2 件目以降が「パスではない」と判定され、**ファイル列挙が名前空間化されて壊れる**
    （2026-09-06 / diff レビューが実際に検出した唯一の意味破壊）。
    """
    start = index
    while start > 0 and line[start - 1] not in _TOKEN_DELIMITERS:
        start -= 1
    end = index
    while end < len(line) and line[end] not in _TOKEN_DELIMITERS:
        end += 1
    return line[start:end]


def _template_fence_lines(text: str):
    """除外 (T) に該当するフェンスの内側の行を (行番号 1-origin, 行) で列挙する。"""
    inside = False
    lang = ""
    for i, line in enumerate(text.split("\n")):
        m = _FENCE_RE.match(line)
        if m:
            if not inside:
                lang = m.group(1).lower()
            inside = not inside
            continue
        if inside and lang in _TEMPLATE_FENCE_LANGS:
            yield i + 1, line


def to_namespaced_agent_text(text: str, namespace: str, names: set) -> str:
    """正本テキストの agent 名参照を名前空間つきへ変換する（規則 R-A）。

    **codemod と検査はこの同一関数を使う**（別実装にすると両者がドリフトする /
    `to_project_text` を生成器と T3 検査が共有しているのと同じ思想）。検査は
    「この変換が恒等写像であること」= 変換すべき箇所が残っていないこと、で表される。
    """
    if not namespace or not names:
        return text
    alternation = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    # 直前が英数字・`_`・`-`・`:`・`/` でないこと。`:` は既に ns 付きのものを、
    # `/` は `agents/<name>` のパス文脈（除外 (P)）を、それぞれ境界だけで弾く。
    pattern = re.compile(r"(?<![A-Za-z0-9_:/-])(" + alternation + r")" + _NAME_BOUNDARY)

    lines = text.split("\n")
    fm_end = _frontmatter_end(lines)
    out = []
    inside = False
    lang = ""
    for i, line in enumerate(lines):
        m = _FENCE_RE.match(line)
        if m:
            if not inside:
                lang = m.group(1).lower()
            inside = not inside
            out.append(line)
            continue
        if inside and lang in _TEMPLATE_FENCE_LANGS:
            out.append(line)  # 除外 (T)
            continue
        if i <= fm_end and _NAME_DECL_RE.match(line):
            out.append(line)  # 除外 (D)
            continue

        def _sub(mm, _line=line):
            # 除外 (P): その語が**ファイルを指している**なら参照ではない。判定は 2 つ。
            if _line[mm.end():].startswith(".md"):
                return mm.group(0)
            if "/" in _enclosing_token(_line, mm.start()):
                return mm.group(0)
            return namespace + mm.group(0)

        out.append(pattern.sub(_sub, line))
    return "\n".join(out)


# --- 規則 R-S: skill 参照の名前空間化（Action 4b / 2026-09-06）----------------------
#
# **skill 名は一般語であり、agent 名（固有名詞）と同じ規則を当てると壊れる** ——
# 実測で `phase="building"` / `"command": "full-review"` / `"mode": "autonomous"` という
# **別名前空間の値**が存在する。そこで R-S は「**ハーネスの起動構文にある出現のみ**」を対象とする。
#
# slash は著者が発明したマークではなく**ハーネス自身の起動文法**であり、
# 「読者がそれで解決する唯一の signal」という条件を満たす（RFC 1946 の設計と同型）。
# 置換候補 125 箇所を全数レビューし、誤爆 0 を実測した（2026-09-06）。
#
# **bare は「短縮形」ではない。** 名前空間を省くと、利用者環境に同名の personal / project skill が
# あればそちらが起動する（`templates/starter/CLAUDE.md`）。Ansible の `ansible.legacy.copy` と
# 同型であり、この変換は**意味を変える**（だからこそ配布物には名前空間つきが正しい）。

def skill_names(plugin_dir: Path) -> set:
    """skill 名の集合を plugin の実在から導出する（維持リストを持たない）。"""
    skills_dir = plugin_dir / "skills"
    if not skills_dir.is_dir():
        return set()
    return {p.name for p in skills_dir.iterdir() if p.is_dir()}


def to_namespaced_skill_text(text: str, namespace: str, names: set) -> str:
    """skill のハーネス起動構文を名前空間つきへ変換する（規則 R-S）。

    対象は slash 形 `/<name>` と `Skill(skill="<name>")` のみ。**slash の無い bare は
    概念の言及と定義し、対象外とする**。除外 (T)（言語タグ `markdown` / `json` のフェンス内 =
    出力テンプレート・スキーマ）は R-A と共通。
    """
    if not namespace or not names:
        return text
    alternation = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    # 直前が英数字・`_`・`-`・`/` でない `/`。既に `/<ns>:<name>` の形は name の直前が `:` なので当たらない
    slash_re = re.compile(r"(?<![A-Za-z0-9_/-])/(" + alternation + r")(?![A-Za-z0-9_:-])")
    call_re = re.compile(r"(?<=skill=[\"'])(" + alternation + r")(?=[\"'])")

    out = []
    inside = False
    lang = ""
    for line in text.split("\n"):
        m = _FENCE_RE.match(line)
        if m:
            if not inside:
                lang = m.group(1).lower()
            inside = not inside
            out.append(line)
            continue
        if inside and lang in _TEMPLATE_FENCE_LANGS:
            out.append(line)  # 除外 (T)
            continue
        line = slash_re.sub(lambda mm: "/" + namespace + mm.group(1), line)
        line = call_re.sub(lambda mm: namespace + mm.group(1), line)
        out.append(line)
    return "\n".join(out)


def to_distributed_text(text: str, namespace: str, agents: set, skills: set) -> str:
    """配布される側のテキストを導出する（規則 R-A ∘ R-S）。

    **ADR-0010 追補 3**: 不変条件は「**配布される側**に bare の実行参照が残っていないこと」。
    T3 では配布側 = 正本（`plugins/`）なので正本に直接適用し、T1 では配布側 = 派生
    （`templates/managed/`）なので生成時に適用する。
    """
    return to_namespaced_skill_text(
        to_namespaced_agent_text(text, namespace, agents), namespace, skills
    )


def derive_managed_text(rel: Path, text: str, namespace: str, agents: set, skills: set) -> str:
    """T1 の導出: `.claude/` 正本 → `templates/managed/` 派生。

    **Markdown だけを変換する。** `.py` / `.sh` はそのまま複製する —— 実行されるコードであり、
    コメントの読者は開発者であってハーネスでもモデルでもない（4a の hooks 除外と同じ理由 /
    実測: managed scripts の slash 形は docstring・コメントの 7 箇所のみ）。
    """
    if rel.suffix.lower() != ".md":
        return text
    return to_distributed_text(text, namespace, agents, skills)


def invert_managed_text(rel: Path, text: str, namespace: str, every: set) -> str:
    """`derive_managed_text` の逆写像（往復恒等の検証に使う）。

    **`.md` 以外に `to_project_text` を当ててはならない。** 導出が恒等写像である領域に
    prefix 除去を当てると、**もともと名前空間つきで書かれていた記述まで剥がしてしまう** ——
    実測: `.claude/scripts/verify_distributable_claims.py` のコメントは
    `/lam-harness:init` の形を**意図的に**持つ（正規表現が `/lam-harness` で切れる件の説明）。
    本関数を素朴に `to_project_text` 一本にすると、この 1 件で往復恒等が偽陽性で落ちる
    （2026-09-06 / 陰性対照テストが実際に検出した）。
    """
    if rel.suffix.lower() != ".md":
        return text
    return to_project_text(text, namespace, every)


def check_source_namespacing(repo_root: Path) -> List[Violation]:
    """T5: 正本（`plugins/<plugin>/{skills,agents}` の Markdown）に bare な agent 名が無いこと。

    射程が Markdown のみであるのは、**モデルが読む文書**が対象だからである。
    `hooks/*.py` は実行されるコードで、コメントの読者は開発者であってハーネスでもモデルでもない
    （実測: agent 名の出現は過去の合議に言及する散文コメント 1 件 / 実行参照 0）。
    """
    violations: List[Violation] = []
    for plugin_dir in sorted((repo_root / "plugins").glob("*/")):
        namespace = plugin_namespace(plugin_dir)
        names = agent_names(plugin_dir)
        skills = skill_names(plugin_dir)
        if not namespace or not names:
            continue
        for area in ("skills", "agents"):
            root = plugin_dir / area
            if not root.is_dir():
                continue
            for path in _iter_text_files(root):
                if path.suffix.lower() != ".md":
                    continue
                shown = path.relative_to(repo_root).as_posix()
                text = _read(path)
                if to_namespaced_agent_text(text, namespace, names) != text:
                    violations.append(
                        Violation(
                            "T5",
                            shown,
                            "bare な agent 名参照が残っている"
                            "（規則 R-A / 利用者環境では解決しないか、別 agent が黙って動く）",
                        )
                    )
                if to_namespaced_skill_text(text, namespace, skills) != text:
                    violations.append(
                        Violation(
                            "T5",
                            shown,
                            "bare な skill 起動参照が残っている"
                            "（規則 R-S / 利用者環境では同名の personal / project skill が起動しうる）",
                        )
                    )
                for lineno, line in _template_fence_lines(text):
                    if _HARNESS_CALL_RE.search(line):
                        violations.append(
                            Violation(
                                "T5",
                                f"{shown}:{lineno}",
                                "出力テンプレート用フェンス（markdown/json）の内側に"
                                "ハーネス呼び出し構文がある（除外 (T) の前提が破れている）",
                            )
                        )
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
                yield plugin_dir, plugin_names[name], dev_names[name]


def _compare_mirror_entry(
    repo_root: Path, plugin_dir: Path, plugin_entry: Path, dev_entry: Path
) -> List[Violation]:
    """同名の複製相エントリ（skill ディレクトリ or agent ファイル）を再帰的に比較する。

    比較は**バイト恒等ではなく「派生 == 導出(正本)」**である（ADR-0010 追補 2）。
    """
    namespace = plugin_namespace(plugin_dir)
    names = component_names(plugin_dir)
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
            expected = to_project_text(_read(plugin_map[rel]), namespace, names)
            if _read(dev_map[rel]) != expected:
                shown = str(plugin_map[rel].relative_to(repo_root)).replace("\\", "/")
                dev_shown = str(dev_map[rel].relative_to(repo_root)).replace("\\", "/")
                violations.append(
                    Violation(
                        "T3",
                        shown,
                        f"開発側が正本からの導出結果と異なる: {dev_shown}"
                        "（`derive_project_copies.py --write` で再生成する）",
                    )
                )
    return violations


def check_mirror_identity(repo_root: Path) -> List[Violation]:
    """T3: 開発側の複製相（skills / agents / hooks）が、**正本からの導出結果と一致する**ことを検査する。

    検査対象は「両側に同名で存在するトップレベルエントリ」から導出する
    （維持リスト不要 / T1 と同型）。片側にしか無いエントリは意図的な差分として
    無視する（モジュール冒頭の docstring 参照）。
    """
    violations: List[Violation] = []
    for plugin_dir, plugin_entry, dev_entry in _iter_mirror_matches(repo_root):
        violations.extend(
            _compare_mirror_entry(repo_root, plugin_dir, plugin_entry, dev_entry)
        )
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
        + check_source_namespacing(repo_root)
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
            "OK  plugin ディレクトリは包含（T1）・閉包（T2）・複製相の導出一致（T3）・"
            "hook 宣言の実体（T4）・正本の名前空間化（T5）を満たす"
        )
        return 0

    print(f"NG  違反 {len(violations)} 件")
    for v in violations:
        print(f"  [{v.check}] {v.path}\n        {v.detail}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

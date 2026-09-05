"""T5 = 正本の名前空間化（規則 R-A）のテスト（2026-09-06 / セッション 34 / Action 4a）.

**なぜ要るか**: plugin 由来の agent は `subagent_type` で必ず名前空間つきでしか解決しない。
正本に bare 名が残ると、利用者環境で `not found` で止まるか —— `test-runner` のように
**組み込みと同名のものは止まらずに別 agent が黙って動く**（2026-09-05 実測）。

設計（分類をやめ、kind と構文位置だけで決まる規則にした経緯）は
`docs/artifacts/2026-09-06-magi-action4-reference-model.md`（MAGI 2 巡 + HGA #34）。

**陰性対照を含む** —— 「落ちない検査」は計器として無価値である（機構 #10 と同じ構え）。
とくに gabriel 2 巡目が「除外 (T) はフェンスタグを実際の不変量の**代理指標**として使っており、
markdown フェンス内に真の実行指示が混入しても検出できない」と指摘したため、
**その混入が実際に赤くなること**を対照として固定する。
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from verify_plugin_containment import (  # noqa: E402
    agent_names,
    check_source_namespacing,
    component_names,
    plugin_namespace,
    to_namespaced_agent_text,
    to_project_text,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_DIR = REPO_ROOT / "plugins" / "lam-harness"

NS = "lam-harness:"
NAMES = {"gabriel", "quality-auditor", "code-reviewer", "test-runner", "goal-driven-l3-executor"}


def _ns(text: str) -> str:
    return to_namespaced_agent_text(text, NS, NAMES)


# --- 規則 R-A の本体 ----------------------------------------------------------------


def test_bare_prose_mention_is_namespaced():
    """散文の言及も変換する。読者は LLM であり、無マークの散文からも tool call を組み立てる。"""
    assert _ns("1 観点）には code-reviewer を使うこと。") == (
        "1 観点）には lam-harness:code-reviewer を使うこと。"
    )


def test_inline_code_and_call_syntax_are_namespaced():
    assert _ns("`subagent_type=gabriel` を起動する") == "`subagent_type=lam-harness:gabriel` を起動する"


def test_already_namespaced_is_untouched():
    """二重接頭辞を作らない。"""
    assert _ns("lam-harness:gabriel") == "lam-harness:gabriel"


def test_partial_word_is_not_matched():
    assert _ns("gabriel-x と gabrielle") == "gabriel-x と gabrielle"


def test_transform_is_idempotent():
    src = "gabriel を quality-auditor と併用する"
    assert _ns(_ns(src)) == _ns(src)


# --- 除外 3 位置（構文だけで決まる / 1 件ずつの判断を含まない）----------------------


def test_exclusion_d_frontmatter_name_declaration():
    """(D) `name:` は宣言。ns 化すると `lam-harness:lam-harness:gabriel` になる。"""
    src = "---\nname: gabriel\ndescription: gabriel が検証する\n---\n本文で gabriel を起動する\n"
    out = _ns(src)
    assert "name: gabriel\n" in out
    assert "description: lam-harness:gabriel が検証する" in out
    assert "本文で lam-harness:gabriel を起動する" in out


def test_exclusion_p_filename_context():
    """(P) その語がファイルを指しているなら参照ではない。"""
    assert _ns("`gabriel.md` を読む") == "`gabriel.md` を読む"
    assert _ns("agents/gabriel を読む") == "agents/gabriel を読む"


def test_exclusion_p_covers_brace_expanded_path_list():
    """(P) **ブレース展開のパス列挙**もファイルを指している。

    `.claude/agents/{a,b,c}.md` の 2 件目以降は直前が `,` であり、`/` の
    lookbehind だけでは捕まらない。**判定は「その語を含むトークンが `/` を含むか」**であり、
    区切りにカンマを含めないことでブレース内が 1 トークンに保たれる。

    これは 2026-09-06 の **diff レビューが実際に検出した唯一の意味破壊**である
    （`docs/internal/08_EXECUTION_DISCIPLINE.md` のファイル列挙が名前空間化されて壊れた）。
    集計ではなく全数目視でしか出てこない類であり、レビュー工程を必須にしている根拠でもある。
    """
    src = "`.claude/agents/{doc-writer,quality-auditor,code-reviewer}.md` — 注入先"
    assert _ns(src) == src


def test_exclusion_p_does_not_swallow_plain_prose():
    """偽陽性の対照 —— `/` を含まないトークンは通常どおり変換される。"""
    assert _ns("`subagent_type=gabriel`") == "`subagent_type=lam-harness:gabriel`"
    assert _ns("docs/specs/ を読む gabriel") == "docs/specs/ を読む lam-harness:gabriel"


def test_exclusion_t_template_fence_is_untouched():
    """(T) 出力テンプレート・スキーマのフェンスは触らない。

    ここを ns 化すると、T1 チェーン（`.claude/rules/decision-making.md` §Output Format /
    `.claude/scripts/magi_dispatch.py` の emit 文字列）と **3 者不一致**になる。
    T1 は向きが逆で順変換が存在しないため、この不一致は解消できない。
    """
    src = "```markdown\n### gabriel probe\n```\n"
    assert _ns(src) == src
    src_json = '```json\n{"description": "gabriel の総合判定"}\n```\n'
    assert _ns(src_json) == src_json


def test_untagged_fence_is_namespaced():
    """タグ無しフェンスは擬似コード・フロー図であり、対象。既定は ns 化。"""
    src = "```\nAgent(quality-auditor): 仕様ドリフト検出\n```\n"
    assert _ns(src) == "```\nAgent(lam-harness:quality-auditor): 仕様ドリフト検出\n```\n"


def test_new_fence_tag_defaults_to_namespacing():
    """除外タグ集合は `{markdown, json}` の 2 個。**未知のタグは安全側（ns 化）に倒れる**。"""
    src = "```yaml\ntools: Agent(goal-driven-l3-executor)\n```\n"
    assert "Agent(lam-harness:goal-driven-l3-executor)" in _ns(src)


# --- skills は対象外（Action 4b）-----------------------------------------------------


def test_skill_names_are_not_touched():
    """skill 名は一般語であり `phase="building"` 等の別名前空間の値と衝突する。"""
    src = '`phase="building"` に戻す / `/full-review` を回す / "command": "full-review"'
    assert to_namespaced_agent_text(src, NS, NAMES) == src


# --- 往復恒等（Zero-Regression の証明）----------------------------------------------


def test_round_trip_leaves_derived_side_unchanged():
    """変換後の正本から導出される開発側テキストが、変換前からのものと一致する。

    これが成り立つ限り `.claude/` 側は 1 バイトも変わらない。LAM 自身は plugin disabled で
    `.claude/` の実体で動いているため、これが本 codemod の Zero-Regression の中身である。
    """
    src = "gabriel と `code-reviewer` を使う\n```markdown\n### gabriel probe\n```\n"
    all_names = NAMES | {"ship", "full-review"}
    assert to_project_text(_ns(src), NS, all_names) == to_project_text(src, NS, all_names)


# --- 陰性対照 ------------------------------------------------------------------------


def _fake_plugin(tmp_path: Path, agent_body: str, skill_body: str = "") -> Path:
    root = tmp_path / "repo"
    plugin = root / "plugins" / "lam-harness"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin" / "plugin.json").write_text(
        '{"name": "lam-harness"}', encoding="utf-8"
    )
    (plugin / "agents").mkdir(parents=True)
    (plugin / "agents" / "gabriel.md").write_text(agent_body, encoding="utf-8")
    (plugin / "agents" / "quality-auditor.md").write_text(
        "---\nname: quality-auditor\n---\n", encoding="utf-8"
    )
    (plugin / "skills" / "magi").mkdir(parents=True)
    (plugin / "skills" / "magi" / "SKILL.md").write_text(skill_body, encoding="utf-8")
    return root


def test_negative_control_bare_reference_is_reported(tmp_path):
    """bare に戻したら赤くなること。落ちない検査は計器として無価値。"""
    root = _fake_plugin(tmp_path, "---\nname: gabriel\n---\nquality-auditor を起動する\n")
    violations = check_source_namespacing(root)
    assert [v.check for v in violations] == ["T5"]
    assert "gabriel.md" in violations[0].path


def test_positive_control_namespaced_reference_is_clean(tmp_path):
    """偽陽性の対照 —— 正しく ns 化されていれば緑であること。"""
    root = _fake_plugin(
        tmp_path, "---\nname: gabriel\n---\nlam-harness:quality-auditor を起動する\n"
    )
    assert check_source_namespacing(root) == []


def test_negative_control_call_syntax_inside_template_fence(tmp_path):
    """gabriel 2 巡目の指摘への対 —— 除外 (T) の内側に実行指示が混入したら赤くなること。

    フェンスタグは「そこには出力テンプレートしか入っていない」ことの**代理指標**にすぎない。
    本対照は、その前提が破れた瞬間に検査が鳴ることを固定する（= 代理を不変条件に変える）。
    """
    root = _fake_plugin(
        tmp_path,
        "---\nname: gabriel\n---\n",
        "```markdown\nsubagent_type=gabriel を起動する\n```\n",
    )
    violations = check_source_namespacing(root)
    assert any("除外 (T) の前提" in v.detail for v in violations)


def test_declaration_only_plugin_is_clean(tmp_path):
    """`name:` だけを持つ agent は違反にならない（除外 (D) の陰性対照）。"""
    root = _fake_plugin(tmp_path, "---\nname: gabriel\n---\n")
    assert check_source_namespacing(root) == []


# --- 実リポジトリへの適用（基質から導出する / 維持リストを持たないことの確認）--------


def test_real_plugin_names_are_derived_from_substrate():
    assert agent_names(PLUGIN_DIR) >= {"gabriel", "quality-auditor", "test-runner"}
    assert plugin_namespace(PLUGIN_DIR) == "lam-harness:"
    # component_names は skills も含む（導出 = to_project_text 側が使う集合）
    assert component_names(PLUGIN_DIR) > agent_names(PLUGIN_DIR)


def test_real_source_has_no_bare_agent_reference():
    """本番の正本が規則 R-A を満たすこと（再混入防止 gate）。"""
    assert check_source_namespacing(REPO_ROOT) == []


def test_frontmatter_still_parses_after_namespacing():
    """`lam-harness:` は **コロンを含む**。frontmatter が YAML として壊れていないこと。

    `description: … lam-harness:code-reviewer を使うこと。` のような plain scalar は、
    コロンの解釈次第で **値が dict になる**（= `description` が文字列でなくなる）。
    ハーネスは frontmatter を構文として読むため、ここが壊れると agent / skill が
    そもそも登録されない —— 本 codemod で唯一「静かに全部壊れる」経路であり、対照を置く。
    """
    import pytest

    yaml = pytest.importorskip("yaml")

    checked = 0
    for base in (
        REPO_ROOT / "plugins" / "lam-harness" / "agents",
        REPO_ROOT / "plugins" / "lam-harness" / "skills",
        REPO_ROOT / ".claude" / "agents",
        REPO_ROOT / ".claude" / "skills",
    ):
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            if not text.startswith("---"):
                continue
            end = text.find("\n---", 3)
            if end < 0:
                continue
            data = yaml.safe_load(text[3:end])
            shown = path.relative_to(REPO_ROOT).as_posix()
            assert isinstance(data, dict), shown
            assert isinstance(data.get("name"), str), shown
            for key, value in data.items():
                assert not isinstance(value, dict), f"{shown}: '{key}' がコロンで dict 化した"
            checked += 1
    assert checked >= 50, f"検査対象が少なすぎる（{checked} 件）= 探索の失敗を緑と誤認しないため"


# --- 規則 R-S: skill 起動参照（Action 4b / 2026-09-06）--------------------------------

SKILLS = {"ship", "full-review", "magi", "building", "retro", "quick-save"}


def _rs(text: str) -> str:
    from verify_plugin_containment import to_namespaced_skill_text

    return to_namespaced_skill_text(text, NS, SKILLS)


def test_rs_slash_form_is_namespaced():
    assert _rs("`/ship` を実行する") == "`/lam-harness:ship` を実行する"


def test_rs_skill_call_form_is_namespaced():
    assert _rs('Skill(skill="magi")') == 'Skill(skill="lam-harness:magi")'


def test_rs_leaves_values_in_other_namespaces_alone():
    """**skill 名は一般語**であり、別名前空間の値と衝突する。slash が無いものは触らない。

    実測で存在した 3 形すべてを固定する —— ここが壊れると
    `autonomous/SKILL.md` の状態遷移や `full-review` のループ状態 JSON が壊れる。
    """
    src = '`phase="building"` に戻す / `"command": "full-review"` / `"mode": "autonomous"`'
    assert _rs(src) == src


def test_rs_does_not_match_path_segments():
    """`docs/full-review/` のようなパス片は起動構文ではない（直前が `/` 以外の語）。"""
    assert _rs("docs/full-review/report.md") == "docs/full-review/report.md"


def test_rs_is_idempotent():
    once = _rs("/ship と /retro")
    assert _rs(once) == once
    assert once == "/lam-harness:ship と /lam-harness:retro"


def test_rs_template_fence_is_untouched():
    src = "```markdown\n実行: /ship\n```\n"
    assert _rs(src) == src


def test_rs_untagged_fence_is_namespaced():
    assert _rs("```\n/ship\n```\n") == "```\n/lam-harness:ship\n```\n"


def test_rs_agent_names_are_not_touched_by_rs():
    """R-S は agent 名に触れない（役割分離の陰性対照）。"""
    assert _rs("gabriel と quality-auditor") == "gabriel と quality-auditor"


def test_distributed_text_composes_both_rules():
    from verify_plugin_containment import to_distributed_text

    src = "`/ship` の後に gabriel を起動する"
    assert to_distributed_text(src, NS, NAMES, SKILLS) == (
        "`/lam-harness:ship` の後に lam-harness:gabriel を起動する"
    )


def test_real_source_has_no_bare_skill_invocation():
    """本番の正本が規則 R-S を満たすこと（再混入防止 gate / T5）。"""
    from verify_plugin_containment import to_namespaced_skill_text

    ns = plugin_namespace(PLUGIN_DIR)
    skills = {p.name for p in (PLUGIN_DIR / "skills").iterdir() if p.is_dir()}
    offenders = []
    for area in ("skills", "agents"):
        for path in sorted((PLUGIN_DIR / area).rglob("*.md")):
            text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
            if to_namespaced_skill_text(text, ns, skills) != text:
                offenders.append(path.relative_to(REPO_ROOT).as_posix())
    assert offenders == []

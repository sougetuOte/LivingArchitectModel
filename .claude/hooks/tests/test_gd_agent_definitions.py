"""test_gd_agent_definitions.py - W2-T1 エージェント定義 3 件の静的検証

対応タスク: docs/specs/goal-driven-orchestration/tasks.md W2-T1
対応仕様:
  - design.md §11（エージェント定義仕様・grader 出力 JSON スキーマ・判定不能時 escalate）
  - design.md §12（effort: default の根拠）
  - design.md §7（構造化報告スキーマ）
  - requirements.md FR-2 / FR-7 / AC-5 / AC-6 / NFR-3 / NFR-5
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# エージェントディレクトリへの絶対パス
_AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "agents"

# 各エージェント定義ファイルのパス
_L2_FOREMAN_PATH = _AGENTS_DIR / "goal-driven-l2-foreman.md"
_L3_EXECUTOR_PATH = _AGENTS_DIR / "goal-driven-l3-executor.md"
_GRADER_PATH = _AGENTS_DIR / "goal-driven-grader.md"

# config.md へのパス（nest_depth_limit 外部化参照の確認用）
_CONFIG_MD_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "docs"
    / "specs"
    / "goal-driven-orchestration"
    / "config.md"
)


def _parse_frontmatter(content: str) -> dict[str, str]:
    """フロントマター（--- ... --- の間）を key: value の辞書に変換する。

    multiline の description は最初の非空白行のみを value とする。
    YAML として完全にパースせず、シンプルな行ベースのパースを行う。

    注意: tools フィールドは文字列として返す（Agent 含有チェックは別途実施）。
    """
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    # 2 番目の "---" を探す
    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return {}

    result: dict[str, str] = {}
    current_key: str | None = None
    in_multiline = False

    for line in lines[1:end_idx]:
        # "key: value" のパターン
        if re.match(r"^[a-zA-Z_-]+\s*:", line):
            in_multiline = False
            key_match = re.match(r"^([a-zA-Z_-]+)\s*:\s*(.*)", line)
            if key_match:
                current_key = key_match.group(1)
                val = key_match.group(2).strip()
                if val == "|":
                    # multiline value（次の行から始まる）
                    in_multiline = True
                    result[current_key] = ""
                else:
                    result[current_key] = val
                    in_multiline = False
        elif in_multiline and current_key is not None:
            # multiline の continuation は最初の非空白行のみを記録
            stripped = line.strip()
            if stripped and not result[current_key]:
                result[current_key] = stripped

    return result


def _get_frontmatter_end(content: str) -> int:
    """フロントマター終端（2 番目の --- の行インデックス）を返す。存在しない場合は -1。"""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return -1
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return i
    return -1


def _get_body(content: str) -> str:
    """フロントマター以降の本文を返す。"""
    lines = content.splitlines()
    end_idx = _get_frontmatter_end(content)
    if end_idx == -1:
        return content
    return "\n".join(lines[end_idx + 1:])


def _tools_contains_agent(tools_value: str) -> bool:
    """tools フィールドの値に 'Agent' が含まれるかを判定する。

    部分文字列一致による誤判定を避けるため、以下のいずれかにマッチする場合のみ True を返す:
    - カンマ区切りリスト内の 'Agent' トークン（前後がカンマ・スペース・行頭行末）
    - 'Agent(' で始まるトークン（Agent(goal-driven-l3-executor) 等）

    例:
        "Read, Agent, Bash"          → True
        "Read, Agent(executor), Bash" → True
        "Read, Bash"                  → False
    """
    # Agent または Agent(...) のトークンを検索
    # トークンの境界: 文字列の始終端、カンマ、スペース
    pattern = r"(?:^|[\s,])Agent(?:\([^)]*\))?(?:$|[\s,])"
    return bool(re.search(pattern, tools_value))


# ---------------------------------------------------------------------------
# W2-T1 完了条件 [1]: 3 ファイルの存在確認
# ---------------------------------------------------------------------------


class TestAgentFilesExist:
    """W2-T1 完了条件 [1]: 3 ファイルがすべて .claude/agents/ に存在する。"""

    def test_l2_foreman_exists(self):
        """goal-driven-l2-foreman.md が存在すること（FR-2 / design §11）。"""
        assert _L2_FOREMAN_PATH.is_file(), (
            f"goal-driven-l2-foreman.md が存在しない: {_L2_FOREMAN_PATH}\n"
            "W2-T1 の完了条件 [1] を満たすために作成すること"
        )

    def test_l3_executor_exists(self):
        """goal-driven-l3-executor.md が存在すること（FR-7 / design §11）。"""
        assert _L3_EXECUTOR_PATH.is_file(), (
            f"goal-driven-l3-executor.md が存在しない: {_L3_EXECUTOR_PATH}\n"
            "W2-T1 の完了条件 [1] を満たすために作成すること"
        )

    def test_grader_exists(self):
        """goal-driven-grader.md が存在すること（FR-2 / NFR-3 / design §11）。"""
        assert _GRADER_PATH.is_file(), (
            f"goal-driven-grader.md が存在しない: {_GRADER_PATH}\n"
            "W2-T1 の完了条件 [1] を満たすために作成すること"
        )


# ---------------------------------------------------------------------------
# W2-T1 完了条件 [2]: l3-executor の tools に Agent が含まれないこと（AC-6）
# ---------------------------------------------------------------------------


class TestL3ExecutorToolsNoAgent:
    """W2-T1 完了条件 [2]: l3-executor の tools フィールドに Agent が含まれない（AC-6 / FR-7）。"""

    def test_l3_executor_tools_no_agent(self):
        """l3-executor の tools フィールドに Agent が含まれないこと。"""
        content = _L3_EXECUTOR_PATH.read_text(encoding="utf-8")
        fm = _parse_frontmatter(content)

        assert "tools" in fm, (
            "l3-executor のフロントマターに tools フィールドが存在しない"
        )
        tools_value = fm["tools"]
        assert not _tools_contains_agent(tools_value), (
            f"l3-executor の tools に Agent が含まれてはならない（FR-7 / AC-6）。\n"
            f"tools フィールドの値: {tools_value!r}"
        )


# ---------------------------------------------------------------------------
# W2-T1 完了条件 [2]: grader の tools に Agent が含まれないこと（AC-6）
# ---------------------------------------------------------------------------


class TestGraderToolsNoAgent:
    """W2-T1 完了条件 [2]: grader の tools フィールドに Agent が含まれない（AC-6 / FR-7）。"""

    def test_grader_tools_no_agent(self):
        """grader の tools フィールドに Agent が含まれないこと。"""
        content = _GRADER_PATH.read_text(encoding="utf-8")
        fm = _parse_frontmatter(content)

        assert "tools" in fm, (
            "grader のフロントマターに tools フィールドが存在しない"
        )
        tools_value = fm["tools"]
        assert not _tools_contains_agent(tools_value), (
            f"grader の tools に Agent が含まれてはならない（FR-7 / AC-6）。\n"
            f"tools フィールドの値: {tools_value!r}"
        )


# ---------------------------------------------------------------------------
# W2-T1 完了条件 [3]: grader の model が haiku であること
# ---------------------------------------------------------------------------


class TestGraderModelHaiku:
    """W2-T1 完了条件 [3]: grader の model が haiku になっている（design §11）。"""

    def test_grader_model_is_haiku(self):
        """grader フロントマターの model フィールドが haiku であること。"""
        content = _GRADER_PATH.read_text(encoding="utf-8")
        fm = _parse_frontmatter(content)

        assert "model" in fm, (
            "grader のフロントマターに model フィールドが存在しない"
        )
        assert fm["model"] == "haiku", (
            f"grader の model は haiku でなければならない（design §11）。\n"
            f"model フィールドの値: {fm['model']!r}"
        )


# ---------------------------------------------------------------------------
# W2-T1 完了条件 [4]: l3-executor に effort: default が含まれること（design §11 / §12）
# ---------------------------------------------------------------------------


class TestL3ExecutorEffortDefault:
    """W2-T1 完了条件 [9][=W6-T2 確認]: l3-executor のフロントマターに effort: default が含まれる（design §11 / §12）。"""

    def test_l3_executor_effort_default(self):
        """l3-executor のフロントマターに effort: default があること。"""
        content = _L3_EXECUTOR_PATH.read_text(encoding="utf-8")
        fm = _parse_frontmatter(content)

        assert "effort" in fm, (
            "l3-executor のフロントマターに effort フィールドが存在しない\n"
            "design §12 の FR-8 対応として effort: default が必要"
        )
        assert fm["effort"] == "default", (
            f"l3-executor の effort は default でなければならない（design §11 / §12）。\n"
            f"effort フィールドの値: {fm['effort']!r}"
        )


# ---------------------------------------------------------------------------
# W2-T1 完了条件 [5]: grader 本文に出力スキーマが存在すること（NFR-3 / design §11）
# ---------------------------------------------------------------------------


class TestGraderOutputSchemaInBody:
    """W2-T1 完了条件 [5]: grader 本文に出力 JSON スキーマが記載されている（NFR-3 / design §11）。"""

    def test_grader_body_has_output_schema(self):
        """grader 本文に出力スキーマ（rubric_version・overall・items フィールド）が含まれること。"""
        content = _GRADER_PATH.read_text(encoding="utf-8")
        body = _get_body(content)

        assert "rubric_version" in body, (
            "grader 本文に出力スキーマの rubric_version フィールドが含まれていない（design §11）"
        )
        assert '"overall"' in body or "overall" in body, (
            "grader 本文に出力スキーマの overall フィールドが含まれていない（design §11）"
        )
        assert '"items"' in body or "items" in body, (
            "grader 本文に出力スキーマの items フィールドが含まれていない（design §11）"
        )

    def test_grader_body_has_pass_fail_values(self):
        """grader 本文に pass / fail の値が含まれること（design §11 スキーマ要件）。"""
        content = _GRADER_PATH.read_text(encoding="utf-8")
        body = _get_body(content)

        assert '"pass"' in body or "'pass'" in body or "pass | fail" in body, (
            "grader 本文に pass 値の定義が含まれていない（design §11）"
        )
        assert '"fail"' in body or "'fail'" in body or "pass | fail" in body, (
            "grader 本文に fail 値の定義が含まれていない（design §11）"
        )


# ---------------------------------------------------------------------------
# W2-T1 完了条件 [6]: grader 本文にログ保存指示が含まれること（NFR-3 / design §11）
# ---------------------------------------------------------------------------


class TestGraderLogSaveInstruction:
    """W2-T1 完了条件 [6]: .claude/logs/gd/ へのログ保存指示が grader 本文にある（NFR-3）。"""

    def test_grader_body_has_log_save_instruction(self):
        """grader 本文に .claude/logs/gd/ へのログ保存指示が含まれること。"""
        content = _GRADER_PATH.read_text(encoding="utf-8")
        body = _get_body(content)

        assert ".claude/logs/gd/" in body, (
            "grader 本文に .claude/logs/gd/ へのログ保存指示が含まれていない（NFR-3 / design §11）"
        )


# ---------------------------------------------------------------------------
# W2-T1 完了条件 [10]: grader 本文に判定不能時の escalate 記述が含まれること（design §11）
# ---------------------------------------------------------------------------


class TestGraderEscalateInstruction:
    """W2-T1 完了条件 [10]: grader に判定不能時の escalate: true 記述がある（design §11）。"""

    def test_grader_body_has_escalate_true(self):
        """grader 本文に escalate: true の設定指示が含まれること。"""
        content = _GRADER_PATH.read_text(encoding="utf-8")
        body = _get_body(content)

        assert "escalate" in body, (
            "grader 本文に escalate の記述が含まれていない（design §11）"
        )
        # "escalate: true" または `"escalate": true` の形式を確認
        has_escalate_true = (
            "escalate: true" in body
            or '"escalate": true' in body
            or '"escalate":true' in body
        )
        assert has_escalate_true, (
            "grader 本文に escalate: true の設定指示が含まれていない（design §11）\n"
            "rubric 記述不足の場合は overall: fail ではなく escalate: true を設定すること"
        )

    def test_grader_body_has_escalate_reason(self):
        """grader 本文に escalate_reason フィールドの記述が含まれること。"""
        content = _GRADER_PATH.read_text(encoding="utf-8")
        body = _get_body(content)

        assert "escalate_reason" in body, (
            "grader 本文に escalate_reason フィールドの記述が含まれていない（design §11）"
        )

    def test_grader_body_escalate_not_overall_fail(self):
        """grader 本文に「判定不能時は overall: fail としない」旨の記述が含まれること。"""
        content = _GRADER_PATH.read_text(encoding="utf-8")
        body = _get_body(content)

        # "fail" とせず escalate を使う旨の記述があること
        has_escalate_instruction = (
            "overall" in body
            and "escalate" in body
            and ("判定不能" in body or "rubric" in body.lower())
        )
        assert has_escalate_instruction, (
            "grader 本文に「判定不能時は overall: fail ではなく escalate を使う」旨の記述が不十分\n"
            "design §11: rubric の記述が不十分で合否を判定できない場合は、\n"
            "overall: fail とせず escalate: true を設定すること"
        )


# ---------------------------------------------------------------------------
# W2-T1 完了条件 [7]: nest_depth_limit の外部化参照が 3 エージェントで一致（NFR-5）
# ---------------------------------------------------------------------------


class TestNestDepthLimitExternalReference:
    """W2-T1 完了条件 [7]: nest_depth_limit の外部化参照が 3 エージェントで一致（NFR-5）。

    design §11 / config.md: nest_depth_limit は gd-session-state.json に外部化する。
    3 エージェントが同一の外部化参照方法（config.md 参照指示）を持つこと。
    """

    def test_l2_foreman_references_config(self):
        """l2-foreman 本文に config.md または nest_depth_limit の外部化参照が含まれること。"""
        content = _L2_FOREMAN_PATH.read_text(encoding="utf-8")
        body = _get_body(content)

        has_config_ref = (
            "config.md" in body
            or "nest_depth_limit" in body
            or "gd-session-state" in body
        )
        assert has_config_ref, (
            "l2-foreman 本文に nest_depth_limit の外部化参照（config.md / gd-session-state）が含まれていない（NFR-5）"
        )

    def test_l3_executor_references_config(self):
        """l3-executor 本文に config.md または nest_depth_limit の外部化参照が含まれること。"""
        content = _L3_EXECUTOR_PATH.read_text(encoding="utf-8")
        body = _get_body(content)

        has_config_ref = (
            "config.md" in body
            or "nest_depth_limit" in body
            or "gd-session-state" in body
        )
        assert has_config_ref, (
            "l3-executor 本文に nest_depth_limit の外部化参照（config.md / gd-session-state）が含まれていない（NFR-5）"
        )

    def test_grader_references_config(self):
        """grader 本文に config.md または nest_depth_limit の外部化参照が含まれること。"""
        content = _GRADER_PATH.read_text(encoding="utf-8")
        body = _get_body(content)

        has_config_ref = (
            "config.md" in body
            or "nest_depth_limit" in body
            or "gd-session-state" in body
        )
        assert has_config_ref, (
            "grader 本文に nest_depth_limit の外部化参照（config.md / gd-session-state）が含まれていない（NFR-5）"
        )

    def test_all_agents_consistent_config_reference(self):
        """3 エージェントが同じ外部化参照先（config.md）を使用していること。

        NFR-5: nest_depth_limit の外部化参照方法が各エージェントで一致している。
        """
        l2_content = _L2_FOREMAN_PATH.read_text(encoding="utf-8")
        l3_content = _L3_EXECUTOR_PATH.read_text(encoding="utf-8")
        grader_content = _GRADER_PATH.read_text(encoding="utf-8")

        l2_body = _get_body(l2_content)
        l3_body = _get_body(l3_content)
        grader_body = _get_body(grader_content)

        # 全エージェントが config.md を参照していること
        assert "config.md" in l2_body, (
            "l2-foreman: config.md への参照が含まれていない（NFR-5 一致要件）"
        )
        assert "config.md" in l3_body, (
            "l3-executor: config.md への参照が含まれていない（NFR-5 一致要件）"
        )
        assert "config.md" in grader_body, (
            "grader: config.md への参照が含まれていない（NFR-5 一致要件）"
        )


# ---------------------------------------------------------------------------
# フロントマターパーサーの単体テスト（補助）
# ---------------------------------------------------------------------------


class TestFrontmatterParser:
    """_parse_frontmatter の単体テスト（実装の信頼性確保）。"""

    def test_parse_simple_frontmatter(self):
        """シンプルなフロントマターを正しくパースできること。"""
        content = "---\nname: test\nmodel: haiku\ntools: Read, Bash\n---\n\nbody"
        fm = _parse_frontmatter(content)
        assert fm["name"] == "test"
        assert fm["model"] == "haiku"
        assert fm["tools"] == "Read, Bash"

    def test_tools_contains_agent_simple(self):
        """'Read, Agent, Bash' は Agent 含有として検出すること。"""
        assert _tools_contains_agent("Read, Agent, Bash") is True

    def test_tools_contains_agent_with_args(self):
        """'Read, Agent(goal-driven-l3-executor), Bash' は Agent 含有として検出すること。"""
        assert _tools_contains_agent("Read, Agent(goal-driven-l3-executor), Bash") is True

    def test_tools_no_agent(self):
        """'Read, Glob, Grep, Write, Edit, Bash' は Agent 非含有として検出すること。"""
        assert _tools_contains_agent("Read, Glob, Grep, Write, Edit, Bash") is False

    def test_tools_no_agent_read_only(self):
        """'Read, Glob, Grep, Bash' は Agent 非含有として検出すること。"""
        assert _tools_contains_agent("Read, Glob, Grep, Bash") is False

"""test_parser_errors_view.py - パーサエラーサマリー表示のテスト（W2-B5-T10）

対応仕様:
  - docs/specs/b4-dashboard/design.md §9「パーサエラーの HTML 表示」
  - docs/specs/b4-dashboard/tasks.md §3 W2-B5-T10
  - docs/specs/b4-dashboard/requirements.md FR-6
  - 実装: builder.py の _render_parser_errors() メソッド および render() 内の差し込み
"""

from __future__ import annotations

import sys
from pathlib import Path

# .claude/scripts を sys.path に追加（test_v2_view.py と同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ─────────────────────────────────────────────
# テスト用ヘルパー
# ─────────────────────────────────────────────


def _make_builder(parser_errors=None):
    """テスト用 DashboardBuilder を生成するヘルパー。

    パーサを呼ばず DashboardData.parser_errors を直接指定する。
    """
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    errors = parser_errors if parser_errors is not None else []
    data = DashboardData(
        parser_errors=errors,
        generated_at="2026-06-21T12:00:00",
    )
    return DashboardBuilder(data)


# ─────────────────────────────────────────────
# 完了条件 1: parser_errors が空のとき セクションが生成されない
# ─────────────────────────────────────────────


def test_no_section_when_no_errors():
    """parser_errors が空のとき <section id="parser-errors"> が HTML に含まれないこと。

    対応完了条件: W2-B5-T10「パーサエラーがない場合、<section id="parser-errors"> が生成されない」
    設計仕様: design.md §9「DashboardData.parser_errors が 1 件以上ある場合、HTML 末尾の
              <section id="parser-errors"> にエラーサマリーを表示する」
    """
    html = _make_builder(parser_errors=[]).render()
    assert '<section id="parser-errors">' not in html, (
        "parser_errors が空のとき <section id=\"parser-errors\"> が生成されています。\n"
        "_render_parser_errors() はエラーなしのとき空文字列を返す必要があります。"
    )


def test_empty_string_from_render_parser_errors_when_no_errors():
    """_render_parser_errors() が parser_errors 空のとき空文字列を返すこと。

    render() から呼ばれる前に _render_parser_errors() 自体が空文字列を返すことを確認。
    """
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    data = DashboardData(parser_errors=[])
    builder = DashboardBuilder(data)
    result = builder._render_parser_errors()
    assert result == "", (
        f"_render_parser_errors() が空リストのとき '' を返す必要があります。実際: {result!r}"
    )


# ─────────────────────────────────────────────
# 完了条件 2: parser_errors に 1 件あるとき セクションが存在する
# ─────────────────────────────────────────────


def test_section_exists_when_one_error():
    """parser_errors に 1 件あるとき <section id="parser-errors"> が HTML に含まれること。

    対応完了条件: W2-B5-T10「パーサエラー 1 件以上の場合、セクションが生成される」
    設計仕様: design.md §9「1 件以上ある場合、HTML 末尾の <section id="parser-errors"> に表示」
    """
    html = _make_builder(parser_errors=["SessionState: ファイル不在"]).render()
    assert '<section id="parser-errors">' in html, (
        "parser_errors が 1 件あるとき <section id=\"parser-errors\"> が HTML にありません。\n"
        "_render_parser_errors() の実装を確認してください。"
    )


def test_error_message_appears_when_one_error():
    """parser_errors に 1 件あるとき、そのエラーメッセージが HTML に含まれること。"""
    html = _make_builder(parser_errors=["SessionState: ファイル不在"]).render()
    assert "SessionState: ファイル不在" in html, (
        "エラーメッセージ「SessionState: ファイル不在」が HTML に含まれていません。"
    )


def test_error_message_in_li_element_when_one_error():
    """1 件のエラーメッセージが <li> タグで囲まれること。

    対応完了条件: W2-B5-T10（完了条件）「エラー内容が <li> タグで表示される」
    """
    html = _make_builder(parser_errors=["SessionState: ファイル不在"]).render()
    assert "<li>SessionState: ファイル不在</li>" in html, (
        "エラーメッセージが <li>...</li> で囲まれていません。"
    )


# ─────────────────────────────────────────────
# 完了条件 3: parser_errors に複数件あるとき全件が <li> で列挙される
# ─────────────────────────────────────────────


def test_multiple_errors_all_appear_as_li():
    """parser_errors に複数件あるとき、全件が <li> で列挙されること。

    対応完了条件: W2-B5-T10「複数件のエラーが全て <li> で列挙される」
    """
    errors = [
        "SessionState: ファイル不在",
        "CurrentPhase: 読み込みエラー",
        "GitHistory: git コマンド失敗",
    ]
    html = _make_builder(parser_errors=errors).render()
    for error in errors:
        assert f"<li>{error}</li>" in html, (
            f"エラーメッセージ「{error}」が <li> 形式で HTML に含まれていません。"
        )


def test_multiple_errors_ul_contains_all_items():
    """複数件のエラーが <ul>...<li>...</ul> 構造内に全て含まれること。"""
    errors = [
        "SessionState: ファイル不在",
        "CurrentPhase: 読み込みエラー",
    ]
    html = _make_builder(parser_errors=errors).render()
    assert "<ul>" in html, "エラー一覧の <ul> 要素がありません。"
    assert "<li>SessionState: ファイル不在</li>" in html
    assert "<li>CurrentPhase: 読み込みエラー</li>" in html


# ─────────────────────────────────────────────
# 完了条件 4: 非エンジニア向け文言の確認
# ─────────────────────────────────────────────


def test_heading_data_error_text():
    """「データ取得エラー」という見出し文言が含まれること。

    対応完了条件: W2-B5-T10「ユーザーが見て「何かおかしい」と判断できる文言」
    設計仕様: design.md §9「非エンジニアが見ても「一部データが取得できていない」と判断できる文言」
    """
    html = _make_builder(parser_errors=["SessionState: ファイル不在"]).render()
    assert "データ取得エラー" in html, (
        "「データ取得エラー」という見出し文言が HTML に含まれていません。\n"
        "非エンジニア向けの文言を確認してください（design.md §9）。"
    )


def test_description_partial_data_error_text():
    """「一部のデータが取得できませんでした」という説明文言が含まれること。

    対応完了条件: W2-B5-T10 文言検証
    設計仕様: design.md §9「非エンジニアが見ても...判断できる文言」
    """
    html = _make_builder(parser_errors=["SessionState: ファイル不在"]).render()
    assert "一部のデータが取得できませんでした" in html, (
        "「一部のデータが取得できませんでした」という説明文が HTML に含まれていません。\n"
        "非エンジニア向けの案内文言を確認してください（design.md §9）。"
    )


def test_error_section_has_h2_heading():
    """エラーセクションに <h2> 見出しが存在すること。"""
    html = _make_builder(parser_errors=["何らかのエラー"]).render()
    # parser-errors セクション内に h2 があること
    section_start = html.find('<section id="parser-errors">')
    assert section_start != -1, "parser-errors セクションが見つかりません。"
    section_fragment = html[section_start:]
    assert "<h2>" in section_fragment, (
        "parser-errors セクション内に <h2> 見出しがありません。"
    )


# ─────────────────────────────────────────────
# 完了条件 5: render() 出力全体への差し込み確認
# ─────────────────────────────────────────────


def test_parser_errors_in_full_render_output():
    """render() の出力全体に parser-errors セクションが正しく差し込まれること。

    対応完了条件: W2-B5-T10「HTML 全体（render() 出力）に parser_errors セクションが正しく差し込まれる」
    設計仕様: design.md §8「HTML 構造」builder.py の {parser_errors_html} 差し込み箇所
    """
    html = _make_builder(parser_errors=["SessionState: ファイル不在"]).render()
    # 完全な HTML ドキュメントであること
    assert "<!DOCTYPE html>" in html, "render() が完全な HTML ドキュメントを返していません。"
    assert "</html>" in html, "HTML の閉じタグ </html> がありません。"
    # parser-errors セクションが <body> 内に存在すること
    body_start = html.find("<body>")
    body_end = html.rfind("</body>")
    assert body_start != -1 and body_end != -1, "<body> タグが見つかりません。"
    body_content = html[body_start:body_end]
    assert '<section id="parser-errors">' in body_content, (
        "parser-errors セクションが <body> 内に配置されていません。"
    )


def test_parser_errors_appears_after_v1_and_v2_sections():
    """parser-errors セクションが V-1、V-2 よりも後に配置されること。

    設計仕様: design.md §8 HTML 構造「パーサエラーサマリー（エラーがある場合のみ表示）」
    は V-4 の後に配置される。
    """
    html = _make_builder(parser_errors=["テストエラー"]).render()
    pos_v1 = html.find('<section id="v1-project-summary">')
    pos_v2 = html.find('<section id="v2-milestones">')
    pos_errors = html.find('<section id="parser-errors">')
    assert pos_v1 != -1, "v1 セクションが見つかりません。"
    assert pos_v2 != -1, "v2 セクションが見つかりません。"
    assert pos_errors != -1, "parser-errors セクションが見つかりません。"
    assert pos_v1 < pos_errors, "parser-errors が v1-project-summary より前に配置されています。"
    assert pos_v2 < pos_errors, "parser-errors が v2-milestones より前に配置されています。"


def test_no_errors_no_parser_errors_section_in_full_render():
    """parser_errors が空のとき、render() 全体で parser-errors セクションが存在しないこと。"""
    html = _make_builder(parser_errors=[]).render()
    assert '<section id="parser-errors">' not in html, (
        "エラーなしのとき render() 出力に parser-errors セクションが含まれています。"
    )


# ─────────────────────────────────────────────
# 完了条件 6: HTML エスケープの検証（特殊文字を含むエラーメッセージ）
# ─────────────────────────────────────────────


def test_special_characters_in_error_message_xss_check():
    """特殊文字（<, >, &）を含むエラーメッセージが HTML エスケープされること。

    T10 Info 修正「html.escape() 適用による防御的プログラミング」

    エスケープあり: &lt;script&gt; が含まれ、生の <script> タグは含まれない。
    """
    error_msg = "SessionState: <script>alert('xss')</script> & 不正入力"
    html = _make_builder(parser_errors=[error_msg]).render()
    # エラーセクション自体が存在することを確認
    assert '<section id="parser-errors">' in html, (
        "特殊文字を含むエラーでも parser-errors セクションが生成されるべきです。"
    )
    # エスケープされた文字列が含まれること
    assert "&lt;script&gt;" in html, (
        "<script> タグが &lt;script&gt; にエスケープされていません。"
        "html.escape() が適用されていない可能性があります。"
    )
    # 生の <script> タグが <li> 内に含まれないこと（XSS 防止）
    assert "<li>SessionState: <script>" not in html, (
        "生の <script> タグが <li> 内に含まれています。XSS 脆弱性の可能性があります。"
    )


def test_ampersand_in_error_message():
    """& を含むエラーメッセージが &amp; にエスケープされること。"""
    error_msg = "Tasks: docs/specs/b4-dashboard/tasks.md & 読み込みエラー"
    html = _make_builder(parser_errors=[error_msg]).render()
    # & がエスケープされた &amp; として含まれること
    assert "&amp;" in html, (
        "& が &amp; にエスケープされていません。"
        "html.escape() が適用されていない可能性があります。"
    )
    # エスケープ前後の文字列が含まれること
    assert "Tasks: docs/specs" in html, (
        "& を含むエラーメッセージの一部が HTML に含まれていません。"
    )
    assert "読み込みエラー" in html, (
        "& 後ろの文字列「読み込みエラー」が HTML に含まれていません。"
    )


# ─────────────────────────────────────────────
# 境界値: エラーが 1 件から複数件への変化
# ─────────────────────────────────────────────


def test_exactly_one_error_one_li():
    """エラーが 1 件のとき、parser-errors セクション内の <li> が 1 個だけ生成されること。

    Wave 6 緩和（W6-B5-T34）: <nav id="nav-landmarks"> 追加により HTML 全体の <li>
    数が増加したため、parser-errors セクションスコープ限定のカウントに変更。
    """
    html = _make_builder(parser_errors=["唯一のエラー"]).render()
    start = html.find('<section id="parser-errors">')
    assert start != -1, "parser-errors セクションが見つかりません"
    end = html.find("</section>", start) + len("</section>")
    errors_section = html[start:end]
    li_count = errors_section.count("<li>")
    assert li_count == 1, (
        f"エラー 1 件のとき parser-errors セクション内の <li> が 1 個であるべきです。実際: {li_count} 個"
    )


def test_four_errors_four_li():
    """エラーが 4 件のとき、parser-errors セクション内の <li> が 4 個生成されること。

    Wave 6 緩和（W6-B5-T34）: <nav id="nav-landmarks"> 追加により HTML 全体の <li>
    数が増加したため、parser-errors セクションスコープ限定のカウントに変更。
    """
    errors = [
        "SessionState: エラー 1",
        "CurrentPhase: エラー 2",
        "Tasks: エラー 3",
        "GitHistory: エラー 4",
    ]
    html = _make_builder(parser_errors=errors).render()
    start = html.find('<section id="parser-errors">')
    assert start != -1, "parser-errors セクションが見つかりません"
    end = html.find("</section>", start) + len("</section>")
    errors_section = html[start:end]
    li_count = errors_section.count("<li>")
    assert li_count == 4, (
        f"エラー 4 件のとき parser-errors セクション内の <li> が 4 個であるべきです。実際: {li_count} 個"
    )


# ─────────────────────────────────────────────
# 回帰テスト: V-1 / V-2 が壊れていないこと
# ─────────────────────────────────────────────


def test_v1_section_not_broken_by_parser_errors():
    """parser_errors 追加後も V-1 セクションが正常に生成されること（回帰テスト）。"""
    html = _make_builder(parser_errors=["エラー"]).render()
    assert '<section id="v1-project-summary">' in html, (
        "parser-errors セクション追加後に V-1 セクションが消えています。"
    )
    assert "LAM Dashboard" in html, "V-1 の LAM Dashboard タイトルが消えています。"


def test_v2_section_not_broken_by_parser_errors():
    """parser_errors 追加後も V-2 セクションが正常に生成されること（回帰テスト）。"""
    html = _make_builder(parser_errors=["エラー"]).render()
    assert '<section id="v2-milestones">' in html, (
        "parser-errors セクション追加後に V-2 セクションが消えています。"
    )

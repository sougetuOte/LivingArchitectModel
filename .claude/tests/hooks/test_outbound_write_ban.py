"""Outbound Write Ban の R3 二重化 TDD（HGA #24 手 2 / W1）.

`docs/private/fable-l3-protocol.md` §2 の **Outbound Write Ban**（制定 2026-07-07 /
外部リポジトリ配下への書込・編集の禁止 / 全レベル共通 **MUST NOT**）は、制定以来
**条文のみで機構を持たなかった**。当該パスへの書込は `normalize_path` で
`__out_of_root__/` マーカーが付き **PM 級（ask ダイアログ）** として扱われる。
すなわち「ユーザーが承認すれば書ける」状態であり、条文の **MUST NOT** と格差があった。
かつ違反しても誰も気づかない = **静かに潜伏する失敗クラス**（HGA #17 crux 3）。

## 2026-09-04: 機構を project 層へ移設した

配布形態を plugin へ移すにあたり、`pre-tool-use.py` は**配布物**になった。作者マシンの
絶対パスをそこに埋めたままだと、利用者は「動いているように見えて何も守らないコード」を
受け取る（**31 回のリリースで実際に配られ続けていた**）。

D-1 design §5 決定 D4 が定めた目標状態「**hook・テスト・条文がすべて配布物から外れる**」に従い:

| | 所在（2026-09-04 以降） | 配布 |
|:--|:--|:--|
| 条文 | `docs/private/fable-l3-protocol.md` §0-§2 | されない |
| 機構 | `.claude/hooks-local/outbound-write-ban.py` | されない |
| テスト | 本ファイル | されない |

hook は設定レベル間で **merge され置換されない**ため、分離しても deny の実効性は落ちない
（`exit 2` は他 hook の allow で覆せない / 公式 fail-secure）。これは不変条件
「私的規範は『追加』のみ許し『置換』を許さない」に厳密に一致する。

**gabriel G-3 が要求した境界条件テストは全て維持している**:
(a) セパレータ正規化（`\\` / `/` / 相対 / symlink）/ (b) `etc-to-alembic` の誤 deny 回帰
（allow 対を殺さない / ADR-0008 D1）。

MAGI 記録: `docs/artifacts/2026-07-27-magi-planning-hook.md`（制定時）/
`docs/artifacts/2026-09-04-magi-distribution-form.md`（移設時）。
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
_LOCAL_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks-local"
_BAN_SCRIPT = _LOCAL_HOOKS_DIR / "outbound-write-ban.py"

if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_pre_tool_use():
    return _load(_HOOKS_DIR / "pre-tool-use.py", "pre_tool_use_for_ban_test")


@pytest.fixture(scope="module")
def ptu():
    """配布物側の hook（out-of-root の PM 級判定を確認するために使う）。"""
    return _load_pre_tool_use()


@pytest.fixture(scope="module")
def owb():
    """project 層の Outbound Write Ban hook（2026-09-04 移設）。"""
    return _load(_BAN_SCRIPT, "outbound_write_ban_for_test")


@pytest.fixture
def nonexistent_phase_file(tmp_path: Path) -> Path:
    return tmp_path / "no-such-phase.md"


# --- 移設そのものの検査（2026-09-04 追加） -------------------------------------


def test_ban_script_exists():
    assert _BAN_SCRIPT.is_file(), f"project 層の機構が存在しない: {_BAN_SCRIPT}"


def test_distributed_hook_has_no_author_paths():
    """**配布物側に作者環境の絶対パスが残っていないこと**（移設の目的そのもの）。

    ここが赤くなるのは「私的ガードを配布物へ書き戻した」ときであり、
    利用者に死んだコードを配る状態への逆戻りを意味する。
    """
    source = (_HOOKS_DIR / "pre-tool-use.py").read_text(encoding="utf-8")
    for needle in ("Fable-Alembic", "etc-to-alembic", "_OUTBOUND_WRITE_BAN_ROOTS"):
        assert needle not in source, (
            f"配布される pre-tool-use.py に {needle!r} が残っている。"
            "私的ガードは .claude/hooks-local/ に置くこと（D-1 design §5 決定 D4）"
        )


def test_ban_script_is_self_contained():
    """project 層の機構が配布物側の内部実装に依存しないこと。

    `_hook_utils` を import すると、配布物が動いた瞬間に project 層が壊れる。
    """
    source = _BAN_SCRIPT.read_text(encoding="utf-8")
    # docstring では `_hook_utils` に**言及する**（なぜ依存しないかの説明）。
    # 禁じているのは実際の import であって語の出現ではない。
    for line in source.splitlines():
        stripped = line.strip()
        assert not stripped.startswith("import _hook_utils")
        assert not stripped.startswith("from _hook_utils")


# --- (a) セパレータ 4 形すべてで deny されること -------------------------------


@pytest.mark.parametrize(
    "file_path",
    [
        r"D:\work7\Fable-Alembic\knowledge\Fable行動規範.md",
        "D:/work7/Fable-Alembic/knowledge/Fable行動規範.md",
        r"D:\work7\Fable-Alembic\README.md",
        "D:/work7/Fable-Alembic/",
    ],
)
def test_outbound_write_ban_denies_all_separator_forms(owb, file_path):
    """`Fable-Alembic` 配下は表記形（絶対パス）によらず deny となる。

    gabriel G-3(a): 素朴な前方一致ではセパレータ違いを取りこぼす。
    実装は `Path.resolve()` による正規化を経ること。

    絶対パス形は `resolve_target()` が `project_root` を参照しないため、
    `_REPO_ROOT`（= 実行環境でのこのリポジトリの clone 位置）に依存しない。
    相対形（`../Fable-Alembic/...`）の検査は配置依存になるため、
    `test_outbound_write_ban_denies_relative_forms_via_synthetic_root` へ分離した
    （2026-09-05: 素の clone を別ディレクトリに置くと相対形 2 件だけが赤くなる
    ことを実測し、性質を保ったまま配置非依存な形へ書き換えた）。
    """
    reason = owb.check(file_path, _REPO_ROOT)
    assert reason is not None, f"{file_path!r} が deny されない"
    assert "Outbound Write Ban" in reason


@pytest.mark.parametrize(
    "file_path",
    [
        "../Fable-Alembic/knowledge/x.md",
        r"..\Fable-Alembic\knowledge\x.md",
    ],
)
def test_outbound_write_ban_denies_relative_forms_via_synthetic_root(owb, file_path):
    """相対形（`../Fable-Alembic/...`）もセパレータ違いによらず deny となる。

    gabriel G-3(a) の相対 traversal ケース。`resolve_target()` は非絶対パスを
    `project_root / file_path` として解決するため、相対形の判定結果は
    呼び出し時に渡す `project_root` に依存する。

    旧テストはここで `_REPO_ROOT`（実行環境でのこのリポジトリの clone 位置）を
    渡していたため、**本リポジトリが `D:/work7/Fable-Alembic` の兄弟位置に
    clone された構成でしか deny にならなかった**（配置依存）。別ディレクトリへ
    clone した素の clone では、同じ相対 traversal + セパレータ正規化という
    検査対象の性質を検証できないまま赤くなる。

    そこで `project_root` に実際の clone 位置ではなく、テスト内で組み立てた
    合成値 `D:/work7/<任意名>` を渡す。`_BAN_ROOTS` は `D:/work7/Fable-Alembic`
    に固定されている（本 hook 自体が作者環境限定 / SE 級）ため、この合成値は
    実在しなくても `Path.resolve()` が `..` を lexical に畳み込み、
    `D:/work7/Fable-Alembic/...` へ正規化される。すなわち本テストは
    「相対パスの解決に `Path.resolve()` の正規化を経ていること」だけを検査し、
    実行環境でのこのリポジトリの実配置には依存しない。
    """
    # 合成 root は `_BAN_ROOTS` から**導出する**（リテラルで持たない）。
    # 「ban root の兄弟位置」という関係そのものが本テストの前提であり、
    # リテラルで書くと `_BAN_ROOTS` の変更に追随せず関係が黙って崩れる
    # （維持リストを持たない = 機構 #7 / #11 と同型の構え）。
    synthetic_project_root = owb._BAN_ROOTS[0].parent / "_lam_outbound_ban_relative_form_probe"
    reason = owb.check(file_path, synthetic_project_root)
    assert reason is not None, f"{file_path!r} が deny されない"
    assert "Outbound Write Ban" in reason


def test_ban_is_structurally_phase_independent(owb):
    """フェーズ非依存が**構造として**保証されていること。

    条文は「全レベル共通 MUST NOT」でありフェーズに条件づけられていない。
    移設前は `_determine_by_path` の最前段で判定することで達成していたが、
    移設後は **hook がフェーズを読まない**ことで構造的に達成される。
    """
    source = _BAN_SCRIPT.read_text(encoding="utf-8")
    assert "current-phase" not in source
    assert "PLANNING" not in source
    assert "AUTONOMOUS" not in source


# --- (b) allow 対: handoff 経路を殺さないこと（ADR-0008 D1） --------------------


@pytest.mark.parametrize(
    "file_path",
    [
        r"D:\work7\etc-to-alembic\handoff\observation-2026-07-27.md",
        "D:/work7/etc-to-alembic/handoff/observation-2026-07-27.md",
        r"D:\work7\etc-to-alembic\README.md",
        "D:/work7/etc-to-alembic/",
    ],
)
def test_etc_to_alembic_is_not_denied(owb, file_path):
    """`etc-to-alembic` は deny されない（**allow 対** / ADR-0008 D1）。

    gabriel G-3(b): 実装が `"alembic"` の部分一致で書かれると、条文が明示的に
    許可した唯一の受け渡し経路を殺す。
    """
    assert owb.check(file_path, _REPO_ROOT) is None, f"{file_path!r} が誤って deny された"


@pytest.mark.parametrize(
    "file_path",
    [
        r"D:\work7\etc-to-alembic\handoff\observation-2026-07-27.md",
        r"D:\work7\Fable-Alembic\knowledge\x.md",
    ],
)
def test_out_of_root_still_asks(ptu, nonexistent_phase_file, file_path):
    """配布物側は out-of-root を **PM 級（ask）** に留める（移設後も不変）。

    「deny されない」= 素通しではない。PG 級 auto allow にしないのは、リポジトリ外
    書込を無確認で通すことが R1-I18 の「安全側維持」判断を覆すため。
    """
    level, _reason = ptu._determine_by_path(file_path, _REPO_ROOT, nonexistent_phase_file)
    assert level == "PM", f"{file_path!r} は out-of-root PM 級であるべき（level={level}）"


# --- 既存挙動の回帰（リポジトリ内は無影響） ------------------------------------


@pytest.mark.parametrize(
    ("file_path", "expected_level"),
    [
        (".claude/rules/phase-rules.md", "PM"),
        ("docs/specs/x/design.md", "PM"),
        ("docs/artifacts/x.md", "SE"),
        ("CLAUDE.md", "PM"),
    ],
)
def test_in_repo_paths_are_unaffected(
    ptu, nonexistent_phase_file, file_path, expected_level
):
    """リポジトリ内パスの判定は移設で一切変わらない（Zero-Regression）。"""
    level, _reason = ptu._determine_by_path(file_path, _REPO_ROOT, nonexistent_phase_file)
    assert level == expected_level


# --- end-to-end: hook として起動したときの終了コード ---------------------------


def _run_hook(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_BAN_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_hook_exits_2_on_banned_path():
    """`exit 2` = blocking。他 hook が allow を返しても覆せない（公式 fail-secure）。"""
    r = _run_hook({"tool_name": "Write", "tool_input": {"file_path": "D:/work7/Fable-Alembic/x.md"}})
    assert r.returncode == 2, f"returncode={r.returncode} / stderr={r.stderr}"
    payload = json.loads(r.stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_hook_exits_0_on_allowed_path():
    r = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "D:/work7/etc-to-alembic/handoff/a.md"}}
    )
    assert r.returncode == 0, f"returncode={r.returncode} / stderr={r.stderr}"


def test_hook_exits_0_without_file_path():
    """`file_path` を持たない tool（Bash 等）では素通しする。

    Bash 経由の書込は本機構の射程外である（対処は Layer 1 = `permissions.deny` の領分）。
    """
    assert _run_hook({"tool_name": "Bash", "tool_input": {"command": "ls"}}).returncode == 0


def test_hook_exits_0_on_malformed_input():
    """入力が壊れていても他 hook の判定を邪魔しない。"""
    r = subprocess.run(
        [sys.executable, str(_BAN_SCRIPT)],
        input="not json",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert r.returncode == 0


# --- drift 検査: 機構と条文の SSOT 整合 ---------------------------------------


def _missing_roots(roots) -> list:
    """実在しないルートを列挙する（純関数 / 下の 2 テストが共有する）。"""
    return [r for r in roots if not Path(r).exists()]


# 所有者環境の判定シグナル（2026-07-27 / MAGI + gabriel / 循環を避けるための設計）。
#
# `SESSION_STATE.md` は **gitignore 済でローカル限定**であるため、clone した配布先には
# 存在しない。したがって「条文を書いた当の環境か」の代理として使える。
#
# **なぜ `not path.exists()` を skip 条件にしないか**: 検出したい事象（ban root が
# 実在しない）そのものが skip 条件になり、検査として機能しなくなる（循環）。
_IS_AUTHORING_ENV = (_REPO_ROOT / "SESSION_STATE.md").exists()

# 既知の弱点（受忍済）: 所有者が SESSION_STATE.md を削除すると本検査は静かに skip される。


@pytest.mark.skipif(
    not _IS_AUTHORING_ENV,
    reason="所有者環境（SESSION_STATE.md が存在する）でのみ実行する",
)
def test_outbound_roots_exist_in_authoring_env(owb):
    """条文を書いた環境では、禁止ルートと許可ルートが**実在**すること。

    drift 検査が守るのは「条文と機構が同じ文字列を持つこと」だけであり、
    **その文字列が実在するかは検査していない**。リポジトリ群を移動すると条文と機構は
    仲良く同じ嘘をつき、drift 検査は緑のまま通る —— すなわち **ガードが沈黙して
    守らなくなっても誰も気づかない**。本テストはその穴を塞ぐ。
    """
    roots = list(owb._BAN_ROOTS) + list(owb._ALLOW_ROOTS)
    missing = _missing_roots(roots)
    assert missing == [], (
        f"Outbound Write Ban の対象が実在しない: {missing}。"
        "リポジトリ群を移動した場合、`docs/private/fable-l3-protocol.md` §2（SSOT）と "
        "`.claude/hooks-local/outbound-write-ban.py` の `_BAN_ROOTS` / `_ALLOW_ROOTS` の"
        "**両方**を更新すること"
    )


def test_root_existence_check_detects_missing():
    """`_missing_roots` が実際に不在を検出する（**上のテストが vacuous でないことの保証**）。"""
    nonexistent = Path("D:/work7/__lam_nonexistent_root_for_test__")
    assert not nonexistent.exists(), "テスト前提: このパスは存在しないこと"
    assert _missing_roots([nonexistent]) == [nonexistent]
    assert _missing_roots([_REPO_ROOT]) == [], "実在するルートは検出されない"


@pytest.mark.skipif(
    not _IS_AUTHORING_ENV,
    reason="所有者環境でのみ実行する。条文は docs/private/ にあり配布先では削除されうる",
)
def test_banned_root_matches_rule_document(owb):
    """機構の禁止ルートが `fable-l3-protocol.md` の記載と一致する。

    条文側（§2 / §0）が SSOT。機構側が別の値を持つと **沈黙して守らなくなる**ため、
    文字列の存在を突合する（**部分文字列の存在確認のみ** / prose の構造解析はしない）。
    """
    rule_text = (_REPO_ROOT / "docs" / "private" / "fable-l3-protocol.md").read_text(
        encoding="utf-8"
    )
    for banned in owb._BAN_ROOTS:
        windows_form = str(banned).replace("/", "\\")
        assert windows_form in rule_text, (
            f"禁止ルート {windows_form!r} が fable-l3-protocol.md に見つからない。"
            "条文と機構が drift している可能性がある"
        )

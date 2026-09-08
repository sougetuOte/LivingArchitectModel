"""base.py - BaseParser 抽象クラス定義（W1-B5-T1）

対応仕様: docs/specs/b4-dashboard/design.md §5「パーサ共通インターフェース」
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseParser(ABC):
    """全パーサの共通基底クラス。

    サブクラスは parse() を実装し、以下の形式の dict を返すこと（MUST）。

    戻り値の形式::

        {
            "ok": bool,           # 読み込み成功フラグ
            "error": str | None,  # 失敗時のエラーメッセージ（ok=False のとき）
            "data": dict | None,  # 成功時のパース結果（ok=False のときは None）
        }

    例外は外に伝播させず、ok=False の dict を返すこと（MUST）。
    これにより build_dashboard.py がパーサ失敗を検知し、残りのパーサを継続呼び出しできる。

    例::

        class MyParser(BaseParser):
            def parse(self) -> dict:
                try:
                    data = self._load()
                    return {"ok": True, "error": None, "data": data}
                except Exception as e:
                    return {"ok": False, "error": str(e), "data": None}
    """

    @abstractmethod
    def parse(self) -> dict:
        """データソースを読み込み、正規化されたデータを返す。

        Returns:
            dict: ok / error / data の 3 キーを持つ dict。
                - ok (bool): 読み込み成功フラグ。
                - error (str | None): 失敗時のエラーメッセージ。ok=True のとき None。
                - data (dict | None): 成功時のパース結果。ok=False のとき None。
        """

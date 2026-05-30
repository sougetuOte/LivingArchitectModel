"""checkers - AUTONOMOUS モードの決定的 Green State checker 群（design D3）。

各 checker は Stop hook（lam-stop-hook.py）からサブプロセス実行され、
実 exit code でモデル改竄不能な判定を返す。出力規約（findings B）:
PASS=exit 0 / FAIL=exit 2（stderr に赤の詳細）。
"""

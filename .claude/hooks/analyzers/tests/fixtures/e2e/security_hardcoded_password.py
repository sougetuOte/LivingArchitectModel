"""E2E テストフィクスチャ: Security - Hardcoded Password (3箇所)

bandit B105/B106 が検出するパターンを使用。

仕込み箇所:
  FIXTURE-ISSUE-1 (line ~12): DEFAULT_PASSWORD — bandit B105
  FIXTURE-ISSUE-2 (line ~17): connect_database の password キー — bandit B106
  FIXTURE-ISSUE-3 (line ~24): AuthManager.API_KEY — bandit B105
"""
from __future__ import annotations

# FIXTURE-ISSUE-1: bandit B105 - hardcoded password string
DEFAULT_PASSWORD = "admin123"  # noqa: S105


def connect_database() -> dict:
    # FIXTURE-ISSUE-2: bandit B106 - hardcoded password in function call
    return {"host": "localhost", "password": "secret_password"}  # noqa: S106


class AuthManager:
    # FIXTURE-ISSUE-3: bandit B105 - hardcoded API key (treated as password)
    API_KEY = "sk-hardcoded-api-key-abc123"  # noqa: S105

    def authenticate(self, user: str) -> bool:
        return user == "admin"

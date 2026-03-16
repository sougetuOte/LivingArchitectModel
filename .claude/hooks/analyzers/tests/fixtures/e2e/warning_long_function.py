"""E2E テストフィクスチャ: Warning - Long Function (51行+) × 2箇所

仕込み箇所:
  FIXTURE-ISSUE-1 (line ~10): validate_and_transform_user — 51行超
  FIXTURE-ISSUE-2 (line ~70): generate_report — 51行超
"""
from __future__ import annotations


# FIXTURE-ISSUE-1: Long Function — データ検証 + 変換 + フォーマットを1関数に詰め込む (51行超)
def validate_and_transform_user(user_data: dict) -> dict:
    # ステップ1: 入力バリデーション
    if not user_data:
        raise ValueError("user_data is empty")

    if "name" not in user_data:
        raise ValueError("name is required")

    if "email" not in user_data:
        raise ValueError("email is required")

    if "age" not in user_data:
        raise ValueError("age is required")

    name = user_data["name"]
    if not isinstance(name, str):
        raise TypeError("name must be a string")
    if len(name) < 2:
        raise ValueError("name must be at least 2 characters")
    if len(name) > 100:
        raise ValueError("name must be at most 100 characters")

    email = user_data["email"]
    if not isinstance(email, str):
        raise TypeError("email must be a string")
    if "@" not in email:
        raise ValueError("email must contain @")
    if "." not in email.split("@")[-1]:
        raise ValueError("email domain must contain .")

    age = user_data["age"]
    if not isinstance(age, int):
        raise TypeError("age must be an integer")
    if age < 0:
        raise ValueError("age must be non-negative")
    if age > 150:
        raise ValueError("age must be at most 150")

    # ステップ2: 変換処理
    normalized_name = name.strip().title()
    normalized_email = email.strip().lower()
    age_group = "minor" if age < 18 else "adult" if age < 65 else "senior"

    # ステップ3: 出力フォーマット
    return {
        "name": normalized_name,
        "email": normalized_email,
        "age": age,
        "age_group": age_group,
        "display_name": f"{normalized_name} <{normalized_email}>",
    }


# FIXTURE-ISSUE-2: Long Function — 集計 + フォーマット + 出力を1関数に詰め込む (51行超)
def generate_report(records: list[dict]) -> str:
    # ステップ1: 集計
    total = len(records)
    if total == 0:
        return "No records found."

    success_count = 0
    failure_count = 0
    warning_count = 0
    total_amount = 0.0
    max_amount = 0.0
    min_amount = float("inf")
    categories: dict[str, int] = {}

    for record in records:
        status = record.get("status", "unknown")
        if status == "success":
            success_count += 1
        elif status == "failure":
            failure_count += 1
        elif status == "warning":
            warning_count += 1

        amount = record.get("amount", 0.0)
        total_amount += amount
        if amount > max_amount:
            max_amount = amount
        if amount < min_amount:
            min_amount = amount

        category = record.get("category", "uncategorized")
        categories[category] = categories.get(category, 0) + 1

    avg_amount = total_amount / total if total > 0 else 0.0

    # ステップ2: フォーマット
    lines = [
        "=== Report ===",
        f"Total records: {total}",
        f"Success: {success_count}",
        f"Failure: {failure_count}",
        f"Warning: {warning_count}",
        f"Total amount: {total_amount:.2f}",
        f"Average amount: {avg_amount:.2f}",
        f"Max amount: {max_amount:.2f}",
        f"Min amount: {min_amount:.2f}",
        "Categories:",
    ]
    for cat, count in sorted(categories.items()):
        lines.append(f"  {cat}: {count}")

    return "\n".join(lines)

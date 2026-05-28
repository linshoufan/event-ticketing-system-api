"""本地測試用：自己簽一個合法 JWT（不用跑 Google OAuth）。

用法：
    python scripts/make_token.py <user_id> [role]

範例：
    python scripts/make_token.py u-123 employee
    python scripts/make_token.py wf-1 welfare_member

注意：
- JWT_SECRET_KEY / JWT_ALGORITHM 必須跟 Account Service 的 .env 一致，
  簽出來的 token 才能被 Transaction Service 驗證通過。
- 這只是本地測試的捷徑，正式環境的 token 一律由 Account Service 透過 OAuth 發。
- user_id 必須是 Account Service DB 裡真實存在的使用者，否則 eligibility 會回 USER_NOT_FOUND。
"""
import sys
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/make_token.py <user_id> [role]")
        sys.exit(1)

    user_id = sys.argv[1]
    role = sys.argv[2] if len(sys.argv) > 2 else "employee"

    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    print(token)


if __name__ == "__main__":
    main()

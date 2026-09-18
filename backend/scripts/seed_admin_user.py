"""One-time script: seed the initial sfm_admin account so there's a way to
log in and grant everyone else access.

Not part of seed.py or backend startup - run manually, once, from the
backend directory:

    .venv/Scripts/python.exe -m scripts.seed_admin_user

The generated password is printed once and is not stored anywhere in the
codebase - record it immediately.
"""

import secrets

from app.auth import hash_password
from app.database import SessionLocal
from app.models import User

ADMIN_EMAIL = "sfm_admin"


def main() -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if existing is not None:
            print(f"'{ADMIN_EMAIL}' already exists (id={existing.id}); not touching it.")
            return

        password = secrets.token_urlsafe(18)
        user = User(email=ADMIN_EMAIL, password_hash=hash_password(password), is_admin=True)
        db.add(user)
        db.commit()

        print(f"Created admin user '{ADMIN_EMAIL}' with password:\n\n    {password}\n")
        print("Record this password now - it is not stored anywhere else.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

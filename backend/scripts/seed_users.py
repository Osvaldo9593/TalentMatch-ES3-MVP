"""Create the initial TalentMatch users from environment configuration."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole


def create_user(db, email: str, password: str, role: UserRole) -> None:
    user = db.query(User).filter(User.email == email).first()
    if user:
        print(f"Usuario ya existente: {email} ({role.value})")
        return
    db.add(User(email=email, hashed_password=get_password_hash(password), role=role))
    print(f"Usuario creado: {email} ({role.value})")


def main() -> None:
    db = SessionLocal()
    try:
        create_user(db, settings.SEED_ADMIN_EMAIL, settings.SEED_ADMIN_PASSWORD, UserRole.ADMIN)
        create_user(db, settings.SEED_RECRUITER_EMAIL, settings.SEED_RECRUITER_PASSWORD, UserRole.RECRUITER)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()

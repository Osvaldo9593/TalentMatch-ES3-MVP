from app.core.security import get_password_hash
from app.models.user import User, UserRole


def create_user(db_session, email: str, password: str, role: UserRole) -> User:
    user = User(email=email, hashed_password=get_password_hash(password), role=role)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_login_valid_and_invalid_credentials(client, db_session):
    create_user(db_session, "admin@test.local", "correct-password", UserRole.ADMIN)

    success = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "correct-password"},
    )
    assert success.status_code == 200
    assert success.json()["token_type"] == "bearer"

    invalid = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "wrong-password"},
    )
    assert invalid.status_code == 401


def test_protected_cv_actions_require_token(client):
    assert client.patch("/api/v1/cvs/999/status", json={"status": "EN_REVISION"}).status_code == 401
    assert client.delete("/api/v1/cvs/999/hard-delete").status_code == 401


def test_recruiter_cannot_hard_delete(client, db_session):
    user = create_user(db_session, "recruiter@test.local", "recruiter-password", UserRole.RECRUITER)
    token = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "recruiter-password"},
    ).json()["access_token"]

    response = client.delete(
        "/api/v1/cvs/999/hard-delete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403

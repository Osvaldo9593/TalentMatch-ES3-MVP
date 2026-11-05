from pathlib import Path

from app.core.security import get_password_hash
from app.models.candidate_cv import CandidateCV
from app.models.candidate_evaluation import CandidateEvaluation
from app.models.job_offer import JobOffer
from app.models.user import User, UserRole


def setup_candidate(db_session):
    offer = JobOffer(
        title="Ingeniero de pruebas",
        description="Oferta de prueba",
        location="Santiago",
        employment_type="Remoto",
        experience_required="3 años",
        status="active",
        required_skills=["Python"],
        preferred_skills=[],
        requirements=[],
    )
    db_session.add(offer)
    db_session.flush()
    cv = CandidateCV(
        job_offer_id=offer.id,
        original_filename="candidate.pdf",
        stored_filename="candidate-test.pdf",
        file_path="storage/cvs/candidate-test.pdf",
        file_size=10,
        mime_type="application/pdf",
        extracted_text="Texto de prueba",
        processing_status="processed",
        extraction_status="OK",
    )
    db_session.add(cv)
    db_session.commit()
    db_session.refresh(cv)
    return cv


def auth_header(client, db_session, role):
    user = User(
        email=f"{role.value}@actions.test",
        hashed_password=get_password_hash("password"),
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    token = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "password"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_update_candidate_status(client, db_session):
    cv = setup_candidate(db_session)
    headers = auth_header(client, db_session, UserRole.RECRUITER)
    response = client.patch(
        f"/api/v1/cvs/{cv.id}/status",
        json={"status": "EN_REVISION"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["application_status"] == "EN_REVISION"


def test_admin_hard_delete_purges_record_evaluation_and_file(client, db_session, tmp_path, monkeypatch):
    cv = setup_candidate(db_session)
    evaluation = CandidateEvaluation(
        cv_id=cv.id,
        score=80,
        recommendation="recommended",
        experience_range="3-5",
        education_level="profesional",
        matched_required_skills=[],
        missing_required_skills=[],
        matched_preferred_skills=[],
        experience_analysis="Correcta",
        requirements_analysis="Correcta",
        summary="Correcta",
    )
    db_session.add(evaluation)
    db_session.commit()
    file_path = Path(tmp_path) / cv.stored_filename
    file_path.write_bytes(b"pdf")
    from app.services.cv_service import cv_service
    monkeypatch.setattr(cv_service, "get_absolute_path", lambda _: file_path)
    headers = auth_header(client, db_session, UserRole.ADMIN)

    response = client.delete(f"/api/v1/cvs/{cv.id}/hard-delete", headers=headers)
    assert response.status_code == 200
    assert db_session.get(CandidateCV, cv.id) is None
    assert db_session.query(CandidateEvaluation).filter_by(cv_id=cv.id).first() is None
    assert not file_path.exists()

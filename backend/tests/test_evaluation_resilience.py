from app.api.v1.endpoints.evaluations import _mark_evaluation_error
from app.models.candidate_cv import CandidateCV


def _create_cv(db_session, job_offer_id: int, filename: str, status: str):
    cv = CandidateCV(
        job_offer_id=job_offer_id,
        original_filename=filename,
        stored_filename=f"{filename}.pdf",
        file_path=f"cvs/{filename}.pdf",
        file_size=10,
        mime_type="application/pdf",
        extracted_text="Texto de prueba",
        processing_status="processed" if status != "error" else "failed",
        status=status,
    )
    db_session.add(cv)
    db_session.commit()
    db_session.refresh(cv)
    return cv


def test_evaluation_progress_reports_counts_and_current_cv(client, db_session):
    offer = client.post(
        "/api/v1/job-offers/",
        json={"title": "Oferta resiliente", "description": "Prueba", "required_skills": [], "status": "active"},
    ).json()
    _create_cv(db_session, offer["id"], "evaluated", "evaluated")
    _create_cv(db_session, offer["id"], "failed", "error")
    _create_cv(db_session, offer["id"], "active", "processing")

    response = client.get(f"/api/v1/job-offers/{offer['id']}/evaluation-progress")

    assert response.status_code == 200
    assert response.json() == {
        "total": 3,
        "completed": 1,
        "failed": 1,
        "pending": 0,
        "in_progress": 1,
        "current_cv": {"id": 3, "original_filename": "active"},
    }


def test_worker_error_is_persisted_without_losing_original_exception(db_session):
    cv = _create_cv(db_session, 1, "timeout", "processing")

    _mark_evaluation_error(db_session, cv, TimeoutError("Tiempo de espera agotado al consultar la IA"))

    db_session.refresh(cv)
    assert cv.status == "error"
    assert cv.processing_status == "failed"
    assert "Tiempo de espera agotado" in cv.error_message

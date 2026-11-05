import pytest
from app.models.candidate_cv import CandidateCV
from tests.test_candidate_cvs import create_minimal_text_pdf_bytes


@pytest.fixture
def created_job_offer(client):
    response = client.post(
        "/api/v1/job-offers/",
        json={
            "title": "Oferta de documentación",
            "description": "Prueba de errores documentales",
            "location": "Santiago",
            "employment_type": "Remoto",
            "experience_required": "2 años",
            "status": "active",
            "required_skills": ["Python"],
            "preferred_skills": [],
            "requirements": [],
        },
    )
    assert response.status_code == 201
    return response.json()


def test_pdf_without_extractable_text_sets_error_format(client, created_job_offer, db_session):
    blank_pdf = create_minimal_text_pdf_bytes([])
    response = client.post(
        f"/api/v1/job-offers/{created_job_offer['id']}/cvs/",
        files={"file": ("blank.pdf", blank_pdf, "application/pdf")},
    )
    assert response.status_code == 201
    cv = db_session.query(CandidateCV).filter_by(id=response.json()["id"]).one()
    assert cv.processing_status == "failed"
    assert cv.extraction_status == "ERROR_FORMATO"
    assert cv.error_message

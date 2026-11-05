import io
import pytest

from docx import Document

from app.models.candidate_cv import CandidateCV
from app.services.pdf_service import pdf_service


@pytest.fixture
def created_job_offer(client):
    response = client.post(
        "/api/v1/job-offers/",
        json={
            "title": "Ingeniero DOCX",
            "description": "Oferta para validar documentos DOCX.",
            "required_skills": ["Python", "FastAPI"],
            "status": "active",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_docx_bytes() -> bytes:
    document = Document()
    document.add_paragraph("Candidato DOCX")
    document.add_paragraph("Ingeniero Python con experiencia en FastAPI")
    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Habilidad"
    table.rows[0].cells[1].text = "Python"
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def test_docx_parser_extracts_paragraphs_and_tables():
    extracted, error = pdf_service.extract_docx_text(create_docx_bytes())
    assert error is None
    assert extracted is not None
    assert "Candidato DOCX" in extracted
    assert "Python" in extracted


def test_docx_parser_rejects_corrupt_document():
    valid, error = pdf_service.validate_docx_structure(b"not-a-docx")
    assert valid is False
    assert "DOCX" in error


def test_docx_parser_rejects_empty_document():
    document = Document()
    output = io.BytesIO()
    document.save(output)
    valid, error = pdf_service.validate_docx_structure(output.getvalue())
    assert valid is False
    assert "contenido" in error


def test_upload_valid_docx_success(client, created_job_offer, db_session):
    response = client.post(
        f"/api/v1/job-offers/{created_job_offer['id']}/cvs/",
        files={
            "file": (
                "candidate.docx",
                create_docx_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["mime_type"].endswith("wordprocessingml.document")
    assert data["processing_status"] == "processed"
    assert db_session.query(CandidateCV).filter_by(id=data["id"]).one().extracted_text


def test_upload_corrupt_docx_returns_bad_request(client, created_job_offer):
    response = client.post(
        f"/api/v1/job-offers/{created_job_offer['id']}/cvs/",
        files={"file": ("corrupt.docx", b"invalid", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 400
    assert "DOCX" in response.json()["detail"]

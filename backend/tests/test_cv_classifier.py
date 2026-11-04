import json
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.job_offer import JobOffer
from app.models.candidate_cv import CandidateCV
from app.models.candidate_evaluation import CandidateEvaluation
from app.services.openrouter_service import openrouter_service
from app.api.v1.endpoints import cvs as cvs_endpoint
from tests.test_candidate_cvs import create_minimal_text_pdf_bytes


@pytest.fixture
def sample_job_offer(db_session: Session) -> JobOffer:
    offer = JobOffer(
        title="Desarrollador Backend Python Senior",
        description="Buscamos ingeniero con experiencia sólida en FastAPI, PostgreSQL y Docker.",
        location="Santiago, Chile",
        employment_type="Remoto",
        experience_required="3+ años",
        status="active",
        required_skills=["Python", "FastAPI", "PostgreSQL"],
        preferred_skills=["Docker", "AWS", "Git"],
        requirements=["Título en Informática o equivalente", "Experiencia con arquitecturas REST"],
    )
    db_session.add(offer)
    db_session.commit()
    db_session.refresh(offer)
    return offer


@pytest.fixture
def sample_candidate_cv(db_session: Session, sample_job_offer: JobOffer) -> CandidateCV:
    cv = CandidateCV(
        job_offer_id=sample_job_offer.id,
        original_filename="cv_candidato_prueba.pdf",
        stored_filename="uuid-candidato-prueba.pdf",
        file_path="storage/cvs/uuid-candidato-prueba.pdf",
        file_size=20480,
        mime_type="application/pdf",
        extracted_text=(
            "Juan Pérez - Desarrollador de Software\n"
            "Experiencia laboral de 4 años desarrollando APIs con Python y FastAPI.\n"
            "Manejo avanzado de PostgreSQL, SQLAlchemy, Docker y control de versiones con Git.\n"
            "Ingeniero en Informática titulado de la Universidad de Chile."
        ),
        processing_status="processed",
    )
    db_session.add(cv)
    db_session.commit()
    db_session.refresh(cv)
    return cv


VALID_AI_EVALUATION_JSON = json.dumps({
    "score": 85,
    "recommendation": "recommended",
    "experience_range": "3-5",
    "education_level": "profesional",
    "matched_required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "missing_required_skills": [],
    "matched_preferred_skills": ["Docker", "Git"],
    "experience_analysis": "El candidato cuenta con 4 años de experiencia en desarrollo backend con Python y FastAPI, cumpliendo los 3 años requeridos.",
    "requirements_analysis": "Posee el título de Ingeniero en Informática y experiencia comprobada en APIs REST.",
    "summary": "Perfil altamente compatible con los requerimientos técnicos y experiencia del cargo."
})


def test_evaluate_cv_success(client: TestClient, sample_job_offer: JobOffer, db_session: Session):
    """
    Prueba 1: CV procesado + oferta válida -> evaluación exitosa y persistencia en DB.
    """
    mock_response = {
        "status": "ok",
        "provider": "openrouter",
        "model": "openrouter/free",
        "content": f"```json\n{VALID_AI_EVALUATION_JSON}\n```"
    }

    pdf_bytes = create_minimal_text_pdf_bytes(["Candidato", "4 años de experiencia", "Ingeniero en Informática"])
    with patch.object(cvs_endpoint, "SessionLocal", return_value=db_session), \
         patch.object(openrouter_service, "generate_chat_completion", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_response

        response = client.post(
            f"/api/v1/job-offers/{sample_job_offer.id}/cvs/",
            files={"file": ("candidate.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 201
        data = response.json()
        assert "segundo plano" in data["message"]
        mock_generate.assert_awaited_once()

        # Verificar persistencia en base de datos
        db_eval = db_session.query(CandidateEvaluation).filter_by(cv_id=data["id"]).first()
        assert db_eval is not None
        assert db_eval.score == 85
        assert db_eval.recommendation == "recommended"


def test_evaluate_cv_without_extracted_text(client: TestClient, sample_job_offer: JobOffer, db_session: Session):
    """
    Prueba 2: CV sin texto extraído -> no permitir evaluación (HTTP 400).
    """
    empty_cv = CandidateCV(
        job_offer_id=sample_job_offer.id,
        original_filename="cv_sin_texto.pdf",
        stored_filename="uuid-cv-sin-texto.pdf",
        file_path="storage/cvs/uuid-cv-sin-texto.pdf",
        file_size=1024,
        mime_type="application/pdf",
        extracted_text=None,
        processing_status="processed",
    )
    db_session.add(empty_cv)
    db_session.commit()
    db_session.refresh(empty_cv)

    from app.services.cv_classifier_service import cv_classifier_service
    with pytest.raises(Exception, match="no contiene texto extraído"):
        import asyncio
        asyncio.run(cv_classifier_service.evaluate_cv(db_session, sample_job_offer, empty_cv))


def test_evaluate_cv_unprocessed_status(client: TestClient, sample_job_offer: JobOffer, db_session: Session):
    """
    Prueba 3: CV con processing_status != 'processed' -> error 400.
    """
    unprocessed_cv = CandidateCV(
        job_offer_id=sample_job_offer.id,
        original_filename="cv_pendiente.pdf",
        stored_filename="uuid-cv-pendiente.pdf",
        file_path="storage/cvs/uuid-cv-pendiente.pdf",
        file_size=1024,
        mime_type="application/pdf",
        extracted_text="Texto extraído",
        processing_status="uploaded",
    )
    db_session.add(unprocessed_cv)
    db_session.commit()
    db_session.refresh(unprocessed_cv)

    from app.services.cv_classifier_service import cv_classifier_service
    with pytest.raises(Exception, match="no está en estado procesado"):
        import asyncio
        asyncio.run(cv_classifier_service.evaluate_cv(db_session, sample_job_offer, unprocessed_cv))


def test_evaluate_cv_ai_invalid_json(client: TestClient, sample_job_offer: JobOffer, sample_candidate_cv: CandidateCV, db_session: Session):
    """
    Prueba 6: Respuesta de IA con JSON inválido o malformado -> HTTP 502 y sin persistencia parcial.
    """
    mock_response = {
        "status": "ok",
        "provider": "openrouter",
        "model": "openrouter/free",
        "content": "Lo siento, como modelo de lenguaje no puedo procesar este documento de manera estructurada."
    }

    with patch.object(cvs_endpoint, "SessionLocal", return_value=db_session), \
         patch.object(openrouter_service, "generate_chat_completion", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_response

        response = client.post(f"/api/v1/job-offers/{sample_job_offer.id}/cvs/",
                               files={"file": ("candidate.pdf", create_minimal_text_pdf_bytes(["Candidato"]), "application/pdf")})
        assert response.status_code == 201
        assert db_session.query(CandidateCV).filter_by(id=response.json()["id"]).one().error_message


def test_evaluate_cv_ai_score_out_of_range(client: TestClient, sample_job_offer: JobOffer, sample_candidate_cv: CandidateCV, db_session: Session):
    """
    Prueba 7: Score devuelto por la IA fuera del rango 0-100 -> validación Pydantic falla con HTTP 502.
    """
    invalid_score_json = json.dumps({
        "score": 125,  # Fuera de rango
        "recommendation": "recommended",
        "experience_range": "3-5",
        "education_level": "profesional",
        "matched_required_skills": ["Python"],
        "missing_required_skills": [],
        "matched_preferred_skills": [],
        "experience_analysis": "Buena experiencia",
        "requirements_analysis": "Cumple requisitos",
        "summary": "Buen candidato"
    })

    mock_response = {
        "status": "ok",
        "provider": "openrouter",
        "model": "openrouter/free",
        "content": invalid_score_json
    }

    with patch.object(cvs_endpoint, "SessionLocal", return_value=db_session), \
         patch.object(openrouter_service, "generate_chat_completion", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_response

        response = client.post(f"/api/v1/job-offers/{sample_job_offer.id}/cvs/",
                               files={"file": ("candidate.pdf", create_minimal_text_pdf_bytes(["Candidato"]), "application/pdf")})
        assert response.status_code == 201
        assert db_session.query(CandidateCV).filter_by(id=response.json()["id"]).one().error_message


def test_evaluate_cv_threshold_normalization(client: TestClient, sample_job_offer: JobOffer, sample_candidate_cv: CandidateCV, db_session: Session):
    """
    Prueba 8: Normalización consistente de recomendaciones basada en los umbrales configurados.
    Si el score es 50 pero la IA devolvió "recommended", el backend normaliza a "not_recommended".
    """
    divergent_json = json.dumps({
        "score": 50,  # Menor a 60
        "recommendation": "recommended",  # Inconsistente con score < 60
        "experience_range": "0-2",
        "education_level": "tecnico",
        "matched_required_skills": [],
        "missing_required_skills": ["Python", "FastAPI"],
        "matched_preferred_skills": [],
        "experience_analysis": "Poca experiencia relevante.",
        "requirements_analysis": "Faltan requisitos indispensables.",
        "summary": "Candidato no cumple con los requisitos base."
    })

    mock_response = {
        "status": "ok",
        "provider": "openrouter",
        "model": "openrouter/free",
        "content": divergent_json
    }

    with patch.object(cvs_endpoint, "SessionLocal", return_value=db_session), \
         patch.object(openrouter_service, "generate_chat_completion", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_response

        response = client.post(f"/api/v1/job-offers/{sample_job_offer.id}/cvs/",
                               files={"file": ("candidate.pdf", create_minimal_text_pdf_bytes(["Candidato"]), "application/pdf")})
        assert response.status_code == 201
        evaluation = db_session.query(CandidateEvaluation).filter_by(cv_id=response.json()["id"]).one()
        assert evaluation.score == 50
        assert evaluation.recommendation == "not_recommended"


def test_evaluate_cv_openrouter_error(client: TestClient, sample_job_offer: JobOffer, sample_candidate_cv: CandidateCV, db_session: Session):
    """
    Prueba 9: Error de conexión o autenticación de OpenRouter -> HTTP 502 sin filtrar credenciales.
    """
    mock_response = {
        "status": "error",
        "provider": "openrouter",
        "model": "openrouter/free",
        "error": "Error de autenticación con OpenRouter: API Key inválida o sin permisos."
    }

    with patch.object(cvs_endpoint, "SessionLocal", return_value=db_session), \
         patch.object(openrouter_service, "generate_chat_completion", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_response

        response = client.post(f"/api/v1/job-offers/{sample_job_offer.id}/cvs/",
                               files={"file": ("candidate.pdf", create_minimal_text_pdf_bytes(["Candidato"]), "application/pdf")})
        assert response.status_code == 201
        assert db_session.query(CandidateCV).filter_by(id=response.json()["id"]).one().error_message


def test_get_cv_evaluation_endpoint(client: TestClient, sample_job_offer: JobOffer, sample_candidate_cv: CandidateCV, db_session: Session):
    """
    Prueba 10: GET evaluation recupera la evaluación guardada sin invocar el LLM.
    Si no existe, devuelve 404.
    """
    # 1. Cuando aún no existe evaluación
    response_not_found = client.get(f"/api/v1/job-offers/{sample_job_offer.id}/cvs/{sample_candidate_cv.id}/evaluation")
    assert response_not_found.status_code == 404

    # 2. Creamos una evaluación directamente en la BD
    evaluation = CandidateEvaluation(
        cv_id=sample_candidate_cv.id,
        score=90,
        recommendation="recommended",
        experience_range="5+",
        education_level="postgrado",
        matched_required_skills=["Python", "FastAPI"],
        missing_required_skills=[],
        matched_preferred_skills=["Docker"],
        experience_analysis="Excelente trayectoria",
        requirements_analysis="Cumple 100%",
        summary="Candidato sobresaliente",
        model_used="openrouter/free"
    )
    db_session.add(evaluation)
    db_session.commit()

    # 3. Consultamos el endpoint GET
    with patch.object(openrouter_service, "generate_chat_completion", new_callable=AsyncMock) as mock_generate:
        response_success = client.get(f"/api/v1/job-offers/{sample_job_offer.id}/cvs/{sample_candidate_cv.id}/evaluation")
        assert response_success.status_code == 200
        data = response_success.json()
        assert data["score"] == 90
        assert data["recommendation"] == "recommended"
        assert data["summary"] == "Candidato sobresaliente"
        # Comprobar que OpenRouter NO fue llamado
        mock_generate.assert_not_called()

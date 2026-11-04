import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.schemas.candidate_evaluation import CandidateEvaluationAIResponse
from app.models.job_offer import JobOffer
from app.models.candidate_cv import CandidateCV
from app.models.candidate_evaluation import CandidateEvaluation
from app.services.openrouter_service import openrouter_service
from app.core.config import settings


def test_root_health_endpoint(client: TestClient):
    """Verifica que el endpoint GET /health responda correctamente con estado y base de datos."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert data["service"] == settings.PROJECT_NAME
    assert data["version"] == settings.VERSION
    assert "database" in data


def test_cors_origins_resolution():
    """Verifica la resolución correcta de orígenes CORS."""
    origins = settings.get_cors_origins()
    assert isinstance(origins, list)
    assert len(origins) >= 1
    assert "http://localhost:5173" in origins


def test_candidate_evaluation_schema_resilience():
    """Verifica que el esquema CandidateEvaluationAIResponse maneje números flotantes, strings y mayúsculas."""
    # 1. Float score and uppercase recommendation
    raw = {
        "score": 85.0,
        "recommendation": "RECOMMENDED",
        "matched_required_skills": ["Python", "FastAPI"],
        "missing_required_skills": [],
        "matched_preferred_skills": "Docker, Kubernetes",  # String instead of list
        "experience_analysis": "3 años de experiencia relevante en backend.",
        "requirements_analysis": "Cumple con todos los requisitos mínimos.",
        "summary": "Perfil idóneo para la posición técnica."
    }
    validated = CandidateEvaluationAIResponse(**raw)
    assert validated.score == 85
    assert validated.recommendation == "recommended"
    assert "Docker" in validated.matched_preferred_skills
    assert "Kubernetes" in validated.matched_preferred_skills

    # 2. String score
    raw_str_score = dict(raw, score="90")
    validated_str = CandidateEvaluationAIResponse(**raw_str_score)
    assert validated_str.score == 90


def test_candidate_evaluation_schema_out_of_range():
    """Verifica que un score fuera de rango (0-100) continúe fallando la validación."""
    raw_invalid = {
        "score": 150,
        "recommendation": "recommended",
        "matched_required_skills": [],
        "missing_required_skills": [],
        "matched_preferred_skills": [],
        "experience_analysis": "Análisis",
        "requirements_analysis": "Requisitos",
        "summary": "Resumen"
    }
    with pytest.raises(Exception):
        CandidateEvaluationAIResponse(**raw_invalid)


def test_existing_evaluation_is_reused_without_llm_call(
    client: TestClient,
    db_session: Session
):
    """Verifica que la evaluación automática no reemplace una evaluación existente."""
    # 1. Crear oferta
    offer = JobOffer(
        title="Ingeniero Backend Senior",
        description="Puesto para desarrollo backend con Python.",
        status="active",
        required_skills=["Python", "FastAPI"],
        preferred_skills=["Docker"],
        requirements=["3 años de experiencia"],
    )
    db_session.add(offer)
    db_session.commit()
    db_session.refresh(offer)

    # 2. Crear CV procesado
    cv = CandidateCV(
        job_offer_id=offer.id,
        original_filename="cv_evaluado.pdf",
        stored_filename="uuid-cv-evaluado-test.pdf",
        file_path="storage/cvs/uuid-cv-evaluado-test.pdf",
        file_size=2048,
        mime_type="application/pdf",
        extracted_text="Experiencia técnica avanzada en Python y FastAPI.",
        processing_status="processed",
    )
    db_session.add(cv)
    db_session.commit()
    db_session.refresh(cv)

    # 3. Guardar una evaluación previa para cv
    existing_eval = CandidateEvaluation(
        cv_id=cv.id,
        score=88,
        recommendation="recommended",
        experience_range="3-5",
        education_level="profesional",
        matched_required_skills=["Python"],
        missing_required_skills=[],
        matched_preferred_skills=[],
        experience_analysis="Experiencia demostrada",
        requirements_analysis="Requisitos cumplidos",
        summary="Candidato ya evaluado previamente",
        model_used="openrouter/free"
    )
    db_session.add(existing_eval)
    db_session.commit()

    # 4. Consultar la evaluación existente sin invocar OpenRouter
    with patch.object(openrouter_service, "generate_chat_completion", new_callable=AsyncMock) as mock_llm:
        response = client.get(f"/api/v1/job-offers/{offer.id}/cvs/{cv.id}/evaluation")
        assert response.status_code == 200
        data = response.json()
        assert data["cv_id"] == cv.id
        assert data["score"] == 88
        mock_llm.assert_not_called()

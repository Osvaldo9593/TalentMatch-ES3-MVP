import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.job_offer import JobOffer
from app.models.candidate_cv import CandidateCV
from app.models.candidate_evaluation import CandidateEvaluation


def test_dashboard_stats_empty(client: TestClient):
    """
    Verifica que el endpoint de estadísticas retorne ceros cuando la base de datos está vacía.
    """
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["active_offers"] == 0
    assert data["total_cvs"] == 0
    assert data["evaluated_cvs"] == 0
    assert data["pending_cvs"] == 0


def test_dashboard_stats_with_data(client: TestClient, db_session: Session):
    """
    Verifica el cálculo correcto de métricas con ofertas activas/inactivas,
    CVs procesados, CVs evaluados y pendientes.
    """
    # 1. Crear oferta activa y oferta inactiva
    active_offer = JobOffer(
        title="Desarrollador Python",
        description="Backend con FastAPI",
        status="active",
        required_skills=["Python"],
    )
    inactive_offer = JobOffer(
        title="Diseñador UI",
        description="Figma y Tailwind",
        status="inactive",
        required_skills=["Figma"],
    )
    db_session.add(active_offer)
    db_session.add(inactive_offer)
    db_session.commit()
    db_session.refresh(active_offer)
    db_session.refresh(inactive_offer)

    # 2. Agregar CVs a la oferta activa
    # CV 1: Procesado y Evaluado
    cv1 = CandidateCV(
        job_offer_id=active_offer.id,
        original_filename="cv_juan_perez.pdf",
        stored_filename="uuid1.pdf",
        file_path="storage/cvs/uuid1.pdf",
        file_size=10240,
        processing_status="processed",
        extracted_text="Python FastAPI PostgreSQL",
    )
    # CV 2: Procesado pero Pendiente de Evaluación
    cv2 = CandidateCV(
        job_offer_id=active_offer.id,
        original_filename="cv_maria_lopez.pdf",
        stored_filename="uuid2.pdf",
        file_path="storage/cvs/uuid2.pdf",
        file_size=12000,
        processing_status="processed",
        extracted_text="Python Django",
    )
    # CV 3: Fallido
    cv3 = CandidateCV(
        job_offer_id=active_offer.id,
        original_filename="cv_corrupto.pdf",
        stored_filename="uuid3.pdf",
        file_path="storage/cvs/uuid3.pdf",
        file_size=500,
        processing_status="failed",
        error_message="Error de lectura",
    )
    db_session.add_all([cv1, cv2, cv3])
    db_session.commit()
    db_session.refresh(cv1)
    db_session.refresh(cv2)

    # 3. Crear evaluación para cv1
    eval1 = CandidateEvaluation(
        cv_id=cv1.id,
        score=90,
        recommendation="recommended",
        experience_range="5+",
        education_level="postgrado",
        matched_required_skills=["Python"],
        missing_required_skills=[],
        matched_preferred_skills=[],
        experience_analysis="Excelente experiencia",
        requirements_analysis="Cumple requisitos",
        summary="Candidato ideal",
        model_used="openrouter/free",
    )
    db_session.add(eval1)
    db_session.commit()

    # 4. Consultar estadísticas
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["active_offers"] == 1
    assert data["total_cvs"] == 3
    assert data["evaluated_cvs"] == 1
    assert data["pending_cvs"] == 1  # Solo cv2 es 'processed' sin evaluación


def test_job_offers_include_cvs_and_evaluated_counts(client: TestClient, db_session: Session):
    """
    Verifica que el listado de ofertas laborales incluya cvs_count y evaluated_count.
    """
    offer = JobOffer(
        title="Ingeniero Cloud",
        description="AWS / GCP",
        status="active",
    )
    db_session.add(offer)
    db_session.commit()
    db_session.refresh(offer)

    cv = CandidateCV(
        job_offer_id=offer.id,
        original_filename="cv_cloud.pdf",
        stored_filename="uuid_cloud.pdf",
        file_path="storage/cvs/uuid_cloud.pdf",
        file_size=15000,
        processing_status="processed",
        extracted_text="AWS Cloud Terraform",
    )
    db_session.add(cv)
    db_session.commit()
    db_session.refresh(cv)

    eval_obj = CandidateEvaluation(
        cv_id=cv.id,
        score=85,
        recommendation="recommended",
        experience_range="3-5",
        education_level="profesional",
        matched_required_skills=["AWS"],
        missing_required_skills=[],
        matched_preferred_skills=[],
        experience_analysis="Senior",
        requirements_analysis="Completo",
        summary="Buen perfil",
        model_used="openrouter/free",
    )
    db_session.add(eval_obj)
    db_session.commit()

    # Consultar oferta por ID
    res_get = client.get(f"/api/v1/job-offers/{offer.id}")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["cvs_count"] == 1
    assert data["evaluated_count"] == 1

    # Consultar listado de ofertas
    res_list = client.get("/api/v1/job-offers/")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert len(list_data) == 1
    assert list_data[0]["cvs_count"] == 1
    assert list_data[0]["evaluated_count"] == 1

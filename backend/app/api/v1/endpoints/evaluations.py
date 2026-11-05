import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.database import SessionLocal
from app.services.job_offer_service import job_offer_service
from app.services.cv_service import cv_service
from app.services.cv_classifier_service import cv_classifier_service
from app.models.candidate_cv import CandidateCV
from app.schemas.candidate_evaluation import (
    CandidateEvaluationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def _evaluate_pending_cvs(job_offer_id: int, cv_ids: list[int]) -> None:
    db = SessionLocal()
    try:
        offer = job_offer_service.get_by_id(db, job_offer_id=job_offer_id)
        if not offer:
            return
        for cv_id in cv_ids:
            cv = cv_service.get_by_id(db, job_offer_id=job_offer_id, cv_id=cv_id)
            if not cv or cv.evaluation is not None or cv.processing_status != "processed":
                continue
            try:
                await cv_classifier_service.evaluate_cv(db=db, job_offer=offer, cv=cv)
            except Exception:
                logger.exception("Error en evaluación batch para CV id=%s", cv_id)
                cv.error_message = "Error durante la evaluación automática del currículum."
                db.commit()
    finally:
        db.close()


@router.post(
    "/job-offers/{job_offer_id}/evaluate",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Iniciar evaluación asíncrona de CVs pendientes",
)
def evaluate_job_offer_cvs(
    job_offer_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    offer = job_offer_service.get_by_id(db, job_offer_id=job_offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Oferta laboral no encontrada")
    pending_cvs = (
        db.query(CandidateCV)
        .filter(
            CandidateCV.job_offer_id == job_offer_id,
            CandidateCV.processing_status == "processed",
        )
        .all()
    )
    pending_ids = [cv.id for cv in pending_cvs if cv.evaluation is None]
    if pending_ids:
        background_tasks.add_task(_evaluate_pending_cvs, job_offer_id, pending_ids)
    return {
        "message": "La evaluación de los CVs pendientes fue programada en segundo plano.",
        "job_offer_id": job_offer_id,
        "queued_count": len(pending_ids),
    }


def _get_validated_job_offer_and_cv(job_offer_id: int, cv_id: int, db: Session):
    """
    Función auxiliar para validar la existencia de la oferta y que el CV le pertenezca.
    """
    offer = job_offer_service.get_by_id(db, job_offer_id=job_offer_id)
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Oferta laboral con ID {job_offer_id} no encontrada",
        )

    cv = cv_service.get_by_id(db, job_offer_id=job_offer_id, cv_id=cv_id)
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Currículum con ID {cv_id} no encontrado en la oferta laboral {job_offer_id}",
        )

    return offer, cv


@router.get(
    "/job-offers/{job_offer_id}/cvs/{cv_id}/evaluation",
    response_model=CandidateEvaluationResponse,
    summary="Obtener la evaluación existente de un CV",
    description="Recupera la evaluación almacenada en la base de datos para el CV especificado sin volver a invocar el modelo.",
)
def get_candidate_cv_evaluation(
    job_offer_id: int,
    cv_id: int,
    db: Session = Depends(get_db),
):
    _get_validated_job_offer_and_cv(job_offer_id, cv_id, db)
    evaluation = cv_classifier_service.get_evaluation_by_cv(db=db, cv_id=cv_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El currículum con ID {cv_id} aún no ha sido evaluado.",
        )
    return evaluation

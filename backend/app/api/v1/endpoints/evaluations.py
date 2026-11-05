import logging
from datetime import datetime, timedelta, timezone
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


def _mark_evaluation_error(db: Session, cv: CandidateCV, exc: Exception) -> None:
    cv.status = "error"
    cv.processing_status = "failed"
    cv.error_message = str(exc) or "Error desconocido durante la evaluación."
    db.commit()


async def _evaluate_cv_safely(job_offer_id: int, cv_id: int) -> None:
    db = SessionLocal()
    try:
        offer = job_offer_service.get_by_id(db, job_offer_id=job_offer_id)
        cv = cv_service.get_by_id(db, job_offer_id=job_offer_id, cv_id=cv_id)
        if not offer or not cv:
            return
        await cv_classifier_service.evaluate_cv(db=db, job_offer=offer, cv=cv)
    except Exception as exc:
        logger.exception("Error en evaluación para CV id=%s", cv_id)
        cv = cv_service.get_by_id(db, job_offer_id=job_offer_id, cv_id=cv_id)
        if cv:
            _mark_evaluation_error(db, cv, exc)
    finally:
        db.close()


async def _evaluate_pending_cvs(job_offer_id: int, cv_ids: list[int]) -> None:
    for cv_id in cv_ids:
        await _evaluate_cv_safely(job_offer_id, cv_id)


def _recover_zombie_cvs(db: Session, job_offer_id: int) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    zombies = (
        db.query(CandidateCV)
        .filter(
            CandidateCV.job_offer_id == job_offer_id,
            CandidateCV.status == "processing",
            CandidateCV.updated_at < cutoff,
        )
        .all()
    )
    for cv in zombies:
        cv.status = "error"
        cv.processing_status = "failed"
        cv.error_message = "La evaluación excedió el tiempo máximo de 5 minutos."
    if zombies:
        db.commit()


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
    _recover_zombie_cvs(db, job_offer_id)
    pending_cvs = (
        db.query(CandidateCV)
        .filter(
            CandidateCV.job_offer_id == job_offer_id,
            CandidateCV.processing_status == "processed",
            CandidateCV.status.in_(("pending", "error")),
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


@router.get(
    "/job-offers/{job_offer_id}/evaluation-progress",
    summary="Obtener progreso de evaluación de CVs",
)
def get_evaluation_progress(job_offer_id: int, db: Session = Depends(get_db)):
    offer = job_offer_service.get_by_id(db, job_offer_id=job_offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Oferta laboral no encontrada")
    _recover_zombie_cvs(db, job_offer_id)
    cvs = db.query(CandidateCV).filter(CandidateCV.job_offer_id == job_offer_id).all()
    completed = sum(1 for cv in cvs if cv.status == "evaluated" or cv.evaluation is not None)
    failed = sum(1 for cv in cvs if cv.status == "error" or cv.processing_status == "failed")
    in_progress = sum(1 for cv in cvs if cv.status == "processing")
    pending = max(0, len(cvs) - completed - failed - in_progress)
    current = next((cv for cv in cvs if cv.status == "processing"), None)
    return {
        "total": len(cvs),
        "completed": completed,
        "failed": failed,
        "pending": pending,
        "in_progress": in_progress,
        "current_cv": (
            {"id": cv.id, "original_filename": cv.original_filename}
            if (cv := current) else None
        ),
    }


@router.post(
    "/job-offers/{job_offer_id}/cvs/{cv_id}/evaluate",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Reintentar evaluación individual de un CV",
)
def retry_cv_evaluation(
    job_offer_id: int,
    cv_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    _offer, cv = _get_validated_job_offer_and_cv(job_offer_id, cv_id, db)
    if cv.status not in ("pending", "error") and cv.processing_status not in ("processed", "failed"):
        raise HTTPException(status_code=409, detail="El CV ya está siendo evaluado.")
    cv.status = "pending"
    cv.processing_status = "processed"
    cv.error_message = None
    db.commit()
    background_tasks.add_task(_evaluate_cv_safely, job_offer_id, cv_id)
    return {"message": "La evaluación fue programada nuevamente.", "cv_id": cv_id}


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

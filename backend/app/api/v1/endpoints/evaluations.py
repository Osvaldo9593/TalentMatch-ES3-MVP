import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.job_offer_service import job_offer_service
from app.services.cv_service import cv_service
from app.services.cv_classifier_service import cv_classifier_service
from app.models.candidate_cv import CandidateCV
from app.schemas.candidate_evaluation import (
    CandidateEvaluationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


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

from typing import List
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.database import SessionLocal
from app.services.job_offer_service import job_offer_service
from app.services.cv_service import cv_service
from app.services.cv_classifier_service import cv_classifier_service
from app.schemas.candidate_evaluation import CandidateEvaluationResponse
from app.schemas.candidate_cv import (
    CandidateCVResponse,
    CandidateCVListResponse,
    CandidateCVDetailResponse,
    CandidateCVDeleteResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def _evaluate_cv_in_background(cv_id: int, job_offer_id: int) -> None:
    db = SessionLocal()
    try:
        offer = job_offer_service.get_by_id(db, job_offer_id=job_offer_id)
        cv = cv_service.get_by_id(db, job_offer_id=job_offer_id, cv_id=cv_id)
        if offer and cv and cv.processing_status == "processed" and cv.evaluation is None:
            await cv_classifier_service.evaluate_cv(db=db, job_offer=offer, cv=cv)
    except Exception:
        logger.exception("Error en evaluación automática del CV %s", cv_id)
    finally:
        db.close()


def _get_validated_job_offer(job_offer_id: int, db: Session):
    """Helper to verify job offer existence before performing CV operations."""
    offer = job_offer_service.get_by_id(db, job_offer_id=job_offer_id)
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Oferta laboral con ID {job_offer_id} no encontrada",
        )
    return offer


@router.post(
    "/",
    response_model=CandidateCVResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cargar y procesar un CV en PDF",
    description="Recibe un archivo PDF, valida su estructura, extrae su texto normalizado y lo asocia a la oferta laboral.",
)
async def upload_candidate_cv(
    job_offer_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Documento de currículum en formato PDF"),
    db: Session = Depends(get_db),
):
    _get_validated_job_offer(job_offer_id, db)

    # Initial file check
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionó ningún archivo para cargar.",
        )

    # Check extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo no soportado. Se requiere un documento en formato PDF (.pdf).",
        )

    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo proporcionado está vacío.",
            )

        saved_cv = cv_service.process_and_save_cv(
            db=db,
            job_offer_id=job_offer_id,
            original_filename=file.filename,
            file_bytes=file_bytes,
        )
        if saved_cv.processing_status == "processed":
            background_tasks.add_task(_evaluate_cv_in_background, saved_cv.id, job_offer_id)
        response = CandidateCVResponse.model_validate(saved_cv)
        response.message = (
            "Currículum cargado. La evaluación se está procesando en segundo plano."
            if saved_cv.processing_status == "processed"
            else "Currículum cargado, pero no fue posible extraer texto para evaluarlo."
        )
        return response

    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno durante el procesamiento del CV: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=List[CandidateCVListResponse],
    summary="Listar CVs de una oferta laboral",
    description="Devuelve el listado de todos los currículums cargados para una convocatoria específica.",
)
def get_job_offer_cvs(
    job_offer_id: int,
    db: Session = Depends(get_db),
):
    _get_validated_job_offer(job_offer_id, db)
    cvs = cv_service.get_by_job_offer(db, job_offer_id=job_offer_id)
    return cvs


@router.get(
    "/{cv_id}",
    response_model=CandidateCVDetailResponse,
    summary="Obtener detalle de un CV",
    description="Devuelve los metadatos completos y el texto extraído del currículum.",
)
def get_candidate_cv_detail(
    job_offer_id: int,
    cv_id: int,
    db: Session = Depends(get_db),
):
    _get_validated_job_offer(job_offer_id, db)
    cv_obj = cv_service.get_by_id(db, job_offer_id=job_offer_id, cv_id=cv_id)
    if not cv_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Currículum con ID {cv_id} no encontrado en la oferta laboral {job_offer_id}",
        )
    return cv_obj


@router.delete(
    "/{cv_id}",
    response_model=CandidateCVDeleteResponse,
    summary="Eliminar un CV",
    description="Elimina de forma segura el registro del currículum en la base de datos y su archivo físico del disco.",
)
def delete_candidate_cv(
    job_offer_id: int,
    cv_id: int,
    db: Session = Depends(get_db),
):
    _get_validated_job_offer(job_offer_id, db)
    cv_obj = cv_service.get_by_id(db, job_offer_id=job_offer_id, cv_id=cv_id)
    if not cv_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Currículum con ID {cv_id} no encontrado en la oferta laboral {job_offer_id}",
        )

    try:
        cv_service.delete_cv(db, cv_obj=cv_obj)
        return CandidateCVDeleteResponse(
            message="Currículum eliminado exitosamente",
            id=cv_id,
            success=True,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al eliminar el currículum: {str(e)}",
        ) from e


@router.get(
    "/{cv_id}/file",
    summary="Visualizar o descargar el PDF original",
    description="Permite el acceso seguro al archivo PDF almacenado.",
)
def get_candidate_cv_file(
    job_offer_id: int,
    cv_id: int,
    db: Session = Depends(get_db),
):
    _get_validated_job_offer(job_offer_id, db)
    cv_obj = cv_service.get_by_id(db, job_offer_id=job_offer_id, cv_id=cv_id)
    if not cv_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Currículum con ID {cv_id} no encontrado en la oferta laboral {job_offer_id}",
        )

    try:
        target_path = cv_service.get_absolute_path(cv_obj.stored_filename)
        if not target_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El archivo físico del currículum no existe en el almacenamiento.",
            )

        return FileResponse(
            path=str(target_path),
            media_type="application/pdf",
            filename=cv_obj.original_filename,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al acceder al archivo: {str(e)}",
        ) from e

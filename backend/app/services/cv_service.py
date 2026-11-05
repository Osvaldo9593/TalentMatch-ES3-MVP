import os
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.config import settings
from app.models.candidate_cv import CandidateCV
from app.models.candidate_evaluation import CandidateEvaluation
from app.services.pdf_service import pdf_service


class CVService:
    def __init__(self):
        # Resolve absolute storage directory
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.storage_dir = (base_dir / settings.CV_STORAGE_PATH).resolve()
        self.ensure_storage_dir()

    def ensure_storage_dir(self) -> Path:
        """
        Ensures that the physical storage directory for CVs exists on disk.
        """
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        return self.storage_dir

    def get_absolute_path(self, stored_filename: str) -> Path:
        """
        Safely resolves the absolute path for a stored filename within the storage directory,
        preventing any path traversal attempts.
        """
        # Strip path characters from filename
        safe_name = os.path.basename(stored_filename)
        resolved_path = (self.storage_dir / safe_name).resolve()

        # Guard against traversal outside storage_dir
        if not str(resolved_path).startswith(str(self.storage_dir)):
            raise ValueError("Ruta de archivo no autorizada o fuera del directorio de almacenamiento.")

        return resolved_path

    def process_and_save_cv(
        self,
        db: Session,
        job_offer_id: int,
        original_filename: str,
        file_bytes: bytes,
    ) -> CandidateCV:
        """
        Validates the PDF, saves the file to local storage with a UUID,
        extracts normalized text, and persists the record to the database.
        """
        # 1. Size validation
        file_size = len(file_bytes)
        if file_size > settings.max_cv_file_size_bytes:
            raise ValueError(
                f"El archivo excede el tamaño máximo permitido de {settings.MAX_CV_FILE_SIZE_MB} MB."
            )

        # 3. Clean and sanitize original filename for metadata display
        sanitized_original_name = os.path.basename(original_filename.strip()) or "cv_document.pdf"
        extension = Path(sanitized_original_name).suffix.lower()
        if extension not in {".pdf", ".docx"}:
            raise ValueError("Formato no soportado. Se requiere un archivo PDF o DOCX.")
        is_valid_document, validation_err = pdf_service.validate_document(file_bytes, extension)
        if not is_valid_document:
            raise ValueError(validation_err or "El archivo enviado no es válido.")

        # 4. Generate unique stored filename with UUID
        unique_id = str(uuid.uuid4())
        stored_filename = f"{unique_id}{extension}"
        target_path = self.get_absolute_path(stored_filename)

        # 5. Write file physically to storage
        try:
            with open(target_path, "wb") as f:
                f.write(file_bytes)
        except Exception as e:
            raise RuntimeError(f"No fue posible guardar el archivo en el almacenamiento: {str(e)}")

        # 6. Extract text from the selected document format
        extracted_text, extract_error = pdf_service.extract_document_text(file_bytes, extension)

        # 7. Determine processing status
        if extracted_text and not extract_error:
            processing_status = "processed"
            error_message = None
            extraction_status = "OK"
        else:
            processing_status = "failed"
            error_message = extract_error or "No se pudo extraer texto del documento."
            extraction_status = "ERROR_FORMATO"

        # 8. Create and persist database entity
        relative_file_path = f"{settings.CV_STORAGE_PATH}/{stored_filename}"
        cv_obj = CandidateCV(
            job_offer_id=job_offer_id,
            original_filename=sanitized_original_name,
            stored_filename=stored_filename,
            file_path=relative_file_path,
            file_size=file_size,
            mime_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                if extension == ".docx"
                else "application/pdf"
            ),
            extracted_text=extracted_text,
            processing_status=processing_status,
            error_message=error_message,
            extraction_status=extraction_status,
        )

        try:
            db.add(cv_obj)
            db.commit()
            db.refresh(cv_obj)
            return cv_obj
        except Exception as e:
            db.rollback()
            # Clean up saved file if DB commit fails
            if target_path.exists():
                try:
                    target_path.unlink()
                except Exception:
                    pass
            raise e

    def get_by_job_offer(self, db: Session, job_offer_id: int) -> List[CandidateCV]:
        """
        Retrieves all candidate CVs linked to a specific job offer ordered newest first.
        """
        return (
            db.query(CandidateCV)
            .filter(CandidateCV.job_offer_id == job_offer_id)
            .order_by(desc(CandidateCV.created_at))
            .all()
        )

    def count_by_job_offer(self, db: Session, job_offer_id: int) -> int:
        """
        Counts the number of CVs uploaded for a given job offer.
        """
        return (
            db.query(CandidateCV)
            .filter(CandidateCV.job_offer_id == job_offer_id)
            .count()
        )

    def get_by_id(self, db: Session, job_offer_id: int, cv_id: int) -> Optional[CandidateCV]:
        """
        Retrieves a single CV by ID, verifying that it belongs to the given job offer.
        """
        return (
            db.query(CandidateCV)
            .filter(
                CandidateCV.id == cv_id,
                CandidateCV.job_offer_id == job_offer_id
            )
            .first()
        )

    def delete_cv(self, db: Session, cv_obj: CandidateCV) -> None:
        """
        Deletes the CV record from the database and removes the physical file from disk.
        """
        # Determine physical file path
        target_path = self.get_absolute_path(cv_obj.stored_filename)

        # Delete the dependent evaluation explicitly so purge works consistently
        # across PostgreSQL and SQLite test databases.
        db.query(CandidateEvaluation).filter(CandidateEvaluation.cv_id == cv_obj.id).delete(
            synchronize_session=False
        )
        db.delete(cv_obj)
        db.commit()

        # Remove physical file if it exists
        if target_path.exists():
            try:
                target_path.unlink()
            except Exception:
                # File removal warning logged without failing the API response
                pass


cv_service = CVService()

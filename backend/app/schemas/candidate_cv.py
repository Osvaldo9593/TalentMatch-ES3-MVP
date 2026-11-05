from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.candidate_evaluation import CandidateEvaluationSummary

CandidateCVStatus = Literal["uploaded", "processing", "processed", "failed"]
EvaluationStatus = Literal["pending", "processing", "evaluated", "error"]
ApplicationStatus = Literal["PENDIENTE", "EN_REVISION", "DESCARTADO", "SELECCIONADO"]


class CandidateCVBase(BaseModel):
    id: int
    job_offer_id: int
    original_filename: str = Field(..., description="Nombre original del archivo proporcionado por el usuario")
    file_size: int = Field(..., description="Tamaño del archivo en bytes")
    mime_type: str = Field(default="application/pdf", description="Tipo MIME del documento")
    processing_status: CandidateCVStatus = Field(default="uploaded", description="Estado del procesamiento")
    status: EvaluationStatus = Field(default="pending", description="Estado de evaluación con IA")
    error_message: Optional[str] = Field(default=None, description="Mensaje de error en caso de fallo en el procesamiento")
    application_status: ApplicationStatus = "PENDIENTE"
    extraction_status: str = "PENDIENTE"
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def file_size_formatted(self) -> str:
        """Helper to present human-readable file size (KB / MB)."""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.2f} MB"

    model_config = ConfigDict(from_attributes=True)


class CandidateCVListResponse(CandidateCVBase):
    """
    Lightweight schema for CV listings.
    Omits full extracted_text to keep responses lightweight and fast,
    but includes evaluation summary if available.
    """
    evaluation: Optional[CandidateEvaluationSummary] = None


class CandidateCVResponse(CandidateCVBase):
    """
    Standard response returned after uploading or querying a CV.
    """
    evaluation: Optional[CandidateEvaluationSummary] = None
    message: str = "Currículum cargado correctamente."


class CandidateCVDetailResponse(CandidateCVBase):
    """
    Detailed response including extracted text and content statistics.
    """
    extracted_text: Optional[str] = Field(default=None, description="Texto extraído y normalizado del PDF")

    @computed_field
    @property
    def text_length(self) -> int:
        return len(self.extracted_text) if self.extracted_text else 0

    @computed_field
    @property
    def word_count(self) -> int:
        return len(self.extracted_text.split()) if self.extracted_text else 0


class CandidateCVDeleteResponse(BaseModel):
    message: str
    id: int
    success: bool = True

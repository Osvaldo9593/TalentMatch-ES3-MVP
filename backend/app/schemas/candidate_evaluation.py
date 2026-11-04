from datetime import datetime
from typing import List, Optional, Literal, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

EvaluationRecommendation = Literal["recommended", "review", "not_recommended"]
ExperienceRange = Literal["0-2", "3-5", "5+"]
EducationLevel = Literal["tecnico", "profesional", "postgrado"]


class CandidateEvaluationAIResponse(BaseModel):
    """
    Esquema para validar estrictamente la respuesta estructurada JSON devuelta por el LLM.
    """
    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Puntaje de compatibilidad estimado entre 0 y 100"
    )
    recommendation: EvaluationRecommendation = Field(
        ...,
        description="Categoría de recomendación ('recommended', 'review', 'not_recommended')"
    )
    experience_range: ExperienceRange = Field("0-2", description="Rango de años de experiencia explícito en el CV")
    education_level: EducationLevel = Field("tecnico", description="Nivel de estudios explícito en el CV")
    matched_required_skills: List[str] = Field(
        default_factory=list,
        description="Habilidades obligatorias demostradas en el CV"
    )
    missing_required_skills: List[str] = Field(
        default_factory=list,
        description="Habilidades obligatorias requeridas no encontradas"
    )
    matched_preferred_skills: List[str] = Field(
        default_factory=list,
        description="Habilidades deseadas o plus demostradas"
    )
    experience_analysis: str = Field(
        ...,
        description="Análisis cualitativo de la experiencia laboral contra el perfil"
    )
    requirements_analysis: str = Field(
        ...,
        description="Análisis del cumplimiento de requisitos generales y académicos"
    )
    summary: str = Field(
        ...,
        description="Resumen ejecutivo de la preselección del candidato"
    )

    @field_validator("score", mode="before")
    @classmethod
    def validate_score(cls, v: Any) -> int:
        if isinstance(v, (int, float)):
            val = int(round(v))
            return val
        if isinstance(v, str):
            try:
                val = int(round(float(v.strip())))
                return val
            except ValueError:
                pass
        return v

    @field_validator("recommendation", mode="before")
    @classmethod
    def validate_recommendation(cls, v: Any) -> str:
        if isinstance(v, str):
            normalized = v.strip().lower()
            if normalized in ("recommended", "review", "not_recommended"):
                return normalized
            # Normalize common variants
            if "not" in normalized or "no" in normalized:
                return "not_recommended"
            if "review" in normalized or "revisar" in normalized:
                return "review"
            if "recommend" in normalized or "recomend" in normalized:
                return "recommended"
        return v

    @field_validator("matched_required_skills", "missing_required_skills", "matched_preferred_skills", mode="before")
    @classmethod
    def validate_skill_lists(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        if isinstance(v, str) and v.strip():
            import re
            parts = re.split(r'[,;\n]+', v)
            return [p.strip() for p in parts if p.strip()]
        return []


class CandidateEvaluationResponse(CandidateEvaluationAIResponse):
    """
    Esquema completo devuelto por los endpoints al consultar una evaluación guardada.
    """
    id: int
    cv_id: int
    model_used: str = Field(..., description="Identificador del modelo IA utilizado")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateEvaluationSummary(BaseModel):
    """
    Resumen liviano de evaluación para incluir en listados de CVs.
    """
    id: int
    score: int
    recommendation: str
    experience_range: ExperienceRange
    education_level: EducationLevel
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateEvaluationBatchItem(BaseModel):
    """
    Resultado individual para la evaluación masiva de CVs de una oferta.
    """
    cv_id: int
    status: Literal["success", "error", "skipped"]
    score: Optional[int] = None
    recommendation: Optional[str] = None
    message: Optional[str] = None

import json
import logging
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.job_offer import JobOffer
from app.models.candidate_cv import CandidateCV
from app.models.candidate_evaluation import CandidateEvaluation
from app.schemas.candidate_evaluation import CandidateEvaluationAIResponse
from app.services.openrouter_service import openrouter_service

logger = logging.getLogger(__name__)


class CVClassifierService:
    """
    Servicio encargado de orquestar la evaluación y clasificación de currículums mediante IA,
    comparando los requisitos de la oferta laboral con el contenido del CV de forma objetiva,
    libre de sesgos y con validación estricta de la estructura JSON devuelta.
    """

    def __init__(self):
        self.model = settings.OPENROUTER_MODEL
        self.max_text_length = settings.MAX_CV_TEXT_LENGTH
        self.threshold_recommended = settings.EVALUATION_SCORE_RECOMMENDED_THRESHOLD
        self.threshold_review = settings.EVALUATION_SCORE_REVIEW_THRESHOLD

    def determine_recommendation(self, score: int) -> str:
        """
        Determina de forma centralizada la categoría de recomendación según el puntaje de compatibilidad.
        """
        if score >= self.threshold_recommended:
            return "recommended"
        elif score >= self.threshold_review:
            return "review"
        else:
            return "not_recommended"

    def clean_and_truncate_text(self, text: Optional[str]) -> str:
        """
        Limpia y trunca el texto del CV si excede la longitud máxima configurada,
        conservando las primeras secciones más relevantes.
        """
        if not text:
            return ""

        cleaned = text.strip()
        if len(cleaned) <= self.max_text_length:
            return cleaned

        truncated = cleaned[:self.max_text_length]
        # Intentar cortar en el último salto de línea o punto para no cortar una palabra a la mitad
        last_break = max(truncated.rfind("\n"), truncated.rfind(". "))
        if last_break > int(self.max_text_length * 0.8):
            truncated = truncated[:last_break]

        return truncated + "\n... [Texto truncado automáticamente para optimización de contexto]"

    def build_system_prompt(self) -> str:
        """
        Construye las directivas del sistema con énfasis estricto en objetividad,
        cero alucinaciones, ausencia de sesgos personales y respuesta JSON obligatoria.
        """
        return (
            "Eres un asistente experto en reclutamiento y selección de talento para evaluación preliminar de currículums (CVs).\n"
            "Tu tarea es analizar la compatibilidad técnica y profesional entre una oferta laboral y el CV de un candidato.\n\n"
            "REGLAS OBLIGATORIAS:\n"
            "0. IDIOMA: Toda la evaluación, incluyendo análisis, resumen y razones, DEBE estar escrita obligatoriamente en español. "
            "No traduzcas nombres propios ni tecnologías; conserva nombres como 'FastAPI' y 'Python'.\n"
            "1. CERO SESGOS: Evalúa ÚNICAMENTE competencias laborales y técnicas directamente relacionadas con el cargo. "
            "Ignora por completo edad, género, nacionalidad, estado civil, religión, dirección particular, apariencia o situación familiar. "
            "Bajo ningún concepto estos factores deben influir en el puntaje o la recomendación.\n"
            "2. FIDELIDAD A LA INFORMACIÓN: Analiza estrictamente lo que esté explícitamente mencionado en el CV. "
            "No inventes ni asumas habilidades, certificaciones ni años de experiencia que no figuren en el texto. "
            "Si una habilidad no está descrita en el CV, debes considerarla como 'no demostrada' o 'faltante'.\n"
            "3. DIFERENCIACIÓN CLARA: Distingue rigurosamente entre habilidades obligatorias (must-have) y deseadas/plus (nice-to-have).\n"
            "4. ROL DE APOYO: Esta evaluación es un informe de apoyo a la preselección para el reclutador humano; "
            "no tomes decisiones definitivas de contratación.\n"
            "5. FORMATO ESTRICTO: Responde ÚNICAMENTE con un objeto JSON válido, sin texto introductorio ni conclusiones fuera del JSON. "
            "La respuesta debe seguir exactamente esta estructura:\n"
            "{\n"
            '  "score": <entero entre 0 y 100>,\n'
            '  "recommendation": <"recommended" | "review" | "not_recommended">,\n'
            '  "experience_range": <"0-2" | "3-5" | "5+">,\n'
            '  "education_level": <"tecnico" | "profesional" | "postgrado">,\n'
            '  "matched_required_skills": [<habilidades obligatorias demostradas en el CV>],\n'
            '  "missing_required_skills": [<habilidades obligatorias requeridas no encontradas>],\n'
            '  "matched_preferred_skills": [<habilidades deseadas demostradas en el CV>],\n'
            '  "experience_analysis": "<análisis breve y conciso de los años y relevancia de la experiencia laboral>",\n'
            '  "requirements_analysis": "<análisis del cumplimiento de formación o requisitos generales>",\n'
            '  "summary": "<resumen objetivo del perfil enfocado en su ajuste al puesto>"\n'
            "}"
        )

    def build_user_prompt(self, job_offer: JobOffer, cv_text: str) -> str:
        """
        Estructura los datos de la oferta laboral y del currículum para el análisis.
        """
        required_skills_str = ", ".join(job_offer.required_skills) if job_offer.required_skills else "Ninguna especificada"
        preferred_skills_str = ", ".join(job_offer.preferred_skills) if job_offer.preferred_skills else "Ninguna especificada"
        requirements_str = "; ".join(job_offer.requirements) if job_offer.requirements else "Ninguno especificado"

        return (
            "=== DATOS DE LA OFERTA LABORAL ===\n"
            f"Título del puesto: {job_offer.title}\n"
            f"Descripción: {job_offer.description}\n"
            f"Modalidad: {job_offer.employment_type or 'No especificada'}\n"
            f"Experiencia requerida: {job_offer.experience_required or 'No especificada'}\n"
            f"Habilidades Obligatorias (Must-Have): {required_skills_str}\n"
            f"Habilidades Deseadas (Nice-to-Have): {preferred_skills_str}\n"
            f"Requisitos adicionales: {requirements_str}\n\n"
            "=== TEXTO EXTRAÍDO DEL CURRÍCULUM DEL CANDIDATO ===\n"
            f"{cv_text}\n\n"
            "=== INSTRUCCIÓN FINAL ===\n"
            "Compara el CV con la oferta laboral y devuelve exclusivamente el JSON estructurado con el análisis.\n"
            f"Nota de recomendación: score >= {self.threshold_recommended} -> 'recommended'; "
            f"score >= {self.threshold_review} -> 'review'; score < {self.threshold_review} -> 'not_recommended'."
        )

    def extract_and_parse_json(self, raw_content: str) -> Dict[str, Any]:
        """
        Extrae y decodifica con seguridad el objeto JSON de la respuesta de texto del modelo,
        removiendo posibles delimitadores de bloques de código markdown.
        """
        content = raw_content.strip()

        # Quitar bloques de código markdown tipo ```json ... ``` o ``` ... ```
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if json_match:
            content = json_match.group(1).strip()
        else:
            # Buscar el primer '{' y el último '}'
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                content = content[start:end + 1]

        try:
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("El contenido JSON no corresponde a un objeto/diccionario.")
            return parsed
        except Exception as exc:
            logger.error(f"Error al parsear JSON devuelto por el LLM: {str(exc)}")
            raise ValueError(f"La respuesta de la IA no contiene un formato JSON válido: {str(exc)}") from exc

    async def evaluate_cv(self, db: Session, job_offer: JobOffer, cv: CandidateCV) -> CandidateEvaluation:
        """
        Ejecuta el flujo completo de evaluación de un currículum:
        1. Validaciones de estado y contenido de texto.
        2. Preparación del prompt y llamada a OpenRouter.
        3. Extracción, parseo y validación estricta con Pydantic.
        4. Normalización de umbrales y persistencia en PostgreSQL.
        """
        # 1. Validaciones previas
        if cv.processing_status != "processed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El currículum '{cv.original_filename}' no está en estado procesado (estado actual: {cv.processing_status}).",
            )

        if not cv.extracted_text or not cv.extracted_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El currículum '{cv.original_filename}' no contiene texto extraído para ser evaluado.",
            )

        # 2. Preparar el contenido del CV
        processed_cv_text = self.clean_and_truncate_text(cv.extracted_text)

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt(job_offer, processed_cv_text)}
        ]

        # 3. Invocar a OpenRouter
        logger.info(f"Iniciando evaluación con IA para CV ID {cv.id} (Oferta ID {job_offer.id})")
        ai_response = await openrouter_service.generate_chat_completion(
            messages=messages,
            temperature=0.2
        )

        if ai_response.get("status") != "ok":
            error_msg = ai_response.get("error", "Error desconocido al comunicarse con OpenRouter")
            logger.error(f"Fallo en OpenRouter para CV ID {cv.id}: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error al evaluar con OpenRouter: {error_msg}"
            )

        raw_content = ai_response.get("content", "")
        if not raw_content:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenRouter devolvió una respuesta vacía."
            )

        # 4. Parsear y Validar mediante Pydantic
        try:
            parsed_json = self.extract_and_parse_json(raw_content)
            validated_ai = CandidateEvaluationAIResponse(**parsed_json)
        except ValueError as ve:
            logger.error(f"Fallo de estructura en la respuesta de IA: {str(ve)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"La IA generó una respuesta estructurada inválida: {str(ve)}"
            )

        # 5. Normalizar la recomendación según los umbrales centralizados
        calculated_recommendation = self.determine_recommendation(validated_ai.score)
        recommendation_to_use = calculated_recommendation

        # 6. Persistir en Base de Datos (Insertar o Actualizar)
        try:
            existing_eval = (
                db.query(CandidateEvaluation)
                .filter(CandidateEvaluation.cv_id == cv.id)
                .first()
            )

            if existing_eval:
                existing_eval.score = validated_ai.score
                existing_eval.recommendation = recommendation_to_use
                existing_eval.experience_range = validated_ai.experience_range
                existing_eval.education_level = validated_ai.education_level
                existing_eval.matched_required_skills = validated_ai.matched_required_skills
                existing_eval.missing_required_skills = validated_ai.missing_required_skills
                existing_eval.matched_preferred_skills = validated_ai.matched_preferred_skills
                existing_eval.experience_analysis = validated_ai.experience_analysis
                existing_eval.requirements_analysis = validated_ai.requirements_analysis
                existing_eval.summary = validated_ai.summary
                existing_eval.model_used = self.model
                evaluation_record = existing_eval
            else:
                evaluation_record = CandidateEvaluation(
                    cv_id=cv.id,
                    score=validated_ai.score,
                    recommendation=recommendation_to_use,
                    experience_range=validated_ai.experience_range,
                    education_level=validated_ai.education_level,
                    matched_required_skills=validated_ai.matched_required_skills,
                    missing_required_skills=validated_ai.missing_required_skills,
                    matched_preferred_skills=validated_ai.matched_preferred_skills,
                    experience_analysis=validated_ai.experience_analysis,
                    requirements_analysis=validated_ai.requirements_analysis,
                    summary=validated_ai.summary,
                    model_used=self.model,
                )
                db.add(evaluation_record)

            db.commit()
            db.refresh(evaluation_record)
            logger.info(f"Evaluación completada y guardada con éxito para CV ID {cv.id} (Score: {evaluation_record.score})")
            return evaluation_record

        except Exception as e:
            db.rollback()
            logger.error(f"Error al guardar la evaluación en PostgreSQL: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al persistir la evaluación en la base de datos: {str(e)}"
            ) from e

    def get_evaluation_by_cv(self, db: Session, cv_id: int) -> Optional[CandidateEvaluation]:
        """
        Recupera la evaluación almacenada de un CV si existe, sin invocar nuevamente al modelo.
        """
        return (
            db.query(CandidateEvaluation)
            .filter(CandidateEvaluation.cv_id == cv_id)
            .first()
        )


cv_classifier_service = CVClassifierService()

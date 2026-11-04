import React from 'react';
import { CandidateEvaluation } from '../types/candidateEvaluation';

interface CVEvaluationDetailModalProps {
  isOpen: boolean;
  evaluation: CandidateEvaluation | null;
  cvFilename?: string;
  cvFileUrl?: string;
  isLoading: boolean;
  error?: string | null;
  onClose: () => void;
}

export const CVEvaluationDetailModal: React.FC<CVEvaluationDetailModalProps> = ({
  isOpen,
  evaluation,
  cvFilename,
  cvFileUrl,
  isLoading,
  error,
  onClose,
}) => {
  if (!isOpen) return null;

  const getRecommendationBadge = (recommendation: string) => {
    switch (recommendation) {
      case 'recommended':
        return {
          label: 'Recomendado',
          bg: 'bg-[#EBF5EC]',
          text: 'text-[#28572E]',
          border: 'border-[#D5EBD7]',
          dot: 'bg-[#28572E]',
        };
      case 'review':
        return {
          label: 'Revisar',
          bg: 'bg-[#FEF7E6]',
          text: 'text-[#8F6B00]',
          border: 'border-[#FEEFC3]',
          dot: 'bg-[#8F6B00]',
        };
      case 'not_recommended':
      default:
        return {
          label: 'No Recomendado',
          bg: 'bg-[#FDEBEC]',
          text: 'text-[#9F2F2D]',
          border: 'border-[#F9D2D4]',
          dot: 'bg-[#9F2F2D]',
        };
    }
  };

  const badge = evaluation ? getRecommendationBadge(evaluation.recommendation) : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white border border-[#EAEAEA] rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden text-left">
        {/* Header */}
        <div className="p-5 border-b border-[#EAEAEA] flex items-start justify-between gap-4 bg-[#FAFAFA]">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono text-[#787774] uppercase tracking-wider">
                Evaluación Asistida por IA
              </span>
              {evaluation && (
                <span className="font-mono text-[10px] px-2 py-0.5 bg-[#F0F0EE] text-[#555555] rounded border border-[#E5E5E3]">
                  {evaluation.model_used}
                </span>
              )}
            </div>
            <h3 className="text-lg font-serif font-semibold text-[#111111] truncate mt-1">
              {cvFilename || 'Currículum del Candidato'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-[#787774] hover:text-[#111111] hover:bg-[#EAEAE6] rounded-md transition-colors"
            title="Cerrar modal"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
          {isLoading || (!evaluation && !error) ? (
            <div className="py-12 text-center space-y-3">
              <div className="w-8 h-8 border-2 border-[#111111] border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-[#666666] font-mono">La evaluación se está procesando en segundo plano...</p>
            </div>
          ) : error ? (
            <div className="p-4 bg-[#FDEBEC] border border-[#F9D2D4] rounded-lg text-[#9F2F2D] space-y-1">
              <p className="font-medium">Error al cargar la evaluación</p>
              <p className="text-[11px]">{error}</p>
            </div>
          ) : evaluation ? (
            <>
              {/* Score & Recommendation Banner */}
              <div className="p-5 rounded-xl border border-[#EAEAEA] bg-[#FCFCFB] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <span className="text-[11px] font-mono text-[#787774] uppercase tracking-wider block">
                    Puntaje de Compatibilidad
                  </span>
                  <div className="flex items-baseline gap-1 mt-0.5">
                    <span className="text-4xl font-serif font-bold text-[#111111]">
                      {evaluation.score}
                    </span>
                    <span className="text-sm font-mono text-[#787774]">/ 100</span>
                  </div>
                </div>

                {badge && (
                  <div className="flex flex-col sm:items-end gap-1">
                    <span className="text-[11px] font-mono text-[#787774] uppercase tracking-wider">
                      Recomendación IA
                    </span>
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold font-mono border ${badge.bg} ${badge.text} ${badge.border}`}>
                      <span className={`w-2 h-2 rounded-full ${badge.dot}`} />
                      {badge.label}
                    </span>
                  </div>
                )}
              </div>

              {/* Resumen Ejecutivo */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-[#111111] uppercase tracking-wider font-mono">
                  Resumen Ejecutivo
                </h4>
                <p className="text-[#333333] leading-relaxed bg-[#F7F6F3] p-3.5 rounded-lg border border-[#EAEAEA]">
                  {evaluation.summary}
                </p>
              </div>

              {/* Habilidades Requeridas Encontradas vs Faltantes */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Requeridas Encontradas */}
                <div className="p-4 rounded-lg border border-[#D5EBD7] bg-[#F4FAF5] space-y-2">
                  <div className="flex items-center gap-1.5 text-[#28572E] font-semibold font-mono text-[11px] uppercase tracking-wider">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    Habilidades Obligatorias Demostradas
                  </div>
                  {evaluation.matched_required_skills && evaluation.matched_required_skills.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {evaluation.matched_required_skills.map((skill, i) => (
                        <span key={i} className="px-2 py-0.5 bg-white text-[#28572E] border border-[#D5EBD7] rounded text-[11px] font-medium font-mono">
                          {skill}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-[11px] text-[#787774] italic">Ninguna identificada explícitamente.</p>
                  )}
                </div>

                {/* Requeridas Faltantes */}
                <div className="p-4 rounded-lg border border-[#F9D2D4] bg-[#FDF2F2] space-y-2">
                  <div className="flex items-center gap-1.5 text-[#9F2F2D] font-semibold font-mono text-[11px] uppercase tracking-wider">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    Habilidades Obligatorias Faltantes
                  </div>
                  {evaluation.missing_required_skills && evaluation.missing_required_skills.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {evaluation.missing_required_skills.map((skill, i) => (
                        <span key={i} className="px-2 py-0.5 bg-white text-[#9F2F2D] border border-[#F9D2D4] rounded text-[11px] font-medium font-mono">
                          {skill}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-[11px] text-[#28572E] font-medium">Cumple con todas las habilidades requeridas.</p>
                  )}
                </div>
              </div>

              {/* Habilidades Deseadas (Nice to have) */}
              <div className="p-4 rounded-lg border border-[#E9D5FF] bg-[#FAF5FF] space-y-2">
                <span className="text-[11px] font-mono text-[#6B21A8] uppercase tracking-wider font-semibold block">
                  Habilidades Deseadas / Plus Demostradas
                </span>
                {evaluation.matched_preferred_skills && evaluation.matched_preferred_skills.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {evaluation.matched_preferred_skills.map((skill, i) => (
                      <span key={i} className="px-2 py-0.5 bg-white text-[#6B21A8] border border-[#E9D5FF] rounded text-[11px] font-medium font-mono">
                        +{skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-[11px] text-[#787774] italic">No se identificaron habilidades complementarias.</p>
                )}
              </div>

              {/* Análisis de Experiencia */}
              <div className="space-y-1.5">
                <h4 className="text-xs font-semibold text-[#111111] uppercase tracking-wider font-mono">
                  Análisis de Experiencia Laboral
                </h4>
                <p className="text-[#444444] leading-relaxed bg-[#FAFAFA] p-3 rounded-lg border border-[#EAEAEA]">
                  {evaluation.experience_analysis}
                </p>
              </div>

              {/* Análisis de Requisitos */}
              <div className="space-y-1.5">
                <h4 className="text-xs font-semibold text-[#111111] uppercase tracking-wider font-mono">
                  Análisis de Requisitos y Formación
                </h4>
                <p className="text-[#444444] leading-relaxed bg-[#FAFAFA] p-3 rounded-lg border border-[#EAEAEA]">
                  {evaluation.requirements_analysis}
                </p>
              </div>

              {/* Aviso Ético / Metodológico */}
              <div className="p-3.5 rounded-lg bg-[#F7F6F3] border border-[#E5E5E3] text-[11px] text-[#666666] flex items-start gap-2.5">
                <svg className="w-4 h-4 text-[#888888] shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>
                  <strong>Herramienta de preselección asistida:</strong> Esta evaluación fue generada mediante Inteligencia Artificial ({evaluation.model_used}) analizando exclusivamente la información explícita del currículum frente a los criterios del cargo. No constituye una decisión contractual ni reemplaza el criterio del evaluador humano.
                </span>
              </div>
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#EAEAEA] bg-[#FAFAFA] flex items-center justify-between gap-2">
          <div>
            {cvFileUrl && (
              <a
                href={cvFileUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-1.5 text-xs font-medium text-[#111111] bg-white hover:bg-[#F0F0EE] border border-[#D1D1CF] rounded-md transition-colors inline-flex items-center gap-1.5 shadow-xs"
              >
                <svg className="w-3.5 h-3.5 text-[#555555]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                <span>Ver CV original (PDF)</span>
              </a>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-[#111111] bg-white hover:bg-[#F0F0EE] border border-[#D1D1CF] rounded-md transition-colors"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

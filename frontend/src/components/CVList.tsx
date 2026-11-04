import React, { useState, useMemo } from 'react';
import { CandidateCV } from '../types/candidateCv';
import { candidateCvService } from '../services/candidateCvService';

interface CVListProps {
  cvs: CandidateCV[];
  jobOfferId: number;
  isLoading: boolean;
  evaluatingCvId?: number | null;
  onDeleteCV: (cv: CandidateCV) => void;
  onViewDetail: (cvId: number) => void;
  onViewEvaluation: (cv: CandidateCV) => void;
  onEvaluateCV?: (cv: CandidateCV) => void;
  onBatchEvaluate?: () => void;
}

type SortOption = 'score_desc' | 'score_asc' | 'date_desc' | 'name_asc';
type StatusFilter = 'all' | 'pending' | 'evaluated';
type RecommendationFilter = 'all' | 'recommended' | 'review' | 'not_recommended';

export const CVList: React.FC<CVListProps> = ({
  cvs,
  jobOfferId,
  isLoading,
  onDeleteCV,
  onViewDetail,
  onViewEvaluation,
}) => {
  // Search, filter, and sort state
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [recommendationFilter, setRecommendationFilter] = useState<RecommendationFilter>('all');
  const [sortBy, setSortBy] = useState<SortOption>('score_desc');
  const [experienceFilter, setExperienceFilter] = useState<'all' | '0-2' | '3-5' | '5+'>('all');
  const [educationFilter, setEducationFilter] = useState<'all' | 'tecnico' | 'profesional' | 'postgrado'>('all');

  // Badges visuales para recomendación
  const getRecommendationBadge = (recommendation: string) => {
    switch (recommendation) {
      case 'recommended':
        return {
          label: 'Recomendado',
          bg: 'bg-[#EBF5EC]',
          text: 'text-[#28572E]',
          border: 'border-[#D5EBD7]',
          dot: 'bg-[#28572E]',
          bar: 'bg-[#28572E]',
        };
      case 'review':
        return {
          label: 'Revisar',
          bg: 'bg-[#FEF7E6]',
          text: 'text-[#8F6B00]',
          border: 'border-[#FEEFC3]',
          dot: 'bg-[#8F6B00]',
          bar: 'bg-[#8F6B00]',
        };
      case 'not_recommended':
      default:
        return {
          label: 'No recomendado',
          bg: 'bg-[#FDEBEC]',
          text: 'text-[#9F2F2D]',
          border: 'border-[#F9D2D4]',
          dot: 'bg-[#9F2F2D]',
          bar: 'bg-[#9F2F2D]',
        };
    }
  };

  // Filtrado y ordenamiento en cliente
  const filteredAndSortedCvs = useMemo(() => {
    // 1. Filtrar
    const filtered = cvs.filter((cv) => {
      // Filtro de búsqueda por nombre de archivo
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        if (!cv.original_filename.toLowerCase().includes(q)) {
          return false;
        }
      }

      // Filtro por estado de evaluación
      if (statusFilter === 'pending') {
        if (cv.processing_status !== 'processed' || cv.evaluation) {
          return false;
        }
      } else if (statusFilter === 'evaluated') {
        if (!cv.evaluation) {
          return false;
        }
      }

      // Filtro por recomendación
      if (recommendationFilter !== 'all') {
        if (cv.evaluation?.recommendation !== recommendationFilter) {
          return false;
        }
      }

      if (experienceFilter !== 'all' && cv.evaluation?.experience_range !== experienceFilter) return false;
      if (educationFilter !== 'all' && cv.evaluation?.education_level !== educationFilter) return false;

      return true;
    });

    // 2. Ordenar
    return filtered.sort((a, b) => {
      if (sortBy === 'score_desc') {
        const aHasEval = Boolean(a.evaluation);
        const bHasEval = Boolean(b.evaluation);
        if (aHasEval && bHasEval) {
          return (b.evaluation?.score ?? 0) - (a.evaluation?.score ?? 0);
        }
        if (aHasEval && !bHasEval) return -1;
        if (!aHasEval && bHasEval) return 1;
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }

      if (sortBy === 'score_asc') {
        const aHasEval = Boolean(a.evaluation);
        const bHasEval = Boolean(b.evaluation);
        if (aHasEval && bHasEval) {
          return (a.evaluation?.score ?? 0) - (b.evaluation?.score ?? 0);
        }
        if (aHasEval && !bHasEval) return -1;
        if (!aHasEval && bHasEval) return 1;
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }

      if (sortBy === 'date_desc') {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }

      if (sortBy === 'name_asc') {
        return a.original_filename.localeCompare(b.original_filename);
      }

      return 0;
    });
  }, [cvs, searchQuery, statusFilter, recommendationFilter, sortBy, experienceFilter, educationFilter]);

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 bg-[#FAFAFA] border border-[#EAEAEA] rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  // Estado vacío inicial: no hay CVs en la oferta
  if (cvs.length === 0) {
    return (
      <div className="p-10 border border-[#EAEAEA] rounded-xl bg-white text-center space-y-3 shadow-xs">
        <div className="w-12 h-12 rounded-full bg-[#F4F4F2] border border-[#EAEAEA] flex items-center justify-center mx-auto text-[#787774]">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="1.5"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <p className="text-sm font-serif font-semibold text-[#111111]">
          No hay CVs cargados para esta oferta
        </p>
        <p className="text-xs text-[#787774] max-w-sm mx-auto">
          Utiliza la zona de carga para añadir los currículums de los postulantes en formato PDF.
        </p>
      </div>
    );
  }

  const handleResetFilters = () => {
    setSearchQuery('');
    setStatusFilter('all');
    setRecommendationFilter('all');
    setSortBy('score_desc');
    setExperienceFilter('all');
    setEducationFilter('all');
  };

  const pendingCount = cvs.filter((c) => c.processing_status === 'processed' && !c.evaluation).length;
  const evaluatedCount = cvs.filter((c) => Boolean(c.evaluation)).length;

  return (
    <div className="space-y-4">
      {/* Search, Filter and Sort Toolbar */}
      <div className="p-3.5 bg-[#FAFAFA] border border-[#EAEAEA] rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
        {/* Search input */}
        <div className="relative w-full md:w-64">
          <input
            type="text"
            placeholder="Buscar por nombre de archivo..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs bg-white border border-[#EAEAEA] rounded-md focus:outline-none focus:ring-1 focus:ring-[#111111] transition-all placeholder:text-[#AAAAAA]"
          />
          <svg
            className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[#888888]"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>

        {/* Filter and Sort Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Status Filter */}
          <div className="flex items-center gap-1">
            <span className="text-[11px] font-mono text-[#787774] hidden sm:inline">
              Estado:
            </span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              className="py-1 px-2.5 bg-white border border-[#EAEAEA] rounded-md text-xs font-medium text-[#111111] focus:outline-none focus:ring-1 focus:ring-[#111111]"
            >
              <option value="all">Todos ({cvs.length})</option>
              <option value="pending">Pendientes ({pendingCount})</option>
              <option value="evaluated">Evaluados ({evaluatedCount})</option>
            </select>
          </div>

          <div className="flex items-center gap-1">
            <span className="text-[11px] font-mono text-[#787774] hidden sm:inline">Experiencia:</span>
            <select value={experienceFilter} onChange={(e) => setExperienceFilter(e.target.value as typeof experienceFilter)} className="py-1 px-2.5 bg-white border border-[#EAEAEA] rounded-md text-xs font-medium text-[#111111]">
              <option value="all">Todos</option>
              <option value="0-2">0-2 años</option>
              <option value="3-5">3-5 años</option>
              <option value="5+">+5 años</option>
            </select>
          </div>

          <div className="flex items-center gap-1">
            <span className="text-[11px] font-mono text-[#787774] hidden sm:inline">Estudios:</span>
            <select value={educationFilter} onChange={(e) => setEducationFilter(e.target.value as typeof educationFilter)} className="py-1 px-2.5 bg-white border border-[#EAEAEA] rounded-md text-xs font-medium text-[#111111]">
              <option value="all">Todos</option>
              <option value="tecnico">Técnico</option>
              <option value="profesional">Profesional</option>
              <option value="postgrado">Postgrado</option>
            </select>
          </div>

          {/* Recommendation Filter */}
          <div className="flex items-center gap-1">
            <span className="text-[11px] font-mono text-[#787774] hidden sm:inline">
              Recomendación:
            </span>
            <select
              value={recommendationFilter}
              onChange={(e) => setRecommendationFilter(e.target.value as RecommendationFilter)}
              className="py-1 px-2.5 bg-white border border-[#EAEAEA] rounded-md text-xs font-medium text-[#111111] focus:outline-none focus:ring-1 focus:ring-[#111111]"
            >
              <option value="all">Todas</option>
              <option value="recommended">Recomendado</option>
              <option value="review">Revisar</option>
              <option value="not_recommended">No recomendado</option>
            </select>
          </div>

          {/* Sort By */}
          <div className="flex items-center gap-1">
            <span className="text-[11px] font-mono text-[#787774] hidden sm:inline">
              Ordenar:
            </span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="py-1 px-2.5 bg-white border border-[#EAEAEA] rounded-md text-xs font-medium text-[#111111] focus:outline-none focus:ring-1 focus:ring-[#111111]"
            >
              <option value="score_desc">Score: mayor a menor</option>
              <option value="score_asc">Score: menor a mayor</option>
              <option value="date_desc">Fecha: más reciente</option>
              <option value="name_asc">Nombre: A-Z</option>
            </select>
          </div>

          {/* Reset Filters button if any is active */}
          {(searchQuery || statusFilter !== 'all' || recommendationFilter !== 'all' || sortBy !== 'score_desc') && (
            <button
              onClick={handleResetFilters}
              className="px-2 py-1 text-[11px] text-[#666666] hover:text-[#111111] hover:underline"
              title="Restablecer filtros"
            >
              Limpiar
            </button>
          )}
        </div>
      </div>

      {/* Main Table or Filtered Empty State */}
      {filteredAndSortedCvs.length === 0 ? (
        <div className="p-8 border border-[#EAEAEA] rounded-xl bg-white text-center space-y-3">
          <p className="text-sm font-medium text-[#111111]">
            {statusFilter === 'evaluated' && evaluatedCount === 0
              ? 'Aún no hay CVs evaluados en esta oferta'
              : 'No encontramos CVs que coincidan con tu búsqueda'}
          </p>
          <p className="text-xs text-[#787774] max-w-sm mx-auto">
            {statusFilter === 'evaluated' && evaluatedCount === 0
              ? 'Puedes evaluar individualmente los CVs o procesar el lote completo.'
              : 'Prueba ajustando los términos de búsqueda o limpiando los filtros seleccionados.'}
          </p>
          <div className="pt-1 flex items-center justify-center gap-2">
            <button
                type="button"
                onClick={handleResetFilters}
                className="px-3 py-1.5 text-xs font-medium text-[#111111] bg-[#F7F6F3] hover:bg-[#EAEAE6] border border-[#EAEAEA] rounded-md transition-colors"
              >
                Restablecer filtros
              </button>
          </div>
        </div>
      ) : (
        <div className="border border-[#EAEAEA] rounded-xl bg-white overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-[#F7F6F3] border-b border-[#EAEAEA] text-[#787774] font-mono text-[11px] uppercase tracking-wider">
                  <th className="py-3 px-4 font-semibold">Candidato / CV</th>
                  <th className="py-3 px-4 font-semibold">Estado</th>
                  <th className="py-3 px-4 font-semibold">Score</th>
                  <th className="py-3 px-4 font-semibold">Compatibilidad</th>
                  <th className="py-3 px-4 font-semibold">Fecha</th>
                  <th className="py-3 px-4 font-semibold text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F0F0EE]">
                {filteredAndSortedCvs.map((cv) => {
                  const fileUrl = candidateCvService.getCVFileUrl(jobOfferId, cv.id);
                  const isCurrentEvaluating = false;
                  const hasEvaluation = Boolean(cv.evaluation);
                  const evalBadge = cv.evaluation ? getRecommendationBadge(cv.evaluation.recommendation) : null;

                  return (
                    <tr key={cv.id} className="hover:bg-[#FAFAFA] transition-colors group">
                      {/* Document / CV Name */}
                      <td className="py-3.5 px-4 font-medium text-[#111111]">
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded bg-[#FDEBEC] border border-[#F9D2D4] flex items-center justify-center text-[#9F2F2D] shrink-0 font-mono font-bold text-[10px]">
                            PDF
                          </div>
                          <div>
                            <span className="truncate max-w-[180px] sm:max-w-xs block font-semibold text-[#111111]" title={cv.original_filename}>
                              {cv.original_filename}
                            </span>
                            <span className="text-[10px] text-[#888888] font-mono block">
                              {cv.file_size_formatted}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Processing / Evaluation Status */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {isCurrentEvaluating ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-medium font-mono bg-[#FEF7E6] text-[#8F6B00] border border-[#FEEFC3]">
                            <div className="w-2.5 h-2.5 border-2 border-[#8F6B00] border-t-transparent rounded-full animate-spin" />
                            Evaluando CV...
                          </span>
                        ) : hasEvaluation ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-medium font-mono bg-[#EBF5EC] text-[#28572E] border border-[#D5EBD7]">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#28572E]" />
                            Evaluado
                          </span>
                        ) : cv.processing_status === 'processed' ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-medium font-mono bg-[#FEF3C7] text-[#B45309] border border-[#FDE68A]">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#B45309]" />
                            Pendiente de evaluación
                          </span>
                        ) : cv.processing_status === 'failed' ? (
                          <span
                            className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-medium font-mono bg-[#FDEBEC] text-[#9F2F2D] border border-[#F9D2D4] cursor-help"
                            title={cv.error_message || 'Fallo en la extracción de texto'}
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-[#9F2F2D]" />
                            Error de procesamiento
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-medium font-mono bg-[#E1F3FE] text-[#1F6C9F] border border-[#C7E6FD]">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#1F6C9F] animate-pulse" />
                            Procesando
                          </span>
                        )}
                      </td>

                      {/* Visual Score */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {cv.evaluation && evalBadge ? (
                          <div className="flex items-center gap-2">
                            <span className="font-serif font-bold text-sm text-[#111111]">
                              {cv.evaluation.score}
                              <span className="text-[10px] text-[#787774] font-mono font-normal"> / 100</span>
                            </span>
                            <div className="w-12 h-1.5 bg-[#EEEEEE] rounded-full overflow-hidden hidden sm:block">
                              <div
                                className={`h-full rounded-full ${evalBadge.bar}`}
                                style={{ width: `${Math.min(100, Math.max(0, cv.evaluation.score))}%` }}
                              />
                            </div>
                          </div>
                        ) : (
                          <span className="text-[#AAAAAA] font-mono text-[11px]">—</span>
                        )}
                      </td>

                      {/* Recommendation Badge */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {cv.evaluation && evalBadge ? (
                          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-medium font-mono border ${evalBadge.bg} ${evalBadge.text} ${evalBadge.border}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${evalBadge.dot}`} />
                            {evalBadge.label}
                          </span>
                        ) : cv.processing_status === 'processed' ? (
                          <span className="text-[#888888] font-mono text-[11px]">
                            Pendiente
                          </span>
                        ) : (
                          <span className="text-[#AAAAAA] font-mono text-[11px]">
                            No disponible
                          </span>
                        )}
                      </td>

                      {/* Upload Date */}
                      <td className="py-3.5 px-4 text-[#787774] font-mono whitespace-nowrap">
                        {new Date(cv.created_at).toLocaleDateString('es-CL')}
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          {/* Evaluar o Ver evaluación */}
                          {hasEvaluation ? (
                            <button
                              type="button"
                              onClick={() => onViewEvaluation(cv)}
                              className="px-2.5 py-1.5 text-[11px] font-medium text-[#111111] bg-[#F7F6F3] hover:bg-[#EAEAE6] border border-[#D1D1CF] rounded-md transition-colors inline-flex items-center gap-1 shadow-xs"
                              title="Ver análisis de compatibilidad detallado"
                            >
                              <svg className="w-3.5 h-3.5 text-[#1E40AF]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                              <span>Ver</span>
                            </button>
                          ) : null}

                          {/* Ver texto extraído */}
                          <button
                            type="button"
                            onClick={() => onViewDetail(cv.id)}
                            className="p-1.5 text-[#555555] hover:text-[#111111] hover:bg-[#F4F4F2] border border-[#EAEAEA] rounded transition-colors"
                            title="Ver texto extraído del PDF"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16m-7 6h7" />
                            </svg>
                          </button>

                          {/* Ver PDF original */}
                          <a
                            href={fileUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1.5 text-[#555555] hover:text-[#111111] hover:bg-[#F4F4F2] border border-[#EAEAEA] rounded transition-colors"
                            title="Abrir PDF original en pestaña nueva"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>

                          {/* Eliminar CV */}
                          <button
                            type="button"
                            onClick={() => onDeleteCV(cv)}
                            className="p-1.5 text-[#9F2F2D] hover:bg-[#FDEBEC] border border-transparent hover:border-[#F9D2D4] rounded transition-colors"
                            title="Eliminar este currículum"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

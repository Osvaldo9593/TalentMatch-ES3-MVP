import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { jobOfferService } from '../services/jobOfferService';
import { candidateCvService } from '../services/candidateCvService';
import { candidateEvaluationService } from '../services/candidateEvaluationService';
import { JobOffer } from '../types/jobOffer';
import { CandidateCV } from '../types/candidateCv';
import { CandidateEvaluation } from '../types/candidateEvaluation';
import { ConfirmModal } from '../components/ConfirmModal';
import { Toast, ToastType } from '../components/Toast';
import { CVUploadZone } from '../components/CVUploadZone';
import { CVList } from '../components/CVList';
import { CVTextPreviewModal } from '../components/CVTextPreviewModal';
import { CVEvaluationDetailModal } from '../components/CVEvaluationDetailModal';

export const JobOfferDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Offer State
  const [offer, setOffer] = useState<JobOffer | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Offer Delete State
  const [isDeleteOfferModalOpen, setIsDeleteOfferModalOpen] = useState<boolean>(false);
  const [isDeletingOffer, setIsDeletingOffer] = useState<boolean>(false);

  // CVs State
  const [cvs, setCvs] = useState<CandidateCV[]>([]);
  const [isLoadingCVs, setIsLoadingCVs] = useState<boolean>(true);
  const [previewCvId, setPreviewCvId] = useState<number | null>(null);
  const [cvToDelete, setCvToDelete] = useState<CandidateCV | null>(null);
  const [isDeletingCV, setIsDeletingCV] = useState<boolean>(false);

  // AI Evaluation State
  const [isEvaluationModalOpen, setIsEvaluationModalOpen] = useState<boolean>(false);
  const [selectedEvaluation, setSelectedEvaluation] = useState<CandidateEvaluation | null>(null);
  const [selectedEvaluationCvFilename, setSelectedEvaluationCvFilename] = useState<string | undefined>(undefined);
  const [isLoadingEvaluationModal, setIsLoadingEvaluationModal] = useState<boolean>(false);
  const [evaluationModalError, setEvaluationModalError] = useState<string | null>(null);

  // Toast Notification State
  const [toast, setToast] = useState<{ message: string; type: ToastType } | null>(null);

  useEffect(() => {
    const fetchOfferAndCVs = async () => {
      if (!id) return;
      setIsLoading(true);
      setError(null);
      try {
        const offerData = await jobOfferService.getJobOfferById(id);
        setOffer(offerData);

        // Fetch CVs
        setIsLoadingCVs(true);
        try {
          const cvsData = await candidateCvService.getCVsByJobOffer(id);
          setCvs(cvsData);
        } catch (cvErr: any) {
          console.error('Error fetching CVs:', cvErr);
        } finally {
          setIsLoadingCVs(false);
        }
      } catch (err: any) {
        setError(err.message || 'No se pudo cargar la información de la oferta.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchOfferAndCVs();
  }, [id]);

  const handleOfferDeleteConfirm = async () => {
    if (!offer) return;
    setIsDeletingOffer(true);
    try {
      await jobOfferService.deleteJobOffer(offer.id);
      setIsDeleteOfferModalOpen(false);
      navigate('/job-offers');
    } catch (err: any) {
      setToast({
        message: err.message || 'Error al eliminar la oferta.',
        type: 'error',
      });
      setIsDeletingOffer(false);
      setIsDeleteOfferModalOpen(false);
    }
  };

  const handleUploadSuccess = (newCv: CandidateCV) => {
    setCvs((prev) => [newCv, ...prev.filter((item) => item.id !== newCv.id)]);
    setToast({
      message: newCv.message || `CV "${newCv.original_filename}" cargado y enviado a evaluación automática.`,
      type: 'success',
    });
  };

  const handleCVDeleteConfirm = async () => {
    if (!offer || !cvToDelete) return;
    setIsDeletingCV(true);
    try {
      await candidateCvService.deleteCV(offer.id, cvToDelete.id);
      setCvs((prev) => prev.filter((item) => item.id !== cvToDelete.id));
      setToast({
        message: `Currículum "${cvToDelete.original_filename}" eliminado correctamente.`,
        type: 'success',
      });
      setCvToDelete(null);
    } catch (err: any) {
      setToast({
        message: err.message || 'Error al eliminar el currículum.',
        type: 'error',
      });
    } finally {
      setIsDeletingCV(false);
    }
  };

  // Handler: Ver detalle de evaluación guardada
  const handleViewEvaluation = async (cv: CandidateCV) => {
    if (!offer) return;
    setSelectedEvaluation(null);
    setSelectedEvaluationCvFilename(cv.original_filename);
    setEvaluationModalError(null);
    setIsLoadingEvaluationModal(true);
    setIsEvaluationModalOpen(true);

    try {
      const evaluationData = await candidateEvaluationService.getEvaluation(offer.id, cv.id);
      setSelectedEvaluation(evaluationData);
    } catch (err: any) {
      setEvaluationModalError(err.message || 'No fue posible cargar la evaluación.');
    } finally {
      setIsLoadingEvaluationModal(false);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12 w-full text-left space-y-6">
        <div className="h-6 bg-[#EEEEEE] rounded w-1/4 animate-pulse" />
        <div className="h-10 bg-[#EEEEEE] rounded w-2/3 animate-pulse" />
        <div className="h-40 bg-[#FAFAFA] border border-[#EAEAEA] rounded-lg animate-pulse" />
      </div>
    );
  }

  if (error || !offer) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12 w-full text-left">
        <div className="editorial-card p-10 text-center space-y-4">
          <h2 className="text-xl font-serif font-semibold text-[#111111]">
            Oferta laboral no encontrada
          </h2>
          <p className="text-xs text-[#666666]">
            {error || 'El proceso de selección solicitado no existe o fue eliminado.'}
          </p>
          <Link
            to="/job-offers"
            className="inline-flex px-4 py-2 text-xs font-medium text-white bg-[#111111] rounded-md hover:bg-[#333333]"
          >
            ← Volver al listado de ofertas
          </Link>
        </div>
      </div>
    );
  }

  const evaluatedCvs = cvs.filter((c) => Boolean(c.evaluation));
  const evaluatedCount = evaluatedCvs.length;
  const pendingEvaluationCount = cvs.filter((c) => c.processing_status === 'processed' && !c.evaluation).length;
  const averageScore = evaluatedCount > 0
    ? Math.round(evaluatedCvs.reduce((acc, c) => acc + (c.evaluation?.score ?? 0), 0) / evaluatedCount)
    : null;

  return (
    <div className="max-w-4xl mx-auto px-6 py-10 w-full text-left space-y-8">
      {/* Toast Alert */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Navigation Breadcrumb */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-mono text-[#666666]">
          <Link
            to="/dashboard"
            className="hover:text-[#111111] transition-colors inline-flex items-center gap-1"
          >
            ← Dashboard
          </Link>
          <span>/</span>
          <Link
            to="/job-offers"
            className="hover:text-[#111111] transition-colors"
          >
            Ofertas Laborales
          </Link>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to={`/job-offers/${offer.id}/edit`}
            className="px-3 py-1.5 text-xs font-medium text-[#111111] bg-white border border-[#D1D1CF] rounded-md hover:bg-[#F7F6F3] transition-colors"
          >
            Editar Oferta
          </Link>
          <button
            onClick={() => setIsDeleteOfferModalOpen(true)}
            className="px-3 py-1.5 text-xs font-medium text-[#9F2F2D] bg-[#FDEBEC] border border-[#F9D2D4] rounded-md hover:bg-[#FCD8D9] transition-colors"
          >
            Eliminar
          </button>
        </div>
      </div>

      {/* Header Profile Section */}
      <div className="space-y-3 border-b border-[#EAEAEA] pb-6">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={`px-2 py-0.5 rounded text-[11px] font-medium font-mono uppercase tracking-wider ${
              offer.status === 'active'
                ? 'bg-[#EBF5EC] text-[#28572E] border border-[#D5EBD7]'
                : 'bg-[#F0F0EE] text-[#787774] border border-[#E5E5E3]'
            }`}
          >
            {offer.status === 'active' ? 'Convocatoria Abierta' : 'Convocatoria Cerrada'}
          </span>
          {offer.employment_type && (
            <span className="px-2 py-0.5 bg-[#F7F6F3] text-[#555555] border border-[#EAEAEA] rounded text-[11px] font-mono">
              {offer.employment_type}
            </span>
          )}
          {offer.location && (
            <span className="px-2 py-0.5 bg-[#F7F6F3] text-[#555555] border border-[#EAEAEA] rounded text-[11px] font-mono">
              📍 {offer.location}
            </span>
          )}
          {offer.experience_required && (
            <span className="px-2 py-0.5 bg-[#F7F6F3] text-[#555555] border border-[#EAEAEA] rounded text-[11px] font-mono">
              Exp: {offer.experience_required}
            </span>
          )}
        </div>

        <h1 className="text-2xl sm:text-3xl font-serif font-bold text-[#111111] tracking-tight">
          {offer.title}
        </h1>

        <div className="flex items-center gap-4 text-xs text-[#787774] font-mono">
          <span>Creada: {new Date(offer.created_at).toLocaleDateString('es-CL')}</span>
          <span>•</span>
          <span>Actualizada: {new Date(offer.updated_at).toLocaleDateString('es-CL')}</span>
        </div>
      </div>

      {/* Resumen del Proceso de Selección */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-white p-4 border border-[#EAEAEA] rounded-xl shadow-xs">
        <div className="p-3 bg-[#FBFBFA] border border-[#EAEAEA] rounded-lg">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#787774] block">
            Total CVs
          </span>
          <span className="text-2xl font-serif font-bold text-[#111111] mt-1 block">
            {cvs.length}
          </span>
        </div>
        <div className="p-3 bg-[#F4FAF5] border border-[#D5EBD7] rounded-lg">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#28572E] block">
            Evaluados
          </span>
          <span className="text-2xl font-serif font-bold text-[#28572E] mt-1 block">
            {evaluatedCount}
          </span>
        </div>
        <div className="p-3 bg-[#FEF3C7] border border-[#FDE68A] rounded-lg">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#B45309] block">
            Pendientes
          </span>
          <span className="text-2xl font-serif font-bold text-[#B45309] mt-1 block">
            {pendingEvaluationCount}
          </span>
        </div>
        <div className="p-3 bg-[#EFF6FF] border border-[#DBEAFE] rounded-lg flex flex-col justify-between">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#1E40AF] block">
            Promedio de Score
          </span>
          <span className="text-sm font-serif font-bold text-[#1E40AF] mt-1 block">
            {averageScore !== null ? `${averageScore} / 100` : 'Sin evaluaciones todavía'}
          </span>
        </div>
      </div>

      {/* Description */}
      <div className="editorial-card p-6 sm:p-8 space-y-4">
        <h2 className="text-base font-serif font-semibold text-[#111111] border-b border-[#EAEAEA] pb-2">
          Descripción del Cargo
        </h2>
        <div className="text-xs text-[#333333] leading-relaxed whitespace-pre-line font-sans">
          {offer.description}
        </div>
      </div>

      {/* Selection Criteria / Skills */}
      <div className="editorial-card p-6 sm:p-8 space-y-6">
        <h2 className="text-base font-serif font-semibold text-[#111111] border-b border-[#EAEAEA] pb-2">
          Criterios de Evaluación y Habilidades
        </h2>

        {/* Required Skills */}
        <div className="space-y-2">
          <span className="text-xs font-semibold text-[#111111] uppercase tracking-wider font-mono block">
            Habilidades Obligatorias (Must Have)
          </span>
          {offer.required_skills && offer.required_skills.length > 0 ? (
            <div className="flex flex-wrap gap-2 pt-1">
              {offer.required_skills.map((skill, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-[#F0FDF4] text-[#166534] border border-[#DCFCE7] rounded-md text-xs font-medium"
                >
                  {skill}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-[#888888] italic">No se indicaron habilidades obligatorias.</p>
          )}
        </div>

        {/* Preferred Skills */}
        <div className="space-y-2 pt-2 border-t border-[#F0F0EE]">
          <span className="text-xs font-semibold text-[#111111] uppercase tracking-wider font-mono block">
            Habilidades Deseadas / Plus (Nice to Have)
          </span>
          {offer.preferred_skills && offer.preferred_skills.length > 0 ? (
            <div className="flex flex-wrap gap-2 pt-1">
              {offer.preferred_skills.map((skill, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-[#FAF5FF] text-[#6B21A8] border border-[#F3E8FF] rounded-md text-xs font-medium"
                >
                  {skill}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-[#888888] italic">No se indicaron habilidades deseadas.</p>
          )}
        </div>

        {/* Requirements */}
        <div className="space-y-2 pt-2 border-t border-[#F0F0EE]">
          <span className="text-xs font-semibold text-[#111111] uppercase tracking-wider font-mono block">
            Requisitos Generales y Académicos
          </span>
          {offer.requirements && offer.requirements.length > 0 ? (
            <ul className="space-y-2 pt-1">
              {offer.requirements.map((req, idx) => (
                <li key={idx} className="flex items-start gap-2 text-xs text-[#333333]">
                  <span className="text-[#111111] font-bold">•</span>
                  <span>{req}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-[#888888] italic">No se indicaron requisitos adicionales.</p>
          )}
        </div>
      </div>

      {/* Section: Candidatos / CVs y Clasificación con IA (Paso 4) */}
      <div className="editorial-card p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#EAEAEA] pb-4">
          <div>
            <h2 className="text-base font-serif font-semibold text-[#111111]">
              Candidatos y Evaluación de CVs con IA
            </h2>
            <p className="text-xs text-[#787774] mt-0.5">
              Carga currículums en PDF y evalúa la compatibilidad con el perfil mediante OpenRouter.
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-xs text-[#111111] bg-[#F7F6F3] border border-[#EAEAEA] px-2.5 py-1 rounded-md">
              {evaluatedCount} / {cvs.length} evaluados
            </span>

          </div>
        </div>

        {/* Upload Zone */}
        <CVUploadZone
          jobOfferId={offer.id}
          onUploadSuccess={handleUploadSuccess}
        />

        {/* CV Table List */}
        <div className="space-y-3 pt-2">
          <h3 className="text-xs font-semibold text-[#111111] uppercase tracking-wider font-mono">
            Lista de Postulantes ({cvs.length})
          </h3>
          <CVList
            cvs={cvs}
            jobOfferId={offer.id}
            isLoading={isLoadingCVs}
            onDeleteCV={(cv) => setCvToDelete(cv)}
            onViewDetail={(cvId) => setPreviewCvId(cvId)}
            onViewEvaluation={handleViewEvaluation}
            onCVsRefresh={setCvs}
          />
        </div>
      </div>

      {/* Info notice: Aviso ético sobre evaluaciones de IA */}
      <div className="p-4 rounded-xl bg-[#F7F6F3] border border-[#EAEAEA] text-xs text-[#555555] flex items-start sm:items-center gap-3">
        <svg className="w-5 h-5 text-[#888888] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="leading-relaxed">
          <strong>Aviso de preselección asistida:</strong> Las evaluaciones generadas por IA son una herramienta de apoyo para la preselección. La decisión final corresponde al reclutador.
        </span>
      </div>

      {/* Modal: Confirm deletion of Job Offer */}
      <ConfirmModal
        isOpen={isDeleteOfferModalOpen}
        title="¿Eliminar oferta laboral?"
        message={
          cvs.length > 0
            ? `Esta oferta tiene ${cvs.length} CV(s) asociado(s). Debes eliminar primero los CVs antes de eliminar la oferta.`
            : `¿Estás seguro de que deseas eliminar permanentemente la oferta "${offer.title}"?`
        }
        confirmText="Sí, eliminar oferta"
        cancelText="Cancelar"
        isLoading={isDeletingOffer}
        onConfirm={handleOfferDeleteConfirm}
        onCancel={() => setIsDeleteOfferModalOpen(false)}
      />

      {/* Modal: Confirm deletion of CV */}
      <ConfirmModal
        isOpen={cvToDelete !== null}
        title="¿Eliminar currículum?"
        message={`¿Deseas eliminar este CV? Esta acción eliminará el archivo "${cvToDelete?.original_filename}" y su información asociada.`}
        confirmText="Sí, eliminar CV"
        cancelText="Cancelar"
        isLoading={isDeletingCV}
        onConfirm={handleCVDeleteConfirm}
        onCancel={() => setCvToDelete(null)}
      />

      {/* Modal: Preview Extracted Text */}
      <CVTextPreviewModal
        isOpen={previewCvId !== null}
        jobOfferId={offer.id}
        cvId={previewCvId}
        onClose={() => setPreviewCvId(null)}
      />

      {/* Modal: AI Evaluation Details */}
      <CVEvaluationDetailModal
        isOpen={isEvaluationModalOpen}
        evaluation={selectedEvaluation}
        cvFilename={selectedEvaluationCvFilename}
        cvFileUrl={
          offer && selectedEvaluation
            ? candidateCvService.getCVFileUrl(offer.id, selectedEvaluation.cv_id)
            : undefined
        }
        isLoading={isLoadingEvaluationModal}
        error={evaluationModalError}
        onClose={() => setIsEvaluationModalOpen(false)}
      />
    </div>
  );
};

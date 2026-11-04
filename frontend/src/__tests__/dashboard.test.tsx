import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act, render, screen, fireEvent } from '@testing-library/react';
import { DashboardStats } from '../components/DashboardStats';
import { CVList } from '../components/CVList';
import { CVEvaluationDetailModal } from '../components/CVEvaluationDetailModal';
import { CandidateCV } from '../types/candidateCv';
import { CandidateEvaluation } from '../types/candidateEvaluation';
import { candidateCvService } from '../services/candidateCvService';

// Mock mock CVs
const mockCvs: CandidateCV[] = [
  {
    id: 1,
    job_offer_id: 10,
    original_filename: 'cv_carlos_soto.pdf',
    file_size: 15420,
    file_size_formatted: '15.1 KB',
    mime_type: 'application/pdf',
    processing_status: 'processed',
    error_message: null,
    created_at: '2026-09-20T10:00:00Z',
    updated_at: '2026-09-20T10:00:00Z',
    evaluation: {
      id: 101,
      score: 92,
      recommendation: 'recommended',
      created_at: '2026-09-20T10:05:00Z',
    },
  },
  {
    id: 2,
    job_offer_id: 10,
    original_filename: 'cv_ana_morales.pdf',
    file_size: 20480,
    file_size_formatted: '20.0 KB',
    mime_type: 'application/pdf',
    processing_status: 'processed',
    error_message: null,
    created_at: '2026-09-21T11:00:00Z',
    updated_at: '2026-09-21T11:00:00Z',
    evaluation: {
      id: 102,
      score: 65,
      recommendation: 'review',
      created_at: '2026-09-21T11:05:00Z',
    },
  },
  {
    id: 3,
    job_offer_id: 10,
    original_filename: 'cv_pedro_ramirez.pdf',
    file_size: 12000,
    file_size_formatted: '11.7 KB',
    mime_type: 'application/pdf',
    processing_status: 'processed',
    error_message: null,
    created_at: '2026-09-22T09:00:00Z',
    updated_at: '2026-09-22T09:00:00Z',
    evaluation: null, // Pendiente
  },
  {
    id: 4,
    job_offer_id: 10,
    original_filename: 'cv_luis_corrupto.pdf',
    file_size: 500,
    file_size_formatted: '500 B',
    mime_type: 'application/pdf',
    processing_status: 'failed',
    error_message: 'Fallo al extraer texto',
    created_at: '2026-09-22T10:00:00Z',
    updated_at: '2026-09-22T10:00:00Z',
    evaluation: null,
  },
];

const mockEvaluationDetail: CandidateEvaluation = {
  id: 101,
  cv_id: 1,
  score: 92,
  recommendation: 'recommended',
  matched_required_skills: ['Python', 'FastAPI'],
  missing_required_skills: ['AWS'],
  matched_preferred_skills: ['Docker'],
  experience_analysis: '5 años construyendo servicios escalables.',
  requirements_analysis: 'Ingeniero civil en informática con disponibilidad inmediata.',
  summary: 'Excelente perfil técnico alineado a los requisitos.',
  model_used: 'openrouter/free',
  created_at: '2026-09-20T10:05:00Z',
  updated_at: '2026-09-20T10:05:00Z',
};

describe('Paso 5 — Dashboard y Visualización de Resultados', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // 1. DashboardStats renders correctly with values
  it('1. Renderiza correctamente las métricas en DashboardStats', () => {
    const statsData = {
      active_offers: 4,
      total_cvs: 18,
      evaluated_cvs: 12,
      pending_cvs: 6,
    };

    render(<DashboardStats stats={statsData} isLoading={false} />);

    expect(screen.getByText('Ofertas Activas')).toBeDefined();
    expect(screen.getByText('4')).toBeDefined();
    expect(screen.getByText('Total de CVs')).toBeDefined();
    expect(screen.getByText('18')).toBeDefined();
    expect(screen.getByText('CVs Evaluados')).toBeDefined();
    expect(screen.getByText('12')).toBeDefined();
    expect(screen.getByText('Evaluaciones Pendientes')).toBeDefined();
    expect(screen.getByText('6')).toBeDefined();
  });

  // 2. CVList renders list of candidates
  it('2. Una oferta muestra la lista de CVs postulantes', () => {
    render(
      <CVList
        cvs={mockCvs}
        jobOfferId={10}
        isLoading={false}
        evaluatingCvId={null}
        onDeleteCV={vi.fn()}
        onViewDetail={vi.fn()}
        onEvaluateCV={vi.fn()}
        onViewEvaluation={vi.fn()}
      />
    );

    expect(screen.getByText('cv_carlos_soto.pdf')).toBeDefined();
    expect(screen.getByText('cv_ana_morales.pdf')).toBeDefined();
    expect(screen.getByText('cv_pedro_ramirez.pdf')).toBeDefined();
    expect(screen.getByText('cv_luis_corrupto.pdf')).toBeDefined();
  });

  // 3. Evaluated CVs show score and recommendation in Spanish
  it('3. Los CVs evaluados muestran su score y recomendación en español', () => {
    render(
      <CVList
        cvs={mockCvs}
        jobOfferId={10}
        isLoading={false}
        evaluatingCvId={null}
        onDeleteCV={vi.fn()}
        onViewDetail={vi.fn()}
        onEvaluateCV={vi.fn()}
        onViewEvaluation={vi.fn()}
      />
    );

    expect(screen.getByText('92')).toBeDefined();
    expect(screen.getAllByText('Recomendado').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('65')).toBeDefined();
    expect(screen.getAllByText('Revisar').length).toBeGreaterThanOrEqual(1);
  });

  // 4. Pending CVs show automatic processing status without manual action
  it('4. Los CVs procesados pendientes muestran el indicador de procesamiento sin botón manual', () => {
    render(
      <CVList
        cvs={mockCvs}
        jobOfferId={10}
        isLoading={false}
        evaluatingCvId={null}
        onDeleteCV={vi.fn()}
        onViewDetail={vi.fn()}
        onEvaluateCV={vi.fn()}
        onViewEvaluation={vi.fn()}
      />
    );

    expect(screen.getByText(/Procesando CV con IA/)).toBeDefined();
    expect(screen.queryByRole('button', { name: /evaluar/i })).toBeNull();
  });

  it('4b. Actualiza automáticamente los CVs pendientes cada cinco segundos', async () => {
    vi.useFakeTimers();
    const refresh = vi.fn();
    const getCVsByJobOffer = vi
      .spyOn(candidateCvService, 'getCVsByJobOffer')
      .mockResolvedValue(mockCvs);

    render(
      <CVList
        cvs={mockCvs}
        jobOfferId={10}
        isLoading={false}
        onDeleteCV={vi.fn()}
        onViewDetail={vi.fn()}
        onViewEvaluation={vi.fn()}
        onCVsRefresh={refresh}
      />
    );

    await act(async () => {
      vi.advanceTimersByTime(5000);
      await Promise.resolve();
    });

    expect(getCVsByJobOffer).toHaveBeenCalledWith(10);
    expect(refresh).toHaveBeenCalledWith(mockCvs);
    getCVsByJobOffer.mockRestore();
    vi.useRealTimers();
  });

  // 5. Failed CVs show Error de procesamiento
  it('5. Los CVs con error de extracción muestran "Error de procesamiento"', () => {
    render(
      <CVList
        cvs={mockCvs}
        jobOfferId={10}
        isLoading={false}
        evaluatingCvId={null}
        onDeleteCV={vi.fn()}
        onViewDetail={vi.fn()}
        onEvaluateCV={vi.fn()}
        onViewEvaluation={vi.fn()}
      />
    );

    expect(screen.getByText('Error de procesamiento')).toBeDefined();
  });

  // 6. Filter by evaluation status
  it('6. El filtro por estado (Pendientes / Evaluados) funciona correctamente', () => {
    render(
      <CVList
        cvs={mockCvs}
        jobOfferId={10}
        isLoading={false}
        evaluatingCvId={null}
        onDeleteCV={vi.fn()}
        onViewDetail={vi.fn()}
        onEvaluateCV={vi.fn()}
        onViewEvaluation={vi.fn()}
      />
    );

    // First combobox is status filter
    const comboboxes = screen.getAllByRole('combobox');
    fireEvent.change(comboboxes[0], { target: { value: 'pending' } });

    // Only pedro ramirez should be visible
    expect(screen.getByText('cv_pedro_ramirez.pdf')).toBeDefined();
    expect(screen.queryByText('cv_carlos_soto.pdf')).toBeNull();
    expect(screen.queryByText('cv_ana_morales.pdf')).toBeNull();
  });

  // 7. Filter by recommendation
  it('7. El filtro por recomendación (Recomendado / Revisar) funciona correctamente', () => {
    render(
      <CVList
        cvs={mockCvs}
        jobOfferId={10}
        isLoading={false}
        evaluatingCvId={null}
        onDeleteCV={vi.fn()}
        onViewDetail={vi.fn()}
        onEvaluateCV={vi.fn()}
        onViewEvaluation={vi.fn()}
      />
    );

    const comboboxes = screen.getAllByRole('combobox');
    // comboboxes[3] is recommendation filter after the new experience and education filters
    fireEvent.change(comboboxes[3], { target: { value: 'recommended' } });

    expect(screen.getByText('cv_carlos_soto.pdf')).toBeDefined();
    expect(screen.queryByText('cv_ana_morales.pdf')).toBeNull();
    expect(screen.queryByText('cv_pedro_ramirez.pdf')).toBeNull();
  });

  // 8. Search by filename
  it('8. La búsqueda en tiempo real por nombre de archivo funciona', () => {
    render(
      <CVList
        cvs={mockCvs}
        jobOfferId={10}
        isLoading={false}
        evaluatingCvId={null}
        onDeleteCV={vi.fn()}
        onViewDetail={vi.fn()}
        onEvaluateCV={vi.fn()}
        onViewEvaluation={vi.fn()}
      />
    );

    const searchInput = screen.getByPlaceholderText(/buscar por nombre de archivo/i);
    fireEvent.change(searchInput, { target: { value: 'ana' } });

    expect(screen.getByText('cv_ana_morales.pdf')).toBeDefined();
    expect(screen.queryByText('cv_carlos_soto.pdf')).toBeNull();
  });

  // 11. Evaluation Detail Modal displays AI analysis correctly
  it('11. El modal de detalle muestra correctamente los resultados de la IA', () => {
    const handleClose = vi.fn();

    render(
      <CVEvaluationDetailModal
        isOpen={true}
        evaluation={mockEvaluationDetail}
        cvFilename="cv_carlos_soto.pdf"
        cvFileUrl="http://localhost:8000/api/v1/job-offers/10/cvs/1/file"
        isLoading={false}
        onClose={handleClose}
      />
    );

    expect(screen.getByText('92')).toBeDefined();
    expect(screen.getByText('Recomendado')).toBeDefined();
    expect(screen.getByText('Excelente perfil técnico alineado a los requisitos.')).toBeDefined();
    expect(screen.getByText('Python')).toBeDefined();
    expect(screen.getByText('FastAPI')).toBeDefined();
    expect(screen.getByText('AWS')).toBeDefined();
    expect(screen.getByText('+Docker')).toBeDefined();
    expect(screen.getByText(/5 años construyendo servicios escalables/i)).toBeDefined();
    expect(screen.getByText(/ingeniero civil en informática/i)).toBeDefined();
    expect(screen.getByText(/ver cv original \(pdf\)/i)).toBeDefined();
  });
});

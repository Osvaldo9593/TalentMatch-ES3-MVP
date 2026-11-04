import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiService } from '../services/api';
import { dashboardService } from '../services/dashboardService';
import { jobOfferService } from '../services/jobOfferService';
import { candidateEvaluationService } from '../services/candidateEvaluationService';

describe('Frontend Services Integration & Error Handling', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('apiService.getApiHealth handles successful response', async () => {
    const mockHealth = {
      status: 'ok',
      service: 'TalentMatch API',
      version: '1.0.0',
      environment: 'development',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockHealth,
    } as any);

    const result = await apiService.getApiHealth();
    expect(result.data.status).toBe('ok');
    expect(result.data.service).toBe('TalentMatch API');
    expect(result.latencyMs).toBeGreaterThanOrEqual(0);
  });

  it('dashboardService.getDashboardStats parses consolidated metrics', async () => {
    const mockStats = {
      active_offers: 5,
      total_cvs: 18,
      evaluated_cvs: 14,
      pending_cvs: 4,
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockStats,
    } as any);

    const stats = await dashboardService.getDashboardStats();
    expect(stats.active_offers).toBe(5);
    expect(stats.total_cvs).toBe(18);
    expect(stats.evaluated_cvs).toBe(14);
    expect(stats.pending_cvs).toBe(4);
  });

  it('jobOfferService handles backend error messages gracefully', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: async () => ({
        detail: 'No se puede eliminar la oferta laboral porque tiene 2 CV(s) asociado(s).',
      }),
    } as any);

    await expect(jobOfferService.deleteJobOffer(1)).rejects.toThrow(
      'No se puede eliminar la oferta laboral porque tiene 2 CV(s) asociado(s).'
    );
  });

  it('candidateEvaluationService handles missing evaluations without freezing', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 502,
      statusText: 'Bad Gateway',
      json: async () => ({
        detail: 'El currículum aún no ha sido evaluado.',
      }),
    } as any);

    await expect(candidateEvaluationService.getEvaluation(1, 10)).rejects.toThrow(
      'El currículum aún no ha sido evaluado.'
    );
  });
});

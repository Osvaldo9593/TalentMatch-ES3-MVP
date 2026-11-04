import {
  CandidateEvaluation,
} from '../types/candidateEvaluation';

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');

class CandidateEvaluationService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  /**
   * Obtiene la evaluación guardada de un CV sin volver a llamar a la IA.
   */
  async getEvaluation(
    jobOfferId: number | string,
    cvId: number | string
  ): Promise<CandidateEvaluation> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/job-offers/${jobOfferId}/cvs/${cvId}/evaluation`,
      {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      }
    );

    if (!response.ok) {
      let errorDetail = `Error al obtener la evaluación (${response.status})`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) {
          errorDetail = typeof errorJson.detail === 'string'
            ? errorJson.detail
            : JSON.stringify(errorJson.detail);
        }
      } catch {
        // Fallback
      }
      throw new Error(errorDetail);
    }

    return response.json();
  }

}

export const candidateEvaluationService = new CandidateEvaluationService(API_BASE_URL);

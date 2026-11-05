import { CandidateCV, CandidateCVDetail, CandidateCVDeleteResponse, EvaluationProgress } from '../types/candidateCv';

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');

class CandidateCvService {
  constructor(private readonly baseUrl: string) {}

  async getCVsByJobOffer(jobOfferId: number | string): Promise<CandidateCV[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/job-offers/${jobOfferId}/cvs/`, {
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);
    return response.json();
  }

  async getEvaluationProgress(jobOfferId: number | string): Promise<EvaluationProgress> {
    const response = await fetch(`${this.baseUrl}/api/v1/job-offers/${jobOfferId}/evaluation-progress`);
    if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);
    return response.json();
  }

  async retryEvaluation(jobOfferId: number | string, cvId: number | string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/v1/job-offers/${jobOfferId}/cvs/${cvId}/evaluate`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) throw new Error(`No fue posible reintentar la evaluación (${response.status})`);
  }

  async uploadCV(jobOfferId: number | string, file: File): Promise<CandidateCV> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${this.baseUrl}/api/v1/job-offers/${jobOfferId}/cvs/`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const errorJson = await response.json().catch(() => ({}));
      throw new Error(errorJson.detail || `Error al cargar el archivo (${response.status})`);
    }
    return response.json();
  }

  async getCVDetail(jobOfferId: number | string, cvId: number | string): Promise<CandidateCVDetail> {
    const response = await fetch(`${this.baseUrl}/api/v1/job-offers/${jobOfferId}/cvs/${cvId}`);
    if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);
    return response.json();
  }

  async deleteCV(jobOfferId: number | string, cvId: number | string): Promise<CandidateCVDeleteResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/job-offers/${jobOfferId}/cvs/${cvId}`, {
      method: 'DELETE',
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) throw new Error(`Error al eliminar el CV (${response.status})`);
    return response.json();
  }

  async updateStatus(
    cvId: number,
    applicationStatus: NonNullable<CandidateCV['application_status']>,
    token: string,
  ): Promise<CandidateCV> {
    const response = await fetch(`${this.baseUrl}/api/v1/cvs/${cvId}/status`, {
      method: 'PATCH',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + token,
      },
      body: JSON.stringify({ status: applicationStatus }),
    });
    if (!response.ok) throw new Error('No fue posible actualizar el estado del candidato.');
    return response.json();
  }

  async hardDelete(cvId: number, token: string): Promise<CandidateCVDeleteResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/cvs/${cvId}/hard-delete`, {
      method: 'DELETE',
      headers: { Accept: 'application/json', Authorization: 'Bearer ' + token },
    });
    if (!response.ok) throw new Error('No fue posible eliminar definitivamente el CV.');
    return response.json();
  }

  getCVFileUrl(jobOfferId: number | string, cvId: number | string): string {
    return `${this.baseUrl}/api/v1/job-offers/${jobOfferId}/cvs/${cvId}/file`;
  }
}

export const candidateCvService = new CandidateCvService(API_BASE_URL);

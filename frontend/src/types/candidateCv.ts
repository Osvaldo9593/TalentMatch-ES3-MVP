import { CandidateEvaluationSummary } from './candidateEvaluation';

export type CandidateCVStatus = 'uploaded' | 'processing' | 'processed' | 'failed';
export type ApplicationStatus = 'PENDIENTE' | 'EN_REVISION' | 'DESCARTADO' | 'SELECCIONADO';

export interface CandidateCV {
  id: number;
  job_offer_id: number;
  original_filename: string;
  file_size: number;
  file_size_formatted: string;
  mime_type: string;
  processing_status: CandidateCVStatus;
  error_message: string | null;
  application_status?: ApplicationStatus;
  extraction_status?: string;
  created_at: string;
  updated_at: string;
  message?: string;
  evaluation?: CandidateEvaluationSummary | null;
}

export interface CandidateCVDetail extends CandidateCV {
  extracted_text: string | null;
  text_length: number;
  word_count: number;
}

export interface CandidateCVDeleteResponse {
  message: string;
  id: number;
  success: boolean;
}

export interface UploadQueueItem {
  id: string;
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  result?: CandidateCV;
  errorMessage?: string;
}

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { CVUploadZone } from '../components/CVUploadZone';
import { candidateCvService } from '../services/candidateCvService';

describe('carga de CV', () => {
  it('acepta DOCX y rechaza extensiones no soportadas', async () => {
    vi.spyOn(candidateCvService, 'uploadCV').mockResolvedValue({
      id: 1,
      job_offer_id: 1,
      original_filename: 'candidate.docx',
      file_size: 10,
      file_size_formatted: '10 B',
      mime_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      processing_status: 'processed',
      error_message: null,
      application_status: 'PENDIENTE',
      extraction_status: 'OK',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
      evaluation: null,
    });
    const onUploadSuccess = vi.fn();
    render(<CVUploadZone jobOfferId={1} onUploadSuccess={onUploadSuccess} />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, {
      target: { files: [new File(['docx'], 'candidate.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })] },
    });
    await waitFor(() => expect(onUploadSuccess).toHaveBeenCalled());

    fireEvent.change(input, {
      target: { files: [new File(['txt'], 'candidate.txt', { type: 'text/plain' })] },
    });
    expect(await screen.findByText(/solo se admiten archivos \.pdf o \.docx/)).toBeDefined();
  });
});

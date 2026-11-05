import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { CVList } from '../components/CVList';
import { CandidateCV } from '../types/candidateCv';

const cv: CandidateCV = {
  id: 1,
  job_offer_id: 1,
  original_filename: 'candidate.pdf',
  file_size: 10,
  file_size_formatted: '10 B',
  mime_type: 'application/pdf',
  processing_status: 'processed',
  error_message: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  application_status: 'PENDIENTE',
  extraction_status: 'OK',
  evaluation: null,
};

describe('acciones de CV', () => {
  it('permite cambiar el estado y muestra la acción de purga solo a admin', () => {
    const onStatusChange = vi.fn().mockResolvedValue(undefined);
    const onHardDelete = vi.fn();
    render(
      <CVList
        cvs={[cv]}
        jobOfferId={1}
        isLoading={false}
        onDeleteCV={vi.fn()}
        onViewDetail={vi.fn()}
        onViewEvaluation={vi.fn()}
        onStatusChange={onStatusChange}
        currentUserRole="admin"
        onHardDelete={onHardDelete}
      />,
    );
    fireEvent.change(screen.getByLabelText('Estado de candidate.pdf'), { target: { value: 'SELECCIONADO' } });
    expect(onStatusChange).toHaveBeenCalledWith(cv, 'SELECCIONADO');
    fireEvent.click(screen.getByTitle('Eliminar definitivamente este currículum'));
    expect(onHardDelete).toHaveBeenCalledWith(cv);
  });
});

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { EvaluationProgress } from '../EvaluationProgress';

describe('EvaluationProgress', () => {
  it('muestra el CV actual y el avance', () => {
    render(
      <EvaluationProgress
        progress={{
          total: 4,
          completed: 2,
          failed: 0,
          pending: 1,
          in_progress: 1,
          current_cv: { id: 8, original_filename: 'CV_Ingeniero.pdf' },
        }}
      />,
    );

    expect(screen.getByText(/CV_Ingeniero\.pdf/)).toBeTruthy();
    expect(screen.getByText('2 de 4 completados')).toBeTruthy();
    expect(screen.getByRole('progressbar').getAttribute('aria-valuenow')).toBe('50');
  });

  it('no renderiza una barra cuando no quedan CVs en proceso', () => {
    const { container } = render(
      <EvaluationProgress
        progress={{ total: 2, completed: 2, failed: 0, pending: 0, in_progress: 0, current_cv: null }}
      />,
    );
    expect(container.firstChild).toBeNull();
  });
});

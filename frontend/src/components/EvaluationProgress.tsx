import React from 'react';
import { EvaluationProgress as EvaluationProgressData } from '../types/candidateCv';

interface EvaluationProgressProps {
  progress: EvaluationProgressData | null;
}

export const EvaluationProgress: React.FC<EvaluationProgressProps> = ({ progress }) => {
  if (!progress || progress.total === 0 || progress.in_progress === 0) return null;

  const percentage = Math.round(((progress.completed + progress.failed) / progress.total) * 100);
  return (
    <section aria-label="Progreso de evaluación" className="rounded-xl border border-[#EAEAEA] bg-white p-4">
      <div className="flex items-center justify-between gap-3 text-xs">
        <span className="font-medium text-[#111111]">
          Analizando con IA: {progress.current_cv?.original_filename || 'CV en proceso'}
        </span>
        <span className="font-mono text-[#787774]">
          {progress.completed + progress.failed} de {progress.total} completados
        </span>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-[#EEEEEE]">
        <div
          className="h-full rounded-full bg-[#1F6C9F] transition-all duration-500"
          style={{ width: `${Math.min(100, percentage)}%` }}
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </section>
  );
};

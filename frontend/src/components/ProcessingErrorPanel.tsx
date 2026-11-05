import { CandidateCV } from '../types/candidateCv';

export function ProcessingErrorPanel({ cvs }: { cvs: CandidateCV[] }) {
  const failed = cvs.filter((cv) => cv.processing_status === 'failed' || cv.extraction_status === 'ERROR_FORMATO');
  if (!failed.length) return null;
  return (
    <aside className="rounded-lg border border-[#F9D2D4] bg-[#FDEBEC] p-4 text-left">
      <h3 className="text-sm font-semibold text-[#9F2F2D]">Archivos descartados técnicamente</h3>
      <ul className="mt-2 space-y-1 text-xs text-[#7F1D1D]">
        {failed.map((cv) => <li key={cv.id}>{cv.original_filename}: {cv.error_message || 'Error de formato o extracción.'}</li>)}
      </ul>
    </aside>
  );
}

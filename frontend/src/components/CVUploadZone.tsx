import React, { useState, useRef } from 'react';
import { candidateCvService } from '../services/candidateCvService';
import { CandidateCV, UploadQueueItem } from '../types/candidateCv';

interface CVUploadZoneProps {
  jobOfferId: number;
  onUploadSuccess: (cv: CandidateCV) => void;
  maxFileSizeMb?: number;
}

export const CVUploadZone: React.FC<CVUploadZoneProps> = ({
  jobOfferId,
  onUploadSuccess,
  maxFileSizeMb = 10,
}) => {
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [queue, setQueue] = useState<UploadQueueItem[]>([]);
  const [isProcessingQueue, setIsProcessingQueue] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const maxSizeBytes = maxFileSizeMb * 1024 * 1024;

  const handleFilesSelected = (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const newItems: UploadQueueItem[] = [];

    Array.from(files).forEach((file) => {
      // Client-side validation: PDF or DOCX
      const isPdf = file.name.toLowerCase().endsWith('.pdf') || file.type === 'application/pdf';
      const isDocx = file.name.toLowerCase().endsWith('.docx') ||
        file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
      if (!isPdf && !isDocx) {
        newItems.push({
          id: Math.random().toString(36).substring(2, 9),
          file,
          status: 'error',
          progress: 0,
          errorMessage: 'Formato no soportado (solo se admiten archivos .pdf o .docx)',
        });
        return;
      }

      // Client-side validation: max size
      if (file.size > maxSizeBytes) {
        newItems.push({
          id: Math.random().toString(36).substring(2, 9),
          file,
          status: 'error',
          progress: 0,
          errorMessage: `El archivo supera el tamaño máximo de ${maxFileSizeMb} MB`,
        });
        return;
      }

      newItems.push({
        id: Math.random().toString(36).substring(2, 9),
        file,
        status: 'pending',
        progress: 0,
      });
    });

    setQueue((prev) => [...newItems, ...prev]);

    // Clear input value so same files can be re-selected if needed
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }

    // Process pending uploads sequentially
    processUploadQueue(newItems);
  };

  const processUploadQueue = async (itemsToProcess: UploadQueueItem[]) => {
    setIsProcessingQueue(true);

    for (const item of itemsToProcess) {
      if (item.status !== 'pending') continue;

      // Update status to uploading
      setQueue((prev) =>
        prev.map((q) => (q.id === item.id ? { ...q, status: 'uploading', progress: 30 } : q))
      );

      try {
        const result = await candidateCvService.uploadCV(jobOfferId, item.file);

        setQueue((prev) =>
          prev.map((q) =>
            q.id === item.id
              ? {
                  ...q,
                  status: 'success',
                  progress: 100,
                  result,
                }
              : q
          )
        );

        onUploadSuccess(result);
      } catch (err: any) {
        setQueue((prev) =>
          prev.map((q) =>
            q.id === item.id
              ? {
                  ...q,
                  status: 'error',
                  progress: 0,
                  errorMessage: err.message || 'Error al procesar el archivo',
                }
              : q
          )
        );
      }
    }

    setIsProcessingQueue(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    handleFilesSelected(e.dataTransfer.files);
  };

  const clearQueueItem = (id: string) => {
    setQueue((prev) => prev.filter((item) => item.id !== id));
  };

  const clearCompletedQueue = () => {
    setQueue((prev) => prev.filter((item) => item.status === 'uploading' || item.status === 'pending'));
  };

  const hasFinishedItems = queue.some((q) => q.status === 'success' || q.status === 'error');

  return (
    <div className="space-y-4">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        multiple
        onChange={(e) => handleFilesSelected(e.target.files)}
        className="hidden"
      />

      {/* Drag & Drop Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-6 sm:p-8 text-center cursor-pointer transition-all duration-200 ${
          isDragging
            ? 'border-[#111111] bg-[#F7F6F3] scale-[0.99]'
            : 'border-[#D1D1CF] hover:border-[#888888] bg-[#FAFAFA] hover:bg-[#F7F6F3]'
        }`}
      >
        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-white border border-[#EAEAEA] flex items-center justify-center text-[#555555] shadow-subtle">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.75"
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>

          <div>
            <p className="text-sm font-medium text-[#111111]">
              Arrastra y suelta currículums en PDF o DOCX aquí, o{' '}
              <span className="underline underline-offset-2 text-[#111111]">selecciona archivos</span>
            </p>
            <p className="text-xs text-[#787774] mt-1 font-mono">
              Admite selección múltiple • PDF/DOCX • Máx. {maxFileSizeMb} MB por archivo
            </p>
          </div>
        </div>
      </div>

      {/* Upload queue / feedback list */}
      {queue.length > 0 && (
        <div className="border border-[#EAEAEA] rounded-lg bg-white overflow-hidden text-xs">
          <div className="px-4 py-2.5 bg-[#F7F6F3] border-b border-[#EAEAEA] flex items-center justify-between">
            <span className="font-mono font-medium text-[#111111] flex items-center gap-2">
              <span>Cargas recientes ({queue.length})</span>
              {isProcessingQueue && (
                <span className="inline-flex items-center gap-1 text-[11px] text-[#555555]">
                  <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping" />
                  Procesando...
                </span>
              )}
            </span>
            {hasFinishedItems && (
              <button
                type="button"
                onClick={clearCompletedQueue}
                className="text-[11px] text-[#787774] hover:text-[#111111] font-mono hover:underline"
              >
                Limpiar completados
              </button>
            )}
          </div>

          <div className="divide-y divide-[#F0F0EE] max-h-60 overflow-y-auto">
            {queue.map((item) => (
              <div key={item.id} className="p-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  {/* Status icon */}
                  {item.status === 'uploading' && (
                    <div className="w-5 h-5 rounded-full border-2 border-blue-500 border-t-transparent animate-spin shrink-0" />
                  )}
                  {item.status === 'success' && (
                    <div
                      className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${
                        item.result?.processing_status === 'processed'
                          ? 'bg-[#EBF5EC] text-[#28572E]'
                          : 'bg-[#FFFBEB] text-[#B45309]'
                      }`}
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  )}
                  {item.status === 'error' && (
                    <div className="w-5 h-5 rounded-full bg-[#FDEBEC] text-[#9F2F2D] flex items-center justify-center shrink-0">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </div>
                  )}
                  {item.status === 'pending' && (
                    <div className="w-5 h-5 rounded-full bg-[#F2F2F2] text-[#888888] flex items-center justify-center shrink-0">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#888888]" />
                    </div>
                  )}

                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-[#111111] truncate">{item.file.name}</p>
                    <p className="text-[11px] text-[#787774] font-mono">
                      {(item.file.size / 1024).toFixed(1)} KB •{' '}
                      {item.status === 'uploading' && 'Cargando y procesando...'}
                      {item.status === 'pending' && 'En cola...'}
                      {item.status === 'success' && (
                        <span
                          className={
                            item.result?.processing_status === 'processed'
                              ? 'text-[#28572E]'
                              : 'text-[#B45309]'
                          }
                        >
                          {item.result?.processing_status === 'processed'
                            ? 'Procesado correctamente'
                            : 'Cargado (Aviso: sin texto extraíble)'}
                        </span>
                      )}
                      {item.status === 'error' && (
                        <span className="text-[#9F2F2D]">{item.errorMessage}</span>
                      )}
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => clearQueueItem(item.id)}
                  className="text-[#888888] hover:text-[#111111] p-1 rounded transition-colors"
                  title="Cerrar notificación"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

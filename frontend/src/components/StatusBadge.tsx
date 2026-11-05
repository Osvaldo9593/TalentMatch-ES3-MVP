import React from 'react';
import { HealthStatusType } from '../types/api';

interface StatusBadgeProps {
  status: HealthStatusType;
  customText?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, customText }) => {
  if (status === 'loading') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono tracking-wider uppercase bg-[#FBF3DB] text-[#956400] border border-[#F3E7BE]">
        <span className="w-1.5 h-1.5 rounded-full bg-[#956400] animate-pulse" />
        {customText || 'Comprobando'}
      </span>
    );
  }

  if (status === 'connected') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono tracking-wider uppercase bg-[#EDF3EC] text-[#346538] border border-[#D6E5D4]">
        <span className="w-1.5 h-1.5 rounded-full bg-[#346538]" />
        {customText || 'Conectado'}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono tracking-wider uppercase bg-[#FDEBEC] text-[#9F2F2D] border border-[#F9D2D4]">
      <span className="w-1.5 h-1.5 rounded-full bg-[#9F2F2D]" />
      {customText || 'Desconectado'}
    </span>
  );
};

export function CandidateStatusBadge({ status }: { status: 'PENDIENTE' | 'EN_REVISION' | 'DESCARTADO' | 'SELECCIONADO' }) {
  const styles = {
    PENDIENTE: 'bg-[#F7F6F3] text-[#666666] border-[#EAEAEA]',
    EN_REVISION: 'bg-[#FEF7E6] text-[#8F6B00] border-[#FEEFC3]',
    DESCARTADO: 'bg-[#FDEBEC] text-[#9F2F2D] border-[#F9D2D4]',
    SELECCIONADO: 'bg-[#EBF5EC] text-[#28572E] border-[#D5EBD7]',
  };
  return <span className={`inline-flex px-2 py-1 rounded text-[10px] font-mono border ${styles[status]}`}>{status.replace('_', ' ')}</span>;
}

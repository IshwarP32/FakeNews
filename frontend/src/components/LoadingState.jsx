import React from 'react';

export default function LoadingState({ isAnalyzing }) {
  if (!isAnalyzing) return null;
  return (
    <div className="flex items-center justify-center p-4 text-xs text-slate-400 gap-2.5">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
      <span>Verifying with Multi-Agent Pipeline...</span>
    </div>
  );
}

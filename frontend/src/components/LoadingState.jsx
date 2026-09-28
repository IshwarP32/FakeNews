import React from 'react';

export default function LoadingState({ isAnalyzing }) {
  if (!isAnalyzing) return null;
  return <div className="loading-panel"><div className="progress-track"><span /></div><div><strong>PIPELINE ACTIVE</strong><p>Planner / scraper / evidence analyzer are working.</p></div></div>;
}

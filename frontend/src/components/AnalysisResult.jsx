import React from 'react';
import SourceList from './SourceList';

const verdictStyles = {
  True: {
    badge: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    icon: '✅',
    label: 'Verified True',
    border: 'border-emerald-500/20 bg-emerald-950/10',
  },
  False: {
    badge: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
    icon: '❌',
    label: 'Fabricated / False',
    border: 'border-rose-500/20 bg-rose-950/10',
  },
  'Partially True': {
    badge: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    icon: '⚠️',
    label: 'Partially True',
    border: 'border-amber-500/20 bg-amber-950/10',
  },
  Unverified: {
    badge: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
    icon: '❓',
    label: 'Unverified',
    border: 'border-white/10 bg-[#292929]',
  },
};

export default function AnalysisResult({ result }) {
  if (!result) return null;

  const verdictData = result?.verdict || {};
  const verdictKey = verdictData.verdict || 'Unverified';
  const style = verdictStyles[verdictKey] || verdictStyles.Unverified;
  const sources = verdictData.grounding_sources || [];
  const sourceUrls = verdictData.sources_used || [];

  return (
    <div className={`border rounded-2xl p-6 flex flex-col gap-5 shadow-2xl transition ${style.border}`}>
      {/* Verdict Header */}
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{style.icon}</span>
          <div>
            <span className="text-xs uppercase tracking-wider text-[#8e8e8e] block font-medium">Verdict</span>
            <h2 className="text-xl font-bold text-white">{style.label}</h2>
          </div>
        </div>

        <span className={`text-xs font-semibold uppercase tracking-wider px-3 py-1.5 rounded-full border ${style.badge}`}>
          {verdictData.confidence || 'Low'} Confidence
        </span>
      </div>

      {/* Summary */}
      {verdictData.summary && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[#8e8e8e] mb-1.5">Executive Summary</h3>
          <p className="text-sm text-[#d8d8d8] leading-relaxed">{verdictData.summary}</p>
        </div>
      )}

      {/* Reasoning Bullet Points */}
      {verdictData.reasoning && verdictData.reasoning.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[#8e8e8e] mb-2">Key Findings & Evidence</h3>
          <ul className="flex flex-col gap-2">
            {verdictData.reasoning.map((reason, i) => (
              <li key={i} className="flex items-start gap-2.5 text-xs text-[#c8c8c8] leading-relaxed">
                <span className="text-white/40 mt-0.5">•</span>
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Corrected News */}
      {verdictData.corrected_news && (
        <div className="bg-black/20 border border-white/5 p-4 rounded-xl">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[#8e8e8e] mb-1">Verified Fact Context</h3>
          <p className="text-xs text-[#b8b8b8] leading-relaxed italic">"{verdictData.corrected_news}"</p>
        </div>
      )}

      {/* Referenced Sources */}
      <SourceList sources={sources} sourceUrls={sourceUrls} />
    </div>
  );
}

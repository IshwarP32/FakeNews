import React from 'react';
import { AlertTriangle, CheckCircle2, CircleHelp, XCircle } from 'lucide-react';

const verdictStyles = {
  True: { icon: CheckCircle2, label: 'Verified True', tone: 'true' },
  False: { icon: XCircle, label: 'Fabricated / False', tone: 'false' },
  'Partially True': { icon: AlertTriangle, label: 'Partially True', tone: 'partial' },
  Misleading: { icon: AlertTriangle, label: 'Misleading', tone: 'partial' },
  'Not Checkable': { icon: CircleHelp, label: 'Not Checkable', tone: 'neutral' },
  Unverified: { icon: CircleHelp, label: 'Unverified', tone: 'neutral' },
};

export default function AnalysisResult({ result }) {
  if (!result) return <div className="result-panel empty-result"><span>Submit a claim to initialize analysis output.</span></div>;
  const verdict = result.verdict || {};
  const style = verdictStyles[verdict.verdict] || verdictStyles.Unverified;
  const Icon = style.icon;
  return <div className={`result-panel tone-${style.tone}`}>
    <div className="verdict-header"><div className="verdict-title"><span className="verdict-icon"><Icon size={22} /></span><div><p className="eyebrow">AI VERDICT</p><h2>{style.label}</h2></div></div><span className="status-chip">{verdict.confidence || 'Low'} CONFIDENCE</span></div>
    {result.coverage && <p className="coverage-line">Checked {result.coverage.articles_analysed || 0} analysed articles from {result.coverage.independent_sources || 0} independent sources.</p>}
    {verdict.summary && <div className="content-block"><h3>EXECUTIVE SUMMARY</h3><p>{verdict.summary}</p></div>}
    {verdict.date_analysis && <div className="notice-block"><h3>DATE / FRESHNESS CHECK</h3><p>{verdict.date_analysis}</p></div>}
    {verdict.reasoning?.length > 0 && <div className="content-block"><h3>KEY FINDINGS</h3><ul className="findings-list">{verdict.reasoning.map((reason, index) => <li key={index}><span>0{index + 1}</span>{reason}</li>)}</ul></div>}
    {verdict.corrected_news && <div className="content-block corrected"><h3>VERIFIED FACT CONTEXT</h3><p>"{verdict.corrected_news}"</p></div>}
    {verdict.limitations && <div className="notice-block"><h3>LIMITATIONS</h3><p>{verdict.limitations}</p></div>}
  </div>;
}

import React from 'react';
import { Check, Circle, LoaderCircle } from 'lucide-react';

const steps = [
  ['Agent 1', 'Query Planner', 'Generating search queries...'],
  ['Agent 2', 'News Scraper', 'Scraping RSS news feeds for PTI / UNI...'],
  ['Agent 3', 'Evidence Analyzer', 'Evaluating claim against evidence...'],
];

export default function AgentTimeline({ isAnalyzing, activeStep, result }) {
  const isComplete = Boolean(result);
  const activeIndex = activeStep || (isAnalyzing ? 1 : 0);
  return <section className="timeline-card"><div className="timeline-title"><div><p className="eyebrow">03 / LIVE EXECUTION</p><h2>Live Agent Execution Pipeline</h2></div><span className={`pulse-dot ${isComplete ? 'pipeline-complete' : ''}`} /></div><div className="timeline-list">{steps.map(([agent, role, detail], index) => { const complete = isComplete || activeIndex > index + 1; const active = !isComplete && isAnalyzing && activeIndex === index + 1; return <div className={`timeline-step ${complete ? 'complete' : ''} ${active ? 'active' : ''}`} key={agent}><div className="timeline-marker">{complete ? <Check size={13} /> : active ? <LoaderCircle size={13} className="spin-icon" /> : <Circle size={10} />}</div><div><strong>{agent} <span>({role})</span></strong><p>{active ? detail : complete ? 'Complete. Signals passed to next agent.' : detail}</p></div></div>; })}</div></section>;
}

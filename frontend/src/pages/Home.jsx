import React from 'react';
import { Activity, Zap } from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';
import AnalysisForm from '../components/AnalysisForm';
import ErrorMessage from '../components/ErrorMessage';
import LoadingState from '../components/LoadingState';
import AnalysisResult from '../components/AnalysisResult';
import AgentTimeline from '../components/AgentTimeline';
import SourceList from '../components/SourceList';
import MLPrediction from '../components/MLPrediction';

const quickSamples = [
  { label: 'IIT Bombay Caste Case (Real)', title: 'IIT Bombay caste discrimination case reported by official sources', text: '' },
  { label: 'Chandrayaan-3 Launch (Real)', title: 'Chandrayaan-3 successfully launched by ISRO', text: '' },
  { label: 'RBI ₹500 Note Ban (Fake)', title: 'RBI announces a ban on all ₹500 notes', text: '' },
];

export default function Home() {
  const { title, setTitle, text, setText, isAnalyzing, activeStep, result, errorMsg, handleAnalyze, handleClear, hasContent } = useAnalysis();
  const applySample = (sample) => { setTitle(sample.title); setText(sample.text); };
  return (
    <div className="app-shell">
      <main className="workspace">
        <section className="intro-row"><div><p className="eyebrow">MULTI-AGENT INTELLIGENCE TOOL</p><h1>Verify news authenticity<br />in real-time.</h1><p className="intro-copy">Our multi-agent system formulates search queries, scrapes live news feeds (PTI, UNI, PIB), and cross-examines claims.</p></div><div className="sample-area"><p className="eyebrow">QUICK TEST SAMPLES</p><div className="sample-row">{quickSamples.map((sample) => <button key={sample.label} type="button" className="sample-button" onClick={() => applySample(sample)}><Zap size={12} />{sample.label}</button>)}</div></div></section>
        <div className="analysis-grid">
          <aside className="control-column"><div className="panel-heading"><span>01 / CLAIM INPUT</span><Activity size={15} /></div><AnalysisForm title={title} setTitle={setTitle} text={text} setText={setText} onSubmit={handleAnalyze} onClear={handleClear} isAnalyzing={isAnalyzing} hasContent={hasContent} /><ErrorMessage message={errorMsg} /><LoadingState isAnalyzing={isAnalyzing} /><div className="panel-heading result-heading"><span>02 / AI VERDICT</span><span className="live-label">{result ? 'RESULT READY' : 'AWAITING INPUT'}</span></div><AnalysisResult result={result} /></aside>
          <section className="result-column"><AgentTimeline isAnalyzing={isAnalyzing} activeStep={activeStep} result={result} /><div className="panel-heading ml-heading"><span>04 / ML PREDICTION</span><span className="live-label">LOCAL CLASSIFIER</span></div><MLPrediction result={result} /></section>
        </div>
        <section className="evidence-section"><div className="evidence-heading"><div><p className="eyebrow">05 / LIVE SOURCE GROUNDING</p><h2>Scraped News Evidence Outlets</h2></div>{result?.verdict?.grounding_sources?.length ? <span className="outlet-count">{result.verdict.grounding_sources.length} VERIFIED OUTLETS</span> : null}</div><SourceList sources={result?.verdict?.grounding_sources || []} sourceUrls={result?.verdict?.sources_used || []} /></section>
      </main>
      <footer><span>TRUTH//SIGNAL</span><span>AI output is probabilistic. Inspect the cited evidence.</span></footer>
    </div>
  );
}

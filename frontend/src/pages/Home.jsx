import React from 'react';
import { Activity, Zap } from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';
import AnalysisForm from '../components/AnalysisForm';
import ErrorMessage from '../components/ErrorMessage';
import AnalysisResult from '../components/AnalysisResult';
import AgentTimeline from '../components/AgentTimeline';
import SourceList from '../components/SourceList';
import SystemGuide from '../components/SystemGuide';

const quickSamples = [
  { label: 'IIT Bombay Case (Real)', title: 'IIT Bombay caste discrimination case reported by official sources', text: '' },
  { label: 'Chandrayaan-3 Moon Landing (Real)', title: 'Chandrayaan-3 landed on the Moon on 23 August 2023', text: '' },
  { label: 'RBI ₹500 Note Ban (Fake)', title: 'RBI announces a ban on all ₹500 notes', text: '' },
];

export default function Home() {
  const { title, setTitle, text, setText, isAnalyzing, activeStep, result, errorMsg, handleAnalyze, handleClear, hasContent } = useAnalysis();
  const applySample = (sample) => { setTitle(sample.title); setText(sample.text); };
  return (
    <div className="app-shell">
      <main className="workspace">
        <section className="intro-row">
          <div>
            <p className="eyebrow">MULTI-AGENT INTELLIGENCE TOOL</p>
            <h1>Verify news authenticity<br />in real-time.</h1>
            <p className="intro-copy">
              Multi-agent verification pipeline that formulates temporal search plans, cross-examines claims across multi-platform news archives (official portals, national wires, certified fact-checkers, and major publishers), and enforces strict code-side grounding.
            </p>
          </div>
        </section>

        <section className="samples-banner">
          <div>
            <p className="eyebrow">QUICK TEST SAMPLES</p>
            <span>Load a prepared claim into the verification pipeline.</span>
          </div>
          <div className="sample-row">
            {quickSamples.map((sample) => (
              <button key={sample.label} type="button" className="sample-button" onClick={() => applySample(sample)}>
                <Zap size={12} />
                {sample.label}
              </button>
            ))}
          </div>
        </section>

        <div className="analysis-grid">
          <aside className="control-column">
            <div className="panel-heading">
              <span>01 / CLAIM INPUT</span>
              <Activity size={15} />
            </div>
            <AnalysisForm 
              title={title} 
              setTitle={setTitle} 
              text={text} 
              setText={setText} 
              onSubmit={handleAnalyze} 
              onClear={handleClear} 
              isAnalyzing={isAnalyzing} 
              hasContent={hasContent} 
            />
            <ErrorMessage message={errorMsg} />
            
            <div className="panel-heading result-heading">
              <span>02 / AI VERDICT</span>
              <span className="live-label">{result ? 'RESULT READY' : 'AWAITING INPUT'}</span>
            </div>
            <AnalysisResult result={result} />
          </aside>

          <section className="result-column">
            <AgentTimeline isAnalyzing={isAnalyzing} activeStep={activeStep} result={result} />
          </section>
        </div>

        <section className="evidence-section">
          <div className="evidence-heading">
            <div>
              <p className="eyebrow">05 / LIVE SOURCE GROUNDING</p>
              <h2>Scraped News Evidence Outlets</h2>
            </div>
            {result?.evidence_articles?.length ? (
              <span className="outlet-count">{result.evidence_articles.length} EVIDENCE ARTICLES</span>
            ) : null}
          </div>
          <SourceList 
            evidenceSources={result?.evidence_articles || []} 
            contextSources={result?.context_articles || []} 
          />
        </section>

        {/* Informative System Guide placed cleanly at the bottom */}
        <SystemGuide />
      </main>
      <footer>
        <span>VERISCAN AI // TRUTH SIGNAL</span>
        <span>Deterministic Multi-Agent Verification • Inspect cited evidence for full transparency.</span>
      </footer>
    </div>
  );
}

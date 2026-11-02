import React, { useState } from 'react';
import { Activity, Info } from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';
import AnalysisForm from '../components/AnalysisForm';
import ErrorMessage from '../components/ErrorMessage';
import AnalysisResult from '../components/AnalysisResult';
import AgentTimeline from '../components/AgentTimeline';
import SystemGuideModal from '../components/SystemGuideModal';

export default function Home() {
  const { 
    title, 
    setTitle, 
    isAnalyzing, 
    activeStep, 
    result, 
    errorMsg, 
    handleAnalyze, 
    handleClear, 
    hasContent 
  } = useAnalysis();

  const [isGuideOpen, setIsGuideOpen] = useState(false);

  return (
    <div className="app-shell">
      {/* Top Header Bar with Brand and small (i) button */}
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark">V</div>
          <div>
            <strong>VERISCAN AI</strong>
            <span>Multi-Agent News Authenticity Engine</span>
          </div>
        </div>

        <div className="topbar-actions">
          <div className="system-state">
            <i />
            <span>SYSTEM ONLINE</span>
          </div>
          
          <button
            type="button"
            className="info-icon-btn"
            onClick={() => setIsGuideOpen(true)}
            aria-label="System Guide & Methodology"
            title="System Guide & Verification Methodology"
          >
            <Info size={16} />
            <span className="info-btn-text">Methodology</span>
          </button>
        </div>
      </header>

      <main className="workspace">
        {/* Hero Section */}
        <section className="intro-row">
          <div>
            <p className="eyebrow">MULTI-AGENT INTELLIGENCE PLATFORM</p>
            <h1>Verify news authenticity<br />in real-time.</h1>
            <p className="intro-copy">
              Multi-agent verification pipeline that formulates temporal search plans, cross-examines claims across multi-platform news archives (official portals, national wires, certified fact-checkers, and major publishers), and enforces strict code-side grounding.
            </p>
          </div>
        </section>

        {/* Top Section: Single Claim Input on Left, Live Pipeline Execution beside it on Right */}
        <section className="pipeline-top-grid">
          <div className="claim-input-column">
            <div className="panel-heading">
              <span>CLAIM INPUT</span>
              <Activity size={14} />
            </div>
            <AnalysisForm 
              title={title} 
              setTitle={setTitle} 
              onSubmit={handleAnalyze} 
              onClear={handleClear} 
              isAnalyzing={isAnalyzing} 
              hasContent={hasContent} 
            />
            <ErrorMessage message={errorMsg} />
          </div>

          <div className="execution-timeline-column">
            <div className="panel-heading">
              <span>LIVE PIPELINE EXECUTION</span>
              <span className="live-label">
                {isAnalyzing ? 'RUNNING NOW' : result ? 'COMPLETED' : 'AWAITING INPUT'}
              </span>
            </div>
            <AgentTimeline 
              isAnalyzing={isAnalyzing} 
              activeStep={activeStep} 
              result={result} 
            />
          </div>
        </section>

        {/* Bottom Section: Full Width for Verification Result */}
        <section className="result-full-section">
          <div className="panel-heading result-heading">
            <span>VERIFICATION RESULT</span>
            <span className="live-label">
              {result ? 'RESULT READY' : 'AWAITING RUN'}
            </span>
          </div>
          <AnalysisResult result={result} />
        </section>
      </main>

      {/* System Guide and Methodology Popup Modal */}
      <SystemGuideModal 
        isOpen={isGuideOpen} 
        onClose={() => setIsGuideOpen(false)} 
      />

      <footer>
        <span>VERISCAN AI // TRUTH SIGNAL</span>
        <span>Deterministic Multi-Agent Verification • Inspect cited evidence for full transparency.</span>
      </footer>
    </div>
  );
}

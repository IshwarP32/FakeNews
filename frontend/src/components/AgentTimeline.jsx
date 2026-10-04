import React from 'react';
import { Check, Circle, LoaderCircle, XCircle } from 'lucide-react';

const steps = [
  ['Agent 1', 'Query Planner', 'Decomposing claim propositions & planning search queries...'],
  ['Agent 2', 'News Scraper', 'Retrieving date-bounded archives across multiple verified platforms...'],
  ['Agent 3', 'Evidence Analyzer', 'Cross-examining claim against collected evidence quotes...'],
];

export default function AgentTimeline({ isAnalyzing, activeStep, result }) {
  const isComplete = Boolean(result) && !result.error;
  const isFailed = Boolean(result?.error);
  const failedAgent = result?.error?.failed_agent || '';
  const activeIndex = activeStep || (isAnalyzing ? 1 : 0);

  const getStepState = (index) => {
    const stepNum = index + 1;
    if (isFailed) {
      if (failedAgent.includes(`Agent ${stepNum}`)) {
        return 'failed';
      }
      if (failedAgent.includes('Agent 1') && stepNum > 1) return 'unreached';
      if (failedAgent.includes('Agent 2') && stepNum > 2) return 'unreached';
      return 'complete';
    }
    if (isComplete || activeIndex > stepNum) return 'complete';
    if (!isComplete && isAnalyzing && activeIndex === stepNum) return 'active';
    return 'unreached';
  };

  return (
    <section className="timeline-card">
      <div className="timeline-title">
        <div>
          <p className="eyebrow">03 / LIVE EXECUTION</p>
          <h2>Live Agent Execution Pipeline</h2>
        </div>
        <span
          className={`pulse-dot ${
            isFailed ? 'pipeline-failed' : isComplete ? 'pipeline-complete' : ''
          }`}
        />
      </div>
      <div className="timeline-list">
        {steps.map(([agent, role, detail], index) => {
          const state = getStepState(index);
          const isCurrentActive = state === 'active';
          const isCurrentComplete = state === 'complete';
          const isCurrentFailed = state === 'failed';

          return (
            <div
              className={`timeline-step ${isCurrentComplete ? 'complete' : ''} ${
                isCurrentActive ? 'active' : ''
              } ${isCurrentFailed ? 'failed' : ''}`}
              key={agent}
            >
              <div className="timeline-marker">
                {isCurrentFailed ? (
                  <XCircle size={13} />
                ) : isCurrentComplete ? (
                  <Check size={13} />
                ) : isCurrentActive ? (
                  <LoaderCircle size={13} className="spin-icon" />
                ) : (
                  <Circle size={10} />
                )}
              </div>
              <div>
                <strong>
                  {agent} <span>({role})</span>
                </strong>
                <p>
                  {isCurrentFailed
                    ? `Failed: ${result.error?.message || result.error?.reason_code || 'Execution halted.'}`
                    : isCurrentActive
                    ? detail
                    : isCurrentComplete
                    ? 'Complete. Signals passed to next agent.'
                    : detail}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

import React from 'react';
import { AlertTriangle, CheckCircle2, CircleHelp, XCircle } from 'lucide-react';

const statusConfig = {
  supported: { label: 'Supported', tone: 'supported', icon: CheckCircle2 },
  contradicted: { label: 'Contradicted', tone: 'contradicted', icon: XCircle },
  partially_supported: { label: 'Partially supported', tone: 'partial', icon: AlertTriangle },
  contested: { label: 'Contested', tone: 'partial', icon: AlertTriangle },
  no_direct_evidence: { label: 'No direct evidence', tone: 'unknown', icon: CircleHelp },
};

export default function ClaimBreakdown({ propositions = [] }) {
  if (!propositions.length) return null;

  return (
    <div className="content-block proposition-block">
      <h3>CLAIM BREAKDOWN</h3>
      <div className="proposition-list">
        {propositions.map((proposition, index) => {
          const config = statusConfig[proposition.status] || statusConfig.no_direct_evidence;
          const Icon = config.icon;
          return (
            <article className={`proposition-card proposition-${config.tone}`} key={`${proposition.text}-${index}`}>
              <div className="proposition-header">
                <span className="proposition-number">0{index + 1}</span>
                <span className="proposition-status">
                  <Icon size={14} />
                  {config.label}
                </span>
              </div>
              <p>{proposition.text}</p>
              {proposition.note && <small>{proposition.note}</small>}
              <div className="proposition-sources">
                {proposition.supporting_ids?.length > 0 && (
                  <span className="proposition-support">Supporting: {proposition.supporting_ids.join(', ')}</span>
                )}
                {proposition.contradicting_ids?.length > 0 && (
                  <span className="proposition-contradict">Contradicting: {proposition.contradicting_ids.join(', ')}</span>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

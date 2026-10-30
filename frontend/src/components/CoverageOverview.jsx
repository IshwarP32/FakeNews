import React from 'react';
import { AlertTriangle, CheckCircle2, Database, Search, Users } from 'lucide-react';

const formatDate = (value) => {
  if (!value) return 'Not recorded';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export default function CoverageOverview({ coverage }) {
  if (!coverage) return null;

  const metrics = [
    { label: 'Queries searched', value: coverage.queries_run || coverage.windows?.length || 0, icon: Search },
    { label: 'Articles retrieved', value: coverage.articles_retrieved || 0, icon: Database },
    { label: 'Articles analysed', value: coverage.articles_analysed || 0, icon: CheckCircle2 },
    { label: 'Independent sources', value: coverage.independent_sources || 0, icon: Users },
  ];

  return (
    <div className="content-block coverage-block">
      <div className="section-heading-row">
        <div>
          <h3>VERIFICATION COVERAGE</h3>
          <p className="section-description">What the pipeline searched before producing this result.</p>
        </div>
        {coverage.retrieval_incomplete && (
          <span className="coverage-warning"><AlertTriangle size={13} /> Incomplete retrieval</span>
        )}
      </div>
      <div className="coverage-metrics">
        {metrics.map(({ label, value, icon: Icon }) => (
          <div className="coverage-metric" key={label}>
            <Icon size={15} />
            <strong>{value}</strong>
            <span>{label}</span>
          </div>
        ))}
      </div>
      <div className="coverage-range">
        <span>Publication range</span>
        <strong>{formatDate(coverage.date_range?.earliest_publication)} — {formatDate(coverage.date_range?.latest_publication)}</strong>
      </div>
      {coverage.windows?.length > 0 && (
        <div className="coverage-windows">
          {coverage.windows.map((window, index) => (
            <div className="coverage-window" key={`${window.role}-${window.after}-${index}`}>
              <span className={`window-status window-${window.status || 'ok'}`} />
              <div>
                <strong>{window.role || window.purpose || 'Search window'}</strong>
                <span>{formatDate(window.after)} — {formatDate(window.before)}</span>
              </div>
              <small>{window.items_kept || 0} kept</small>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

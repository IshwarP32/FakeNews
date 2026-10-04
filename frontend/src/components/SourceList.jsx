import React from 'react';
import { ExternalLink } from 'lucide-react';

export default function SourceList({ evidenceSources = [], contextSources = [] }) {
  if (!evidenceSources.length && !contextSources.length) return <p className="empty-sources">No validated evidence articles found.</p>;
  const renderSource = (source, index) => <a key={`${source.id}-${index}`} href={source.link} target="_blank" rel="noreferrer" className="source-item"><div className="source-card-top"><p className="source-title">{source.publisher_site || source.source || 'Unknown publisher'} <span>{source.source_tier || 'unknown'}</span></p><ExternalLink size={14} /></div><p className="source-headline">{source.title || 'Evidence article'}</p><span className="source-date">PUBLISHED {source.pub_date || 'UNKNOWN'}{source.event_date?.value ? ` | EVENT ${source.event_date.value}` : ''}</span>{source.evidence_quote ? <p className="source-quote">&quot;{source.evidence_quote}&quot;</p> : null}<p className="source-url">{source.link}</p></a>;
  const supporting = evidenceSources.filter((source) => source.stance === 'supports');
  const contradicting = evidenceSources.filter((source) => source.stance === 'contradicts');
  const renderGroup = (label, sources) => sources.length ? (
    <div className="source-group">
      <h3>{label} ({sources.length})</h3>
      <div className="sources-grid">{sources.map(renderSource)}</div>
    </div>
  ) : null;
  return (
    <div className="sources-block">
      {renderGroup('Supporting evidence', supporting)}
      {renderGroup('Contradicting evidence', contradicting)}
      {renderGroup('Historical and contextual reference articles', contextSources)}
    </div>
  );
}

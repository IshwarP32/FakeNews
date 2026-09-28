import React from 'react';
import { ExternalLink } from 'lucide-react';

export default function SourceList({ sources, sourceUrls }) {
  if ((!sources || !sources.length) && (!sourceUrls || !sourceUrls.length)) return null;
  return <div className="sources-block"><div className="sources-grid">{sources && sources.length ? sources.map((source, index) => <a key={index} href={source.url} target="_blank" rel="noreferrer" className="source-item"><div className="source-card-top"><p className="source-title">{source.publisher_site || 'Verified publisher'}</p><ExternalLink size={14} /></div><p className="source-headline">{source.title || 'Grounding article'}</p><span className="source-date">{source.pub_date || 'RECENT'}</span><p className="source-url">{source.url}</p></a>) : sourceUrls.map((source, index) => { const url = typeof source === 'string' ? source : source.url; const title = typeof source === 'string' ? source : source.title || url; return <a key={index} href={url} target="_blank" rel="noreferrer" className="source-item"><div className="source-card-top"><p className="source-title">Verified source</p><ExternalLink size={14} /></div><p className="source-headline">{title}</p><p className="source-url">{url}</p></a>; })}</div></div>;
}

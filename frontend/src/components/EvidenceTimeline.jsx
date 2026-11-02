import React from 'react';
import { CalendarDays, FileText } from 'lucide-react';

const getDate = (article) => article.event_date?.value || article.pub_date || '';

const formatDate = (value) => {
  if (!value) return 'Date unavailable';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export default function EvidenceTimeline({ evidenceSources = [], contextSources = [], historicalContext = [] }) {
  const historicalEvents = historicalContext.map((item, index) => ({
    id: `history-${index}`,
    date: item.event_date,
    title: item.statement || 'Historical context identified',
    detail: item.supporting_ids?.length ? `Supported by ${item.supporting_ids.join(', ')}` : 'Contextual reference',
    kind: 'historical',
  }));
  const articleEvents = [...evidenceSources, ...contextSources]
    .map((article) => ({
      id: article.id || article.link,
      date: getDate(article),
      title: article.title || 'Evidence article',
      detail: `${article.publisher_site || article.source || 'Unknown publisher'} · ${article.stance === 'contradicts' ? 'Contradicts claim' : article.stance === 'supports' ? 'Supports claim' : 'Context'}`,
      kind: article.stance === 'contradicts' ? 'contradicts' : article.stance === 'supports' ? 'supports' : 'context',
      link: article.link || '',
    }));
  const events = [...historicalEvents, ...articleEvents]
    .filter((event) => event.date || event.title)
    .sort((a, b) => {
      if (!a.date) return 1;
      if (!b.date) return -1;
      return new Date(a.date).getTime() - new Date(b.date).getTime();
    });

  if (!events.length) return null;

  return (
    <div className="content-block evidence-timeline-block">
      <div className="section-heading-row">
        <div>
          <h3>EVENT TIMELINE</h3>
          <p className="section-description">Publication and event dates found across the evidence set.</p>
        </div>
        <CalendarDays size={17} />
      </div>
      <div className="evidence-timeline">
        {events.map((event) => (
          <div className={`evidence-event evidence-event-${event.kind}`} key={event.id}>
            <div className="evidence-event-marker"><FileText size={13} /></div>
            <div className="evidence-event-body">
              <time>{formatDate(event.date)}</time>
              {event.link ? (
                <a
                  href={event.link}
                  target="_blank"
                  rel="noreferrer"
                  className="evidence-event-link"
                  title="Open original article"
                >
                  <strong>{event.title}</strong>
                </a>
              ) : (
                <strong>{event.title}</strong>
              )}
              <span>{event.detail}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

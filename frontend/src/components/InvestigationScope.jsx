import React, { useState } from 'react';
import { ExternalLink } from 'lucide-react';

const formatDate = (value) => {
  if (!value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
  });
};

export default function InvestigationScope({ 
  coverage, 
  evidenceArticles = [], 
  contextArticles = [], 
  analyzedArticles = [] 
}) {
  const [openIndex, setOpenIndex] = useState(null);

  if (!coverage || !coverage.windows?.length) return null;

  // Helper to get sort timestamp for a window: latest publication date first
  const getWindowSortTime = (win) => {
    if (win.before) {
      const t = new Date(win.before).getTime();
      if (!Number.isNaN(t)) return t;
    }
    if (win.after) {
      const t = new Date(win.after).getTime();
      if (!Number.isNaN(t)) return t;
    }
    return -Infinity;
  };

  // Sort windows datewise: latest first, older next, and queries without dates at the bottom
  const windows = [...coverage.windows].sort((a, b) => {
    const timeA = getWindowSortTime(a);
    const timeB = getWindowSortTime(b);
    if (timeB !== timeA) {
      return timeB - timeA;
    }
    const afterA = a.after ? new Date(a.after).getTime() : -Infinity;
    const afterB = b.after ? new Date(b.after).getTime() : -Infinity;
    if (afterB !== afterA) {
      return afterB - afterA;
    }
    return 0;
  });

  // Use all analyzed articles if available so the user sees everything that reached the LLM
  const allArticles = analyzedArticles?.length > 0
    ? analyzedArticles
    : [...evidenceArticles, ...contextArticles];

  const toggle = (i) => setOpenIndex(openIndex === i ? null : i);

  const articlesForWindow = (win) => {
    const qt = (win.query_text || '').trim().toLowerCase();
    if (qt.startsWith('wikipedia:')) {
      return allArticles.filter((a) => (a.query || '').toLowerCase().startsWith('wikipedia:'));
    }
    if (qt) {
      return allArticles.filter((a) => (a.query || '').trim().toLowerCase() === qt);
    }
    return allArticles.filter((a) => a.retrieval_pool === win.role);
  };

  const dateRange = (win) => {
    const a = formatDate(win.after);
    const b = formatDate(win.before);
    if (a && b) return `${a} – ${b}`;
    if (a) return `After ${a}`;
    if (b) return `Before ${b}`;
    return 'No date filter';
  };

  const stanceConfig = (article) => {
    if (article.relevance === 'irrelevant') {
      return { label: 'Irrelevant', cls: 'is-irrelevant' };
    }
    if (article.stance === 'supports') {
      return { label: 'Supports', cls: 'is-supports' };
    }
    if (article.stance === 'contradicts') {
      return { label: 'Contradicts', cls: 'is-contradicts' };
    }
    return { label: 'Context', cls: 'is-context' };
  };

  const totalKept = windows.reduce((sum, win) => sum + (win.items_kept ?? 0), 0);
  const totalPassedToLLM = windows.reduce((sum, win) => {
    if (typeof win.passed_to_llm === 'number') {
      return sum + win.passed_to_llm;
    }
    return sum + articlesForWindow(win).length;
  }, 0);
  const totalQueries = Math.max(coverage.queries_run || 0, windows.length);

  return (
    <div className="scope-block">
      <div className="scope-summary">
        <div className="scope-summary-left">
          <span className="scope-label">Investigation Scope & Grounding</span>
          <div className="scope-stats">
            Searched <strong>{totalQueries}</strong> queries
            <span className="sep">·</span>
            <strong>{totalKept}</strong> candidates kept
            <span className="sep">·</span>
            <strong>{totalPassedToLLM || coverage.articles_analysed || 0}</strong> passed to LLM
            <span className="sep">·</span>
            <strong>{coverage.independent_sources || 0}</strong> independent sources
          </div>
        </div>
        {coverage.date_range && (
          <div className="scope-pub-range">
            <span className="scope-range-label">Publication range</span>
            <span className="scope-range-value">
              {formatDate(coverage.date_range.earliest_publication) || '—'} – {formatDate(coverage.date_range.latest_publication) || '—'}
            </span>
          </div>
        )}
      </div>

      {windows.map((win, i) => {
        const isOpen = openIndex === i;
        const articles = articlesForWindow(win);
        const keptCount = win.items_kept ?? 0;
        const llmCount = win.passed_to_llm ?? articles.length;

        return (
          <div className={`scope-qrow${isOpen ? ' open' : ''}`} key={`${win.query_text || win.role}-${i}`}>
            <button className="scope-qtrigger" type="button" onClick={() => toggle(i)}>
              <span className="scope-qnum">{i + 1}</span>
              <div className="scope-qbody">
                <div className="scope-qtext">{win.query_text || win.role || `Query ${i + 1}`}</div>
                <div className="scope-qmeta">
                  <span className="scope-qtag scope-qtag-role">{win.role || win.purpose || 'search'}</span>
                  <span className="scope-qtag scope-qtag-date">{dateRange(win)}</span>
                  {win.site_hint && <span className="scope-qtag scope-qtag-site">site:{win.site_hint}</span>}
                </div>
              </div>
              <div className="scope-qright">
                <div className="scope-dual-counts">
                  <span className={`scope-count-tag ${keptCount > 0 ? 'is-kept' : 'is-zero'}`}>
                    {keptCount} kept
                  </span>
                  <span className="scope-count-sep">·</span>
                  <span className={`scope-count-tag ${llmCount > 0 ? 'is-llm' : 'is-zero'}`}>
                    {llmCount} to LLM
                  </span>
                </div>
                <span className="scope-qchevron">›</span>
              </div>
            </button>

            <div className="scope-qarticles">
              <div className="scope-qarticles-inner">
                {articles.length > 0 ? (
                  articles.map((article) => {
                    const stance = stanceConfig(article);
                    return (
                      <a
                        className="scope-arow"
                        key={article.id || article.link}
                        href={article.link}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        title={`Open original article from ${article.source || article.publisher_site || 'source'}`}
                      >
                        <div className="scope-aheadline-wrap">
                          <div className="scope-aheadline">
                            <span>{article.title || 'Evidence article'}</span>
                            <ExternalLink size={12} className="scope-ext-icon" />
                          </div>
                          <div className="scope-aline2">
                            <span className="scope-apub">{article.source || article.publisher_site || 'Unknown'}</span>
                            <span className="scope-atier">· {article.source_tier || 'unknown'}</span>
                            {article.pub_date && <span className="scope-adate">· {formatDate(article.pub_date)}</span>}
                            <span className="scope-aid">{article.id}</span>
                          </div>
                          {article.evidence_quote && (
                            <p className="scope-aquote">"{article.evidence_quote}"</p>
                          )}
                        </div>
                        <span className={`scope-astance ${stance.cls}`}>
                          {stance.label}
                        </span>
                      </a>
                    );
                  })
                ) : (
                  <div className="scope-qempty">
                    {keptCount > 0 && llmCount === 0 ? (
                      <span>
                        <strong>{keptCount} candidate article{keptCount > 1 ? 's' : ''} retrieved</strong> by scraper, but 0 passed ranking threshold to LLM (prioritized by concept coverage and tier quotas).
                      </span>
                    ) : keptCount === 0 ? (
                      <span>No matching articles found in news corpus for this query & time window.</span>
                    ) : (
                      <span>No articles matched this query after coverage filtering.</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

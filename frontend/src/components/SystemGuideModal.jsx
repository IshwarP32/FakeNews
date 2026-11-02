import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Scale, 
  ShieldCheck, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  CircleHelp, 
  Layers, 
  Clock, 
  FileCheck,
  Filter,
  Info,
  Server,
  Sparkles,
  X
} from 'lucide-react';

const trustedPlatformCategories = [
  {
    category: 'Official Government & Institutional Portals',
    tier: 'official',
    badge: 'Tier 1 (Highest Authority)',
    color: '#c6ac8f',
    description: 'Direct primary sources with statutory or institutional authority.',
    platforms: [
      { name: 'Press Information Bureau (PIB)', domain: 'pib.gov.in' },
      { name: 'ISRO (Space Research Org)', domain: 'isro.gov.in' },
      { name: 'Reserve Bank of India (RBI)', domain: 'rbi.org.in' },
      { name: 'Election Commission of India (ECI)', domain: 'eci.gov.in' },
      { name: 'Supreme Court of India', domain: 'supremecourtofindia.nic.in' },
    ],
  },
  {
    category: 'National Wire Agencies',
    tier: 'wire_national',
    badge: 'Tier 2 (Primary Wires)',
    color: '#38bdf8',
    description: 'First-party national reporting and verified ground correspondents.',
    platforms: [
      { name: 'Press Trust of India (PTI)', domain: 'pti.in' },
      { name: 'United News of India (UNI)', domain: 'uniindia.com' },
      { name: 'Asian News International (ANI)', domain: 'ani.in' },
    ],
  },
  {
    category: 'Certified Fact-Checking Desks',
    tier: 'factchecker',
    badge: 'Tier 3 (Fact-Checkers)',
    color: '#34d399',
    description: 'IFCN-certified fact-checking platforms specialized in viral claim debunks.',
    platforms: [
      { name: 'AltNews', domain: 'altnews.in' },
      { name: 'BOOM Live', domain: 'boomlive.in' },
      { name: 'Factly', domain: 'factly.in' },
      { name: 'The Quint WebQoof', domain: 'thequint.com' },
    ],
  },
  {
    category: 'Leading National Dailies & Publishers',
    tier: 'mainstream',
    badge: 'Tier 4 (Major Media)',
    color: '#fbbf24',
    description: 'Reputable national editorial newsrooms with established bylines.',
    platforms: [
      { name: 'The Hindu', domain: 'thehindu.com' },
      { name: 'The Indian Express', domain: 'indianexpress.com' },
      { name: 'NDTV News', domain: 'ndtv.com' },
      { name: 'Hindustan Times', domain: 'hindustantimes.com' },
      { name: 'Times of India', domain: 'timesofindia.indiatimes.com' },
      { name: 'ThePrint', domain: 'theprint.in' },
      { name: 'Firstpost', domain: 'firstpost.com' },
      { name: 'The Week', domain: 'theweek.in' },
    ],
  },
  {
    category: 'Reference & Historical Archives',
    tier: 'reference',
    badge: 'Tier 5 (Encyclopedic)',
    color: '#a78bfa',
    description: 'Encyclopedic reference archives for timeless historical context.',
    platforms: [
      { name: 'Wikipedia API', domain: 'wikipedia.org' },
      { name: 'Institutional Archives', domain: 'archive.org' },
    ],
  },
];

const scrapeMetrics = [
  {
    label: 'Raw Ingestion Volume',
    value: 'Up to 100 / query',
    desc: 'Each RSS query feed retrieves up to 100 recent & historical candidate dispatches.',
  },
  {
    label: 'Dual-Pool Quota',
    value: '≥ 1/3 per pool',
    desc: 'At least 5 slots reserved for historical archives and 5 for recent news, neutralizing recency bias.',
  },
  {
    label: 'Ranked Candidates',
    value: 'Top 15 Articles',
    desc: 'Ranked via concept coverage & source credibility priors; only the top 15 reach the LLM Analyzer.',
  },
  {
    label: 'Quote Verification',
    value: '100% Verbatim',
    desc: 'Every cited quote must match character-for-character in scraped text, or it is automatically discarded.',
  },
];

const activeFilters = [
  {
    name: '1. Date-Window Operators',
    rule: 'after:YYYY-MM-DD & before:YYYY-MM-DD',
    detail: 'Explicit event years map directly to bounded temporal search windows, ensuring claims pull authentic contemporary records.',
  },
  {
    name: '2. Concept Group Gate',
    rule: 'must_have_terms coverage',
    detail: 'Articles must match all required core entity groups (e.g. institution name + event concept). Articles matching 0 groups are immediately dropped.',
  },
  {
    name: '3. Near-Miss Confusion Penalty',
    rule: 'likely_confusions penalty',
    detail: 'Articles discussing look-alike competitions or near-miss events are penalized to prevent mistaken attribution.',
  },
  {
    name: '4. Wire Syndication Deduplication',
    rule: 'Clustering identical wire copy',
    detail: 'Identical syndicated PTI or ANI copy appearing across multiple newspapers is collapsed into 1 cluster to prevent artificial consensus.',
  },
  {
    name: '5. SSRF-Protected Body Extraction',
    rule: 'Full-text extraction with snippet fallback',
    detail: 'Extracts full body text around must-have terms. For paywalled sites, safely falls back to RSS snippets and caps confidence.',
  },
];

const verdicts = [
  {
    type: 'Verified True',
    tone: 'true',
    icon: CheckCircle2,
    meaning: 'Every core proposition is directly supported by authoritative reporting with matching event dates.',
  },
  {
    type: 'Fabricated / False',
    tone: 'false',
    icon: XCircle,
    meaning: 'Directly contradicted by affirmative statements from credible news outlets or official releases.',
  },
  {
    type: 'Partially True',
    tone: 'partial',
    icon: AlertTriangle,
    meaning: 'The central event occurred, but material details (dates, numbers, quotes, or attendees) are inaccurate.',
  },
  {
    type: 'Misleading (Recycled)',
    tone: 'partial',
    icon: AlertTriangle,
    meaning: 'An authentic older event circulating with misleading recency cues (e.g. "Breaking today") or taken out of context.',
  },
  {
    type: 'Unverified',
    tone: 'neutral',
    icon: CircleHelp,
    meaning: 'Insufficient direct reporting found in the news corpus. We never assume absence of coverage means false.',
  },
  {
    type: 'Not Checkable',
    tone: 'neutral',
    icon: CircleHelp,
    meaning: 'Subjective opinions, future predictions, satire, or value judgements that lack verifiable factual propositions.',
  },
];

const guarantees = [
  {
    icon: FileCheck,
    title: '100% Verbatim Quote Grounding',
    desc: 'Python code verifies that every cited quote is an exact character-level substring of the original article. Non-verbatim quotes are automatically discarded.',
  },
  {
    icon: Layers,
    title: 'Two-Pool Quota Retrieval',
    desc: 'Retrieval reserves separate quotas for recent and historical news pools so newer articles never crowd out authentic past records.',
  },
  {
    icon: ShieldCheck,
    title: 'Zero Tools for Evidence Analyzer',
    desc: 'The evaluating agent has zero web-browsing tools and cannot query external memory. It is strictly limited to the provided articles.',
  },
  {
    icon: Clock,
    title: 'Date & Freshness Calculus',
    desc: 'Differentiates publication date from real-world event date. Older reporting from the exact event period is accepted without recency penalties.',
  },
];

export default function SystemGuideModal({ isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState('platforms');

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div 
        className="modal-dialog guide-modal-dialog" 
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <div className="modal-header">
          <div className="modal-header-info">
            <span className="modal-eyebrow">VERISCAN AI // SYSTEM METHODOLOGY</span>
            <h2 id="modal-title">Verification Architecture & Sourcing Guide</h2>
          </div>
          <button 
            type="button" 
            className="modal-close-btn" 
            onClick={onClose}
            aria-label="Close dialog"
            title="Close (Esc)"
          >
            <X size={18} />
          </button>
        </div>

        <div className="modal-tabs">
          <button
            type="button"
            className={`modal-tab ${activeTab === 'platforms' ? 'active' : ''}`}
            onClick={() => setActiveTab('platforms')}
          >
            <Database size={14} />
            <span>Platforms & Filtering</span>
          </button>
          <button
            type="button"
            className={`modal-tab ${activeTab === 'verdicts' ? 'active' : ''}`}
            onClick={() => setActiveTab('verdicts')}
          >
            <Scale size={14} />
            <span>Verdict Classifications</span>
          </button>
          <button
            type="button"
            className={`modal-tab ${activeTab === 'guarantees' ? 'active' : ''}`}
            onClick={() => setActiveTab('guarantees')}
          >
            <ShieldCheck size={14} />
            <span>Anti-Hallucination Rules</span>
          </button>
        </div>

        <div className="modal-content-scroll">
          {activeTab === 'platforms' && (
            <div className="guide-pane">
              <div className="guide-subheading">
                <Server size={15} />
                <h3>Scraping Volume & Retrieval Quotas</h3>
              </div>
              <div className="metrics-strip">
                {scrapeMetrics.map((m) => (
                  <div key={m.label} className="metric-box">
                    <span className="metric-value">{m.value}</span>
                    <strong className="metric-label">{m.label}</strong>
                    <p className="metric-desc">{m.desc}</p>
                  </div>
                ))}
              </div>

              <div className="guide-subheading" style={{ marginTop: '24px' }}>
                <Filter size={15} />
                <h3>The 5-Stage Verification Filters</h3>
              </div>
              <div className="filters-grid">
                {activeFilters.map((f) => (
                  <div key={f.name} className="filter-card">
                    <div className="filter-card-top">
                      <strong>{f.name}</strong>
                      <code>{f.rule}</code>
                    </div>
                    <p>{f.detail}</p>
                  </div>
                ))}
              </div>

              <div className="guide-subheading" style={{ marginTop: '24px' }}>
                <Sparkles size={15} />
                <h3>Catalog of Trusted Multi-Platform Sources</h3>
              </div>
              <p className="pane-note">
                Rather than generic web crawls, VeriScan AI queries a curated taxonomy of hundreds of Indian and international news publishers categorized across five credibility tiers:
              </p>
              <div className="trusted-tiers-list">
                {trustedPlatformCategories.map((cat) => (
                  <div key={cat.category} className="tier-group-card">
                    <div className="tier-group-header">
                      <div>
                        <h4>{cat.category}</h4>
                        <p>{cat.description}</p>
                      </div>
                      <span className="tier-badge" style={{ borderColor: cat.color, color: cat.color }}>
                        {cat.badge}
                      </span>
                    </div>
                    <div className="platform-pills-row">
                      {cat.platforms.map((p) => (
                        <span key={p.domain} className="platform-pill">
                          <strong>{p.name}</strong>
                          <small>{p.domain}</small>
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'verdicts' && (
            <div className="guide-pane">
              <div className="pane-intro">
                <Info size={16} />
                <p>
                  Verdicts are synthesized through proposition-level logic enforced by code algorithms, not generative whim:
                </p>
              </div>
              <div className="verdicts-grid">
                {verdicts.map((v) => {
                  const IconComponent = v.icon;
                  return (
                    <div key={v.type} className={`verdict-explainer-card tone-${v.tone}`}>
                      <div className="verdict-explainer-header">
                        <IconComponent size={18} />
                        <strong>{v.type}</strong>
                      </div>
                      <p>{v.meaning}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {activeTab === 'guarantees' && (
            <div className="guide-pane">
              <div className="pane-intro">
                <Info size={16} />
                <p>
                  VeriScan AI enforces strict Code-Side Authority. While AI models evaluate candidate articles, deterministic Python validation rules inspect every citation:
                </p>
              </div>
              <div className="guarantees-grid">
                {guarantees.map((g) => {
                  const Icon = g.icon;
                  return (
                    <div key={g.title} className="guarantee-card">
                      <div className="guarantee-icon-wrap">
                        <Icon size={18} />
                      </div>
                      <div>
                        <strong>{g.title}</strong>
                        <p>{g.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

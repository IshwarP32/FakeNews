import React, { useState } from 'react';
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
  SlidersHorizontal,
  ExternalLink,
  Info,
  Server,
  Sparkles,
  ChevronDown,
  ChevronUp,
  BookOpen
} from 'lucide-react';

const trustedPlatformCategories = [
  {
    category: 'Official Government & Institutional Portals',
    tier: 'official',
    badge: 'Tier 1 (Highest Trust)',
    color: '#818cf8',
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
    description: 'First-party national news reporting and ground correspondents.',
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
    description: 'IFCN-certified fact-checking platforms specialized in viral debunks.',
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
    description: 'Encyclopedic reference databases for timeless historical events.',
    platforms: [
      { name: 'Wikipedia API', domain: 'wikipedia.org' },
      { name: 'Institutional Archives', domain: 'archive.org' },
    ],
  },
];

const scrapeMetrics = [
  {
    label: 'Raw Scrape Volume',
    value: 'Up to 100 / query',
    desc: 'Each RSS query feed returns up to 100 recent & historical items (retrieving 100-300+ items per claim).',
  },
  {
    label: 'Dual-Pool Quota',
    value: '≥ 1/3 per pool',
    desc: 'At least 5 slots reserved for historical archives and 5 for recent news, preventing recency bias.',
  },
  {
    label: 'Ranked Candidates',
    value: 'Top 15 Articles',
    desc: 'Scored via concept coverage & source credibility priors; only the top 15 reach Agent 3.',
  },
  {
    label: 'Quote Verification',
    value: '100% Verbatim',
    desc: 'Every supporting quote must match character-for-character, or it is automatically discarded.',
  },
];

const activeFilters = [
  {
    name: '1. Date-Window Operators',
    rule: 'after:YYYY-MM-DD & before:YYYY-MM-DD',
    detail: 'Explicit years or dates map directly to bounded search windows, ensuring historical claims pull authentic records from that era.',
  },
  {
    name: '2. Concept Group Gate',
    rule: 'must_have_terms concepts',
    detail: 'Articles must match all required core entity groups (e.g. institution name + event concept). Articles matching 0 groups are immediately dropped.',
  },
  {
    name: '3. Near-Miss Confusion Penalty',
    rule: 'likely_confusions penalty',
    detail: 'Articles discussing look-alike competitions (e.g. Inter IIT Tech Meet vs Sports Meet) are penalized to prevent mistaken attribution.',
  },
  {
    name: '4. Wire Syndication Deduplication',
    rule: 'Clustering identical wire copy',
    detail: 'If the same PTI or ANI dispatch appears in 5 newspapers, it is collapsed into 1 independent source cluster to prevent artificial consensus.',
  },
  {
    name: '5. SSRF-Protected Body Extraction',
    rule: 'Full-text extraction with snippet fallback',
    detail: 'Attempts deep text extraction around must-have terms. For paywalled sites, safely falls back to RSS snippets and caps confidence.',
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
    meaning: 'Insufficient direct reporting found in the corpus. We never assume absence of coverage means false.',
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

export default function SystemGuide() {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('platforms');

  return (
    <section className={`system-guide-section ${isOpen ? 'is-open' : ''}`}>
      <div 
        className="guide-header-bar"
        onClick={() => setIsOpen(!isOpen)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setIsOpen(!isOpen); } }}
        aria-expanded={isOpen}
      >
        <div className="guide-header-left">
          <div className="guide-icon-badge">
            <BookOpen size={20} />
          </div>
          <div className="guide-header-text">
            <p className="eyebrow">06 / VERIFICATION METHODOLOGY & SYSTEM GUIDE</p>
            <h2>How Claims Are Verified & How To Read Your Results</h2>
            <p className="guide-subtitle">
              {isOpen 
                ? 'Multi-platform sourcing hierarchy, dual-pool scraping volume, and code-enforced anti-hallucination rules.'
                : 'Click to expand our multi-platform sourcing catalog, scraping volume quotas, 5-stage filters, and verdict definitions.'}
            </p>
          </div>
        </div>

        <div className="guide-header-right">
          <span className="guide-badge-pill">3 Topics</span>
          <button 
            type="button" 
            className={`guide-toggle-btn ${isOpen ? 'active' : ''}`}
            onClick={(e) => { e.stopPropagation(); setIsOpen(!isOpen); }}
          >
            <span>{isOpen ? 'Collapse Guide' : 'View Methodology'}</span>
            {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="guide-body-wrapper">
          <div className="guide-tabs">
        <button
          type="button"
          className={`guide-tab ${activeTab === 'platforms' ? 'active' : ''}`}
          onClick={() => setActiveTab('platforms')}
        >
          <Database size={14} />
          <span>Platforms, Volume & Filters</span>
        </button>
        <button
          type="button"
          className={`guide-tab ${activeTab === 'verdicts' ? 'active' : ''}`}
          onClick={() => setActiveTab('verdicts')}
        >
          <Scale size={14} />
          <span>Verdict Classifications</span>
        </button>
        <button
          type="button"
          className={`guide-tab ${activeTab === 'guarantees' ? 'active' : ''}`}
          onClick={() => setActiveTab('guarantees')}
        >
          <ShieldCheck size={14} />
          <span>Anti-Hallucination Rules</span>
        </button>
      </div>

      <div className="guide-content-panel">
        {activeTab === 'platforms' && (
          <div className="guide-tab-pane">
            {/* Scraping Volume & Quotas Cards */}
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

            {/* Ingestion & Filtering Rules */}
            <div className="guide-subheading" style={{ marginTop: '28px' }}>
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

            {/* Trusted Platforms List by Tier */}
            <div className="guide-subheading" style={{ marginTop: '28px' }}>
              <Sparkles size={15} />
              <h3>Catalog of Trusted Multi-Platform Sources</h3>
            </div>
            <p className="pane-note">
              Rather than searching only wire snippets, VeriScan AI monitors a structured hierarchy of hundreds of Indian and global news organizations categorized into five credibility tiers:
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
          <div className="guide-tab-pane">
            <div className="pane-intro">
              <Info size={16} />
              <p>
                Verdicts are synthesized through proposition-level logic enforced by code, not generative whim. Here is what each verdict signifies:
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
          <div className="guide-tab-pane">
            <div className="pane-intro">
              <Info size={16} />
              <p>
                VeriScan AI enforces deterministic Code-Side Authority. The AI proposes assessments, but Python algorithms validate and cap every result:
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
  )}
</section>
  );
}

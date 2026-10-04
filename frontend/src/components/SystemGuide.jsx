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
  ChevronDown,
  ChevronUp,
  Info
} from 'lucide-react';

const platforms = [
  {
    tier: 'Official Portals',
    badge: 'official',
    color: '#818cf8',
    description: 'Government portals, ISRO, Supreme Court, official gazettes, and ministry releases (pib.gov.in, sci.gov.in).',
  },
  {
    tier: 'National Wires',
    badge: 'wire',
    color: '#38bdf8',
    description: 'Primary reporting wire agencies including Press Trust of India (PTI), UNI, and ANI.',
  },
  {
    tier: 'Certified Fact-Checkers',
    badge: 'factchecker',
    color: '#34d399',
    description: 'IFCN-certified fact-checking platforms including AltNews, BoomLive, and The Quint WebQoof.',
  },
  {
    tier: 'Major National Dailies',
    badge: 'mainstream',
    color: '#fbbf24',
    description: 'Leading national publications including The Hindu, Indian Express, NDTV, Times of India, and Hindustan Times.',
  },
  {
    tier: 'Reference Archives',
    badge: 'reference',
    color: '#a78bfa',
    description: 'Wikipedia and institutional encyclopedic archives for timeless historical context.',
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
  const [activeTab, setActiveTab] = useState('platforms');

  return (
    <section className="system-guide-section">
      <div className="guide-header">
        <div>
          <p className="eyebrow">06 / VERIFICATION METHODOLOGY & SYSTEM GUIDE</p>
          <h2>How Claims Are Verified & How To Read Your Results</h2>
          <p className="guide-subtitle">
            A transparent overview of our multi-platform sourcing, verdict classifications, and code-enforced anti-hallucination guarantees.
          </p>
        </div>
      </div>

      <div className="guide-tabs">
        <button
          type="button"
          className={`guide-tab ${activeTab === 'platforms' ? 'active' : ''}`}
          onClick={() => setActiveTab('platforms')}
        >
          <Database size={14} />
          <span>Multi-Platform Sourcing</span>
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
            <div className="pane-intro">
              <Info size={16} />
              <p>
                We do not rely on a single publisher or wire. Our multi-agent pipeline scrapes and cross-examines evidence across hundreds of verified portals, categorized into strict trust tiers:
              </p>
            </div>
            <div className="platforms-grid">
              {platforms.map((p) => (
                <div key={p.tier} className="platform-card">
                  <div className="platform-card-header">
                    <strong>{p.tier}</strong>
                    <span className="tier-tag">{p.badge}</span>
                  </div>
                  <p>{p.description}</p>
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
    </section>
  );
}

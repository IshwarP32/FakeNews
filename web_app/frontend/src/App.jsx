import React, { useState } from 'react';

const verdictStyles = {
  True: {
    badge: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    icon: '✅',
    label: 'Verified True',
    border: 'border-emerald-500/20 bg-emerald-950/10',
  },
  False: {
    badge: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
    icon: '❌',
    label: 'Fabricated / False',
    border: 'border-rose-500/20 bg-rose-950/10',
  },
  'Partially True': {
    badge: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    icon: '⚠️',
    label: 'Partially True',
    border: 'border-amber-500/20 bg-amber-950/10',
  },
  Unverified: {
    badge: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
    icon: '❓',
    label: 'Unverified',
    border: 'border-white/10 bg-[#292929]',
  },
};

export default function App() {
  const [title, setTitle] = useState('');
  const [text, setText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const handleAnalyze = async (e) => {
    e?.preventDefault();
    if (!title.trim() && !text.trim()) {
      setErrorMsg('Please enter a headline or article text.');
      return;
    }

    setErrorMsg('');
    setIsAnalyzing(true);
    setResult(null);

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, text }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Analysis request failed.');
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setErrorMsg(err.message || 'Unable to connect to server.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleClear = () => {
    setTitle('');
    setText('');
    setResult(null);
    setErrorMsg('');
  };

  const verdictData = result?.verdict || {};
  const verdictKey = verdictData.verdict || 'Unverified';
  const style = verdictStyles[verdictKey] || verdictStyles.Unverified;
  const sources = verdictData.grounding_sources || [];
  const sourceUrls = verdictData.sources_used || [];

  return (
    <div className="min-h-screen bg-[#1e1e1e] text-[#ececec] flex flex-col items-center px-4 py-8 md:py-12 selection:bg-[#404040]">
      {/* Top Header */}
      <header className="w-full max-w-3xl mb-8 flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center text-base font-bold text-white shadow-sm">
            FN
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-[#ececec]">Fake News Risk Analyzer</h1>
            <p className="text-xs text-[#8e8e8e]">Multi-Agent Fact Verification System</p>
          </div>
        </div>
        <span className="text-xs text-[#a0a0a0] bg-white/5 border border-white/10 px-3 py-1 rounded-full font-medium">
          Multi-Agent Pipeline
        </span>
      </header>

      {/* Main Container */}
      <main className="w-full max-w-3xl flex flex-col gap-6">
        <form onSubmit={handleAnalyze} className="flex flex-col gap-4 bg-[#262626] border border-white/10 rounded-2xl p-6 shadow-xl">
          {/* Headline Input */}
          <div className="flex flex-col gap-1.5">
            <label htmlFor="headline" className="text-xs font-semibold uppercase tracking-wider text-[#b4b4b4]">
              Headline / Claim
            </label>
            <input
              id="headline"
              type="text"
              placeholder="Paste news headline or claim to verify..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-[#1e1e1e] text-[#ececec] placeholder-[#6e6e6e] text-sm rounded-xl border border-white/10 px-4 py-3 focus:outline-none focus:ring-1 focus:ring-white/40 focus:border-white/30 transition"
            />
          </div>

          {/* Article Text Area */}
          <div className="flex flex-col gap-1.5">
            <label htmlFor="article" className="text-xs font-semibold uppercase tracking-wider text-[#b4b4b4]">
              Article Content <span className="text-[#7e7e7e] font-normal">(Optional)</span>
            </label>
            <textarea
              id="article"
              rows={5}
              placeholder="Paste full article text if available..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="w-full bg-[#1e1e1e] text-[#ececec] placeholder-[#6e6e6e] text-sm rounded-xl border border-white/10 p-4 focus:outline-none focus:ring-1 focus:ring-white/40 focus:border-white/30 transition resize-y leading-relaxed"
            />
          </div>

          {/* Error Message */}
          {errorMsg && (
            <p className="text-xs text-rose-400 bg-rose-950/20 border border-rose-500/20 p-3 rounded-lg">
              ⚠ {errorMsg}
            </p>
          )}

          {/* Action Buttons */}
          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={isAnalyzing}
              className="flex-1 bg-white text-black text-sm font-semibold px-6 py-3 rounded-xl hover:bg-[#e5e5e5] active:scale-[0.99] transition disabled:opacity-50 disabled:cursor-wait cursor-pointer shadow-md flex items-center justify-center gap-2"
            >
              {isAnalyzing ? (
                <>
                  <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-black border-t-transparent" />
                  Verifying with Agents...
                </>
              ) : (
                'Verify News Claim'
              )}
            </button>

            {(title || text || result) && (
              <button
                type="button"
                onClick={handleClear}
                className="bg-transparent text-[#b4b4b4] hover:text-white text-sm font-medium px-5 py-3 rounded-xl hover:bg-white/5 active:scale-[0.99] border border-white/10 transition cursor-pointer"
              >
                Clear
              </button>
            )}
          </div>
        </form>

        {/* Results Output Card */}
        {result && (
          <div className={`border rounded-2xl p-6 flex flex-col gap-5 shadow-2xl transition ${style.border}`}>
            {/* Verdict Header */}
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{style.icon}</span>
                <div>
                  <span className="text-xs uppercase tracking-wider text-[#8e8e8e] block font-medium">Verdict</span>
                  <h2 className="text-xl font-bold text-white">{style.label}</h2>
                </div>
              </div>

              <span className={`text-xs font-semibold uppercase tracking-wider px-3 py-1.5 rounded-full border ${style.badge}`}>
                {verdictData.confidence || 'Low'} Confidence
              </span>
            </div>

            {/* Summary */}
            {verdictData.summary && (
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[#8e8e8e] mb-1.5">Executive Summary</h3>
                <p className="text-sm text-[#d8d8d8] leading-relaxed">{verdictData.summary}</p>
              </div>
            )}

            {/* Reasoning Bullet Points */}
            {verdictData.reasoning && verdictData.reasoning.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[#8e8e8e] mb-2">Key Findings & Evidence</h3>
                <ul className="flex flex-col gap-2">
                  {verdictData.reasoning.map((reason, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-xs text-[#c8c8c8] leading-relaxed">
                      <span className="text-white/40 mt-0.5">•</span>
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Corrected News */}
            {verdictData.corrected_news && (
              <div className="bg-black/20 border border-white/5 p-4 rounded-xl">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[#8e8e8e] mb-1">Verified Fact Context</h3>
                <p className="text-xs text-[#b8b8b8] leading-relaxed italic">"{verdictData.corrected_news}"</p>
              </div>
            )}

            {/* Referenced Sources */}
            {(sources.length > 0 || sourceUrls.length > 0) && (
              <div className="border-t border-white/10 pt-4 mt-1">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[#8e8e8e] mb-3">Scraped News Evidence Outlets</h3>
                <div className="grid gap-2.5 md:grid-cols-2">
                  {sources.length > 0
                    ? sources.map((src, i) => (
                        <a
                          key={i}
                          href={src.url}
                          target="_blank"
                          rel="noreferrer"
                          className="bg-[#242424] border border-white/10 p-3 rounded-xl hover:border-white/30 transition block"
                        >
                          <p className="text-xs font-medium text-[#ececec] truncate">{src.title || src.url}</p>
                          <p className="text-[11px] text-[#787878] truncate mt-0.5">{src.url}</p>
                        </a>
                      ))
                    : sourceUrls.map((url, i) => (
                        <a
                          key={i}
                          href={typeof url === 'string' ? url : url.url}
                          target="_blank"
                          rel="noreferrer"
                          className="bg-[#242424] border border-white/10 p-3 rounded-xl hover:border-white/30 transition block"
                        >
                          <p className="text-xs font-medium text-[#ececec] truncate">{typeof url === 'string' ? url : url.title || url.url}</p>
                        </a>
                      ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

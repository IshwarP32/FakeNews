import React, { useState } from 'react';

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

  return (
    <div className="min-h-screen bg-[#212121] text-[#ececec] flex flex-col items-center px-4 py-8 md:py-16 selection:bg-[#404040]">
      {/* Top Header */}
      <header className="w-full max-w-2xl mb-8 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-sm font-semibold text-white">
            FN
          </div>
          <h1 className="text-lg font-medium tracking-tight text-[#ececec]">Fake News Detector</h1>
        </div>
        <span className="text-xs text-[#8e8e8e] bg-white/5 border border-white/10 px-2.5 py-1 rounded-full">
          ML Model
        </span>
      </header>

      {/* Main Container */}
      <main className="w-full max-w-2xl flex flex-col gap-6">
        <form onSubmit={handleAnalyze} className="flex flex-col gap-4">
          {/* Headline Input */}
          <div className="flex flex-col gap-1.5">
            <label htmlFor="headline" className="text-xs font-medium text-[#b4b4b4]">
              Headline
            </label>
            <input
              id="headline"
              type="text"
              placeholder="Paste article title or headline..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-[#2f2f2f] text-[#ececec] placeholder-[#8e8e8e] text-sm rounded-xl border border-white/10 px-4 py-3 focus:outline-none focus:ring-1 focus:ring-white/30 focus:border-white/20 transition"
            />
          </div>

          {/* Article Text Area */}
          <div className="flex flex-col gap-1.5">
            <label htmlFor="article" className="text-xs font-medium text-[#b4b4b4]">
              Article Content
            </label>
            <textarea
              id="article"
              rows={7}
              placeholder="Paste the news story or article text here..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="w-full bg-[#2f2f2f] text-[#ececec] placeholder-[#8e8e8e] text-sm rounded-xl border border-white/10 p-4 focus:outline-none focus:ring-1 focus:ring-white/30 focus:border-white/20 transition resize-y leading-relaxed"
            />
          </div>

          {/* Error Message */}
          {errorMsg && (
            <p className="text-xs text-red-400 px-1">
              {errorMsg}
            </p>
          )}

          {/* Action Buttons */}
          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={isAnalyzing}
              className="bg-white text-black text-sm font-medium px-5 py-2.5 rounded-full hover:bg-[#e5e5e5] active:scale-[0.98] transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {isAnalyzing ? 'Analyzing...' : 'Analyze'}
            </button>
            <button
              type="button"
              onClick={handleClear}
              className="bg-transparent text-[#b4b4b4] hover:text-white text-sm font-medium px-4 py-2.5 rounded-full hover:bg-white/5 active:scale-[0.98] transition cursor-pointer"
            >
              Clear
            </button>
          </div>
        </form>

        {/* Minimal Score Output Card */}
        {result && (
          <div className="mt-4 bg-[#2f2f2f] border border-white/10 rounded-2xl p-6 flex flex-col gap-4 animate-in fade-in duration-200">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-wider text-[#8e8e8e] font-semibold">
                Result
              </span>
              <span
                className={`text-xs font-semibold px-3 py-1 rounded-full ${
                  result.prediction === 'Fake'
                    ? 'bg-red-500/15 text-red-400 border border-red-500/30'
                    : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                }`}
              >
                {result.prediction === 'Fake' ? 'Likely Fake News' : 'Likely Real News'}
              </span>
            </div>

            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold tracking-tight text-white">
                {result.score}%
              </span>
              <span className="text-sm text-[#8e8e8e]">
                Fake Likelihood Score
              </span>
            </div>

            {/* Simple progress bar */}
            <div className="w-full bg-black/30 h-2 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  result.score >= 50 ? 'bg-red-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${result.score}%` }}
              />
            </div>

            <div className="flex justify-between text-xs text-[#8e8e8e] pt-1">
              <span>Real ({result.real_probability}%)</span>
              <span>Fake ({result.fake_probability}%)</span>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

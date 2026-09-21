import React from 'react';

export default function AnalysisForm({
  title,
  setTitle,
  text,
  setText,
  onSubmit,
  onClear,
  isAnalyzing,
  hasContent,
}) {
  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4 bg-[#262626] border border-white/10 rounded-2xl p-6 shadow-xl">
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

        {hasContent && (
          <button
            type="button"
            onClick={onClear}
            className="bg-transparent text-[#b4b4b4] hover:text-white text-sm font-medium px-5 py-3 rounded-xl hover:bg-white/5 active:scale-[0.99] border border-white/10 transition cursor-pointer"
          >
            Clear
          </button>
        )}
      </div>
    </form>
  );
}

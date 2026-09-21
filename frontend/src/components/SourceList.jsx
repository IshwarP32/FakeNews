import React from 'react';

export default function SourceList({ sources, sourceUrls }) {
  if ((!sources || sources.length === 0) && (!sourceUrls || sourceUrls.length === 0)) {
    return null;
  }

  const itemsToRender = sources && sources.length > 0 ? sources : sourceUrls;

  return (
    <div className="border-t border-white/10 pt-4 mt-1">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[#8e8e8e]">
          Scraped News Evidence Outlets ({itemsToRender.length} Sources Found)
        </h3>
      </div>
      
      <div className="grid gap-2.5 md:grid-cols-2">
        {sources && sources.length > 0
          ? sources.map((src, i) => {
              const displayUrl = src.publisher_site || src.url || '';
              return (
                <a
                  key={i}
                  href={src.url}
                  target="_blank"
                  rel="noreferrer"
                  className="bg-[#242424] border border-white/10 p-3 rounded-xl hover:border-white/30 transition block group"
                >
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <p className="text-xs font-medium text-[#ececec] truncate group-hover:text-white">
                      {src.title || displayUrl}
                    </p>
                    {src.pub_date && (
                      <span className="text-[10px] bg-white/10 text-white/70 px-2 py-0.5 rounded-full shrink-0">
                        📅 {src.pub_date}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-[#787878] truncate mt-0.5 font-mono">
                    {displayUrl}
                  </p>
                </a>
              );
            })
          : sourceUrls.map((url, i) => {
              const rawUrl = typeof url === 'string' ? url : url.url || '';
              const title = typeof url === 'string' ? url : url.title || rawUrl;
              return (
                <a
                  key={i}
                  href={rawUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="bg-[#242424] border border-white/10 p-3 rounded-xl hover:border-white/30 transition block"
                >
                  <p className="text-xs font-medium text-[#ececec] truncate">{title}</p>
                  <p className="text-[11px] text-[#787878] truncate mt-0.5 font-mono">{rawUrl}</p>
                </a>
              );
            })}
      </div>
    </div>
  );
}

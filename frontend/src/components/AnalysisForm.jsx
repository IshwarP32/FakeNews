import React from 'react';
import { ArrowUpRight, RotateCcw, Sparkles } from 'lucide-react';

export default function AnalysisForm({ 
  title, 
  setTitle, 
  onSubmit, 
  onClear, 
  isAnalyzing, 
  hasContent 
}) {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      if (!isAnalyzing && title?.trim()) {
        onSubmit(e);
      }
    }
  };

  return (
    <form onSubmit={onSubmit} className="input-panel">
      <div className="field-group single-field-group">
        <div className="field-label-row">
          <label htmlFor="claim-input">
            CLAIM STATEMENT OR HEADLINE
          </label>
          <span className="field-hint">CTRL + ENTER TO RUN</span>
        </div>
        <div className="input-wrapper">
          <textarea
            id="claim-input"
            rows={5}
            placeholder="Paste any headline, viral statement, or claim to verify against official archives and live reporting..."
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onKeyDown={handleKeyDown}
            className="text-input claim-textarea"
            disabled={isAnalyzing}
          />
        </div>
      </div>

      <div className="action-row">
        <button
          type="submit"
          disabled={isAnalyzing || !title?.trim()}
          className="primary-button"
        >
          {isAnalyzing ? (
            <>
              <span className="spinner" />
              <span>RUNNING PIPELINE...</span>
            </>
          ) : (
            <>
              <Sparkles size={15} />
              <span>RUN VERIFICATION</span>
              <ArrowUpRight size={15} />
            </>
          )}
        </button>

        {hasContent && (
          <button
            type="button"
            onClick={onClear}
            disabled={isAnalyzing}
            className="ghost-button"
            title="Clear claim and output"
          >
            <RotateCcw size={13} />
            <span>CLEAR</span>
          </button>
        )}
      </div>
    </form>
  );
}

import React from 'react';
import { ArrowUpRight, RotateCcw } from 'lucide-react';

export default function AnalysisForm({ title, setTitle, text, setText, onSubmit, onClear, isAnalyzing, hasContent }) {
  return (
    <form onSubmit={onSubmit} className="input-panel">
      <div className="field-group"><label htmlFor="headline">HEADLINE / CLAIM <span>REQUIRED</span></label><input id="headline" type="text" placeholder="Paste a headline or claim..." value={title} onChange={(e) => setTitle(e.target.value)} className="text-input" /></div>
      <div className="field-group"><label htmlFor="article">ARTICLE CONTENT <span>OPTIONAL</span></label><textarea id="article" rows={6} placeholder="Paste supporting article text for a deeper read..." value={text} onChange={(e) => setText(e.target.value)} className="text-input text-area" /></div>
      <div className="action-row"><button type="submit" disabled={isAnalyzing} className="primary-button">{isAnalyzing ? <><span className="spinner" /> RUNNING PIPELINE</> : <>RUN VERIFICATION PIPELINE <ArrowUpRight size={16} /></>}</button>{hasContent && <button type="button" onClick={onClear} className="ghost-button"><RotateCcw size={14} /> CLEAR</button>}</div>
    </form>
  );
}

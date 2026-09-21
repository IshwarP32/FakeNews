import React from 'react';
import { useAnalysis } from '../context/AnalysisContext';
import AnalysisForm from '../components/AnalysisForm';
import ErrorMessage from '../components/ErrorMessage';
import LoadingState from '../components/LoadingState';
import AnalysisResult from '../components/AnalysisResult';

export default function Home() {
  const {
    title,
    setTitle,
    text,
    setText,
    isAnalyzing,
    result,
    errorMsg,
    handleAnalyze,
    handleClear,
    hasContent,
  } = useAnalysis();

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

      {/* Main Content */}
      <main className="w-full max-w-3xl flex flex-col gap-6">
        <AnalysisForm
          title={title}
          setTitle={setTitle}
          text={text}
          setText={setText}
          onSubmit={handleAnalyze}
          onClear={handleClear}
          isAnalyzing={isAnalyzing}
          hasContent={hasContent}
        />

        <ErrorMessage message={errorMsg} />

        <LoadingState isAnalyzing={isAnalyzing} />

        <AnalysisResult result={result} />
      </main>
    </div>
  );
}

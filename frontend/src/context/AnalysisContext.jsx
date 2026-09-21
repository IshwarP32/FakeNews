import React, { createContext, useContext, useState, useEffect } from 'react';
import { analyzeClaimApi } from '../services/analysisApi';

const AnalysisContext = createContext();

export function AnalysisProvider({ children }) {
  const [title, setTitle] = useState(() => sessionStorage.getItem('fn_title') || '');
  const [text, setText] = useState(() => sessionStorage.getItem('fn_text') || '');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(() => {
    try {
      const saved = sessionStorage.getItem('fn_result');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    sessionStorage.setItem('fn_title', title);
  }, [title]);

  useEffect(() => {
    sessionStorage.setItem('fn_text', text);
  }, [text]);

  useEffect(() => {
    if (result) {
      sessionStorage.setItem('fn_result', JSON.stringify(result));
    } else {
      sessionStorage.removeItem('fn_result');
    }
  }, [result]);

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
      const data = await analyzeClaimApi({ title, text });
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
    sessionStorage.removeItem('fn_title');
    sessionStorage.removeItem('fn_text');
    sessionStorage.removeItem('fn_result');
  };

  return (
    <AnalysisContext.Provider
      value={{
        title,
        setTitle,
        text,
        setText,
        isAnalyzing,
        result,
        errorMsg,
        handleAnalyze,
        handleClear,
        hasContent: Boolean(title || text || result),
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis() {
  return useContext(AnalysisContext);
}

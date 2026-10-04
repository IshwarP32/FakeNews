import React, { createContext, useContext, useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { analyzeClaimStreamApi } from '../services/analysisApi';

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
  const [activeStep, setActiveStep] = useState(0);

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
      const msg = 'Please enter a headline or article text.';
      setErrorMsg(msg);
      toast.warn(msg, { toastId: 'empty-input' });
      return;
    }

    setErrorMsg('');
    setIsAnalyzing(true);
    setResult(null);
    setActiveStep(1);

    try {
      const data = await analyzeClaimStreamApi({
        title,
        text,
        onProgress: ({ event }) => {
          if (event === 'query_planning') setActiveStep(1);
          if (event === 'web_scraping') setActiveStep(2);
          if (event === 'analyzing_evidence') setActiveStep(3);
        },
      });
      setResult(data);

      if (data?.error) {
        toast.error(data.error, { toastId: 'api-error', autoClose: 6000 });
      } else if (data?.verdict?.flags?.includes('llm_unavailable')) {
        toast.error('AI models are currently unavailable due to API limits.', { toastId: 'quota-alert', autoClose: 6000 });
      } else if (data?.verdict?.flags?.includes('retrieval_incomplete')) {
        toast.info('Notice: Some news source queries timed out; verified with available articles.', { toastId: 'partial-retrieval' });
      } else {
        toast.success('Verification analysis complete!', { toastId: 'analysis-success', autoClose: 3500 });
      }
    } catch (err) {
      const msg = err.message || 'Unable to connect to server.';
      setErrorMsg(msg);
      toast.error(msg, { toastId: 'analysis-error', autoClose: 6000 });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleClear = () => {
    setTitle('');
    setText('');
    setResult(null);
    setErrorMsg('');
    setActiveStep(0);
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
        activeStep,
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

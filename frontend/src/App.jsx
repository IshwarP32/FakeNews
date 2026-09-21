import React from 'react';
import { AnalysisProvider } from './context/AnalysisContext';
import Home from './pages/Home';

export default function App() {
  return (
    <AnalysisProvider>
      <Home />
    </AnalysisProvider>
  );
}

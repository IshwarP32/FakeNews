import React from 'react';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { AnalysisProvider } from './context/AnalysisContext';
import Home from './pages/Home';

export default function App() {
  return (
    <AnalysisProvider>
      <Home />
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
      />
    </AnalysisProvider>
  );
}

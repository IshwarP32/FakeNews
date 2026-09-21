# Fake News Verifier - React Frontend Application

This is the React frontend client for the **Fake News Risk Analyzer**, built using React, Vite, and Tailwind CSS.

## Directory Structure

```
frontend/
├── src/
│   ├── assets/             # Static brand images & icons
│   ├── components/         # Modular UI Components
│   │   ├── AnalysisForm.jsx
│   │   ├── AnalysisResult.jsx
│   │   ├── SourceList.jsx
│   │   ├── LoadingState.jsx
│   │   └── ErrorMessage.jsx
│   ├── context/            # Analysis state management & reload persistence
│   │   └── AnalysisContext.jsx
│   ├── pages/              # Main Application Page Layouts
│   │   └── Home.jsx
│   ├── services/           # Backend API Service Client
│   │   └── analysisApi.js
│   ├── App.css
│   ├── App.jsx             # Root composition component
│   ├── index.css           # Tailwind base styles
│   └── main.jsx            # Entry point
├── index.html
├── package.json
├── vite.config.js
└── README.md
```

## Setup & Running

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start development server:
   ```bash
   npm run dev
   ```

3. Build production bundle:
   ```bash
   npm run build
   ```

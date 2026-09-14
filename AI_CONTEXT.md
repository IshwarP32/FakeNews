# Fake News Risk Analyzer - AI Context

> Persistent handoff file for future AI agents and project sessions. Update this file whenever a decision, implementation change, learning milestone, or blocker occurs.

## Project Snapshot

- **Project:** Fake News Risk Analyzer
- **Current stage:** Full-stack Web Application (FastAPI + React Vite) & Risk Engine
- **Last updated:** 2026-09-14

- **Source document:** `proposal.html`
- **Current workspace:** Contains the proposal, context documentation, two Kaggle CSV datasets under `data/`, and the initial Python baseline structure.

## Problem

Misinformation spreads quickly and can create confusion, fear, and social disruption. A binary true/false result is often too limited for practical use because it does not communicate how suspicious, harmful, urgent, or sensitive a piece of content may be.

## Proposed Solution

Build an application that analyzes a news title, article, or URL and assigns an explainable misinformation **risk score/level**. The result should consider:

- Source reliability
- Emotional tone
- Urgency cues
- Suspicious keywords or language patterns
- Topic sensitivity
- Estimated misinformation severity
- AI-assisted evidence and explanation from trusted-source context

The system should explain why it produced a result. It should not present the risk score as an absolute proof that an article is true or false.

## High-Level Flow

1. **Input:** News title, article text, or URL
2. **Preprocess:** Clean text and extract relevant features
3. **Risk analysis:** Score source, tone, urgency, keywords, and severity
4. **AI evidence:** Use trusted-source context to explain the result
5. **Output:** Risk level, reasons, and evidence summary

## Planned Checkpoints

1. **Problem definition:** Finalize the goal, target use case, and boundaries.
2. **Dataset and baseline:** Review a Kaggle fake/real news dataset and build a baseline text classifier.
3. **Preprocessing and feature design:** Clean text and extract linguistic/content features such as sentiment, urgency, and suspicious language.
4. **Risk engine:** Implement scoring for source reliability, emotional tone, topic sensitivity, and misinformation severity.
5. **Backend and database:** Add backend services, persistence, analyzed articles, scores, and explanations.
6. **AI evidence layer:** Integrate a GenAI API for evidence-based, user-friendly reasoning.
7. **Testing and refinement:** Test the complete workflow and improve model/logic quality.
8. **Final demo and documentation:** Prepare an end-to-end demonstration and document results.

## Technology Direction

These technologies are suggested by the proposal, but have not been finalized:

- **Language/data:** Python
- **NLP/ML:** Text preprocessing, TF-IDF, Logistic Regression and/or Naive Bayes
- **Backend:** Flask or FastAPI
- **API format:** JSON request/response handling and REST endpoints
- **Database:** SQLAlchemy or another SQL model layer
- **Frontend:** React dashboard
- **AI explanation:** GenAI API with carefully designed prompts
- **Possible later enhancement:** Vector search or retrieval-based evidence lookup

Do not add a technology until it supports a concrete project requirement. Prefer the smallest stack that can produce a reliable local demo.

## Dataset Inspection

The two Kaggle files were inspected with a streaming CSV script. They were not loaded into memory or printed in full.

| File | Approximate size | Rows | Columns |
|---|---:|---:|---|
| `Fake.csv` | 62.8 MB | 23,481 | `title`, `text`, `subject`, `date` |
| `True.csv` | 53.6 MB | 21,417 | `title`, `text`, `subject`, `date` |

Observed examples suggest that fake articles commonly have `subject` values such as `News`, while true examples include values such as `politicsNews`; this is a dataset characteristic that must be investigated because it could create label leakage if used directly as a model feature. The `date` field also needs normalization and duplicate/date-overlap checks.

### Dataset decision for the first experiment

- Combine both files and add a generated label: `0 = fake`, `1 = true`.
- Use `title` and `text` as the initial text input, after checking missing values and duplicates.
- Preserve `subject` and `date` for exploratory analysis and reporting, but exclude them from the first baseline model until leakage is assessed.
- Use a stratified train/validation/test split with a fixed random seed so results are reproducible.
- Avoid loading both full dataframes when a streaming or chunked approach is sufficient; the files are large but manageable with a careful local script.

### Dataset limitations to document

- The labels come from the dataset files and may reflect publisher/source conventions rather than universal truth.
- The examples appear concentrated in a particular news and political time period, so performance may not generalize to current news.
- A high classification score will not prove that the system can fact-check arbitrary real-world articles.
- Near-duplicate articles and stylistic/source artifacts may inflate evaluation scores.
- The initial profile found 5,574 repeated title/text rows after the first occurrence in `Fake.csv` and 221 in `True.csv`.
- The initial profile found 630 missing text values in `Fake.csv` and 1 in `True.csv`; the first trainer skips rows with no usable title/text.

## Current Decisions

- The eventual core output is a **risk assessment with reasons**, not only a fake/real label.
- The system should combine a measurable baseline/model with interpretable rule or feature signals.
- Explanations and evidence are part of the product requirement, not a decorative extra.
- The first useful milestone should be a small, testable local workflow before adding the full frontend, database, or GenAI integration.
- The project should focus on learning and demonstrating the minimum practical technologies needed for a working solution.
- The first model input combines available `title` and `text` fields, falling back to whichever field is present; `subject` and `date` are initially analysis-only fields.
- The first classifier uses the generated `fake/true` labels and provides a model-based fake-news likelihood. A user-facing risk score/level will be added later as a separate explainable layer.
- The initial implementation uses Python scripts, scikit-learn TF-IDF, Logistic Regression, and joblib model artifacts.
- The model implementation is split into reusable training functions in `scripts/train_model.py` and a removable presentation walkthrough in `scripts/demo_model.py`.
- The large CSV files are stored under `data/` and excluded from version control; generated reports and models are also excluded.

## Decisions Still Open

- Choose Flask versus FastAPI.
- Choose the initial database and schema.
- Select and verify the dataset, including its labels, licensing, and limitations.
- Define the risk scale and thresholds, for example low/medium/high.
- Decide how source reliability will be represented when the input is only article text.
- Decide which trusted sources and retrieval method will support AI evidence.
- Select the GenAI provider/API and define privacy, cost, rate-limit, and failure behavior.
- Decide whether URL fetching is part of the first demo or a later milestone.
- Define the React dashboard screens and the minimum user workflow.

## Immediate Next Steps

1. Inspect the workspace and confirm the preferred Python environment.
2. Review the profile report and define duplicate handling before final evaluation.
3. Define the first narrow vertical slice: text input -> preprocessing -> fake-news likelihood result.
4. Install dependencies and run the first title-plus-text baseline.
5. Add a small evaluation script using accuracy, precision, recall, and F1-score.
6. Compare a title-only baseline with a title-plus-text baseline.
7. Record every technology and behavior decision in this file as it is made.

## Learning Requirements

### Must learn

- Python basics and data handling
- NLP cleaning, tokenization, stop words, stemming/lemmatization
- Text classification with TF-IDF, Logistic Regression, and/or Naive Bayes
- REST APIs with Flask or FastAPI
- JSON and request/response handling
- GenAI API calls and prompt design
- SQLAlchemy or equivalent SQL model operations
- React basics for a simple dashboard

### Recommended

- Sentiment analysis and keyword feature extraction
- Accuracy, precision, recall, and F1-score
- Presenting model outputs in a web app
- Basic local deployment or hosting

### Optional

- Vector search or retrieval-based evidence lookup
- Advanced prompt engineering
- Topic modeling or clustering

## Validation and Quality Notes

- Keep the current model as a reference so later risk-engine improvements can be compared objectively.
- Evaluate false positives and false negatives, not only overall accuracy.
- Treat AI-generated explanations as potentially fallible and show evidence/source context where possible.
- Avoid claiming certainty about truthfulness when the current model only estimates fake-news likelihood from learned text patterns.
- Test empty, very short, very long, malformed, and unsupported inputs.
- Keep secrets such as API keys out of source files and version control.

## Progress Log

### 2026-09-07 - Initial context created

- Read `proposal.html`.
- Confirmed the project scope, high-level flow, planned checkpoints, and learning requirements.
- Confirmed that the workspace contains two large Kaggle datasets under `data/`: `Fake.csv` and `True.csv`.
- Confirmed both datasets have columns `title`, `text`, `subject`, and `date`.
- Counted 23,481 fake rows and 21,417 true rows using a streaming script.
- Decided to start with `title + text` and keep `subject/date` out of the first model pending leakage checks.
- Confirmed that no implementation files existed at the start of the project.
- Created this handoff document.
- The dataset has now been selected locally; framework, model algorithm, API provider, and database have not been finalized.

### 2026-09-07 - Baseline structure and profile created

- Added `scripts/train_model.py` for TF-IDF plus Logistic Regression experiments.
- Added `requirements.txt`, `README.md`, `.gitignore`, and the initial `src/fake_news_risk` package.
- Python 3.14.6 is available; scikit-learn dependencies still need to be installed before training.
- The baseline was later trained successfully and produced `models/baseline_title-text.joblib` and `reports/baseline_title-text.json`.
- The trainer was refactored into reusable functions, with presentation output moved to a separate `scripts/demo_model.py` module.
- Removed the mode argument; training now selects title, text, or title plus text automatically per row and saves `model.joblib` and `performance_report.json`.
- Removed the redundant profiling script and generated profile JSON after recording its findings here.
- Moved `True.csv` into `data/` and copied `Fake.csv` into `data/`; the original root `Fake.csv` could not be deleted because another Windows process has it open. Close the process/editor lock and remove the root copy when possible.

### 2026-09-14 - Git upstream push and full-stack web_app created

- Initialized Git repository on branch `main`, verified `.gitignore` rules to keep datasets/models/virtualenv excluded.
- Connected remote origin `https://github.com/IshwarP32/FakeNews.git` and successfully pushed upstream.
- Created dedicated application directory `web_app/` housing both backend and frontend.
- Finalized backend framework as **FastAPI** (`web_app/backend/`):
  - Built `RiskAnalyzer` module loading `models/model.joblib` and combining ML prediction with explainable heuristic features (sensationalism keywords, urgency triggers, all-caps formatting, exclamation analysis, and source attribution).
  - Exposed endpoints: `GET /api/health`, `GET /api/presets`, `POST /api/analyze`, `GET /api/history`, `DELETE /api/history`.
- Created frontend in **React + Vite** (`web_app/frontend/`):
  - Designed modern dark-mode glassmorphic UI with animated glowing risk gauge, breakdown progress bars, signal tag badges, explainable bullet points, one-click test presets, and session history log.
  - Verified Vite dev proxy to port 8000 and confirmed end-to-end API communication.
- Added launcher scripts: `web_app/start_backend.bat`, `web_app/start_frontend.bat`, `web_app/start_all.bat`, and `web_app/README.md`.

### 2026-09-14 - Refactor: Tailwind CSS v4 and ChatGPT-style Minimalist UI

- Replaced custom CSS system with **Tailwind CSS v4** (`@tailwindcss/vite`).
- Scrapped extraneous heuristic metrics, preset lists, and session history code across backend and frontend per user direction.
- Refactored `analyzer.py` and `main.py` to directly return pure model-based fake score and prediction.
- Built a distraction-free, ChatGPT-style minimalist UI in `App.jsx`:
  - Centered clean layout with dark theme (`#212121`).
  - Inputs for headline and article text.
  - "Analyze" and "Clear" actions.
  - Clean score card output indicating model fake likelihood % and prediction (Fake vs Real).



## Update Protocol for Future Agents

When continuing the project:

1. Read this file before changing code.
2. Check the current workspace state and tests against the progress recorded here.
3. Record important decisions before or immediately after implementing them.
4. Keep completed work, current work, blockers, and next steps accurate.
5. Do not silently replace an earlier decision; explain the reason and date the change.
6. Update the progress log after each meaningful milestone.

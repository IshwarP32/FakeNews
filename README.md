# Fake News Risk Analyzer

The first milestone is a reproducible text-classification model. It reads the local Kaggle datasets and estimates fake-news likelihood from article text using TF-IDF and Logistic Regression.

## Structure

```text
FakeNews/
|- data/
|  |- Fake.csv               # local dataset, not committed
|  `- True.csv               # local dataset, not committed
|- scripts/
|  |- train_model.py        # reusable TF-IDF + Logistic Regression trainer
|  `- demo_model.py         # presentation walkthrough using trainer functions
|- src/fake_news_risk/      # application package for later stages
|- models/                  # generated model artifacts
|- reports/                 # generated performance and profiling reports
|- proposal.html
|- AI_CONTEXT.md
`- requirements.txt
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## First commands

```powershell
python scripts/train_model.py
python scripts/demo_model.py
```

The model trainer reads the datasets from `data/`, keeps only the text and labels in memory, and excludes `subject` and `date` from model features to reduce data leakage. It combines `title` and `text` when both are available, and uses whichever one is available otherwise. Its prediction is a model-based fake-news likelihood, not proof that an article is true or false. A broader risk score will be added later using evidence, source reliability, severity, and other signals. The reusable functions are kept separate from the presentation-only `demo_model.py`, so the demo can be removed without changing training.
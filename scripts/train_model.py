"""CLI script to train a reproducible TF-IDF + Logistic Regression model."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure root directory is on sys.path for local imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.fake_news_risk.classifier import (
    RANDOM_STATE,
    TrainingResult,
    build_model,
    evaluate_model,
    load_rows,
    save_artifacts,
    train_model,
)


def main() -> None:
    fake_path = ROOT_DIR / "data" / "Fake.csv"
    true_path = ROOT_DIR / "data" / "True.csv"
    print("Training model...")
    result = train_model(fake_path, true_path)

    print("Saving model and report...")
    model_output = ROOT_DIR / "models" / "model.joblib"
    report_output = ROOT_DIR / "reports" / "performance_report.json"
    save_artifacts(result, model_output, report_output)

    print(
        f"Rows used: {result.metrics['rows_used']}; train: {result.metrics['train_rows']}; test: {result.metrics['test_rows']}"
    )
    print(f"Accuracy: {result.metrics['accuracy']:.4f}")
    print(f"Model: {model_output}")
    print(f"Report: {report_output}")


if __name__ == "__main__":
    main()
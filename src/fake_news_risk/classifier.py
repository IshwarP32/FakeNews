"""Text classification model training and evaluation routines."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Tuple

from joblib import dump
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

RANDOM_STATE = 42


@dataclass
class TrainingResult:
    texts: list[str]
    labels: list[int]
    train_texts: list[str]
    test_texts: list[str]
    train_labels: list[int]
    test_labels: list[int]
    model: Pipeline
    predictions: Any
    metrics: dict[str, Any]


def load_rows(fake_path: Path, true_path: Path) -> Tuple[List[str], List[int]]:
    """Load and combine fake (0) and true (1) news dataset CSVs."""
    texts: List[str] = []
    labels: List[int] = []
    for path, label in ((fake_path, 0), (true_path, 1)):
        with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
            for row in csv.DictReader(handle):
                title = (row.get("title") or "").strip()
                body = (row.get("text") or "").strip()
                text = f"{title} {body}".strip()
                if text:
                    texts.append(text)
                    labels.append(label)
    return texts, labels


def build_model() -> Pipeline:
    """Construct TF-IDF + Logistic Regression pipeline."""
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    sublinear_tf=True,
                    max_df=0.95,
                    min_df=2,
                    ngram_range=(1, 2),
                    max_features=250_000,
                ),
            ),
            (
                "classifier",
                LogisticRegression(max_iter=1_000, random_state=RANDOM_STATE),
            ),
        ]
    )


def train_model(fake_path: Path, true_path: Path) -> TrainingResult:
    """Train pipeline on stratified train/test split and evaluate."""
    texts, labels = load_rows(fake_path, true_path)
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts,
        labels,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=labels,
    )
    model = build_model()
    model.fit(train_texts, train_labels)
    predictions = model.predict(test_texts)
    metrics = evaluate_model(
        test_labels, predictions, len(texts), len(train_texts), len(test_texts)
    )
    return TrainingResult(
        texts=texts,
        labels=labels,
        train_texts=train_texts,
        test_texts=test_texts,
        train_labels=train_labels,
        test_labels=test_labels,
        model=model,
        predictions=predictions,
        metrics=metrics,
    )


def evaluate_model(
    test_labels: list[int],
    predictions: Any,
    rows_used: int,
    train_rows: int,
    test_rows: int,
) -> dict[str, Any]:
    """Compute performance metrics (accuracy, precision, recall, confusion matrix)."""
    return {
        "random_state": RANDOM_STATE,
        "rows_used": rows_used,
        "train_rows": train_rows,
        "test_rows": test_rows,
        "accuracy": accuracy_score(test_labels, predictions),
        "classification_report": classification_report(
            test_labels, predictions, output_dict=True, zero_division=0
        ),
        "confusion_matrix_labels": ["fake", "true"],
        "confusion_matrix": confusion_matrix(test_labels, predictions).tolist(),
    }


def save_artifacts(
    result: TrainingResult, model_output: Path, report_output: Path
) -> None:
    """Persist trained joblib model and JSON metrics report."""
    model_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.parent.mkdir(parents=True, exist_ok=True)
    dump(result.model, model_output)
    report_output.write_text(json.dumps(result.metrics, indent=2), encoding="utf-8")

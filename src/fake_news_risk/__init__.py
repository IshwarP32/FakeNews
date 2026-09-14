"""Core package for the Fake News Risk Analyzer."""

from src.fake_news_risk.classifier import (
    RANDOM_STATE,
    TrainingResult,
    build_model,
    evaluate_model,
    load_rows,
    save_artifacts,
    train_model,
)

__all__ = [
    "RANDOM_STATE",
    "TrainingResult",
    "build_model",
    "evaluate_model",
    "load_rows",
    "save_artifacts",
    "train_model",
]

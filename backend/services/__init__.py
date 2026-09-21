"""Services package for Fake News Verifier."""

from backend.services.history import save_history_log
from backend.services.ml_predictor import ModelPredictor

__all__ = ["save_history_log", "ModelPredictor"]

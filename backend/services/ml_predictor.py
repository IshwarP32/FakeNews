"""Machine Learning Model Predictor for Fake News classification."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import joblib

from backend.config import MODEL_PATH, logger


class ModelPredictor:
    """Predicts fake news probability using trained scikit-learn model."""

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or MODEL_PATH
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        if self.model_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                logger.info(f"[ModelPredictor] Loaded model from {self.model_path}")
            except Exception as exc:
                logger.warning(f"[ModelPredictor] Failed to load model: {exc}")
                self.model = None
        else:
            logger.warning(f"[ModelPredictor] Warning: Model file not found at {self.model_path}")

    @property
    def is_model_loaded(self) -> bool:
        return self.model is not None

    def predict(self, title: str, text: str) -> Dict[str, Any]:
        combined = f"{title.strip()} {text.strip()}".strip()
        if not combined:
            raise ValueError("Title or article text must be provided.")

        if not self.model:
            raise RuntimeError("Model is not loaded.")

        # Baseline model convention: 0 = fake, 1 = true
        probs = self.model.predict_proba([combined])[0]
        fake_prob = float(probs[0])
        real_prob = float(probs[1])

        score = round(fake_prob * 100, 1)
        prediction = "Fake" if fake_prob >= 0.5 else "Real"

        return {
            "score": score,
            "prediction": prediction,
            "fake_probability": score,
            "real_probability": round(real_prob * 100, 1),
        }

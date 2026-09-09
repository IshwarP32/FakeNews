"""Model predictor for Fake News classification."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import joblib

MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "models" / "model.joblib"


class ModelPredictor:
    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or MODEL_PATH
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        if self.model_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                print(f"[ModelPredictor] Loaded model from {self.model_path}")
            except Exception as exc:
                print(f"[ModelPredictor] Failed to load model: {exc}")
                self.model = None
        else:
            print(f"[ModelPredictor] Warning: Model file not found at {self.model_path}")

    @property
    def is_model_loaded(self) -> bool:
        return self.model is not None

    def predict(self, title: str, text: str) -> Dict[str, Any]:
        combined = f"{title.strip()} {text.strip()}".strip()
        if not combined:
            raise ValueError("Title or article text must be provided.")

        if not self.model:
            raise RuntimeError("Model is not loaded.")

        # In baseline model: 0 = fake, 1 = true
        probs = self.model.predict_proba([combined])[0]
        fake_prob = float(probs[0])
        real_prob = float(probs[1])

        # Score representing fake likelihood percentage (0 to 100%)
        score = round(fake_prob * 100, 1)
        prediction = "Fake" if fake_prob >= 0.5 else "Real"

        return {
            "score": score,
            "prediction": prediction,
            "fake_probability": score,
            "real_probability": round(real_prob * 100, 1),
        }

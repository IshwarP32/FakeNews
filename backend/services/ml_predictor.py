"""Machine Learning Model Predictor for Fake News classification."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional
import joblib

from backend.config import HISTORY_DIR, MODEL_PATH, logger


class ModelPredictor:
    """Predicts fake news probability using trained scikit-learn model."""

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or MODEL_PATH
        self.feedback_path = HISTORY_DIR / "ml_feedback.jsonl"
        self.model = None
        self._feedback: list[Dict[str, Any]] = []
        self._lock = Lock()
        self._load_model()
        self._load_feedback()

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

    def _load_feedback(self) -> None:
        if not self.feedback_path.exists():
            return
        try:
            with self.feedback_path.open("r", encoding="utf-8") as handle:
                self._feedback = [json.loads(line) for line in handle if line.strip()]
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning(f"[ModelPredictor] Failed to load learning data: {exc}")

    @property
    def learning_count(self) -> int:
        return len(self._feedback)

    def _learned_probability(self, combined: str) -> Optional[float]:
        if not self._feedback or not self.model:
            return None
        vectorizer = self.model.named_steps.get("tfidf")
        if vectorizer is None:
            return None

        query_vector = vectorizer.transform([combined])
        sample_texts = [sample["text"] for sample in self._feedback]
        sample_vectors = vectorizer.transform(sample_texts)
        similarities = (sample_vectors @ query_vector.T).toarray().ravel()
        ranked = sorted(enumerate(similarities), key=lambda item: item[1], reverse=True)[:5]
        neighbors = [(index, score) for index, score in ranked if score > 0]
        if not neighbors:
            return None

        total_weight = sum(score for _, score in neighbors)
        fake_probability = sum(
            self._feedback[index]["fake_probability"] * score for index, score in neighbors
        ) / total_weight
        return float(fake_probability)

    def record_ai_verdict(self, title: str, text: str, verdict: str) -> bool:
        """Persist an AI verdict as a weak label for future predictions."""
        label_map = {"False": 1.0, "True": 0.0, "Partially True": 0.5}
        fake_probability = label_map.get(verdict)
        combined = f"{title.strip()} {text.strip()}".strip()
        if fake_probability is None or not combined:
            return False

        sample = {"text": combined, "fake_probability": fake_probability, "verdict": verdict}
        with self._lock:
            self._feedback.append(sample)
            try:
                self.feedback_path.parent.mkdir(parents=True, exist_ok=True)
                with self.feedback_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(sample, ensure_ascii=True) + "\n")
            except OSError as exc:
                logger.warning(f"[ModelPredictor] Failed to persist learning data: {exc}")
        return True

    def predict(self, title: str, text: str) -> Dict[str, Any]:
        combined = f"{title.strip()} {text.strip()}".strip()
        if not combined:
            raise ValueError("Title or article text must be provided.")

        if not self.model:
            raise RuntimeError("Model is not loaded.")

        # Baseline model convention: 0 = fake, 1 = true
        probs = self.model.predict_proba([combined])[0]
        classifier = self.model.named_steps.get("classifier")
        classes = list(classifier.classes_ if classifier is not None else self.model.classes_)
        fake_prob = float(probs[classes.index(0)])
        learned_prob = self._learned_probability(combined)
        if learned_prob is not None:
            fake_prob = (fake_prob * 0.75) + (learned_prob * 0.25)
        real_prob = 1 - fake_prob

        score = round(fake_prob * 100, 1)
        prediction = "Fake" if fake_prob >= 0.5 else "Real"

        return {
            "score": score,
            "prediction": prediction,
            "fake_probability": score,
            "real_probability": round(real_prob * 100, 1),
            "baseline_fake_probability": round(float(probs[classes.index(0)]) * 100, 1),
            "learned_examples": self.learning_count,
        }

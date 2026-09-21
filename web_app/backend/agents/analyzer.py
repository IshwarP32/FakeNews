"""Agent 3: Evidence Analyzer & Fact Verifier."""

import json
import re
from typing import Any, Dict, List
from web_app.backend.config import logger


class EvidenceAnalyzerAgent:
    """Agent 3 cross-examines claim against evidence and formats structured JSON."""

    def extract_text(self, resp: Any) -> str:
        """Safely extracts raw text from Gemini response candidates."""
        text = getattr(resp, "text", None)
        if not text and hasattr(resp, "candidates") and resp.candidates:
            for c in resp.candidates:
                parts = getattr(getattr(c, "content", None), "parts", []) or []
                pieces = [p.text for p in parts if getattr(p, "text", None)]
                if pieces:
                    text = "\n".join(pieces)
                    break
        return (text or "").strip()

    def parse_json(self, raw_text: str) -> Dict[str, Any]:
        """Parses JSON response string with regex fallback."""
        cleaned = raw_text.strip()
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
            cleaned = match.group(1).strip() if match else cleaned.split("```")[1]
        try:
            return json.loads(cleaned)
        except Exception:
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
            logger.error("JSON parsing failed, returning fallback result.")
            return {
                "verdict": "Unverified",
                "confidence": "Low",
                "summary": raw_text[:300] if raw_text else "Could not parse verdict.",
                "corrected_news": "",
                "reasoning": [raw_text] if raw_text else ["Response parse error"],
                "sources_used": []
            }

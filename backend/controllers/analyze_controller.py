"""Controller for Fake News analysis orchestration."""

import json
from queue import Queue
from threading import Thread
from typing import Any, Dict, Iterator

from fastapi import HTTPException

from backend.agents.verifier import GeminiVerifier
from backend.config import logger
from backend.utils.progress import report

verifier = GeminiVerifier()


def _sse_event(payload: Dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=True)}\n\n"


def analyze_claim(title: str, text: str) -> Dict[str, Any]:
    """Controller function for non-streaming analysis request."""
    title_clean = (title or "").strip()
    text_clean = (text or "").strip()
    if not title_clean and not text_clean:
        raise HTTPException(
            status_code=400,
            detail="Please provide a headline or article text.",
        )

    try:
        verdict = verifier.verify(title=title_clean, text=text_clean)
        claim = " ".join(f"{title_clean} {text_clean}".split())
        return {"claim": claim, "verdict": verdict}
    except Exception as exc:
        logger.exception("analysis_failed")
        raise HTTPException(status_code=500, detail=str(exc))


def stream_claim_analysis(title: str, text: str) -> Iterator[str]:
    """Controller function streaming SSE progress events."""
    title_clean = (title or "").strip()
    text_clean = (text or "").strip()
    if not title_clean and not text_clean:
        raise HTTPException(
            status_code=400,
            detail="Please provide a headline or article text.",
        )

    events: Queue[Dict[str, Any]] = Queue()

    def emit(payload: Dict[str, Any]) -> None:
        events.put(payload)

    def worker() -> None:
        try:
            verdict = verifier.verify(title=title_clean, text=text_clean, on_progress=emit)
            claim = " ".join(f"{title_clean} {text_clean}".split())
            result = {"claim": claim, "verdict": verdict}
            report(emit, "analysis_completed", "Verification complete.", result=result)
        except Exception as exc:
            logger.exception("analysis_failed")
            report(emit, "analysis_failed", "Analysis failed.", error=str(exc))

    Thread(target=worker, daemon=True).start()

    while True:
        payload = events.get()
        yield _sse_event(payload)
        if payload["event"] in {"analysis_completed", "analysis_failed"}:
            break

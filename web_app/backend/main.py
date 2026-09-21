"""FastAPI backend for Fake News Risk Analyzer."""

import json
import logging
from queue import Queue
from threading import Thread
from typing import Any, Dict, Iterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from web_app.backend.gemini_verifier import GeminiVerifier
from web_app.backend.progress import ProgressCallback, report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="Fake News Risk API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

verifier = GeminiVerifier()


class AnalyzeRequest(BaseModel):
    title: str = Field(default="", description="News headline or title")
    text: str = Field(default="", description="Article body text")


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    title = (req.title or "").strip()
    text = (req.text or "").strip()
    if not title and not text:
        raise HTTPException(
            status_code=400,
            detail="Please provide a headline or article text.",
        )
    try:
        verdict = verifier.verify(title=title, text=text)
        claim = " ".join(f"{title} {text}".split())
        return {"claim": claim, "verdict": verdict}
    except Exception as exc:
        logging.getLogger("fake_news_risk").exception("analysis_failed")
        raise HTTPException(status_code=500, detail=str(exc))


def _sse_event(payload: Dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=True)}\n\n"


@app.post("/api/analyze/stream")
def analyze_stream(req: AnalyzeRequest):
    title = (req.title or "").strip()
    text = (req.text or "").strip()
    if not title and not text:
        raise HTTPException(
            status_code=400,
            detail="Please provide a headline or article text.",
        )

    events: Queue[Dict[str, Any]] = Queue()

    def emit(payload: Dict[str, Any]) -> None:
        events.put(payload)

    def worker() -> None:
        try:
            verdict = verifier.verify(title=title, text=text, on_progress=emit)
            claim = " ".join(f"{title} {text}".split())
            result = {"claim": claim, "verdict": verdict}
            report(emit, "analysis_completed", "Verification complete.", result=result)
        except Exception as exc:
            logging.getLogger("fake_news_risk").exception("analysis_failed")
            report(emit, "analysis_failed", "Analysis failed.", error=str(exc))

    Thread(target=worker, daemon=True).start()

    def stream() -> Iterator[str]:
        while True:
            payload = events.get()
            yield _sse_event(payload)
            if payload["event"] in {"analysis_completed", "analysis_failed"}:
                break

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

"""FastAPI application for Fake News Risk Analyzer."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from web_app.backend.analyzer import ModelPredictor

app = FastAPI(
    title="Fake News Risk API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = ModelPredictor()


class AnalyzeRequest(BaseModel):
    title: str = Field(default="", description="News headline or title")
    text: str = Field(default="", description="Article body text")


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": predictor.is_model_loaded,
    }


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
        return predictor.predict(title=title, text=text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

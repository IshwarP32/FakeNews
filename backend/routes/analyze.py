"""Analyze routes for news claim verification."""

from fastapi import APIRouter
from starlette.responses import StreamingResponse

from backend.controllers.analyze_controller import analyze_claim, stream_claim_analysis
from backend.schemas.analyze import AnalyzeRequest

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze")
def analyze_endpoint(req: AnalyzeRequest):
    return analyze_claim(title=req.title, text=req.text)


@router.post("/analyze/stream")
def analyze_stream_endpoint(req: AnalyzeRequest):
    return StreamingResponse(
        stream_claim_analysis(title=req.title, text=req.text),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

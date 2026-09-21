"""Pydantic schemas for verification API requests and responses."""

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    title: str = Field(default="", description="News headline or title")
    text: str = Field(default="", description="Article body text")

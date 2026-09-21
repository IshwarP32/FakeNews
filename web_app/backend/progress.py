"""Shared progress events for logs and browser streaming."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional


ProgressCallback = Callable[[Dict[str, Any]], None]
logger = logging.getLogger("fake_news_risk")


def report(
    callback: Optional[ProgressCallback],
    event: str,
    message: str,
    **details: Any,
) -> Dict[str, Any]:
    payload = {"event": event, "message": message, **details}
    logger.info("%s: %s", event, message, extra={"progress": payload})
    if callback:
        callback(payload)
    return payload
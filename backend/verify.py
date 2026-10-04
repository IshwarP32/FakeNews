"""CLI entrypoint for fake-news verification with tracing support.

Usage:
    python -m backend.verify --claim "Chandrayaan-3 landed on the Moon on 23 August 2023"
    python -m backend.verify --claim "..." --trace
    python -m backend.verify --claim "..." --json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

from backend.agents.verifier import GeminiVerifier


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify a news claim using the multi-agent fake news verification pipeline."
    )
    parser.add_argument(
        "--claim",
        type=str,
        default="",
        help="The news claim or headline to verify.",
    )
    parser.add_argument(
        "--text",
        type=str,
        default="",
        help="Optional additional body text for the claim.",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Print detailed execution trace including queries, retrieved articles, and timing.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON response instead of human-readable summary.",
    )

    args = parser.parse_args()
    claim_text = (args.claim or "").strip()
    body_text = (args.text or "").strip()

    if not claim_text and not body_text:
        parser.print_help()
        sys.exit(1)

    verifier = GeminiVerifier()

    def progress_callback(event: Dict[str, Any]) -> None:
        if args.trace and not args.json:
            step = event.get("step", "")
            msg = event.get("message", "")
            print(f"[{step}] {msg}", file=sys.stderr)

    result = verifier.verify(title=claim_text, text=body_text, on_progress=progress_callback)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    verdict_obj = result.get("verdict")
    error_obj = result.get("error")

    print("\n" + "=" * 60)
    print("VERIFICATION RESULT")
    print("=" * 60)

    if error_obj:
        print(f"Status: ERROR ({error_obj.get('reason_code')})")
        print(f"Message: {error_obj.get('message')}")
        print(f"Guidance: {error_obj.get('guidance')}")
        sys.exit(2)

    if not verdict_obj:
        print("Status: No verdict returned.")
        sys.exit(1)

    print(f"Verdict:    {verdict_obj.get('verdict')}")
    print(f"Confidence: {verdict_obj.get('confidence')}")
    flags = verdict_obj.get("flags", [])
    if flags:
        print(f"Flags:      {', '.join(flags)}")
    print("-" * 60)
    print(f"Summary:\n{verdict_obj.get('summary')}\n")

    if verdict_obj.get("corrected_news"):
        print(f"Corrected News:\n{verdict_obj.get('corrected_news')}\n")

    if verdict_obj.get("limitations"):
        print(f"Limitations:\n{verdict_obj.get('limitations')}\n")

    coverage = result.get("coverage", {})
    if coverage:
        print("-" * 60)
        print("Coverage:")
        print(f"  Queries searched:     {len(coverage.get('windows', []))}")
        print(f"  Articles retrieved:   {coverage.get('articles_retrieved', 0)}")
        print(f"  Articles analysed:    {coverage.get('articles_analysed', 0)}")
        print(f"  Independent sources:  {coverage.get('independent_sources', 0)}")
        print(f"  Retrieval incomplete: {coverage.get('retrieval_incomplete', False)}")

    evidence = result.get("evidence_articles", [])
    if evidence:
        print("-" * 60)
        print(f"Direct Evidence Articles ({len(evidence)}):")
        for art in evidence:
            print(f"  [{art.get('id')}] {art.get('title')} ({art.get('source', 'Unknown')})")
            print(f"       Stance: {art.get('stance')} | Tier: {art.get('source_tier')}")
            if art.get("evidence_quote"):
                print(f"       Quote: \"{art.get('evidence_quote')}\"")

    context = result.get("context_articles", [])
    if context:
        print("-" * 60)
        print(f"Contextual Articles ({len(context)}):")
        for art in context:
            print(f"  [{art.get('id')}] {art.get('title')} ({art.get('source', 'Unknown')})")

    if args.trace:
        print("-" * 60)
        print("Trace Coverage Details:")
        print(json.dumps(coverage, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

# Source Credibility Reference

> Feeds the "source reliability" signal in `RiskAnalyzer`. Use domain matching against
> `title`/`url` input. Weights are suggestions — tune against real predictions later.
> This is a *prior*, not a verdict — a Tier 1 outlet can still publish an error, and an
> unlisted domain should default to "unknown" rather than "low."

## How to use this in the risk engine

- Extract domain from input URL (if provided).
- Look up domain in the map below → get a `tier` and `weight` (0.0–1.0, higher = more reliable).
- Unlisted domains → `tier: "unrated"`, `weight: 0.5` (neutral, don't penalize).
- Never let this override the AI-evidence/model layers — combine, don't replace.
- Recommended weights: Tier 1 = 0.95, Tier 2 = 0.85, Tier 3 = 0.75, Tier 4 (fact-checkers,
  used for evidence lookup not as an input source) = n/a, Tier 5 (low-reliability/tabloid/
  known-misinfo-prone) = 0.2, unrated = 0.5.

---

## Tier 1 — Wire services & highest-reliability global outlets

| Domain | Outlet | Notes |
|---|---|---|
| reuters.com | Reuters | Wire service, minimal editorializing |
| apnews.com | Associated Press | Wire service |
| bbc.com / bbc.co.uk | BBC News | Public broadcaster, editorial standards body |
| afp.com | Agence France-Presse | Wire service |
| npr.org | NPR | Public broadcaster (US) |

## Tier 2 — Major credible national/international outlets

| Domain | Outlet |
|---|---|
| nytimes.com | The New York Times |
| washingtonpost.com | The Washington Post |
| theguardian.com | The Guardian |
| wsj.com | The Wall Street Journal |
| economist.com | The Economist |
| aljazeera.com | Al Jazeera English |
| dw.com | Deutsche Welle |
| bloomberg.com | Bloomberg |

## Tier 3 — Credible Indian outlets

| Domain | Outlet | Notes |
|---|---|---|
| ptinews.com | Press Trust of India | Wire service — treat closer to Tier 1 |
| aninews.in | Asian News International | Wire service |
| thehindu.com | The Hindu | Strong fact-checking desk |
| indianexpress.com | The Indian Express | |
| hindustantimes.com | Hindustan Times | |
| ndtv.com | NDTV | |
| livemint.com | Mint | Business/financial focus |
| thewire.in | The Wire | Independent, investigative |
| scroll.in | Scroll.in | Independent |
| business-standard.com | Business Standard | |
| deccanherald.com | Deccan Herald | |
| telegraphindia.com | The Telegraph (India) | |

*Note: Indian outlets skew toward English-language/national desks here — regional-language
credibility mapping (Dainik Jagran, Malayala Manorama, Eenadu, etc.) is a good v2 addition
once you need multilingual coverage.*

## Tier 4 — Fact-checking organizations (for evidence lookup, not as primary sources)

| Domain | Outlet | Region |
|---|---|---|
| altnews.in | Alt News | India |
| boomlive.in | BOOM | India |
| factly.in | Factly | India |
| vishvasnews.com | Vishvas News | India |
| pib.gov.in/factcheck | PIB Fact Check | India (govt) |
| snopes.com | Snopes | Global |
| politifact.com | PolitiFact | US |
| factcheck.org | FactCheck.org | US |
| fullfact.org | Full Fact | UK |
| reuters.com/fact-check | Reuters Fact Check | Global |
| afp.com/factcheck | AFP Fact Check | Global |

Use these as your "trusted-source context" retrieval targets for the AI evidence layer,
not as a domain-reliability lookup for arbitrary input articles.

## Tier 5 — Lower-reliability / high-misinformation-risk patterns

Rather than naming specific low-quality sites (that list goes stale fast and isn't
something worth hardcoding), flag these **patterns** instead — they're more durable
signals than a domain blocklist:

- Domains with no clear editorial masthead, ownership, or corrections policy
- Domains mimicking legitimate outlet names (typosquatting, e.g. `bbc-news24.com`)
- Aggregator/blog-farm domains with no bylines
- Domains flagged in fact-checker corpora (Alt News, BOOM, Snopes, PolitiFact all
  publish "debunked source" tags you can scrape/ingest periodically)
- Sites using `.info`, `.xyz`, or similar low-cost TLDs combined with high urgency
  language (combine with your existing urgency/tone heuristics rather than domain alone)

## Government / official sources (high trust, narrow use)

| Domain | Body |
|---|---|
| pib.gov.in | Press Information Bureau, India |
| mohfw.gov.in | Ministry of Health & Family Welfare, India |
| who.int | World Health Organization |
| eci.gov.in | Election Commission of India |

---

## Suggested JSON shape for the backend

```json
{
  "reuters.com": {"tier": 1, "weight": 0.95, "type": "wire"},
  "ptinews.com": {"tier": 1, "weight": 0.95, "type": "wire"},
  "thehindu.com": {"tier": 3, "weight": 0.85, "type": "national"},
  "altnews.in": {"tier": 4, "weight": null, "type": "factchecker"}
}
```

Keep this as a separate JSON/YAML config file (not hardcoded in `analyzer.py`) so it can
be updated without touching model logic — consistent with your "smallest stack, minimum
practical technology" principle.

## Practical scraping notes

- Check `robots.txt` on each domain before scraping; several (NYT, WSJ, Bloomberg) restrict
  automated access even for headlines.
- Prefer RSS feeds where available (most Tier 1–3 outlets publish them) over HTML scraping —
  more stable, less likely to break, less legally ambiguous.
- For Indian fact-checkers (Alt News, BOOM, Factly), check whether they expose an API or
  structured feed for their "debunked claims" archive before scraping HTML directly.
- Add a per-domain rate limit and a User-Agent identifying your project, not a browser UA.
- Cache aggressively — you don't need to re-fetch the same article evidence per request.

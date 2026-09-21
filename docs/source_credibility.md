# India-Specific Source Credibility Reference

## Scope

The project currently targets news about India and sources serving Indian
audiences. This list is a starting point for source-context features and
evidence retrieval. It is not a truth whitelist: a credible publisher can make
mistakes, and a less-established publisher can occasionally publish accurate
reporting. Article-level evidence should take priority over the domain score.

## Tier 1 — National news agencies and established newspapers

Use these as the strongest publisher-level source signal when the article URL
can be identified. Verify the exact domain because copied or lookalike domains
must not inherit the parent outlet's score.

| Outlet | Primary domain | Typical coverage |
|---|---|---|
| Press Trust of India (PTI) | `pti.in` | National and international wire reporting |
| United News of India (UNI) | `uniindia.com` | National wire reporting |
| The Hindu | `thehindu.com` | National, state, policy, and explainers |
| The Indian Express | `indianexpress.com` | National, politics, investigations, and explainers |
| Hindustan Times | `hindustantimes.com` | National, cities, and current affairs |
| The Times of India | `timesofindia.indiatimes.com` | National and city reporting |
| Business Standard | `business-standard.com` | Business, economy, and policy |

Asian News International (`aninews.in`) and Reuters India coverage
(`reuters.com/world/india`) may be used as supporting sources for India-related
claims, but should remain identifiable as international wire reporting rather
than being treated as Indian public authorities.

## Tier 2 — Established Indian digital and regional publishers

These are useful corroborating sources, with more variation by desk, topic, and
region. Do not use this tier alone to confirm a high-impact claim.

| Outlet | Primary domain | Typical coverage |
|---|---|---|
| NDTV | `ndtv.com` | National, politics, business, and cities |
| Deccan Herald | `deccanherald.com` | National and southern India coverage |
| The Telegraph India | `telegraphindia.com` | National and eastern India coverage |
| The New Indian Express | `newindianexpress.com` | National and regional coverage |
| The Economic Times | `economictimes.indiatimes.com` | Business, markets, and policy |
| Mint | `livemint.com` | Business, economy, and personal finance |
| India Today | `indiatoday.in` | National news, politics, and investigations |
| News18 | `news18.com` | National and state-level coverage |
| Scroll.in | `scroll.in` | Politics, society, culture, and explainers |
| The Wire | `thewire.in` | Politics, society, and investigations |
| ThePrint | `theprint.in` | Politics, policy, defence, and explainers |

Regional reporting should also be considered, especially when the claim is
local. Examples include Mathrubhumi (`mathrubhumi.com`), Eenadu
(`eenadu.net`), Anandabazar Patrika (`anandabazar.com`), and Lokmat
(`lokmat.com`). Language and regional relevance are evidence-quality signals,
not automatic credibility guarantees.

## Tier 3 — Indian fact-checking and verification sources

These sources are for claim verification and evidence retrieval, not for
automatically labelling every article from the publisher as true or false.

| Organization | Domain | Main use |
|---|---|---|
| Alt News | `altnews.in` | Viral claims, images, videos, and misinformation |
| BOOM | `boomlive.in` | Viral claims, media verification, and fact-checks |
| Factly | `factly.in` | Public data, claims, and viral content |
| Vishvas News | `vishvasnews.com` | Hindi and multilingual claim verification |
| Newschecker | `newschecker.in` | Multilingual fact-checking |
| AFP Fact Check India | `factcheck.afp.com` | International wire-service fact-checks relevant to India |

Google Fact Check Tools API can search `ClaimReview` records from these and
other organizations. Treat a matching fact-check as evidence to inspect, not
as an unexplained numerical override.

## Tier 4 — Indian government and institutional sources

Use official sources when they directly own the fact being checked. They are
high-trust for their mandate, but they are not substitutes for independent
reporting or broader context.

| Source | Domain | Best suited for |
|---|---|---|
| Press Information Bureau (PIB) | `pib.gov.in` | Union government announcements and clarifications |
| Election Commission of India | `eci.gov.in` | Elections, results, and electoral procedures |
| Supreme Court of India | `sci.gov.in` | Court orders and judgments |
| India Code | `indiacode.nic.in` | Acts, rules, and statutory text |
| Ministry of Health and Family Welfare | `mohfw.gov.in` | National health advisories and programmes |
| Indian Meteorological Department | `imd.gov.in` | Weather warnings and forecasts |
| National Disaster Management Authority | `ndma.gov.in` | Disaster guidance and advisories |
| Reserve Bank of India | `rbi.org.in` | Monetary policy, banking, and regulatory notices |
| UIDAI | `uidai.gov.in` | Aadhaar-related official information |

## Recommended source-scoring policy

1. Start with a neutral score when no source URL or domain is available.
2. Match exact, normalized hostnames; do not match arbitrary substrings.
3. Apply a modest positive or negative source signal, rather than deciding the
   result from the domain alone.
4. Give more weight to two or more independent sources that agree on the same
   claim, especially when one is an official source or a fact-check.
5. Penalize missing bylines, missing publication dates, copied text, domain
   lookalikes, and unsupported sensational claims as article-level signals.
6. Keep political viewpoint and ownership separate from factual reliability;
   disagreement with an outlet's editorial position is not proof of falsity.

## Retrieval and safety notes

- Prefer an official API or RSS feed over HTML scraping where available.
- Google Fact Check Tools API is the preferred first lookup for a known claim;
  GDELT and Google News RSS can provide broader corroborating context.
- Check each site's current `robots.txt`, terms, and rate limits before fetching.
- Use a descriptive User-Agent, cache responses, and avoid collecting more
  article content than the application needs.
- Revalidate domains, feeds, and tiers periodically. Ownership, URLs, and feed
  availability change over time.
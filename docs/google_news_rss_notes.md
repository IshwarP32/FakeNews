# Google News RSS Notes

Date checked: 2026-10-04

## Requests Tested

The pipeline used:

`https://news.google.com/rss/search?q=<urlencoded query>&hl=en-IN&gl=IN&ceid=IN:en`

A request for `IIT Madras Inter IIT Sports Meet` with `after:2025-01-01 before:2026-10-05` returned 32 items. The first observed item was:

- Title: `58th Inter IIT Sports Meet 2025 commences at IIT Madras - pib.gov.in`
- Source URL: `https://www.pib.gov.in`
- Publication date: `Sun, 14 Dec 2025 08:00:00 GMT`
- Link: a `news.google.com/rss/articles/...` redirect URL
- Description: contained a short text snippet including the title and publisher.

The same query with `after:2019-01-01 before:2020-01-01` returned 6 items, including January, November, and December 2019 publication dates. This confirms that explicit date windows can retrieve historical results rather than only the latest feed contents.

## Implementation Findings

- `pubDate` is an RSS publication date and must not be treated as the event date.
- `<source url="...">` provides a publisher domain suitable for source-tier lookup; title suffixes are not used for trust classification.
- RSS links are Google redirect URLs and are retained as the display link until canonical URL resolution is implemented.
- The feed returned multiple items for both windows; item counts and ranking must be recorded per query because result limits and relevance may change over time.
- These observations are empirical snapshots, not permanent Google News guarantees.

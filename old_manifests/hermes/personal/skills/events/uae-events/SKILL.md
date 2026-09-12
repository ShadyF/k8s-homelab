---
name: uae-events
description: Search curated Live Nation sources for new interesting UAE events and return a digest only when new events are found.
tags:
  - events
  - uae
  - dubai
  - abu-dhabi
  - cron
---

# uae-events

Use this skill to find and summarize new, credible events in the United Arab Emirates.

## Scope
- Coverage is strictly UAE events.
- Prioritize Dubai and Abu Dhabi, while including notable events elsewhere in the UAE.
- Search English sources.
- Summarize in English.
- Categories:
  - Concerts and large touring music events
  - Comedy
  - Family entertainment
  - Broad notable ticketed public events

## Source priority
Do not use general web search tools for discovery. Check only the approved source URLs below, source-owned endpoints discovered from those URLs, and exact event pages linked from those approved sources. Prefer exact event pages over homepages or broad listings.

1. Live Nation UAE — https://livenation.ae/
2. Live Nation Middle East — https://www.livenation.me/ (UAE listings only)

## Known direct data surfaces
Use these confirmed source patterns before broad HTML crawling. Treat failed probes as non-fatal and fall back to the approved listing/detail pages.

- Live Nation UAE / Live Nation Middle East:
  - No confirmed event API or useful event JSON-LD was found during endpoint discovery.
  - `https://livenation.ae/` may redirect to the Middle East site. Use `https://www.livenation.me/` if needed, but keep only UAE events.
  - Crawl the Live Nation listing/home pages and exact `/event/...` detail pages linked from them.
  - Exact event pages expose title/date/venue in HTML; extract only events with UAE city/venue data.

## Source extraction recipes
Use this table to normalize candidates consistently. If a required field cannot be resolved by the primary method or fallback, drop the candidate instead of guessing.

| Source | Primary method | Date/time | Venue/city | URL | Fallback and notes |
| --- | --- | --- | --- | --- | --- |
| Live Nation UAE | Approved homepage/listing, following redirect if needed | Exact event page date/time | Exact event page venue/city | Exact `/event/...` URL when available | `https://livenation.ae/` may redirect; keep only events in Dubai, Abu Dhabi, or another UAE city. |
| Live Nation Middle East | Homepage/listing cards and exact `/event/...` pages | Exact event page date/time | Exact event page venue/city | Exact `/event/...` URL | Keep UAE listings only; exclude Egypt, Saudi, and other regional events. |
| Live Nation exact event page | Direct event page linked from an approved listing | Page date/time block | Page venue/city block | Current exact page URL | Accept only if title, date, UAE venue/city, and credible URL are all present. |

## Endpoint-first acquisition workflow
For each approved source, use this order:

1. Fetch the approved source URL directly.
2. Check whether the same source exposes structured event data before parsing visible HTML:
   - JSON-LD `Event` objects in `<script type="application/ld+json">`.
   - Embedded app state such as `__NEXT_DATA__`, Nuxt payloads, serialized Redux/Apollo state, or similar JSON blobs.
   - Same-origin API calls referenced by the page scripts or markup.
   - Same-origin RSS/Atom/ICS feeds, sitemaps, or event index files linked from the page.
3. If a same-origin endpoint returns structured event data, use that endpoint as the primary source for that website in the current run.
4. If no structured endpoint is exposed, crawl only the approved listing page and exact event detail pages linked from it.
5. Do not broaden discovery with search-engine results. If an approved source is unavailable or too JavaScript-heavy to inspect, skip it for that run and continue to the next approved source.
6. Keep source attribution as the approved source name even when using a discovered same-origin endpoint.

When crawling fallback pages, extract only event cards or exact event pages with date and UAE venue data.

## Candidate validation rules
- Must have a credible URL, title/name, date, and venue/location/city in the UAE.
- Prefer exact event pages over listing homepages.
- Exclude Egypt and other non-UAE events.
- Exclude expired events, vague promos without dates, and unsupported rumors.
- Treat Live Nation as authoritative for its own ticketed events, but not exhaustive for all UAE events.

## Helper workflow
- Use the installed `events_seen.py` helper when one is available.
- Set `EVENTS_SEEN_HELPER` to the helper script path for the current agent runtime.
- Set `EVENTS_SEEN_STATE` to a durable state file dedicated to UAE events, such as `uae-seen-events.jsonl`.
- Before responding, serialize candidates as a JSON array (`$CANDIDATES_JSON`) with fields:
  - `title`
  - `date`
  - `url`
  - `venue`
  - `city`
  - `category`
  - `source`
  - `why_interesting` (when known)
- Run the helper by piping the JSON array to stdin:

  ```bash
  printf '%s' "$CANDIDATES_JSON" | python3 "$EVENTS_SEEN_HELPER" check --state-file "$EVENTS_SEEN_STATE"
  ```

- Only include events returned under `new`.
- After composing the final digest, serialize the included events as a JSON array (`$INCLUDED_EVENTS_JSON`) and record them by piping that JSON to stdin:

  ```bash
  printf '%s' "$INCLUDED_EVENTS_JSON" | python3 "$EVENTS_SEEN_HELPER" record --state-file "$EVENTS_SEEN_STATE"
  ```

- Do not mention helper internals in the final digest.

## Digest format
Write a concise English digest grouped by category with these headings when applicable:
- `Concerts and music`
- `Comedy`
- `Family entertainment`
- `Broad notable events`

Each bullet should include:
- event title
- date/time if known
- venue/city
- why it is interesting
- source link

## Failure behavior
- If search is weak, sources are unavailable, or there are no credible new results, return exactly `[SILENT]`.
- Do not invent dates or venues.

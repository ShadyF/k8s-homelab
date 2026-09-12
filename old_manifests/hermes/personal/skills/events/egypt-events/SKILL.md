---
name: egypt-events
description: Search curated Arabic/English online sources for new interesting Egypt events, filter out techno/electronic club nights, and return a digest only when new events are found.
tags:
  - events
  - egypt
  - cairo
  - cron
---

# egypt-events

Use this skill to find and summarize new, credible events in Egypt.

## Scope
- Coverage is strictly Egypt, with Cairo/Giza priority while still covering notable events elsewhere in Egypt.
- Search Arabic and English sources.
- Summarize in English.
- Categories:
  - Music/concerts/festivals, excluding techno/electronic club nights
  - Culture/art/film/books/museums/talks
  - Tech/startup/community
  - Broad notable public events

## Source priority
Do not use general web search tools for discovery. Check only the approved source URLs below, source-owned endpoints discovered from those URLs, and exact event pages linked from those approved sources. Prefer exact event pages over homepages or broad listings.

1. Cairo360 Upcoming Events — https://www.cairo360.com/upcoming-events/
2. CairoScene Events — https://cairoscene.com/Events/ plus https://cairoscene.com/
3. TicketsMarche — https://www.ticketsmarche.com/
4. Live Nation Middle East — https://www.livenation.me/ (Egypt listings only)
5. Cairo Opera House — https://www.cairoopera.org/en/calendar/
6. El Sawy Culturewheel — https://www.culturewheel.com/en/events
7. Room Art Space — http://www.roomart.space/events
8. D-CAF — https://d-caf.org/events/
9. AUC Events — https://happening.aucegypt.edu/events/upcoming
10. Tahrir CultureFest — https://tahrirculturefest.aucegypt.edu/program
11. AUC Center for the Arts — https://centerforthearts.aucegypt.edu/index.php/events
12. Zawya — https://zawyacinema.com/calendar
13. Startup Grind New Cairo — https://www.startupgrind.com/new-cairo/
14. Founders Live Cairo — https://www.founderslive.com/events-list/cairo-2026-04

## Known direct data surfaces
Use these confirmed endpoints before HTML crawling. Treat endpoints that fail during a run as non-fatal and fall back to the source's approved listing/detail pages.

- Cairo360:
  - Try The Events Calendar REST endpoint first: `https://www.cairo360.com/wp-json/tribe/events/v1/events?start_date=<YYYY-MM-DD>&end_date=<YYYY-MM-DD>&per_page=50&wpml_language=en`.
  - API documentation/root: `https://www.cairo360.com/wp-json/tribe/events/v1/`.
  - Detail routes include `/events/<id>` and `/events/by-slug/<slug>` under the same API.
  - Caveat: the events endpoint was confirmed by route docs but has returned `502` during probing; if that happens, crawl `https://www.cairo360.com/upcoming-events/` and exact event pages linked from it.
- Cairo Opera House:
  - Use the calendar JSON endpoint: `https://www.cairoopera.org/api/custum/GetAllEventsForCalendarForSearch/?start=<YYYY-MM-DD>&end=<YYYY-MM-DD>&culture=en-us&TheaterId=&CategoryId=&CompanyId=`.
  - Response items include `id`, `title`, `url`, `imageUrl`, `start`, `end`, and `className`; expand relative `url` values against `https://www.cairoopera.org`.
  - Optional lookup endpoints with `culture: en-us` header: `/api/opera/GetAllTheaters`, `/api/opera/GetAllEventCategory`, `/api/opera/GetAllCompanies`.
- El Sawy Culturewheel:
  - Use the monthly export endpoint before scraping cards: `https://www.culturewheel.com/en/events-pdf-export?month=<MM>&year=<YYYY>`.
  - Despite the name, it returns extractable event data with date/day/time, title, room/venue, price, description, image, and entry rules.
  - Also crawl exact event links from `https://www.culturewheel.com/en/events` when needed.
- D-CAF:
  - Use WordPress event posts first: `https://d-caf.org/wp-json/wp/v2/event?per_page=50`.
  - Event objects include `id`, `date`, `modified`, `slug`, `link`, `title.rendered`, `content.rendered`, `excerpt.rendered`, `eventcat`, `organizer`, `event_tags`, `location`, and `_links`.
  - Do not treat WordPress `date` or `modified` as the event date; those are publication/update timestamps. Extract the real event date/time from `content.rendered`, the exact `link` page, or another event-specific field before accepting a candidate.
  - Search endpoint can help resolve known titles: `https://d-caf.org/wp-json/wp/v2/search?search=<query>&per_page=10`, then follow `_links.self.href` for `event` results.
- AUC Events:
  - Use Drupal JSON:API first: `https://happening.aucegypt.edu/jsonapi/node/event?filter%5Bfield_event_date%5D%5Bcondition%5D%5Bpath%5D=field_event_date&filter%5Bfield_event_date%5D%5Bcondition%5D%5Boperator%5D=%3E%3D&filter%5Bfield_event_date%5D%5Bcondition%5D%5Bvalue%5D=<YYYY-MM-DD>&sort=field_event_date&page%5Blimit%5D=50&include=field_event_venu`.
  - Event attributes include `title`, `field_event_date`, `field_event_end_date`, `field_event_time`, `field_event_end_time`, `body`, `field_event_link`, `field_external_image`, `field_cg_event_id`, and `path.alias`.
  - Resolve `relationships.field_event_venu` from the included venue resource, or open the detail page, before accepting the event as having a venue/location.
- Founders Live Cairo:
  - Use JSON-LD `Event` objects embedded in the page before HTML parsing. Confirmed fields include `name`, `startDate`, `endDate`, and page URL data.
- Startup Grind New Cairo:
  - Parse embedded `__NEXT_DATA__`/Bevy page state first when present, then fallback to HTML event cards.
- Room Art Space:
  - No confirmed event API. Crawl the approved listing and exact event pages; event cards may expose Google Calendar/ICS links with date/time and venue details.
- Tahrir CultureFest:
  - No confirmed event API. Crawl program cards and exact detail pages for title, date range, time range, location, description, speaker, and ticket blocks.
- AUC Center for the Arts:
  - No confirmed event API; `/jsonapi/node/event` and `/index.php/jsonapi/node/event` returned 404. Crawl the approved events page and exact event cards.
- Zawya:
  - No confirmed event API or structured event blob. Crawl the approved calendar page and exact screening/event pages.
- CairoScene:
  - No confirmed event API from the approved page. Crawl the approved Events page and exact event pages only.
- TicketsMarche:
  - No confirmed JSON endpoint. Crawl the homepage/listing and exact `/event/...` pages. The observed `/Event_filter_grid/Eventlist_filter` route returns HTML, not JSON.
- Live Nation Middle East:
  - No confirmed event API or useful JSON-LD for events. Crawl the homepage/listing and exact `/event/...` pages linked from it, keeping only Egypt events.

## Source extraction recipes
Use this table to normalize candidates consistently. If a required field cannot be resolved by the primary method or fallback, drop the candidate instead of guessing.

| Source | Primary method | Date/time | Venue/city | URL | Fallback and notes |
| --- | --- | --- | --- | --- | --- |
| Cairo360 | Events Calendar REST `/wp-json/tribe/events/v1/events` | Event API date fields when available | Event API venue fields or exact page text | API link/detail route | Endpoint may return `502`; if so parse approved listing cards and exact event pages only. |
| CairoScene | Approved Events page and exact linked pages | Listing/detail page text | Listing/detail page text | Exact CairoScene event URL | No confirmed event API; skip generic articles that do not expose date and venue. |
| TicketsMarche | Homepage/listing cards and exact `/event/...` pages | Exact event page date/time | Exact event page venue/city | Exact `/event/...` URL | Observed filter route returns HTML, not JSON; use exact pages for final details. |
| Live Nation Middle East | Homepage/listing cards and exact `/event/...` pages | Exact event page date/time | Exact event page venue/city | Exact `/event/...` URL | Keep Egypt listings only; no confirmed useful event API/JSON-LD. |
| Cairo Opera House | Calendar JSON API | `start` and `end` | Detail page or theater lookup if venue is missing | API `url`, resolved against `https://www.cairoopera.org` | Prefer API title/date plus exact page for venue confirmation. |
| El Sawy Culturewheel | Monthly export endpoint | Export date/day/time fields | Export room/venue fields | Exact event link when available | Use listing/detail pages when export data is incomplete. |
| Room Art Space | Approved listing and exact event pages | Event card/detail page date and time, or linked calendar/ICS | Event card/detail venue | Exact Room event URL | No confirmed event API; ignore non-event organization/location structured data. |
| D-CAF | WP REST `wp/v2/event` plus exact event page | Real event date parsed from `content.rendered` or exact page | `location`, rendered content, or exact page | `link` | Never use WP `date`/`modified` as event date. |
| AUC Events | Drupal JSON:API with `include=field_event_venu` | `field_event_date`, `field_event_end_date`, `field_event_time`, `field_event_end_time` | Resolve `relationships.field_event_venu` from `included`, or exact page | `path.alias` or `field_event_link` | Drop candidates with unresolved venue/location. |
| Tahrir CultureFest | Program cards and exact detail pages | Program card/detail date and time range | Program card/detail location | Exact program/detail URL | No confirmed API; parse only program/event blocks. |
| AUC Center for the Arts | Approved events page and exact event cards | Event card/detail text | Event card/detail text | Exact event/card URL | No confirmed JSON:API; use HTML fallback only. |
| Zawya | Calendar/listing and exact screening pages | Screening/detail date/time | Screening/detail venue | Exact Zawya page URL | Calendar may be empty; skip if current listings do not expose valid future events. |
| Startup Grind New Cairo | Embedded `__NEXT_DATA__`/Bevy state | Embedded event date/time | Embedded venue or event page | Event page URL | Fallback to HTML event cards when app state is unavailable. |
| Founders Live Cairo | JSON-LD `Event` objects | `startDate` and `endDate` | JSON-LD location or event page | JSON-LD/page URL | Confirm city is Cairo/Egypt before including. |
| Instagram approved profiles | Public profile/post content only | Post caption/event image text | Post caption/event image text | Public post/profile URL | Use only when accessible without login; do not use search results to discover posts. |

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

When crawling fallback pages, extract only event cards or exact event pages with date and venue data. Avoid generic article, dining, nightlife, or promotion pages unless they clearly describe a valid Egypt event.

## Instagram discovery sources
Use Instagram only as a source-bounded fallback when the public profile or post content is accessible without login. Do not use search-engine results to discover Instagram posts.

- @cairoscene — https://www.instagram.com/cairoscene/
- @scenenowevents — https://www.instagram.com/scenenowevents/
- @ticketsmarche — https://www.instagram.com/ticketsmarche/
- @cairooperahouse_official — https://www.instagram.com/cairooperahouse_official/
- @elsawyculturewheel — https://www.instagram.com/elsawyculturewheel/
- @zawyacinema — https://www.instagram.com/zawyacinema/
- @cairojazzclub — https://www.instagram.com/cairojazzclub/ (strictly exclude techno/electronic/club-night posts)
- @founderslivecairo — https://www.instagram.com/founderslivecairo/

## Candidate validation rules
- Must have a credible URL, title/name, date, and venue/location/city in Egypt.
- Prefer exact event pages over listing homepages.
- Exclude UAE and other non-Egypt events.
- Exclude techno/electronic/DJ/club-night/rave/party/nightlife-only events unless clearly a broader festival or cultural event.
- Exclude expired events, vague promos without dates, and unsupported rumors.

## Helper workflow
- Use the installed `events_seen.py` helper when one is available.
- Set `EVENTS_SEEN_HELPER` to the helper script path for the current agent runtime.
- Set `EVENTS_SEEN_STATE` to a durable state file dedicated to Egypt events, such as `egypt-seen-events.jsonl`.
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
- `Music, concerts, and festivals`
- `Culture, art, film, books, and talks`
- `Tech, startup, and community`
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

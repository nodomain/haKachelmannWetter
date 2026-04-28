# Product

Custom Home Assistant integration for the KachelmannWetter API (Meteologix AG). Provides current weather, hourly/daily forecasts, astronomical data, and automation-ready sensors using all 5 API endpoints with every available field.

## Core Capabilities

- **Weather entity** — current conditions, hourly (24h) and daily (10+ days) forecast
- **33 sensors** — dew point, precipitation, snow, sunshine, cloud coverage, global radiation, astronomy (sun/moon), API rate limit
- **4 binary sensors** — rain expected, frost tonight, thunderstorm expected, daytime
- **Diagnostics** — debug download from HA UI with API key redaction
- **HACS compatible** — custom repository with brand assets

## Hardware Context

- **API:** KachelmannWetter v02 (Meteologix AG), hobby plan (700 req/day)
- **Endpoints:** `/current`, `/advanced/1h`, `/advanced/6h`, `/trend14days`, `/tools/astronomy`
- **Update interval:** 600s default (5 endpoints × 144 updates = 720 req/day)

## Key Design Decisions

- All 5 API calls run in parallel via `asyncio.gather` with 10s timeout
- Daily forecast aggregates from 6h slots — always maps as daytime to avoid night icons leaking
- `clear-night` condition only used for current weather (based on `isDay` field)
- Forecast enrichment: precipitation probability from trend14 merged into daily forecast
- Rate limit tracked from response headers and exposed as diagnostic sensor
- Config flow pre-fills home coordinates, unique ID prevents duplicate entries
- Entity naming follows HA conventions: main entity unnamed (device name), sensors use translation keys

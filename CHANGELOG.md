# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [2.3.2] - 2026-04-28 - Fix moon icon in daily forecast

### Fixed
- Daily forecast no longer shows moon (clear-night) icon — night slots were leaking into day aggregation due to non-deterministic set ordering in worst-condition selection

## [2.3.1] - 2026-04-28 - Security fix: redact sensitive data from logs

### Security
- Remove clear-text logging of user coordinates in coordinator (CodeQL CWE-312/CWE-532)
- Remove clear-text logging of API request URLs containing location data in client (CodeQL CWE-312/CWE-532)

## [2.3.0] - 2026-04-28 - Kachelmann weather icons as entity picture

### Added
- Weather entity shows Kachelmann SVG weather symbol as `entity_picture`
- Icon updates dynamically based on current `weatherSymbol` from API
- Store raw `weather_symbol` in normalized current data

## [2.2.0] - 2026-04-28 - Gold tier with tests and pre-commit

### Added
- 21 unit tests covering config flow, setup/unload, weather entity, sensors, binary sensors, and all helper functions
- Pre-commit hooks (ruff lint + format, pytest)
- pytest-homeassistant-custom-component test infrastructure
- Restore `strings.json` (needed by test framework)

### Changed
- CI: ruff blocking, mypy informational, Node.js 24

## [2.1.0] - 2026-04-28 - Full trend exposure

### Added
- 14-day trend overview sensor with all trend data as attributes — access any day via templates: `{{ state_attr('sensor.kachelmannwetter_trend_14day', 'days')[3].temp_max }}`
- Precipitation forecast sensors for today and tomorrow (mm)
- Max possible sunshine hours sensor for today
- Wind gust forecast sensors for today and tomorrow (from 14-day trend)

## [2.0.0] - 2026-04-28 - HA developer docs compliance

### Changed
- **BREAKING:** Device identifier changed from config entry ID to coordinates — remove and re-add the integration after updating
- Coordinator now passes `config_entry` to HA (required by modern HA)
- All 5 API calls now run in parallel via `asyncio.gather` (significantly faster updates)
- Reauth flow now works correctly — coordinator raises `ConfigEntryAuthFailed` directly
- Weather forecast cards now update live via `async_update_listeners`
- Config flow pre-fills home coordinates as defaults
- Config entry title includes coordinates for clarity
- Device identifier uses coordinates for stable identity across re-adds
- Diagnostics uses HA standard `async_redact_data` instead of custom redaction

### Added
- 10-second request timeout on all API calls
- `integration_type: service` in manifest
- `LIGHT` device class on daytime binary sensor
- `hail` and `windy-variant` weather condition mappings

### Removed
- `strings.json` — custom integrations must only use `translations/`
- `state_class` from forecast-derived sensors (incorrect per HA docs)
- `DISTANCE` device class from snow height (prevented unwanted imperial conversion)
- All hardcoded `name=` and `icon=` from entity descriptions (now from translations and icons.json)

### Fixed
- `round()` crash with None value in wind bearing calculation
- Forecast dicts now use proper `Forecast` TypedDict construction
- Entity description type annotations on entity classes (fixes mypy)
- Unused `InvalidAuth` import removed from `__init__.py`

## [1.0.0] - 2026-04-27 - Feature-complete release

### Added
- Weather entity with daily (10+ days) and hourly (24h) forecast
- Automatic `clear-night` condition at nighttime
- 31 sensor entities: dew point, precipitation, snow, sunshine, cloud coverage (low/medium/high), global radiation (current/today/tomorrow), sunshine hours, wind gust max, precipitation probability, astronomy (sunrise, sunset, solar transit, civil/nautical/astronomical dawn & dusk, moonrise, moonset, moon illumination, moon phase, next full/new moon), API rate limit
- 4 binary sensor entities: rain expected (3h), frost tonight, thunderstorm expected, daytime
- Rate limit tracking from API response headers
- `icons.json` with state-dependent icons (moon phase, day/night)
- Full astronomy endpoint integration
- 14-day trend endpoint with precipitation probability enrichment on daily forecast

## [0.4.0] - 2026-04-27 - HA standards alignment

### Changed
- Reauth flow uses `_get_reauth_entry()` and `async_update_reload_and_abort`
- Options flow uses modern `self.config_entry` pattern
- Config flow sets unique ID from coordinates, prevents duplicate entries
- Weather entity name set to `None` (main device feature pattern)
- `DeviceEntryType.SERVICE` enum instead of string

### Added
- Options reload via `add_update_listener`
- `vol.Range` validation on update interval (60–3600s)
- `vol.Coerce(float)` for lat/lon input
- `already_configured` abort translation

## [0.3.0] - 2026-04-27 - API feature-complete

### Added
- 14-day trend endpoint (`/trend14days`) with precipitation probability, type, thunderstorm warning, sun hours relative, cloud coverage eighths
- Astronomy endpoint (`/tools/astronomy`) with sunrise, sunset, moon data
- `clear-night` condition using `isDay` from current weather
- Fresh snow sensor (`snowAmount`)
- Thunderstorm expected binary sensor
- Daytime binary sensor
- Diagnostics support
- German translations
- HACS compatibility (`hacs.json`)
- Brand assets (icon.png, logo.png)

## [0.2.0] - 2026-04-27 - Hourly forecast and sensors

### Added
- Hourly forecast support (`FORECAST_HOURLY`) via `/advanced/1h` endpoint
- Sensor platform with precipitation, snow height, sunshine duration, global radiation, sunshine hours, wind gust max, cloud coverage (low/medium/high)
- Binary sensor platform: rain expected (3h), frost expected tonight
- Device registration with Meteologix AG manufacturer info
- All current weather fields: dew point, cloud coverage

## [0.1.0] - 2026-04-27 - Initial release

### Added
- Basic weather entity with daily forecast from `/advanced/6h` endpoint
- Current weather conditions from `/current` endpoint
- Config flow with API key and coordinate input
- Options flow for update interval

# Tech Stack

## Platform

- **Home Assistant** — custom integration (HACS compatible)
- **Python 3.12+** — async/await throughout
- **pytest-homeassistant-custom-component** — test framework

## Project Structure

```
haKachelmannWetter/
├── custom_components/kachelmannwetter/
│   ├── __init__.py          # Setup, unload, reauth
│   ├── client.py            # Async API wrapper (aiohttp)
│   ├── config_flow.py       # Config + options + reauth flows
│   ├── const.py             # Constants, entity descriptions
│   ├── coordinator.py       # DataUpdateCoordinator (parallel fetch)
│   ├── helpers.py           # API response normalization, condition mapping
│   ├── weather.py           # WeatherEntity (daily + hourly forecast)
│   ├── sensor.py            # 33 sensor entities
│   ├── binary_sensor.py     # 4 binary sensor entities
│   ├── diagnostics.py       # Debug download with redaction
│   ├── exceptions.py        # Custom exceptions (InvalidAuth, RateLimitError)
│   ├── icons.json           # State-dependent MDI icons
│   ├── manifest.json        # Integration metadata + version
│   ├── strings.json         # Base strings (test framework needs this)
│   └── translations/        # en.json, de.json
├── tests/                   # Unit tests (pytest)
├── brand/                   # icon.png, logo.png for HACS
├── scripts/                 # Utility scripts (audit, etc.)
├── pyproject.toml           # Ruff, mypy, pytest config
└── .pre-commit-config.yaml  # Ruff lint+format, pytest
```

## Quality Gates (pre-commit)

1. **ruff** — lint with `--fix` (E, F, W, I, UP, BLE rules)
2. **ruff format** — auto-format
3. **pytest** — all tests must pass (`-x -q`)

## Code Conventions

- Line length: 100 characters
- All code, comments, docstrings in English
- Type hints on all function signatures
- Async everywhere — no blocking I/O
- Entity descriptions defined in `const.py`, names from `translations/`
- No hardcoded `name=` or `icon=` on entities — use translations and `icons.json`
- Internal/extra forecast fields prefixed with `_` (stripped before HA sees them)

## Commands

```bash
# Run tests
.venv/bin/pytest tests/ -v

# Run single test file
.venv/bin/pytest tests/test_helpers.py -v

# Lint
.venv/bin/ruff check .

# Format
.venv/bin/ruff format .

# Type check (informational, not blocking)
.venv/bin/mypy custom_components/kachelmannwetter/
```

## Key HA Patterns Used

| Pattern | Where |
|---|---|
| `DataUpdateCoordinator` | coordinator.py — single update loop |
| `CoordinatorEntity` | All entity platforms |
| `ConfigEntry` | Setup, options, reauth |
| `DeviceInfo` | Shared device across all entities |
| `WeatherEntityFeature` | FORECAST_DAILY, FORECAST_HOURLY |
| `async_update_listeners` | Live forecast card updates |
| `ConfigEntryAuthFailed` | Triggers reauth flow |
| `async_redact_data` | Diagnostics |

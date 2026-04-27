# KachelmannWetter for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![GitHub Release](https://img.shields.io/github/v/release/nodomain/haKachelmannWetter)](https://github.com/nodomain/haKachelmannWetter/releases)

Custom Home Assistant integration for the [KachelmannWetter API](https://api.kachelmannwetter.com/v02/_doc.html) by Meteologix AG.

Provides current weather, hourly and daily forecasts, astronomical data, and automation-ready sensors — using **all 5 API endpoints** with **every available field**.

## Features

### Weather Entity
- Current conditions with temperature, humidity, pressure, dew point, cloud coverage, wind
- **Hourly forecast** (24h ahead)
- **Daily forecast** (10+ days) with precipitation probability from 14-day trend
- Automatic `clear-night` condition at nighttime

### Sensors (22)

| Sensor | Source |
|---|---|
| Dew point | Current |
| Precipitation (1h) | Current |
| Snow height | Current |
| Fresh snow (snowAmount) | Current |
| Sunshine duration (1h) | Current |
| Cloud coverage low / medium / high | Hourly forecast |
| Global radiation (current hour) | Hourly forecast |
| Global radiation today / tomorrow | 6h forecast |
| Sunshine hours today / tomorrow | 6h forecast |
| Wind gust max today | 6h forecast |
| Precipitation probability today / tomorrow | 14-day trend |
| Sunshine relative today (%) | 14-day trend |
| Sunrise / Sunset | Astronomy |
| Moon illumination (%) | Astronomy |
| Moon phase | Astronomy |
| Next full moon / Next new moon | Astronomy |

### Binary Sensors (4)

| Sensor | Logic |
|---|---|
| Rain expected (3h) | Checks hourly forecast for precipitation or rain conditions |
| Frost expected tonight | Daily forecast templow < 0°C |
| Thunderstorm expected | 14-day trend thunderstorm field (today + tomorrow) |
| Daytime | Current `isDay` field |

### Additional
- Device registration with manufacturer info
- Diagnostics support (debug download from HA UI)
- German and English translations
- HACS compatible

## Prerequisites

1. A **KachelmannWetter Plus subscription** ([kachelmannwetter.com](https://kachelmannwetter.com/))
2. An **API key** — activate it in your [account settings](https://accounts.meteologix.com/subscriptions) under "API-Keys verwalten"
3. A **configured API location** — set it under "API-Standorte verwalten" in your subscription (max 2 locations on the hobby plan)

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu (top right) → **Custom repositories**
3. Add `https://github.com/nodomain/haKachelmannWetter` with category **Integration**
4. Search for "KachelmannWetter" and install it
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/kachelmannwetter` folder to your HA `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **KachelmannWetter**
3. Enter your API key and the coordinates of your configured API location
4. Done — all entities will be created automatically

### Options

After setup, you can adjust the update interval (default: 600 seconds / 10 minutes) via the integration options.

> **Rate limit:** The hobby plan allows 700 requests/day. With 5 endpoints per update and a 10-minute interval, that's ~720 requests/day — right at the limit. Consider increasing the interval to 15 minutes (900s) if you hit rate limits.

## API Coverage

This integration uses **all 5 available API endpoints** and maps **every field**:

| Endpoint | Fields | Status |
|---|---|---|
| `/current/{lat}/{lon}` | 15 | ✅ All mapped |
| `/forecast/{lat}/{lon}/advanced/1h` | 22 | ✅ All mapped |
| `/forecast/{lat}/{lon}/advanced/6h` | 24 | ✅ All mapped |
| `/forecast/{lat}/{lon}/trend14days` | 29 | ✅ All mapped |
| `/tools/astronomy/{lat}/{lon}` | 16 | ✅ All mapped |

Run `scripts/audit_api_coverage.py` to verify coverage.

## Dashboard Widget

```yaml
type: weather-forecast
entity: weather.kachelmannwetter
show_current: true
show_forecast: true
forecast_type: daily
```

For hourly forecast:
```yaml
type: weather-forecast
entity: weather.kachelmannwetter
show_current: true
show_forecast: true
forecast_type: hourly
```

## Credits

- Weather data by [Meteologix AG / Kachelmann Gruppe](https://kachelmannwetter.com/)
- Original integration by [@manutoky](https://github.com/manutoky/haKachelmannWetter)
- Extended by [@nodomain](https://github.com/nodomain)

## License

MIT

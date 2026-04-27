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

### Sensors (31)

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
| Sunrise / Sunset / Solar transit | Astronomy |
| Civil dawn / dusk | Astronomy |
| Nautical dawn / dusk | Astronomy (disabled by default) |
| Astronomical dawn / dusk | Astronomy (disabled by default) |
| Moonrise / Moonset | Astronomy |
| Moon illumination (%) / Moon phase | Astronomy |
| Next full moon / Next new moon | Astronomy |
| API requests remaining | Rate limit |

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

## Automation Examples

### Close roller shutters before a storm

```yaml
automation:
  - alias: "Close shutters before thunderstorm"
    trigger:
      - platform: state
        entity_id: binary_sensor.kachelmannwetter_thunderstorm_expected
        to: "on"
    action:
      - service: cover.close_cover
        target:
          area_id: wohnzimmer
      - service: notify.mobile_app
        data:
          title: "⛈️ Gewitter erwartet"
          message: "Rollläden wurden geschlossen."
```

### Frost warning notification

```yaml
automation:
  - alias: "Frost warning tonight"
    trigger:
      - platform: state
        entity_id: binary_sensor.kachelmannwetter_frost_expected_tonight
        to: "on"
    condition:
      - condition: time
        after: "16:00:00"
        before: "22:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "🥶 Frostwarnung"
          message: >
            Heute Nacht wird es {{ state_attr('weather.kachelmannwetter', 'forecast')[0].native_templow }}°C kalt.
            Pflanzen reinholen!
```

### Umbrella reminder when leaving home

```yaml
automation:
  - alias: "Umbrella reminder"
    trigger:
      - platform: state
        entity_id: person.your_name
        from: "home"
    condition:
      - condition: state
        entity_id: binary_sensor.kachelmannwetter_rain_expected_3h
        state: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "🌧️ Regenschirm mitnehmen!"
          message: >
            Regenwahrscheinlichkeit: {{ states('sensor.kachelmannwetter_precipitation_probability_today') }}%
```

### Turn on garden irrigation only when no rain expected

```yaml
automation:
  - alias: "Garden irrigation"
    trigger:
      - platform: time
        at: "06:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.kachelmannwetter_rain_expected_3h
        state: "off"
      - condition: numeric_state
        entity_id: sensor.kachelmannwetter_precipitation_probability_today
        below: 30
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.garden_irrigation
      - delay: "00:30:00"
      - service: switch.turn_off
        target:
          entity_id: switch.garden_irrigation
```

### PV forecast notification

```yaml
automation:
  - alias: "PV forecast morning briefing"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "☀️ Solar-Prognose"
          message: >
            Heute: {{ states('sensor.kachelmannwetter_global_radiation_today') }} Wh/m²
            ({{ states('sensor.kachelmannwetter_sun_hours_today') }}h Sonne, {{ states('sensor.kachelmannwetter_sun_hours_relative_today') }}%)
            Morgen: {{ states('sensor.kachelmannwetter_global_radiation_tomorrow') }} Wh/m²
            ({{ states('sensor.kachelmannwetter_sun_hours_tomorrow') }}h Sonne)
```

### Outdoor lights based on civil dusk/dawn

```yaml
automation:
  - alias: "Outdoor lights on at civil dusk"
    trigger:
      - platform: template
        value_template: >
          {{ now().isoformat()[:19] == states('sensor.kachelmannwetter_civil_dusk')[:19] }}
    action:
      - service: light.turn_on
        target:
          area_id: vorgarten

  - alias: "Outdoor lights off at civil dawn"
    trigger:
      - platform: template
        value_template: >
          {{ now().isoformat()[:19] == states('sensor.kachelmannwetter_civil_dawn')[:19] }}
    action:
      - service: light.turn_off
        target:
          area_id: vorgarten
```

## Template Sensors

### Daylight duration

```yaml
template:
  - sensor:
      - name: "Daylight duration"
        unit_of_measurement: "h"
        icon: mdi:weather-sunny
        state: >
          {% set rise = states('sensor.kachelmannwetter_sunrise') %}
          {% set sett = states('sensor.kachelmannwetter_sunset') %}
          {% if rise and sett and rise != 'unknown' and sett != 'unknown' %}
            {{ ((as_timestamp(sett) - as_timestamp(rise)) / 3600) | round(1) }}
          {% else %}
            unknown
          {% endif %}
```

### Moon phase name

```yaml
template:
  - sensor:
      - name: "Moon phase name"
        icon: mdi:moon-waning-gibbous
        state: >
          {% set phase = states('sensor.kachelmannwetter_moon_phase') | int(0) %}
          {% if phase <= 5 %}New Moon
          {% elif phase <= 15 %}Waxing Crescent
          {% elif phase <= 25 %}First Quarter
          {% elif phase <= 35 %}Waxing Gibbous
          {% elif phase <= 55 %}Full Moon
          {% elif phase <= 65 %}Waning Gibbous
          {% elif phase <= 75 %}Last Quarter
          {% elif phase <= 85 %}Waning Crescent
          {% else %}New Moon{% endif %}
```

### Weather summary for TTS / notifications

```yaml
template:
  - sensor:
      - name: "Weather summary"
        state: >
          {{ states('weather.kachelmannwetter') | replace('partlycloudy', 'partly cloudy') | replace('clear-night', 'clear') }},
          {{ state_attr('weather.kachelmannwetter', 'temperature') }}°C.
          {% if is_state('binary_sensor.kachelmannwetter_rain_expected_3h', 'on') %}Rain expected within 3 hours.{% endif %}
          {% if is_state('binary_sensor.kachelmannwetter_frost_expected_tonight', 'on') %}Frost warning tonight.{% endif %}
          {% if is_state('binary_sensor.kachelmannwetter_thunderstorm_expected', 'on') %}Thunderstorm expected!{% endif %}
```

### API rate limit warning

```yaml
automation:
  - alias: "API rate limit warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.kachelmannwetter_api_requests_remaining
        below: 50
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ KachelmannWetter API"
          message: >
            Nur noch {{ states('sensor.kachelmannwetter_api_requests_remaining') }} API-Requests übrig.
            Eventuell Update-Intervall erhöhen.
```

## Credits

- Weather data by [Meteologix AG / Kachelmann Gruppe](https://kachelmannwetter.com/)
- Original integration by [@manutoky](https://github.com/manutoky/haKachelmannWetter)
- Extended by [@nodomain](https://github.com/nodomain)

## License

MIT

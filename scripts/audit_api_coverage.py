#!/usr/bin/env python3
"""Audit script: compare all API fields against what the integration uses."""
import asyncio
import aiohttp
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from custom_components.kachelmannwetter.helpers import (
    normalize_current,
    normalize_hourly,
    normalize_daily_from_6h,
    normalize_trend14,
    normalize_astronomy,
)

API_KEY = ""
LAT = 00.0000
LON = 00.0000
BASE = "https://api.kachelmannwetter.com/v02"

ENDPOINTS = {
    "current": f"{BASE}/current/{LAT}/{LON}",
    "hourly_1h": f"{BASE}/forecast/{LAT}/{LON}/advanced/1h",
    "forecast_6h": f"{BASE}/forecast/{LAT}/{LON}/advanced/6h",
    "trend14days": f"{BASE}/forecast/{LAT}/{LON}/trend14days",
    "astronomy": f"{BASE}/tools/astronomy/{LAT}/{LON}",
}


async def fetch_all():
    headers = {"X-API-Key": API_KEY}
    raw = {}
    async with aiohttp.ClientSession() as session:
        for name, url in ENDPOINTS.items():
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    print(f"ERROR {name}: HTTP {resp.status}")
                    continue
                raw[name] = await resp.json()
    return raw


def audit_current(raw):
    data = raw.get("current", {})
    api_fields = set(data.get("data", {}).keys())
    normalized = normalize_current(data)
    used = set(normalized.keys())
    print("=" * 60)
    print("CURRENT WEATHER")
    print("=" * 60)
    print(f"  API fields:        {sorted(api_fields)}")
    print(f"  Normalized fields: {sorted(used)}")
    print()


def audit_hourly(raw):
    data = raw.get("hourly_1h", {})
    entries = data.get("data", [])
    api_fields = set(entries[0].keys()) if entries else set()
    normalized = normalize_hourly(data)
    used = set(normalized[0].keys()) if normalized else set()
    print("=" * 60)
    print("HOURLY FORECAST (1h)")
    print("=" * 60)
    print(f"  API fields ({len(api_fields)}):        {sorted(api_fields)}")
    print(f"  Normalized fields ({len(used)}): {sorted(used)}")
    unused = api_fields - {
        "dateTime", "isDay", "temp", "dewpoint", "pressureMsl",
        "humidityRelative", "windSpeed", "windDirection", "windGust",
        "windGust3h", "cloudCoverage", "cloudCoverageLow",
        "cloudCoverageMedium", "cloudCoverageHigh", "sunHours",
        "globalRadiation", "precCurrent", "prec6h", "precTotal",
        "snowAmount", "snowAmount6h", "snowHeight", "wmoCode",
        "weatherSymbol", "tempMin6h", "tempMax6h",
    }
    if unused:
        print(f"  ⚠️  UNMAPPED API fields: {sorted(unused)}")
    else:
        print("  ✅ All API fields mapped")
    print()


def audit_6h(raw):
    data = raw.get("forecast_6h", {})
    entries = data.get("data", [])
    api_fields = set(entries[0].keys()) if entries else set()
    normalized = normalize_daily_from_6h(data)
    used = set(normalized[0].keys()) if normalized else set()
    print("=" * 60)
    print("6H FORECAST (daily aggregation)")
    print("=" * 60)
    print(f"  API fields ({len(api_fields)}):        {sorted(api_fields)}")
    print(f"  Normalized fields ({len(used)}): {sorted(used)}")
    unused = api_fields - {
        "dateTime", "isDay", "temp", "tempMin6h", "tempMax6h",
        "tempMin12h", "tempMax12h", "dewpoint", "pressureMsl",
        "humidityRelative", "windSpeed", "windDirection", "windGust",
        "cloudCoverage", "cloudCoverageLow", "cloudCoverageMedium",
        "cloudCoverageHigh", "sunHours", "globalRadiation",
        "precCurrent", "prec6h", "prec12h", "precTotal",
        "snowAmount", "snowAmount6h", "snowAmount12h", "snowHeight",
        "wmoCode", "weatherSymbol",
    }
    if unused:
        print(f"  ⚠️  UNMAPPED API fields: {sorted(unused)}")
    else:
        print("  ✅ All API fields mapped")
    print()


def audit_trend14(raw):
    data = raw.get("trend14days", {})
    entries = data.get("data", [])
    api_fields = set(entries[0].keys()) if entries else set()
    normalized = normalize_trend14(data)
    used = set(normalized[0].keys()) if normalized else set()
    print("=" * 60)
    print("14-DAY TREND")
    print("=" * 60)
    print(f"  API fields ({len(api_fields)}):        {sorted(api_fields)}")
    print(f"  Normalized fields ({len(used)}): {sorted(used)}")
    unused = api_fields - {
        "dateTime", "isWeekend", "weekday", "tempMax", "tempMaxLow",
        "tempMaxHigh", "tempMin", "tempMinLow", "tempMinHigh",
        "prec", "precLow", "precHigh", "precProb1mm", "precProb10mm",
        "precType", "precIntensity", "precWord", "windGust",
        "windGustLow", "windGustHigh", "sunMaxPos", "sunHours",
        "sunHoursRelative", "sunHoursLow", "sunHoursHigh",
        "cloudCoverageEighths", "cloudWord", "thunderStorm",
        "weatherSymbol",
    }
    if unused:
        print(f"  ⚠️  UNMAPPED API fields: {sorted(unused)}")
    else:
        print("  ✅ All API fields mapped")
    print()


def audit_astronomy(raw):
    data = raw.get("astronomy", {})
    top_fields = {k for k in data.keys() if k not in ("dailyData", "lat", "lon", "timeZone", "run")}
    day_fields = set(data.get("dailyData", [{}])[0].keys())
    normalized = normalize_astronomy(data)
    norm_top = {k for k in normalized.keys() if k != "days"}
    norm_day = set(normalized.get("days", [{}])[0].keys()) if normalized.get("days") else set()
    print("=" * 60)
    print("ASTRONOMY")
    print("=" * 60)
    print(f"  API top fields:    {sorted(top_fields)}")
    print(f"  Norm top fields:   {sorted(norm_top)}")
    print(f"  API day fields ({len(day_fields)}):  {sorted(day_fields)}")
    print(f"  Norm day fields ({len(norm_day)}): {sorted(norm_day)}")
    unused_top = top_fields - {"nextFullMoon", "nextNewMoon"}
    unused_day = day_fields - {
        "dateTime", "sunrise", "sunset", "transit",
        "civilDawn", "civilDusk", "nauticalDawn", "nauticalDusk",
        "astronomicalDawn", "astronomicalDusk",
        "moonIllumination", "moonPhase", "moonRise", "moonSet",
    }
    if unused_top or unused_day:
        print(f"  ⚠️  UNMAPPED: top={sorted(unused_top)}, day={sorted(unused_day)}")
    else:
        print("  ✅ All API fields mapped")
    print()


async def main():
    print("Fetching all endpoints...")
    raw = await fetch_all()
    print(f"Fetched {len(raw)} endpoints\n")

    audit_current(raw)
    audit_hourly(raw)
    audit_6h(raw)
    audit_trend14(raw)
    audit_astronomy(raw)

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Endpoints used: {len(raw)}/5")
    print("  Run this script after changes to verify full coverage.")


if __name__ == "__main__":
    asyncio.run(main())

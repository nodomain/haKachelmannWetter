"""Constants for the KachelmannWetter integration."""

from homeassistant.const import Platform

DOMAIN = "kachelmannwetter"
DEFAULT_NAME = "KachelmannWetter"
PLATFORMS: list[Platform] = [Platform.WEATHER]

CONF_API_KEY = "api_key"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"

OPTION_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 600  # seconds
MIN_UPDATE_INTERVAL = 60  # seconds
MAX_UPDATE_INTERVAL = 3600  # seconds

API_BASE = "https://api.kachelmannwetter.com/v02"

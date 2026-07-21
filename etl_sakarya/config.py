"""TransitJSON ETL — sabitler (Sakarya / SBB Public API)."""
from __future__ import annotations

# --- SBB Public API ---
BASE_URL = "https://sbbpublicapi.sakarya.bel.tr/api/v1"

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://ulasim.sakarya.bel.tr",
    "Referer": "https://ulasim.sakarya.bel.tr/",
    "Connection": "keep-alive",
}

# --- Shape ---
# GeoJSON MultiLineString [lng,lat] → doğrudan {lat, lon} dizisi; polyline yok.

# --- İstek davranışı ---
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 1.5
SLEEP_BETWEEN = 0.15

# --- Sabit varlıklar ---
COUNTRY = {
    "country_id": "TR",
    "name": "Türkiye",
    "source": "manual",
}

CITY = {
    "city_id": "SAK",
    "slug": "sakarya",
    "country_id": "TR",
    "name": "Sakarya",
    "timezone": "Europe/Istanbul",
    "default_zoom": 12,
    "source": "manual",
    "center_fallback": {"lat": 40.7569, "lon": 30.3781},
}

AGENCY = {
    "agency_id": "sbb",
    "city_id": "SAK",
    "name": "Sakarya Büyükşehir Belediyesi",
    "website": "https://ulasim.sakarya.bel.tr",
    "source": "manual",
}

DEFAULT_AGENCY_ID = "sbb"
DEFAULT_STOP_MODE = "fixed"

CITY_ID = "SAK"
ROUTE_ID_PREFIX = "SAK"
ROUTE_ID_WIDTH = 4
STOP_ID_PREFIX = "SAK_ST"
STOP_ID_WIDTH = 5

SOURCE_API = "api-sbb"
SOURCE_GENERATED = "api-sbb"

# --- 2026 Türkiye resmî tatilleri ---
HOLIDAYS_2026 = [
    ("2026-01-01", "Yılbaşı"),
    ("2026-03-19", "Ramazan Bayramı Arifesi"),
    ("2026-03-20", "Ramazan Bayramı 1. Gün"),
    ("2026-03-21", "Ramazan Bayramı 2. Gün"),
    ("2026-03-22", "Ramazan Bayramı 3. Gün"),
    ("2026-04-23", "Ulusal Egemenlik ve Çocuk Bayramı"),
    ("2026-05-01", "Emek ve Dayanışma Günü"),
    ("2026-05-19", "Atatürk'ü Anma, Gençlik ve Spor Bayramı"),
    ("2026-05-26", "Kurban Bayramı Arifesi"),
    ("2026-05-27", "Kurban Bayramı 1. Gün"),
    ("2026-05-28", "Kurban Bayramı 2. Gün"),
    ("2026-05-29", "Kurban Bayramı 3. Gün"),
    ("2026-05-30", "Kurban Bayramı 4. Gün"),
    ("2026-07-15", "Demokrasi ve Millî Birlik Günü"),
    ("2026-08-30", "Zafer Bayramı"),
    ("2026-10-29", "Cumhuriyet Bayramı"),
]
HOLIDAY_APPLIES_AS = "sunday"

# line-schedule dayParameterValueId
DAY_TO_SERVICE = {
    222: "weekday",
    223: "saturday",
    224: "sunday",
}
SERVICE_SHORT = {"weekday": "wd", "saturday": "sat", "sunday": "sun"}

# routeTypeId gözlemi (M1): 220=gidiş, 221=dönüş — diğer hatlarda doğrulanmadı
ROUTE_TYPE_TO_DIR = {
    220: 0,
    221: 1,
}

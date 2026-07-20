"""TransitJSON ETL — sabitler ve yapılandırma (Bursa / Burulaş)."""
from __future__ import annotations

# --- Burulaş (Bursa Kart) statik API ---
BASE_URL = "https://bursakartapi.abys-web.com/api/static"

REQUEST_HEADERS = {
    "Host": "bursakartapi.abys-web.com",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Referer": "https://www.bursakart.com.tr/",
    "Origin": "https://www.bursakart.com.tr",
    "Connection": "keep-alive",
}

# --- Valhalla (shape / harita eşleme) ---
VALHALLA_URL = "https://valhala.bykemalh.me"
VALHALLA_COSTING = "bus"
VALHALLA_SHAPE_MATCH = "map_snap"
# Valhalla trace_route precision (encoded polyline). 6 döndürür.
VALHALLA_PRECISION = 6
# Ham fallback encode precision (Valhalla başarısız olursa).
RAW_PRECISION = 5

# Valhalla harita eşlemesinin uygulanacağı araç türleri.
# Tram/metro yol ağına oturmadığı için ham koordinat kullanılır.
MAP_SNAP_VEHICLE_TYPES = {"bus"}

# --- İstek davranışı ---
REQUEST_TIMEOUT = 30      # saniye
MAX_RETRIES = 3
RETRY_BACKOFF = 1.5       # saniye (üstel)
SLEEP_BETWEEN = 0.15      # istekler arası nezaket beklemesi

# --- Sabit varlıklar (API'de yok, elle girilir) ---
COUNTRY = {
    "country_id": "TR",
    "name": "Türkiye",
    "source": "manual",
}

CITY = {
    "city_id": "BUR",
    "slug": "bursa",
    "country_id": "TR",
    "name": "Bursa",
    "timezone": "Europe/Istanbul",
    "default_zoom": 12,
    "source": "manual",
    # center + bounds duraklardan hesaplanır; hesaplanamazsa bu fallback kullanılır.
    "center_fallback": {"lat": 40.1885, "lon": 29.0610},
}

AGENCY = {
    "agency_id": "burulas",
    "city_id": "BUR",
    "name": "BURULAŞ",
    "website": "https://www.bursakart.com.tr",
    "source": "manual",
}

# Bu şehirdeki tüm hatlar bu agency'ye bağlanır.
DEFAULT_AGENCY_ID = "burulas"
DEFAULT_STOP_MODE = "fixed"

# --- Kendi ID şeması (Burulaş API id'lerinden bağımsız) ---
# API'nin ham hatNo/stopId değerleri ÇIKTIDA kullanılmaz; kendi id'lerimiz üretilir.
# API id <-> bizim id eşlemesi _id_map.json'a yazılır.
CITY_ID = "BUR"
ROUTE_ID_PREFIX = "BUR"      # hat  -> BUR_0001
ROUTE_ID_WIDTH = 4
STOP_ID_PREFIX = "BUR_ST"    # durak -> BUR_ST_00001
STOP_ID_WIDTH = 5

SOURCE_API = "api-burulas"
SOURCE_GENERATED = "api-burulas"

# --- 2026 Türkiye resmî tatilleri ---
# Karar: tüm tatiller (arifeler dahil) Pazar (sunday) programıyla çalışır.
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

# --- Yön eşlemesi ---
# API: G = Gidiş, D = Dönüş, R = Ring (tek yön döngü)
DIRECTION_G = 0
DIRECTION_D = 1
DIRECTION_R = 0  # ring = tek yön, direction 0
API_DIR_TO_INT = {"G": DIRECTION_G, "D": DIRECTION_D, "R": DIRECTION_R}

# schedulebystop gerçek yanıtı düz listedir: {routeDay, stopTime}
# routeDay: 1=Pzt ... 5=Cum, 6=Cmt, 7=Paz
# 1-5 tek bir "weekday" programında birleştirilir (aynı saatler tekilleştirilir).
ROUTEDAY_TO_SERVICE = {
    1: "weekday",
    2: "weekday",
    3: "weekday",
    4: "weekday",
    5: "weekday",
    6: "saturday",
    7: "sunday",
}
SERVICE_SHORT = {"weekday": "wd", "saturday": "sat", "sunday": "sun"}

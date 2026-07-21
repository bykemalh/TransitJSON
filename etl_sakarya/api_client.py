"""SBB (Sakarya) public API istemcisi — GET + disk cache + retry."""
from __future__ import annotations

import hashlib
import json
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

from . import config

CACHE_DIR = Path(__file__).parent / "cache"


def tr_day_to_api_date(day: date) -> str:
    """TR yerel gün 00:00 → API date (UTC ISO). Örn. 2026-06-21 → 2026-06-20T21:00:00.000Z"""
    # TR = UTC+3 → yerel gece yarısı = önceki gün 21:00 UTC
    local_midnight = datetime(day.year, day.month, day.day, 0, 0, 0)
    utc_dt = local_midnight - timedelta(hours=3)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


class SakaryaClient:
    def __init__(self, cache: bool = True, sleep_between: float | None = None):
        self.session = requests.Session()
        self.session.headers.update(config.REQUEST_HEADERS)
        self.cache = cache
        self.sleep_between = (
            config.SLEEP_BETWEEN if sleep_between is None else sleep_between
        )
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, key: str) -> Path:
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
        safe = key.split("?")[0].strip("/").replace("/", "_")
        return CACHE_DIR / f"{safe}_{digest}.json"

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        params = params or {}
        # cache key: path + sorted params
        param_key = json.dumps(params, sort_keys=True, ensure_ascii=False)
        cache_key = f"{path}?{param_key}"
        cache_path = self._cache_path(cache_key)

        if self.cache and cache_path.exists():
            with cache_path.open(encoding="utf-8") as f:
                return json.load(f)

        url = f"{config.BASE_URL}{path}"
        last_err: Exception | None = None
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                resp = self.session.get(
                    url, params=params, timeout=config.REQUEST_TIMEOUT
                )
                resp.raise_for_status()
                data = resp.json()
                if self.cache:
                    with cache_path.open("w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False)
                if self.sleep_between:
                    time.sleep(self.sleep_between)
                return data
            except (requests.RequestException, ValueError) as exc:
                last_err = exc
                if attempt < config.MAX_RETRIES:
                    time.sleep(config.RETRY_BACKOFF ** attempt)
        raise RuntimeError(f"GET {path} {params} başarısız: {last_err}")

    def route_and_busstops(self, line_id: int) -> dict:
        """Hat güzergahı + duraklar (her yön)."""
        data = self._get(f"/Ulasim/route-and-busstops/{int(line_id)}")
        return data if isinstance(data, dict) else {}

    def line_schedule(self, line_id: int, day: date | None = None) -> dict:
        """Hat sefer tarifesi. day yoksa bugünün TR günü kullanılır."""
        if day is None:
            # Europe/Istanbul ≈ UTC+3
            now_utc = datetime.now(timezone.utc)
            day = (now_utc + timedelta(hours=3)).date()
        api_date = tr_day_to_api_date(day)
        data = self._get(
            "/Ulasim/line-schedule",
            {"date": api_date, "lineId": int(line_id)},
        )
        return data if isinstance(data, dict) else {}

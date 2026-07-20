"""Burulaş (Bursa Kart) statik API istemcisi — disk cache + retry."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import requests

from . import config

CACHE_DIR = Path(__file__).parent / "cache"


class BurulasClient:
    def __init__(self, cache: bool = True, sleep_between: float | None = None):
        self.session = requests.Session()
        self.session.headers.update(config.REQUEST_HEADERS)
        self.cache = cache
        self.sleep_between = (
            config.SLEEP_BETWEEN if sleep_between is None else sleep_between
        )
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # ---- cache yardımcıları ----
    def _cache_path(self, endpoint: str, body: dict) -> Path:
        key = json.dumps(body, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha1(f"{endpoint}:{key}".encode("utf-8")).hexdigest()[:16]
        safe = endpoint.strip("/").replace("/", "_")
        return CACHE_DIR / f"{safe}_{digest}.json"

    # ---- düşük seviye POST ----
    def _post(self, endpoint: str, body: dict) -> dict[str, Any]:
        cache_path = self._cache_path(endpoint, body)
        if self.cache and cache_path.exists():
            with cache_path.open(encoding="utf-8") as f:
                return json.load(f)

        url = f"{config.BASE_URL}{endpoint}"
        last_err: Exception | None = None
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                resp = self.session.post(
                    url, json=body, timeout=config.REQUEST_TIMEOUT
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
        raise RuntimeError(f"{endpoint} {body} başarısız: {last_err}")

    @staticmethod
    def _result(data: dict) -> Any:
        if data.get("statusCode") != 200:
            return None
        return data.get("result")

    # ---- endpoint sarmalayıcılar ----
    def routestat(self, hat_no: int) -> list[dict]:
        """Hattın durak listesi (G/D/R, sequence, lat/lon)."""
        data = self._post("/routestat", {"routeCode": int(hat_no)})
        return self._result(data) or []

    def routecoordinate(self, hat_no: int) -> list[dict]:
        """Hattın güzergah koordinatları (G/D/R)."""
        data = self._post("/routecoordinate", {"keyword": str(hat_no)})
        return self._result(data) or []

    def schedulebystop(self, hat_no: int, direction: str, stop_seq: int = 0) -> list[dict]:
        """Bir hat + yön + durak için sefer saatleri.

        Gerçek yanıt düz listedir: [{routeId, routeCode, routeDay, stopTime}, ...]
        (dokümandaki gruplu yapı eskidir).
        """
        body = {
            "direction": direction,
            "routeId": int(hat_no),
            "stopSequenceNo": int(stop_seq),
            "weekday": 0,
        }
        data = self._post("/schedulebystop", body)
        result = self._result(data)
        return result if isinstance(result, list) else []

"""Burulaş API + bursa.json -> TransitJSON koleksiyonları."""
from __future__ import annotations

from typing import Any

from . import config, shape_encode
from .api_client import BurulasClient


def _f(v: Any) -> float | None:
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def _norm_time(t: str) -> str | None:
    """'06:40' -> '06:40:00'. Zaten HH:MM:SS ise dokunmaz."""
    if not t:
        return None
    parts = t.strip().split(":")
    if len(parts) == 2:
        return f"{int(parts[0]):02d}:{parts[1]}:00"
    if len(parts) == 3:
        return f"{int(parts[0]):02d}:{parts[1]}:{parts[2]}"
    return None


class TransitBuilder:
    def __init__(self, client: BurulasClient, now_iso: str):
        self.client = client
        self.now = now_iso

        self.stops: dict[str, dict] = {}          # stop_id -> stop
        self.routes: list[dict] = []
        self.route_stops: list[dict] = []
        self.shapes: list[dict] = []
        self.trips: list[dict] = []
        self.stop_times: list[dict] = []
        self._trip_ids: set[str] = set()

        # API id -> bizim id kayıtları (izlenebilirlik + tekilleştirme)
        self._route_id_map: dict[int, str] = {}   # hatNo -> route_id
        self._stop_id_map: dict[str, str] = {}    # api stopId (str) -> stop_id
        self._route_seq = 0
        self._stop_seq = 0

    # ---------------------------------------------------------------
    def _route_id(self, hat_no: int) -> str:
        """API hatNo için kendi route_id'mizi üretir/döner (BUR_0001)."""
        rid = self._route_id_map.get(hat_no)
        if rid is None:
            self._route_seq += 1
            rid = f"{config.ROUTE_ID_PREFIX}_{self._route_seq:0{config.ROUTE_ID_WIDTH}d}"
            self._route_id_map[hat_no] = rid
        return rid

    def _stop_id(self, api_stop_id) -> str:
        """API stopId için kendi stop_id'mizi üretir/döner (BUR_ST_00001).

        Aynı durak (aynı API stopId) birden çok hatta geçse bile TEK id alır.
        """
        key = str(api_stop_id)
        sid = self._stop_id_map.get(key)
        if sid is None:
            self._stop_seq += 1
            sid = f"{config.STOP_ID_PREFIX}_{self._stop_seq:0{config.STOP_ID_WIDTH}d}"
            self._stop_id_map[key] = sid
        return sid

    def id_map(self) -> dict:
        return {
            "routes": {str(k): v for k, v in self._route_id_map.items()},
            "stops": dict(self._stop_id_map),
        }

    # ---------------------------------------------------------------
    def build_route(self, raw: dict) -> None:
        """bursa.json'daki tek bir hat kaydını tüm koleksiyonlara işler."""
        hat_no = raw["hatNo"]
        vehicle_type = raw.get("vehicleType", "bus")

        # 1) Duraklar + yönler (route_pattern buradan çıkar)
        # API: G=gidiş, D=dönüş, R=ring
        stat = self.client.routestat(hat_no)
        stops_by_dir = self._group_routestat(stat)
        raw_dirs = set(stops_by_dir.keys())
        if not raw_dirs:
            return  # duraksız hat -> atla (id tüketmeden)

        # Ring (R): tek yön loop. G+D: round_trip. Tek G veya tek D: loop.
        # Edge case D+R: ring kabul edilir, sadece R kullanılır.
        if "R" in raw_dirs and "G" not in raw_dirs:
            directions = ["R"]
            route_pattern = "loop"
        elif "G" in raw_dirs and "D" in raw_dirs:
            directions = ["G", "D"]
            route_pattern = "round_trip"
        else:
            directions = sorted(raw_dirs)
            route_pattern = "loop"

        # route_id yalnızca durağı olan hatlara verilir (id_map temiz kalsın)
        route_id = self._route_id(hat_no)

        self.routes.append({
            "route_id": route_id,
            "agency_id": config.DEFAULT_AGENCY_ID,
            "name": raw.get("aciklama") or raw.get("kod") or route_id,
            "code": raw.get("kod"),
            "color": raw.get("color"),
            "vehicle_type": vehicle_type,
            "route_pattern": route_pattern,
            "stop_mode": config.DEFAULT_STOP_MODE,
            "source": config.SOURCE_API,
            "updated_at": self.now,
        })

        first_stop_by_dir: dict[str, str] = {}
        for api_dir, stop_rows in stops_by_dir.items():
            direction = config.API_DIR_TO_INT[api_dir]
            first_stop_by_dir[api_dir] = self._emit_route_stops(
                route_id, direction, stop_rows
            )

        # 2) Güzergah geometrisi (shape)
        self._build_shapes(route_id, hat_no, directions)

        # 3) Seferler + saatler
        for api_dir in directions:
            first_stop_id = first_stop_by_dir.get(api_dir)
            if not first_stop_id:
                continue
            self._build_trips(route_id, hat_no, api_dir, first_stop_id)

    # ---------------------------------------------------------------
    def _group_routestat(self, rows: list[dict]) -> dict[str, list[dict]]:
        by_dir: dict[str, list[dict]] = {}
        for r in rows:
            d = r.get("direction")
            if d not in config.API_DIR_TO_INT:
                continue
            lat, lon = _f(r.get("latitude")), _f(r.get("longitude"))
            if lat is None or lon is None:
                continue
            by_dir.setdefault(d, []).append({
                "stop_id_raw": r.get("stopId"),
                "name": (r.get("stopName") or "").strip(),
                "lat": lat,
                "lon": lon,
                "seq": r.get("sequence", 0),
            })
        for d in by_dir:
            by_dir[d].sort(key=lambda x: (x["seq"],))
        return by_dir

    def _emit_route_stops(
        self, route_id: str, direction: int, rows: list[dict]
    ) -> str | None:
        """route_stops üretir, global stops'a ekler, ilk durak stop_id döner."""
        first_stop_id = None
        n = len(rows)
        for idx, row in enumerate(rows):
            stop_id = self._stop_id(row["stop_id_raw"])
            # global stop dedup
            if stop_id not in self.stops:
                self.stops[stop_id] = {
                    "stop_id": stop_id,
                    "city_id": config.CITY_ID,
                    "name": row["name"],
                    "lat": row["lat"],
                    "lon": row["lon"],
                    "source": config.SOURCE_API,
                    "updated_at": self.now,
                }
            seq = idx + 1
            rs = {
                "route_id": route_id,
                "direction": direction,
                "stop_id": stop_id,
                "sequence": seq,
                "updated_at": self.now,
                "source": config.SOURCE_API,
            }
            if idx == 0:
                rs["is_first_stop"] = True
                first_stop_id = stop_id
            if idx == n - 1:
                rs["is_last_stop"] = True
            self.route_stops.append(rs)
        return first_stop_id

    # ---------------------------------------------------------------
    def _build_shapes(
        self, route_id: str, hat_no: int, directions: list[str]
    ) -> None:
        coords = self.client.routecoordinate(hat_no)
        pts_by_dir: dict[str, list[tuple[float, float]]] = {}
        for c in coords:
            d = c.get("routeDirection")
            if d not in config.API_DIR_TO_INT:
                continue
            lat = _f(c.get("latitude"))
            lon = _f(c.get("logitude"))  # API'de 'logitude' yazım hatasıyla gelir
            if lat is None or lon is None:
                continue
            pts_by_dir.setdefault(d, []).append((c.get("sequence", 0), lat, lon))

        for api_dir in directions:
            raw_pts = pts_by_dir.get(api_dir)
            if not raw_pts:
                continue
            raw_pts.sort(key=lambda x: x[0])
            points = [(lat, lon) for _, lat, lon in raw_pts]
            shape = shape_encode.build_shape(points)
            if not shape:
                continue
            direction = config.API_DIR_TO_INT[api_dir]
            self.shapes.append({
                "shape_id": f"{route_id}_SH_{direction}",
                "route_id": route_id,
                "direction": direction,
                "coordinates": shape["coordinates"],
                "source": config.SOURCE_API,
                "updated_at": self.now,
            })

    # ---------------------------------------------------------------
    def _build_trips(
        self, route_id: str, hat_no: int, api_dir: str, first_stop_id: str
    ) -> None:
        direction = config.API_DIR_TO_INT[api_dir]
        rows = self.client.schedulebystop(hat_no, api_dir, stop_seq=0)
        if not rows:
            return

        # routeDay -> service_type; aynı service_type içindeki saatler tekilleştirilir
        # (Pzt-Cum çoğu zaman aynı, tek "weekday" programında birleştirilir).
        by_service: dict[str, set[str]] = {}
        for r in rows:
            service_type = config.ROUTEDAY_TO_SERVICE.get(r.get("routeDay"))
            dep = _norm_time(r.get("stopTime"))
            if not service_type or not dep:
                continue
            by_service.setdefault(service_type, set()).add(dep)

        for service_type, times in by_service.items():
            short = config.SERVICE_SHORT[service_type]
            for dep in sorted(times):
                hhmm = dep[:5].replace(":", "")
                trip_id = f"{route_id}_{direction}_{short}_{hhmm}"
                if trip_id in self._trip_ids:
                    suffix = 1
                    while f"{trip_id}-{suffix}" in self._trip_ids:
                        suffix += 1
                    trip_id = f"{trip_id}-{suffix}"
                self._trip_ids.add(trip_id)

                self.trips.append({
                    "trip_id": trip_id,
                    "route_id": route_id,
                    "direction": direction,
                    "service_type": service_type,
                    "source": config.SOURCE_GENERATED,
                    "updated_at": self.now,
                })
                self.stop_times.append({
                    "trip_id": trip_id,
                    "stop_id": first_stop_id,
                    "sequence": 1,
                    "departure_time": dep,
                    "source": config.SOURCE_GENERATED,
                    "updated_at": self.now,
                })

    # ---------------------------------------------------------------
    def country(self) -> list[dict]:
        return [{**config.COUNTRY, "updated_at": self.now}]

    def city(self) -> list[dict]:
        c = dict(config.CITY)
        fallback = c.pop("center_fallback")
        lats = [s["lat"] for s in self.stops.values()]
        lons = [s["lon"] for s in self.stops.values()]
        if lats and lons:
            center = {
                "lat": round((min(lats) + max(lats)) / 2, 6),
                "lon": round((min(lons) + max(lons)) / 2, 6),
            }
            bounds = {
                "north": round(max(lats), 6),
                "south": round(min(lats), 6),
                "east": round(max(lons), 6),
                "west": round(min(lons), 6),
            }
        else:
            center, bounds = fallback, None
        c["center"] = center
        if bounds:
            c["bounds"] = bounds
        c["updated_at"] = self.now
        return [c]

    def agency(self) -> list[dict]:
        return [{**config.AGENCY, "updated_at": self.now}]

    def holidays(self) -> list[dict]:
        return [
            {
                "date": date,
                "country_id": config.COUNTRY["country_id"],
                "name": name,
                "applies_as": config.HOLIDAY_APPLIES_AS,
                "source": "manual",
                "updated_at": self.now,
            }
            for date, name in config.HOLIDAYS_2026
        ]

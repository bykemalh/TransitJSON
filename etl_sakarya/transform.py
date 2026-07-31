"""sakarya.json + SBB API -> TransitJSON koleksiyonları."""
from __future__ import annotations

import re
from typing import Any

from . import config, shape_encode
from .api_client import SakaryaClient


def _f(v: Any) -> float | None:
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def _norm_time(t: str) -> str | None:
    """'06:40' / '06:40:00' -> 'HH:MM:SS'."""
    if not t:
        return None
    parts = t.strip().split(":")
    if len(parts) == 2:
        return f"{int(parts[0]):02d}:{parts[1]}:00"
    if len(parts) == 3:
        return f"{int(parts[0]):02d}:{parts[1]}:{parts[2]}"
    return None


def _vehicle_type(line_number: str | None, name: str | None) -> str:
    code = (line_number or "").strip().upper()
    nm = (name or "").strip().upper()
    if code == "A1" or "ADARAY" in nm:
        return "metro"
    if code == "M1" or re.fullmatch(r"M\d+", code):
        return "metro"
    return "bus"


def _direction_for_route(route: dict, index: int) -> int:
    rt = route.get("routeTypeId")
    if rt in config.ROUTE_TYPE_TO_DIR:
        return config.ROUTE_TYPE_TO_DIR[rt]
    return 0 if index == 0 else 1


class TransitBuilder:
    def __init__(self, client: SakaryaClient, now_iso: str):
        self.client = client
        self.now = now_iso

        self.stops: dict[str, dict] = {}
        self.routes: list[dict] = []
        self.route_stops: list[dict] = []
        self.shapes: list[dict] = []
        self.trips: list[dict] = []
        self.stop_times: list[dict] = []
        self.fares: dict[str, dict] = {}
        self._trip_ids: set[str] = set()

        self._route_id_map: dict[int, str] = {}
        self._stop_id_map: dict[str, str] = {}
        self._api_route_dir: dict[int, int] = {}
        self._route_seq = 0
        self._stop_seq = 0

    def _route_id(self, line_id: int) -> str:
        rid = self._route_id_map.get(line_id)
        if rid is None:
            self._route_seq += 1
            rid = (
                f"{config.ROUTE_ID_PREFIX}_"
                f"{self._route_seq:0{config.ROUTE_ID_WIDTH}d}"
            )
            self._route_id_map[line_id] = rid
        return rid

    def _stop_id(self, api_stop_id) -> str:
        key = str(api_stop_id)
        sid = self._stop_id_map.get(key)
        if sid is None:
            self._stop_seq += 1
            sid = (
                f"{config.STOP_ID_PREFIX}_"
                f"{self._stop_seq:0{config.STOP_ID_WIDTH}d}"
            )
            self._stop_id_map[key] = sid
        return sid

    def _build_fares(self, route_id: str, line_id: int, name: str) -> str | None:
        fare_data = self.client.line_fare(line_id)
        if not fare_data:
            return None

        tariff_map = {}
        for t in fare_data.get("tariffList") or []:
            fare_type_id = t.get("lineFareTypeId")
            type_name = (t.get("typeName") or "").strip()
            if fare_type_id:
                tariff_map[fare_type_id] = type_name

        groups = fare_data.get("groups") or []
        has_multiple = fare_data.get("hasMultipleRoute", False) or fare_data.get("hasMultipleTariffNum", False)

        primary_fare_id = None

        if not has_multiple and groups and groups[0].get("routes"):
            single_route = groups[0]["routes"][0]
            tariffs = single_route.get("tariffs") or []

            for item in tariffs:
                fare_type_id = item.get("lineFareTypeId")
                try:
                    price_val = float(item.get("finalFare", 0))
                except (TypeError, ValueError):
                    price_val = 0.0
                type_name = tariff_map.get(fare_type_id, "Tam")

                type_upper = type_name.upper()
                if "TAM" in type_upper:
                    fare_key = "tam"
                    t_name = f"{name} - Tam Bilet"
                elif "ÖĞRENCİ" in type_upper or "OGRENCI" in type_upper:
                    fare_key = "ogrenci"
                    t_name = f"{name} - Öğrenci Bileti"
                elif "ÖĞRETMEN" in type_upper or "OGRETMEN" in type_upper:
                    fare_key = "ogretmen"
                    t_name = f"{name} - Öğretmen Bileti"
                elif "60" in type_upper or "65" in type_upper:
                    fare_key = "60_65"
                    t_name = f"{name} - 60-65 Yaş Bileti"
                else:
                    fare_key = type_name.lower().replace(" ", "_")
                    t_name = f"{name} - {type_name}"

                fare_id = f"{route_id}_FARE_{fare_key.upper()}"
                if fare_key == "tam" or primary_fare_id is None:
                    primary_fare_id = fare_id

                if fare_id not in self.fares:
                    self.fares[fare_id] = {
                        "fare_id": fare_id,
                        "agency_id": config.DEFAULT_AGENCY_ID,
                        "name": t_name,
                        "name_en": config.FARE_NAME_EN.get(fare_key, t_name),
                        "fare_type": "flat",
                        "price": price_val,
                        "currency": "TRY",
                        "payment_methods": ["smart_card"],
                        "updated_at": self.now,
                        "source": config.SOURCE_API,
                    }
        elif groups:
            # Çok rotalı (bölge/mesafe bazlı) hatlar: fare_rules üretilmez;
            # her tarife tipi için bulunan ilk fiyat tek flat ücret olarak yazılır.
            prices_by_key: dict[str, tuple[str, float]] = {}
            for group in groups:
                for r in group.get("routes") or []:
                    for tariff in r.get("tariffs") or []:
                        fare_type_id = tariff.get("lineFareTypeId")
                        try:
                            price_val = float(tariff.get("finalFare", 0))
                        except (TypeError, ValueError):
                            price_val = 0.0
                        type_name = tariff_map.get(fare_type_id, "Tam")

                        type_upper = type_name.upper()
                        if "TAM" in type_upper:
                            fare_key = "tam"
                            t_name = f"{name} - Tam Bilet"
                        elif "ÖĞRENCİ" in type_upper or "OGRENCI" in type_upper:
                            fare_key = "ogrenci"
                            t_name = f"{name} - Öğrenci Bileti"
                        elif "ÖĞRETMEN" in type_upper or "OGRETMEN" in type_upper:
                            fare_key = "ogretmen"
                            t_name = f"{name} - Öğretmen Bileti"
                        elif "60" in type_upper or "65" in type_upper:
                            fare_key = "60_65"
                            t_name = f"{name} - 60-65 Yaş Bileti"
                        else:
                            fare_key = type_name.lower().replace(" ", "_")
                            t_name = f"{name} - {type_name}"
                        prices_by_key.setdefault(fare_key, (t_name, price_val))

            for fare_key, (t_name, price_val) in prices_by_key.items():
                fare_id = f"{route_id}_FARE_{fare_key.upper()}"
                if fare_key == "tam" or primary_fare_id is None:
                    primary_fare_id = fare_id

                if fare_id not in self.fares:
                    self.fares[fare_id] = {
                        "fare_id": fare_id,
                        "agency_id": config.DEFAULT_AGENCY_ID,
                        "name": t_name,
                        "name_en": config.FARE_NAME_EN.get(fare_key, t_name),
                        "fare_type": "flat",
                        "price": price_val,
                        "currency": "TRY",
                        "payment_methods": ["smart_card"],
                        "updated_at": self.now,
                        "source": config.SOURCE_API,
                    }

        return primary_fare_id

    def id_map(self) -> dict:
        return {
            "routes": {str(k): v for k, v in self._route_id_map.items()},
            "stops": dict(self._stop_id_map),
            "api_route_direction": {
                str(k): v for k, v in self._api_route_dir.items()
            },
        }

    def build_route(self, raw: dict) -> None:
        line_id = int(raw["id"])
        detail = self.client.route_and_busstops(line_id)
        api_routes = detail.get("routes") or []
        if not api_routes:
            return

        # (direction, api_route) — direction çakışmalarında index fallback
        planned: list[tuple[int, dict]] = []
        used_dirs: set[int] = set()
        for idx, api_route in enumerate(api_routes):
            direction = _direction_for_route(api_route, idx)
            if direction in used_dirs:
                direction = 1 if 0 in used_dirs else 0
            if direction in used_dirs:
                continue
            used_dirs.add(direction)
            planned.append((direction, api_route))

        if not planned:
            return

        route_pattern = "round_trip" if len(planned) >= 2 else "loop"
        route_id = self._route_id(line_id)
        code = raw.get("lineNumber") or detail.get("lineNumber")
        name = (
            raw.get("name")
            or detail.get("lineName")
            or code
            or route_id
        )
        color = raw.get("busTypeColor")
        vehicle_type = _vehicle_type(code, name)

        fare_id = self._build_fares(route_id, line_id, name)

        self.routes.append({
            "route_id": route_id,
            "agency_id": config.DEFAULT_AGENCY_ID,
            "name": name,
            "code": code,
            "color": color,
            "vehicle_type": vehicle_type,
            "fare_id": fare_id,
            "route_pattern": route_pattern,
            "stop_mode": config.DEFAULT_STOP_MODE,
            "source": config.SOURCE_API,
            "updated_at": self.now,
        })


        first_stop_by_dir: dict[int, str] = {}
        for direction, api_route in planned:
            api_route_id = api_route.get("routeId")
            if api_route_id is not None:
                self._api_route_dir[int(api_route_id)] = direction

            bus_stops = sorted(
                api_route.get("busStops") or [],
                key=lambda s: s.get("order") or 0,
            )
            rows = []
            for s in bus_stops:
                geom = s.get("busStopGeometry") or {}
                coords = geom.get("coordinates") or []
                if len(coords) < 2:
                    continue
                lon, lat = _f(coords[0]), _f(coords[1])
                if lat is None or lon is None:
                    continue
                rows.append({
                    "stop_id_raw": s.get("id"),
                    "name": (s.get("name") or "").strip(),
                    "lat": lat,
                    "lon": lon,
                })
            if not rows:
                continue

            first = self._emit_route_stops(route_id, direction, rows)
            if first:
                first_stop_by_dir[direction] = first

            self._emit_shape(route_id, direction, api_route)

        self._build_trips(route_id, line_id, first_stop_by_dir)

    def _emit_route_stops(
        self, route_id: str, direction: int, rows: list[dict]
    ) -> str | None:
        first_stop_id = None
        n = len(rows)
        for idx, row in enumerate(rows):
            stop_id = self._stop_id(row["stop_id_raw"])
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
            rs: dict[str, Any] = {
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

    def _emit_shape(
        self, route_id: str, direction: int, api_route: dict
    ) -> None:
        geom = api_route.get("routeGeometry") or {}
        coords = geom.get("coordinates") or []
        points = shape_encode.multilinestring_to_latlon(coords)
        shape = shape_encode.build_shape(points)
        if not shape:
            return
        self.shapes.append({
            "shape_id": f"{route_id}_SH_{direction}",
            "route_id": route_id,
            "direction": direction,
            "coordinates": shape["coordinates"],
            "source": config.SOURCE_API,
            "updated_at": self.now,
        })

    def _build_trips(
        self,
        route_id: str,
        line_id: int,
        first_stop_by_dir: dict[int, str],
    ) -> None:
        sched = self.client.line_schedule(line_id)
        for block in sched.get("schedules") or []:
            api_route_id = block.get("routeId")
            direction = self._api_route_dir.get(int(api_route_id)) if api_route_id is not None else None
            if direction is None:
                # schedule routeId eşleşmezse atla
                continue
            first_stop_id = first_stop_by_dir.get(direction)
            if not first_stop_id:
                continue

            by_service: dict[str, set[str]] = {}
            for row in block.get("routeDetail") or []:
                days = config.DAY_TO_SERVICE.get(row.get("dayParameterValueId"))
                dep = _norm_time(row.get("startTime") or "")
                if not days or not dep:
                    continue
                for service in days:
                    by_service.setdefault(service, set()).add(dep)

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

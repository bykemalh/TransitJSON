"""Valhalla harita eşleme yardımcısı + polyline fallback.

Ham koordinat listesini (yol üzerinde) encoded polyline'a çevirir.
- bus: Valhalla /trace_route (map_snap) ile yola oturtulur (precision 6).
- tram/metro veya Valhalla hatası: ham koordinatlar doğrudan encode edilir (precision 5).
"""
from __future__ import annotations

from typing import Any

import polyline
import requests

from . import config


def _encode_raw(points: list[tuple[float, float]]) -> tuple[str, int, int]:
    """Ham (lat, lon) noktalarını precision 5 ile encode eder."""
    encoded = polyline.encode(points, config.RAW_PRECISION)
    return encoded, config.RAW_PRECISION, len(points)


def _merge_legs(legs: list[dict]) -> list[tuple[float, float]]:
    """trace_route leg'lerinin encoded shape'lerini decode edip birleştirir."""
    coords: list[tuple[float, float]] = []
    for leg in legs:
        shp = leg.get("shape")
        if not shp:
            continue
        decoded = polyline.decode(shp, config.VALHALLA_PRECISION)
        if coords and decoded and coords[-1] == decoded[0]:
            decoded = decoded[1:]
        coords.extend(decoded)
    return coords


def build_shape(
    points: list[tuple[float, float]],
    vehicle_type: str,
    session: requests.Session | None = None,
) -> dict[str, Any] | None:
    """points: [(lat, lon), ...] sıralı güzergah noktaları.

    Döner: {"shape_encoded", "precision", "point_count", "snapped": bool} veya None.
    """
    points = [p for p in points if p is not None]
    if len(points) < 2:
        return None

    use_snap = vehicle_type in config.MAP_SNAP_VEHICLE_TYPES
    if use_snap:
        snapped = _try_valhalla(points, session)
        if snapped is not None:
            return snapped

    encoded, precision, count = _encode_raw(points)
    return {
        "shape_encoded": encoded,
        "precision": precision,
        "point_count": count,
        "snapped": False,
    }


def _try_valhalla(
    points: list[tuple[float, float]], session: requests.Session | None
) -> dict[str, Any] | None:
    body = {
        "shape": [{"lat": lat, "lon": lon} for lat, lon in points],
        "costing": config.VALHALLA_COSTING,
        "shape_match": config.VALHALLA_SHAPE_MATCH,
    }
    http = session or requests
    try:
        resp = http.post(
            f"{config.VALHALLA_URL}/trace_route",
            json=body,
            timeout=config.REQUEST_TIMEOUT,
        )
        data = resp.json()
    except (requests.RequestException, ValueError):
        return None

    if data.get("error_code") or "trip" not in data:
        return None

    legs = data["trip"].get("legs", [])
    coords = _merge_legs(legs)
    if len(coords) < 2:
        return None

    encoded = polyline.encode(coords, config.VALHALLA_PRECISION)
    return {
        "shape_encoded": encoded,
        "precision": config.VALHALLA_PRECISION,
        "point_count": len(coords),
        "snapped": True,
    }

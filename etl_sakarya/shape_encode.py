"""Ham güzergah koordinatlarını TransitJSON shape formatına çevirir."""
from __future__ import annotations

from typing import Any


def build_shape(points: list[tuple[float, float]]) -> dict[str, Any] | None:
    """points: [(lat, lon), ...] sıralı güzergah noktaları.

    Döner: {"coordinates": [{"lat", "lon"}, ...]} veya None.
    Encoded polyline kullanılmaz.
    """
    points = [p for p in points if p is not None]
    if len(points) < 2:
        return None

    return {
        "coordinates": [{"lat": lat, "lon": lon} for lat, lon in points],
    }


def multilinestring_to_latlon(
    coordinates: list,
) -> list[tuple[float, float]]:
    """GeoJSON MultiLineString coordinates [lng,lat][][] → [(lat, lon), ...].

    Segmentler uç uca eklenir; tekrarlayan birleşim noktası atılır.
    """
    points: list[tuple[float, float]] = []
    if not coordinates:
        return points
    for line in coordinates:
        if not line:
            continue
        for pair in line:
            if not pair or len(pair) < 2:
                continue
            lon, lat = float(pair[0]), float(pair[1])
            pt = (lat, lon)
            if points and points[-1] == pt:
                continue
            points.append(pt)
    return points

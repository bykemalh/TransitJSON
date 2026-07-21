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

"""Ham güzergah koordinatlarını encoded polyline'a çevirir."""
from __future__ import annotations

from typing import Any

import polyline

from . import config


def build_shape(points: list[tuple[float, float]]) -> dict[str, Any] | None:
    """points: [(lat, lon), ...] sıralı güzergah noktaları.

    Döner: {"shape_encoded", "precision", "point_count"} veya None.
    """
    points = [p for p in points if p is not None]
    if len(points) < 2:
        return None

    encoded = polyline.encode(points, config.SHAPE_PRECISION)
    return {
        "shape_encoded": encoded,
        "precision": config.SHAPE_PRECISION,
        "point_count": len(points),
    }

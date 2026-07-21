#!/usr/bin/env python3
"""TransitJSON ETL — Sakarya / SBB.

sakarya.json + SBB public API -> JSON/Sakarya/ altına TransitJSON dosyaları.

Kullanım:
    py -m etl_sakarya.main                 # tüm hatlar
    py -m etl_sakarya.main --limit 5
    py -m etl_sakarya.main --no-cache
    py -m etl_sakarya.main --routes 50 51
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .api_client import SakaryaClient
from .transform import TransitBuilder

ROOT = Path(__file__).resolve().parent.parent
SAKARYA_JSON = ROOT / "sakarya.json"
OUTPUT_DIR = ROOT / "JSON" / "Sakarya"

COLLECTIONS = [
    ("countries", "countries.json"),
    ("cities", "cities.json"),
    ("agencies", "agencies.json"),
    ("routes", "routes.json"),
    ("stops", "stops.json"),
    ("route_stops", "route_stops.json"),
    ("shapes", "shapes.json"),
    ("trips", "trips.json"),
    ("stop_times", "stop_times.json"),
    ("holidays", "holidays.json"),
]


def load_routes() -> list[dict]:
    with SAKARYA_JSON.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("sakarya.json bir dizi olmalı")
    return data


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="TransitJSON ETL (Sakarya)")
    parser.add_argument("--limit", type=int, default=None, help="İlk N hat")
    parser.add_argument(
        "--routes", nargs="+", type=int, help="Sadece bu lineId'ler"
    )
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    routes = load_routes()

    if args.routes:
        wanted = set(args.routes)
        routes = [r for r in routes if int(r["id"]) in wanted]
    elif args.limit:
        routes = routes[: args.limit]

    client = SakaryaClient(cache=not args.no_cache)
    builder = TransitBuilder(client, now_iso)

    total = len(routes)
    print(f"{total} hat işlenecek -> {OUTPUT_DIR}")
    for i, raw in enumerate(routes, start=1):
        try:
            builder.build_route(raw)
        except Exception as exc:
            print(
                f"  [HATA] lineId={raw.get('id')} "
                f"kod={raw.get('lineNumber')}: {exc}"
            )
        if i % 25 == 0 or i == total:
            print(f"  {i}/{total} hat")

    bundle = {
        "countries": builder.country(),
        "cities": builder.city(),
        "agencies": builder.agency(),
        "routes": builder.routes,
        "stops": list(builder.stops.values()),
        "route_stops": builder.route_stops,
        "shapes": builder.shapes,
        "trips": builder.trips,
        "stop_times": builder.stop_times,
        "holidays": builder.holidays(),
    }

    for key, filename in COLLECTIONS:
        write_json(OUTPUT_DIR / filename, bundle[key])
    write_json(OUTPUT_DIR / "sakarya-transit.json", bundle)
    write_json(OUTPUT_DIR / "_id_map.json", builder.id_map())

    print("\nÖzet:")
    for key, _ in COLLECTIONS:
        print(f"  {key:12s}: {len(bundle[key])}")
    print(f"  shapes      : {len(builder.shapes)} (GeoJSON -> lat/lon coordinates)")


if __name__ == "__main__":
    main()

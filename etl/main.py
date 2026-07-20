#!/usr/bin/env python3
"""TransitJSON ETL — Bursa / Burulaş.

bursa.json + Burulaş statik API + Valhalla -> JSON/Bursa/ altına TransitJSON dosyaları.

Kullanım:
    python -m etl.main                 # tüm hatlar (414)
    python -m etl.main --limit 5       # ilk 5 hat (test)
    python -m etl.main --no-cache      # cache'i yok say
    python -m etl.main --routes 1107 1026
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .api_client import BurulasClient
from .transform import TransitBuilder

ROOT = Path(__file__).resolve().parent.parent
BURSA_JSON = ROOT / "bursa.json"
OUTPUT_DIR = ROOT / "JSON" / "Bursa"

# koleksiyon -> dosya adı (çoğul)
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
    with BURSA_JSON.open(encoding="utf-8") as f:
        return json.load(f)["routes"]


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="TransitJSON ETL (Bursa)")
    parser.add_argument("--limit", type=int, default=None, help="İlk N hat")
    parser.add_argument("--routes", nargs="+", type=int, help="Sadece bu hatNo'lar")
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    routes = load_routes()

    if args.routes:
        wanted = set(args.routes)
        routes = [r for r in routes if r["hatNo"] in wanted]
    elif args.limit:
        routes = routes[: args.limit]

    client = BurulasClient(cache=not args.no_cache)
    builder = TransitBuilder(client, now_iso)

    total = len(routes)
    print(f"{total} hat işlenecek -> {OUTPUT_DIR}")
    for i, raw in enumerate(routes, start=1):
        try:
            builder.build_route(raw)
        except Exception as exc:  # tek hat hata verse de devam
            print(f"  [HATA] hatNo={raw.get('hatNo')} kod={raw.get('kod')}: {exc}")
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
    write_json(OUTPUT_DIR / "bursa-transit.json", bundle)
    # API id <-> bizim id eşlemesi (şemaya dahil değil, izlenebilirlik için)
    write_json(OUTPUT_DIR / "_id_map.json", builder.id_map())

    print("\nÖzet:")
    for key, _ in COLLECTIONS:
        print(f"  {key:12s}: {len(bundle[key])}")
    snapped = sum(1 for s in builder.shapes if s["source"] == "api-burulas")
    print(f"  shapes(snap) : {snapped}/{len(builder.shapes)} Valhalla ile eşlendi")


if __name__ == "__main__":
    main()

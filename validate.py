"""TransitJSON JSON doğrulayıcı.

Kullanım:
    py validate.py JSON/Bursa
    py validate.py JSON/Sakarya

Verilen klasördeki koleksiyon JSON'larını schema/ altındaki ilgili şemaya
karşı doğrular ve hataları raporlar.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parent
SCHEMA_DIR = ROOT / "schema"

COLLECTION_TO_SCHEMA = {
    "countries.json": "country.schema.json",
    "cities.json": "city.schema.json",
    "agencies.json": "agency.schema.json",
    "routes.json": "route.schema.json",
    "stops.json": "stop.schema.json",
    "route_stops.json": "route_stop.schema.json",
    "shapes.json": "shape.schema.json",
    "trips.json": "trip.schema.json",
    "stop_times.json": "stop_time.schema.json",
    "holidays.json": "holiday.schema.json",
    "fares.json": "fare.schema.json",
}


def load_schema(name: str) -> dict:
    with (SCHEMA_DIR / name).open(encoding="utf-8") as f:
        return json.load(f)


MAX_PRINT_PER_FILE = 20


def validate_file(path: Path, validator: Draft7Validator) -> int:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print(f"  [HATA] {path.name}: dosya kökü bir dizi (liste) olmalı")
        return 1

    errors = 0
    shown = 0
    for i, record in enumerate(data):
        for e in sorted(validator.iter_errors(record), key=lambda x: list(x.path)):
            errors += 1
            if shown < MAX_PRINT_PER_FILE:
                shown += 1
                loc = f"[{i}]"
                if e.absolute_path:
                    loc += "." + ".".join(str(p) for p in e.absolute_path)
                print(f"  [HATA] {path.name} {loc}: {e.message}")
    if errors > shown:
        print(f"  ... ve {errors - shown} hata daha (tamamı için MAX_PRINT_PER_FILE artırın)")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="TransitJSON JSON doğrulayıcı")
    parser.add_argument("folder", help="Kontrol edilecek klasör (örn. JSON/Bursa)")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"[HATA] Klasör bulunamadı: {folder}")
        return 1

    total_errors = 0
    checked = 0
    for filename, schema_name in COLLECTION_TO_SCHEMA.items():
        path = folder / filename
        if not path.exists():
            print(f"  [ATLANDI] {filename} bulunamadı")
            continue
        validator = Draft7Validator(load_schema(schema_name))
        checked += 1
        errors = validate_file(path, validator)
        total_errors += errors
        if errors:
            print(f"  [HATA] {filename}: {errors} hata")
        else:
            print(f"  [OK] {filename}")

    if checked == 0:
        print("[UYARI] Doğrulanabilir dosya bulunamadı")
        return 1
    print(f"\n{checked} dosya kontrol edildi, {total_errors} hata")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())

# TransitJSON (Spec v0.2)

TransitJSON, toplu taşıma verilerini (statik tarifeler, duraklar, rotalar ve canlı araç konumları) JSON formatında hafif, kolay okunabilir ve esnek bir şekilde temsil etmek için geliştirilmiş modern bir veri standardıdır.

Detaylı format spesifikasyonu: [`TransitJSON-README.md`](TransitJSON-README.md) · JSON Schema: [`schema/`](schema/) · Doğrulayıcı: [`validate.py`](validate.py)

## v0.2 Yenilikler

- **Takvim — haftanın 7 günü:** `service_type` artık `weekday/saturday/sunday` değil; her gün için ayrı değer: `monday` | `tuesday` | `wednesday` | `thursday` | `friday` | `saturday` | `sunday`. Her seferin geçerli olduğu gün açıkça belirtilir. (`trips.json`, `holidays.json`'daki `applies_as` dahil)
- **Yeni yön modeli:** `direction: 0` = loop (tek yön döngü), `1` = gidiş, `2` = dönüş. Eski modelde `0` = gidiş ve `1` = dönüş idi (loop hatalı olarak gidişle aynı değeri kullanıyordu). `trip`, `shape`, `route_stop` ve `stop.platforms` şemalarında tutarlı şekilde uygulandı.
- **Ücret sadeleştirmesi — fare_rule kaldırıldı:** `fare_rule.schema.json` ve `fare_rules.json` tamamen kaldırıldı. Tüm hatlar başlangıçtan sona kadar **sabit (flat)** ücret kullanır. `fare_type` artık yalnızca `"flat"` değerini alabilir; zone/distance modeli bu sürümde desteklenmez.
- **Çift dilli ücret adı:** `fares.json` kayıtlarına zorunlu `name_en` (İngilizce ad) eklendi; `name` Türkçe adı tutar. Örn. `"name": "Tam Bilet"`, `"name_en": "Full Ticket"`.
- **Doğrulayıcı script:** [`validate.py`](validate.py) — klasör yolu verilir, içindeki tüm koleksiyon JSON'ları `schema/` altındaki ilgili şemaya karşı doğrulanır. Kullanım: `py validate.py JSON/Bursa`.
- **ETL güncellemeleri:** `etl/` (Bursa) ve `etl_sakarya/` (Sakarya) yeni şemaya göre üretir — her gün için ayrı sefer kayıtları, yeni yön değerleri, flat + çift dilli ücretler.

## Önceki Sürümler

### v2 — Durak Erişilebilirliği & Fiziksel Altyapı

- `wheelchair_accessible`, `has_elevator`, `has_ramp`, `has_tactile_paving`, `has_audio_announcement`, `has_braille_signage`
- `shelter_type` (`none`/`open`/`closed`/`heated`), `has_bench`, `has_lighting`, `has_real_time_display`, `has_ticket_machine`, `has_wifi`, `has_security_camera`, `has_bike_rack`
- Nested `platforms[]` — metro/tren istasyonları için platform listesi (her platform kendi bayraklarını taşır)
- GTFS uyumlu `location_type`: `stop` / `station` / `entrance` / `generic_node`

Tüm yeni alanlar opsiyoneldir; v1 kayıtları geriye uyumlu. Detay: `TransitJSON-README.md` bölüm 18.

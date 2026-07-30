# TransitJSON (Spec v2.0)

TransitJSON, toplu taşıma verilerini (statik tarifeler, duraklar, rotalar ve canlı araç konumları) JSON formatında hafif, kolay okunabilir ve esnek bir şekilde temsil etmek için geliştirilmiş modern bir veri standardıdır.

Detaylı format spesifikasyonu: [`TransitJSON-README.md`](TransitJSON-README.md) · JSON Schema: [`schema/`](schema/)

**shapes.json:** Rota geometrisi encoded polyline değil; doğrudan `{lat, lon}` koordinat dizisidir (`coordinates`).

## v2 Yenilikler

- **Durak erişilebilirliği:** `wheelchair_accessible`, `has_elevator`, `has_ramp`, `has_tactile_paving`, `has_audio_announcement`, `has_braille_signage`
- **Durak fiziksel özellikleri:** `shelter_type` (`none`/`open`/`closed`/`heated` — kapalı durak dahil), `has_bench`, `has_lighting`, `has_real_time_display`, `has_ticket_machine`, `has_wifi`, `has_security_camera`, `has_bike_rack`
- **Nested `platforms[]`:** Metro/tren istasyonları için durağa gömülü platform listesi (her platform kendi erişilebilirlik bayraklarını taşır)
- **GTFS uyumlu `location_type`:** `stop` / `station` / `entrance` / `generic_node`

Tüm yeni alanlar opsiyoneldir; v1 kayıtları geriye uyumlu. Detay: `TransitJSON-README.md` bölüm 18.

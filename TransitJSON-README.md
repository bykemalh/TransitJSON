# TransitJSON

GTFS'ten esinlenen ama daha basit, JSON-native, gerçek dünya kullanım senaryolarına (frekanslı hatlar, serbest biniş hatları, ring hatlar, offline-first mobil önbellekleme) göre tasarlanmış toplu taşıma veri formatı.

## Amaç

```
[GTFS feed'leri]  ─┐
[Diğer API'ler]   ─┼─▶ [Dönüştürücü / ETL] ─▶ TransitJSON dosyaları ─▶ [PostgreSQL] ─▶ [TransitJSON API] ─▶ Uygulama
[Manuel giriş]     ─┘
```

Farklı kaynaklardan (resmi GTFS feed'leri, belediye API'leri, elle girilen özel/minibüs hatları) toplanan veri TransitJSON formatına normalize edilir, veritabanına yazılır ve kendi API'nizden servis edilir.

## GTFS'ten Temel Farklar

| Konu | GTFS | TransitJSON |
|---|---|---|
| İlk/son durak saati | İkisi de zorunlu | Sadece **ilk durak** zorunlu, diğerleri (son durak dahil) opsiyonel |
| Takvim | `calendar.txt` + `calendar_dates.txt`, haftanın her günü bit maskesi | Sadece `service_type` (weekday/saturday/sunday) + `holidays.json` (resmi tatil = pazar kuralı) |
| Rota geometrisi | Ham `{lat,lon}` dizisi (`shapes.txt`) | Ham `{lat, lon}` koordinat dizisi (encoded polyline yok) |
| Frekanslı hatlar | `frequencies.txt` ile ayrı bir soyutlama | Yok — bir generator script ile **önceden somut saatlere genişletilip** normal `stop_times`'a yazılır |
| Serbest biniş hatlar | Yok (GTFS'te her durak açıkça tanımlı olmalı) | `stop_mode: "flexible"` — sadece ilk/son durak tanımlı |
| Cache/güncelleme takibi | Yok (statik feed mantığı) | Her koleksiyonda `updated_at`, route bazlı meta endpoint |
| Coğrafi sorgular | Yok, uygulama tarafında yapılır | PostGIS ile DB seviyesinde |

## Dosya/Koleksiyon Listesi

JSON feed/koleksiyon anahtarları **her zaman çoğuldur**. PostgreSQL tablo adları tekildir (`country`, `city`, …) — bu bilinçli bir ayrım: JSON = dizi koleksiyonu, SQL = satır varlığı.

1. `countries.json` — Ülkeler
2. `cities.json` — Şehirler (slug, timezone, merkez koordinat, sınırlar)
3. `agencies.json` — İşletmeciler (belediye, özel firma)
4. `routes.json` — Hatlar
5. `stops.json` — Duraklar (bağımsız, çok-çoğa paylaşılır)
6. `route_stops.json` — Hat-Durak ilişkisi (yön + sıra)
7. `shapes.json` — Rota geometrisi (doğrudan lat/lon koordinat dizisi; polyline encoding yok)
8. `trips.json` — Somut seferler
9. `stop_times.json` — Sefer-durak-saat ilişkisi
10. `holidays.json` — Resmi tatiller (ülkeye göre)
11. `fares.json` — Ücret tanımları (tam bilet, öğrenci, 65+ vb.)
12. `fare_rules.json` — Ücret kuralları (opsiyonel; zone/distance bazlı ücretler için)

JSON Schema dosyaları proje kökündeki `schema/` klasöründedir (örn. `schema/city.schema.json`).

## Kavramsal Model

```
country ──┬── city ──┬── agency ──┬── route ──┬── route_stop ──── stop
           │          │            │           │
           │          │            │           ├── shape (direction başına)
           │          │            │           │
           │          │            │           └── trip ──── stop_time ──── stop
           │          │            │
           │          │            └── fare ──── fare_rule (opsiyonel)
           │          │
           └── holiday (country_id ile)
```

**Kritik ayrım:** Rotanın "iskeleti" (`route_stops`, `shapes` — statik, bir kere tanımlanır) ile "somut sefer" (`trips`, `stop_times` — her kalkış için ayrı) birbirinden bağımsız tutulur. Bu sayede bir hattın 60 seferi olsa bile durak sırası sadece bir kez yazılır.

**Kapsam sınırı (v1):** Bir `route_id` + `direction` kombinasyonu tek bir `shape` ve tek bir `route_stops` dizisini paylaşır. Trip ayrı bir güzergâh/pattern varyantına bağlanmaz. Short-turn, branch ve varyant güzergâhlar v1'de desteklenmez.

---

## 1. Ortak Kurallar (Tüm Koleksiyonler İçin)

- Her kayıt bir `updated_at` (ISO 8601, UTC) alanı taşır.
- Her kayıt (mümkünse) bir `source` alanı taşır — verinin nereden geldiğini izlemek için (`"gtfs-burulas"`, `"manual"`, `"api-xyz"` gibi).
- Kimlikler (`*_id`) proje genelinde **tekildir** (feed-içi değil), bu sayede bir durak/hat birden fazla ilişkide çakışmadan referans alınabilir.
- Saatler `HH:MM:SS` string formatındadır, 24'ü aşabilir (`25:30:00` = gece yarısını geçen sefer, GTFS'teki gibi — servis günü kaymasın diye). Saatler ilgili şehrin `timezone` alanındaki IANA diliminde yerel saattir.
- Koordinatlar WGS84 (`lat`, `lon`, ondalık derece).

---

## 2. countries.json

```json
{
  "country_id": "TR",
  "name": "Türkiye",
  "updated_at": "2026-07-20T10:00:00Z"
}
```

## 3. cities.json

```json
{
  "city_id": "BUR",
  "slug": "bursa",
  "country_id": "TR",
  "name": "Bursa",
  "timezone": "Europe/Istanbul",
  "center": { "lat": 40.1885, "lon": 29.0610 },
  "default_zoom": 12,
  "bounds": { "north": 40.35, "south": 40.05, "east": 29.30, "west": 28.85 },
  "updated_at": "2026-07-20T10:00:00Z"
}
```
- `slug` benzersizdir, API URL'lerinde kullanılır: `GET /api/cities/bursa/routes`
- `timezone` zorunludur (IANA, örn. `Europe/Istanbul`); `stop_times` içindeki saatler bu dilimde yerel saattir
- `center` + `default_zoom` → harita ilk açıldığında gidilecek konum
- `bounds` → opsiyonel, harita sınırlama / "en yakın şehir" mantığı için

## 4. agencies.json

```json
{
  "agency_id": "burulas",
  "city_id": "BUR",
  "name": "BURULAŞ",
  "phone": "+90 224 xxx xx xx",
  "website": "https://burulas.com.tr",
  "updated_at": "2026-07-20T10:00:00Z"
}
```
Manuel/özel işletmeci örneği:
```json
{
  "agency_id": "inegol-seyahat",
  "city_id": "BUR",
  "name": "İnegöl Seyahat",
  "updated_at": "2026-07-20T10:00:00Z"
}
```

## 5. routes.json

```json
{
  "route_id": "F1",
  "agency_id": "burulas",
  "name": "Kültürpark - Heykel",
  "code": "F1",
  "color": "#FF6600",
  "vehicle_type": "bus",
  "fare_id": "BUR-tam",
  "route_pattern": "round_trip",
  "stop_mode": "fixed",
  "updated_at": "2026-07-20T10:00:00Z"
}
```
- `vehicle_type` (zorunlu): Araç türü. Desteklenen değerler:

  | Değer | Açıklama | Örnek |
  |-------|----------|-------|
  | `"bus"` | Otobüs | Her yerde |
  | `"tram"` | Tramvay / Hafif raylı | İstanbul, Konya, Eskişehir |
  | `"metro"` | Metro / Subway | İstanbul, Ankara, İzmir |
  | `"rail"` | Demiryolu (Marmaray, banliyö, YHT) | İstanbul, Ankara |
  | `"ferry"` | Vapur / Feribot | İstanbul, İzmir |
  | `"cable_tram"` | Kablolu tramvay | San Francisco, Lizbon |
  | `"gondola"` | Teleferik / Gondol (havadan) | Bursa, İstanbul |
  | `"funicular"` | Füniküler (raylı, eğimli) | İstanbul Tünel, Bursa |
  | `"trolleybus"` | Troleybüs (elektrikli katenelli) | Malatya |
  | `"monorail"` | Monoray | Tokyo, Singapur |
  | `"minibus"` | Minibüs / Dolmuş | Türkiye (yaygın) |
  | `"coach"` | Şehirlerarası otobüs | FlixBus, Kamil Koç |
  | `"water_taxi"` | Deniz taksi / Motor | İstanbul, Venedik |

- `fare_id` (opsiyonel): Bu hat için geçerli ücret tanımı. `fares.json`'daki `fare_id`'ye referans verir. Belirtilmezse agency'nin varsayılan ücretleri kullanılır.
- `route_pattern`: `"round_trip"` (gidiş/dönüş) | `"loop"` (ring — tek yön, başlangıç=bitiş)
- `stop_mode`: `"fixed"` (tüm ara duraklar belli, belediye hattı) | `"flexible"` (sadece ilk/son durak belli, serbest biniş — minibüs/İnegöl tipi hatlar)

Ring örneği:
```json
{
  "route_id": "R5",
  "agency_id": "burulas",
  "name": "Kampüs Ring",
  "vehicle_type": "bus",
  "route_pattern": "loop",
  "stop_mode": "fixed",
  "updated_at": "2026-07-20T10:00:00Z"
}
```

Serbest biniş örneği (minibüs hattı):
```json
{
  "route_id": "INE-KET",
  "agency_id": "inegol-seyahat",
  "name": "İnegöl Terminal - Ketsel Metro",
  "vehicle_type": "minibus",
  "fare_id": "INE-tam",
  "route_pattern": "round_trip",
  "stop_mode": "flexible",
  "updated_at": "2026-07-20T10:00:00Z"
}
```

## 6. stops.json

Bağımsız varlık — hiçbir route'a ait değildir, çok-çoğa ilişki `route_stops` üzerinden kurulur.

v2'de durağa erişilebilirlik bayrakları, fiziksel özellikler ve opsiyonel bir `platforms` (nested) dizisi eklendi. Tüm yeni alanlar opsiyoneldir (`null` veya eksik olabilir); v1 kayıtları şema ile tam uyumludur.

```json
{
  "stop_id": "BUR-01023",
  "city_id": "BUR",
  "name": "Heykel",
  "lat": 40.1885,
  "lon": 29.0610,
  "location_type": "stop",
  "wheelchair_accessible": true,
  "has_ramp": true,
  "has_elevator": false,
  "has_tactile_paving": true,
  "has_audio_announcement": true,
  "has_braille_signage": false,
  "shelter_type": "closed",
  "has_bench": true,
  "has_lighting": true,
  "has_real_time_display": true,
  "has_ticket_machine": true,
  "has_trash_bin": true,
  "has_wifi": false,
  "has_security_camera": true,
  "has_bike_rack": false,
  "platforms": [],
  "updated_at": "2026-07-20T10:00:00Z"
}
```
Öneri: `stop_id` üretimini `{city_id}-{sıra}` gibi okunabilir yapın (örn. `BUR-01023`) — hem debug kolaylığı hem şehirler arası doğal tekillik sağlar.

### 6.1 Erişilebilirlik Alanları (v2)

Tüm alanlar opsiyoneldir, tipi `["boolean", "null"]`'dur. `null` = bilinmiyor / veri yok anlamına gelir.

| Alan | Açıklama |
|---|---|
| `wheelchair_accessible` | Tekerlekli sandalye ile durağa/durağın içine erişilebilir mi? |
| `has_ramp` | Rampa var mı? |
| `has_elevator` | Asansör var mı? |
| `has_tactile_paving` | Görme engelliler için taktil (kabartmalı) yüzey var mı? |
| `has_audio_announcement` | Yaklaşan araç/hat için sesli anons var mı? |
| `has_braille_signage` | Braille tabela var mı? |

### 6.2 Fiziksel Özellikler (v2)

| Alan | Tip | Açıklama |
|---|---|---|
| `shelter_type` | enum | `"none"` \| `"open"` \| `"closed"` \| `"heated"`, `null`. Kapalı durak kavramı `closed` (camekanlı) ve `heated` (ısıtmalı kapalı) değerleridir. |
| `has_bench` | bool/null | Oturma yeri |
| `has_lighting` | bool/null | Aydınlatma |
| `has_real_time_display` | bool/null | Canlı kalkış saati ekranı |
| `has_ticket_machine` | bool/null | Bilet makinesi |
| `has_trash_bin` | bool/null | Çöp kutusu |
| `has_wifi` | bool/null | Ücretsiz WiFi |
| `has_security_camera` | bool/null | Güvenlik kamerası |
| `has_bike_rack` | bool/null | Bisiklet parkı |

### 6.3 `location_type` (v2, GTFS uyumlu)

Opsiyonel enum:

| Değer | Açıklama |
|---|---|
| `"stop"` | Basit durak (varsayılan; `null` da bu anlama gelir) |
| `"station"` | İstasyon/kompleks — birden fazla platform içerebilir |
| `"entrance"` | İstasyon girişi (iç platforma erişim noktası) |
| `"generic_node"` | Yolcu erişimi olmayan geometrik nokta |

### 6.4 `platforms[]` (v2)

Büyük istasyonlar (metro, tren, büyük aktarma merkezleri) için **durağa gömülü** platform listesi. Basit duraklarda bu dizi boş veya 1 elemanlıdır.

```json
{
  "stop_id": "BUR-90001",
  "city_id": "BUR",
  "name": "Şehreküstü Metro İstasyonu",
  "lat": 40.1826,
  "lon": 29.0666,
  "location_type": "station",
  "wheelchair_accessible": true,
  "has_elevator": true,
  "has_tactile_paving": true,
  "platforms": [
    {
      "platform_id": "BUR-90001-P1",
      "code": "1",
      "direction": 0,
      "lat": 40.1827,
      "lon": 29.0667,
      "wheelchair_accessible": true,
      "has_elevator": true,
      "has_tactile_paving": true,
      "has_audio_announcement": true,
      "has_shelter": true,
      "shelter_type": "closed",
      "has_bench": true,
      "has_lighting": true,
      "updated_at": "2026-07-20T10:00:00Z"
    },
    {
      "platform_id": "BUR-90001-P2",
      "code": "2",
      "direction": 1,
      "lat": 40.1825,
      "lon": 29.0665,
      "wheelchair_accessible": true,
      "has_elevator": true,
      "has_tactile_paving": true,
      "has_audio_announcement": true,
      "has_shelter": true,
      "shelter_type": "closed",
      "has_bench": true,
      "has_lighting": true,
      "updated_at": "2026-07-20T10:00:00Z"
    }
  ],
  "updated_at": "2026-07-20T10:00:00Z"
}
```

**Neden nested?** Çoğu şehirde platform başına ayrı bir JSON dosyası ve tablo yönetmek overkill; PostgreSQL tarafında `stops.platforms` JSONB kolonu olarak tutulup GIN index ile sorgulanabilir. Erişilebilirlik sorguları (ör. "tekerlekli sandalye erişimli platformlar") `jsonb_path_query` veya `jsonb_exists` ile yapılır.

**Platform düzeyi vs. durak düzeyi:** Platform kendi bayraklarını taşır; durağın kök alanlarından **bağımsızdır**. Örnek: istasyonun asansörü var ama bir platforma yalnızca merdivenle iniliyor — kök `has_elevator: true`, o platform `has_elevator: false`.

## 7. route_stops.json

```json
[
  { "route_id": "F1", "direction": 0, "stop_id": "BUR-01001", "sequence": 1, "is_first_stop": true, "updated_at": "2026-07-20T10:00:00Z" },
  { "route_id": "F1", "direction": 0, "stop_id": "BUR-01023", "sequence": 2, "updated_at": "2026-07-20T10:00:00Z" },
  { "route_id": "F1", "direction": 1, "stop_id": "BUR-01023", "sequence": 1, "is_first_stop": true, "updated_at": "2026-07-20T10:00:00Z" },
  { "route_id": "F1", "direction": 1, "stop_id": "BUR-01001", "sequence": 2, "updated_at": "2026-07-20T10:00:00Z" }
]
```
- `direction: 0` = gidiş, `direction: 1` = dönüş
- `route_pattern: "loop"` olan hatlarda `direction` her zaman `0`'dır, ama ilk ve son kayıt **aynı `stop_id`'ye farklı `sequence` ile** referans verir (döngünün kapandığını gösterir):
```json
[
  { "route_id": "R5", "direction": 0, "stop_id": "BUR-02000", "sequence": 1, "is_first_stop": true },
  { "route_id": "R5", "direction": 0, "stop_id": "BUR-02010", "sequence": 2 },
  { "route_id": "R5", "direction": 0, "stop_id": "BUR-02020", "sequence": 3 },
  { "route_id": "R5", "direction": 0, "stop_id": "BUR-02000", "sequence": 4, "is_last_stop": true }
]
```
- `stop_mode: "flexible"` olan hatlarda sadece 2 kayıt vardır (ilk + son durak).

## 8. shapes.json

```json
{
  "shape_id": "S-F1-0",
  "route_id": "F1",
  "direction": 0,
  "coordinates": [
    { "lat": 40.1885, "lon": 29.0610 },
    { "lat": 40.1901, "lon": 29.0652 },
    { "lat": 40.1920, "lon": 29.0700 }
  ],
  "updated_at": "2026-07-20T10:00:00Z"
}
```
- Güzergâh **doğrudan** `{lat, lon}` koordinat dizisi olarak saklanır. Encoded polyline (`shape_encoded`) kullanılmaz.
- Duraklar ve şehir merkezi ile aynı koordinat modeli (`lat` / `lon`).
- Her `route_id` + `direction` kombinasyonu için ayrı bir shape kaydı olur (gidiş/dönüş genelde farklı güzergah izler).

## 9. trips.json

```json
{ "trip_id": "F1-0700-G", "route_id": "F1", "direction": 0, "service_type": "weekday", "updated_at": "2026-07-20T10:00:00Z" }
```
- `service_type`: `"weekday"` | `"saturday"` | `"sunday"`
- Frekanslı hatlarda (örn. İnegöl-Ketsel her 15 dk) her sefer yine ayrı bir `trip` kaydı olarak somutlaştırılmış halde bulunur — bunlar elle değil, bir **generator script** ile üretilir (bkz. bölüm 12).
- **v1 kapsam sınırı:** Trip, ayrı bir `shape` veya `route_stops` varyantına bağlanmaz. Aynı `route_id` + `direction` altındaki tüm seferler tek güzergâhı paylaşır (short-turn / branch / varyant yok).

## 10. stop_times.json

```json
[
  { "trip_id": "F1-0700-G", "stop_id": "BUR-01001", "sequence": 1, "departure_time": "07:00:00", "updated_at": "2026-07-20T10:00:00Z" },
  { "trip_id": "F1-0700-G", "stop_id": "BUR-01023", "sequence": 2, "departure_time": null, "updated_at": "2026-07-20T10:00:00Z" }
]
```
**Kural:** `sequence == 1` (ilk durak) için `departure_time` zorunludur. Diğer tüm duraklar (son durak dahil) için opsiyoneldir (`null` veya alan hiç yazılmayabilir). Detaylı kural JSON Schema'da `if/then` ile ifade edilir (bkz. `schema/stop_time.schema.json`).

## 11. holidays.json

```json
{ "date": "2026-04-23", "country_id": "TR", "name": "23 Nisan", "applies_as": "sunday", "updated_at": "2026-07-20T10:00:00Z" }
```
- `applies_as`: o gün hangi `service_type` programının uygulanacağı (`"sunday"` sabit kuraldır).
- API mantığı: `bugün holidays içinde var mı? → varsa applies_as kullan; yoksa haftanın gününden service_type türet.`

## 12. fares.json

Ücret tanımları. Her agency'nin farklı yolcu profilleri (tam, öğrenci, 65+) veya farklı ücret modelleri için ayrı fare kayıtları oluşturulur.

```json
{
  "fare_id": "BUR-tam",
  "agency_id": "burulas",
  "name": "Tam Bilet",
  "fare_type": "flat",
  "price": 17.80,
  "currency": "TRY",
  "payment_methods": ["smart_card", "credit_card"],
  "transfer_duration": 90,
  "transfer_limit": 3,
  "updated_at": "2026-07-20T10:00:00Z"
}
```
- `fare_type` (zorunlu): `"flat"` (sabit ücret) | `"zone"` (bölge bazlı, `fare_rules.json` gerekir) | `"distance"` (mesafe bazlı, `fare_rules.json` gerekir)
- `price` (zorunlu): Birim fiyat. `flat` için tam fiyat; `zone`/`distance` için baz fiyat.
- `currency` (zorunlu): ISO 4217 para birimi kodu (`"TRY"`, `"EUR"`, `"USD"`).
- `payment_methods` (opsiyonel): Kabul edilen ödeme yöntemleri: `"cash"` | `"smart_card"` | `"credit_card"` | `"mobile"` | `"contactless"` | `"qr"`
- `transfer_duration` (opsiyonel): Aktarma süresi (dakika). Bu süre içinde yapılan aktarmalarda ek ücret alınmaz. `null` = aktarma hakkı yok.
- `transfer_limit` (opsiyonel): `transfer_duration` süresi içinde kaç aktarma hakkı var. `null` = sınırsız.

Öğrenci ve 65+ örnekleri:
```json
[
  { "fare_id": "BUR-tam",     "agency_id": "burulas", "name": "Tam Bilet",     "fare_type": "flat", "price": 17.80, "currency": "TRY", "updated_at": "2026-07-20T10:00:00Z" },
  { "fare_id": "BUR-ogrenci", "agency_id": "burulas", "name": "Öğrenci Bilet", "fare_type": "flat", "price": 8.90,  "currency": "TRY", "updated_at": "2026-07-20T10:00:00Z" },
  { "fare_id": "BUR-65plus",  "agency_id": "burulas", "name": "65+ Bilet",     "fare_type": "flat", "price": 0.00,  "currency": "TRY", "updated_at": "2026-07-20T10:00:00Z" }
]
```

**Route bağlantısı:** Route'un `fare_id` alanı `fares.json`'daki `fare_id`'ye referans verir. Eğer bir route'un kendi `fare_id`'si yoksa, o route'un agency'sine ait tüm fare kayıtları geçerlidir.

## 13. fare_rules.json (opsiyonel)

Sadece `fare_type: "zone"` veya `"distance"` kullanan ajanslar için gereklidir. Flat ücretli şehirler bu dosyayı hiç oluşturmak zorunda değildir.

Zone bazlı örnek:
```json
[
  { "fare_rule_id": "IST-r1", "fare_id": "IST-zone-ab", "route_id": null, "from_zone": "A", "to_zone": "B", "price_override": 22.50, "updated_at": "2026-07-20T10:00:00Z" },
  { "fare_rule_id": "IST-r2", "fare_id": "IST-zone-ac", "route_id": null, "from_zone": "A", "to_zone": "C", "price_override": 30.00, "updated_at": "2026-07-20T10:00:00Z" }
]
```

Mesafe bazlı örnek:
```json
[
  { "fare_rule_id": "ANK-d1", "fare_id": "ANK-dist", "min_distance_km": 0,  "max_distance_km": 10, "price_override": 15.00, "updated_at": "2026-07-20T10:00:00Z" },
  { "fare_rule_id": "ANK-d2", "fare_id": "ANK-dist", "min_distance_km": 10, "max_distance_km": 25, "price_override": 20.00, "updated_at": "2026-07-20T10:00:00Z" },
  { "fare_rule_id": "ANK-d3", "fare_id": "ANK-dist", "min_distance_km": 25, "max_distance_km": null, "price_override": 28.00, "updated_at": "2026-07-20T10:00:00Z" }
]
```

---

## 14. Frekanslı Hatlar — Generator Yaklaşımı

`frequencies.json` gibi ayrı bir soyutlama **kullanılmaz** — gereksiz karmaşıklık olarak değerlendirildi. Bunun yerine:

1. Kural parametre olarak generator script'e verilir: başlangıç saati, bitiş saati, aralık (dakika), `route_id`.
2. Script bu parametreleri **somut `trip` + `stop_time` kayıtlarına genişletir** (07:00, 07:15, 07:30 ... 22:00).
3. Çıktı normal `trips.json` / `stop_times.json` formatındadır — API ve uygulama tarafında hiçbir özel durum kodu gerekmez.
4. Script bir kere çalıştırılır, çıktısı normal upload akışına sokulur; headway değişirse script yeniden çalıştırılıp dosya yeniden yüklenir (bkz. bölüm 15, replace stratejisi).

```python
# generate_schedule.py — kavramsal örnek
def generate(route_id, direction, start="06:00:00", end="22:00:00",
             interval_minutes=15, service_type="weekday", stop_sequence=None):
    trips, stop_times = [], []
    t = parse_time(start)
    i = 0
    while t <= parse_time(end):
        trip_id = f"{route_id}-{i:04d}"
        trips.append({
            "trip_id": trip_id, "route_id": route_id,
            "direction": direction, "service_type": service_type
        })
        for seq, (stop_id, offset_seconds) in enumerate(stop_sequence, start=1):
            stop_times.append({
                "trip_id": trip_id, "stop_id": stop_id, "sequence": seq,
                "departure_time": format_time(t + offset_seconds) if seq == 1 or offset_seconds is not None else None
            })
        t += interval_minutes * 60
        i += 1
    return trips, stop_times
```

---

## 15. Import / Güncelleme Stratejisi

**Model: tam replace (scope'u sınırlı).** Bir şehir/agency için yeni dosya yüklendiğinde, o kapsamdaki (`city_id` + `source` ile sınırlı) eski kayıtlar silinip yenisi yazılır — tüm tablo değil, sadece ilgili kaynağın kayıtları. Ücret verileri (`fares`, `fare_rules`) de aynı stratejiye tabidir.

```sql
BEGIN;
DELETE FROM stops WHERE city_id = 'BUR' AND source = 'gtfs-burulas';
INSERT INTO stops (...) VALUES (...);  -- staging'den
UPDATE stops SET updated_at = now() WHERE city_id = 'BUR' AND source = 'gtfs-burulas';
COMMIT;
```

- Transaction zorunlu — yükleme yarıda kesilirse veri tutarsız kalmamalı.
- `stop_id` üretimini mümkünse **kalıcı** tutun (isim/konuma göre eşleştirip aynı ID'yi koruyun); aksi halde kullanıcıların favori durak/hat referansları kırılır.

## 16. Cache / `updated_at` Mantığı

Her koleksiyonda `updated_at` bulunur. Ayrıca route bazlı hafif bir **meta endpoint** önerilir:

```
GET /api/routes/f1/meta
{
  "route_id": "F1",
  "route_stops_updated_at": "2026-07-15T10:30:00Z",
  "shapes_updated_at": "2026-06-01T08:00:00Z",
  "stop_times_updated_at": "2026-07-18T14:00:00Z",
  "trips_updated_at": "2026-07-18T14:00:00Z"
}
```

Uygulama önce bu küçük objeyi çeker, cihazdaki önbellekle karşılaştırır, sadece değişen parçayı indirir. Favori hatlarda shape + durak listesi + saatler cihaza kaydedilip hızlıca gösterilir; ağır veri (shape) her açılışta tekrar indirilmez.

## 17. Önerilen Teknoloji Yığını

**PostgreSQL + PostGIS** (MongoDB değil):
- Veri doğası ilişkisel (country→city→agency→route→stop→trip→stop_time zinciri), Mongo'da bu ilişkileri modellemek gereksiz karmaşıklık yaratır.
- `JSONB` kolonları esnek/opsiyonel alanlar için Mongo'nun esnekliğini zaten sağlar.
- `PostGIS` ile "en yakın durak", "X metre yarıçapındaki duraklar" gibi coğrafi sorgular endeksli ve hızlı çalışır.
- ACID transaction garantisi, bölüm 13'teki replace stratejisi için kritik.
- Opsiyonel: **Redis** — API response cache katmanı (bölüm 14'teki meta endpoint'i hızlandırmak için).

Detaylı tablo yapısı için `transitjson-schema.sql` dosyasına bakın.

---

## 18. Sürüm Geçmişi

### v2 — Durak Erişilebilirliği & Fiziksel Altyapı

**Kapsam:** Sadece `stops.json` ve ilgili şema (`schema/stop.schema.json`).

**Yeni alanlar (tümü opsiyonel, `null` veya eksik olabilir):**

- **Erişilebilirlik flag'leri:** `wheelchair_accessible`, `has_ramp`, `has_elevator`, `has_tactile_paving`, `has_audio_announcement`, `has_braille_signage`
- **Fiziksel özellikler:** `shelter_type` (enum: `none`/`open`/`closed`/`heated`), `has_bench`, `has_lighting`, `has_real_time_display`, `has_ticket_machine`, `has_trash_bin`, `has_wifi`, `has_security_camera`, `has_bike_rack`
- **Konum tipi:** `location_type` (GTFS uyumlu enum: `stop`/`station`/`entrance`/`generic_node`)
- **Nested `platforms[]`:** Büyük istasyonlar için durağa gömülü platform listesi. Her platform kendi erişilebilirlik/fiziksel bayraklarını taşır.

**Geriye uyumluluk:** v1 formatındaki mevcut `stops.json` dosyaları v2 şemasıyla **doğrulanmaya devam eder**. Yeni alanlar `additionalProperties: false` kuralı istisnası değildir; sadece `required` listesinde olmadıkları için eski kayıtlarda eksik bırakılabilir. Mevcut ETL çıktıları (`bursa.json`, `sakarya.json`) dokunulmaz — yeni alanları agency'ler kademeli olarak doldurabilir.

**PostgreSQL önerisi:** `stops` tablosuna `platforms JSONB` kolonu + `GIN` index eklenir. Erişilebilirlik sorguları:
```sql
SELECT stop_id FROM stops WHERE (platforms #> '{0,wheelchair_accessible}')::bool = true;
-- veya kök düzey için:
SELECT stop_id FROM stops WHERE wheelchair_accessible = true;
```

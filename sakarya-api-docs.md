# Sakarya Büyükşehir Belediyesi (SBB) Ulaşım Public API Dokümantasyonu

**Base URL:** `https://sbbpublicapi.sakarya.bel.tr/api/v1`

> Bu dokümantasyon, tarayıcı network trafiği incelenerek reverse-engineer edilmiştir. Resmi değildir, doğrulanmamış alanlar açıkça belirtilmiştir.

---

## Genel Notlar

- API CORS kontrolü yapıyor; sunucu tarafı `Origin` whitelist kontrolü var. Tarayıcı dışından (Postman, backend kod) istek atarken **mutlaka uygun `Origin`/`Referer` header'ları gönderilmeli**, aksi halde CORS/403 hatası alınabilir.
- Tüm koordinatlar **GeoJSON standardına uygun `[longitude, latitude]`** sırasıyla döner (lat/lng bekleyen haritalama kütüphanelerinde ters çevirme gerekir).
- `lineId` ile `AsisId` (asisIntegrationId) **farklı kimlik alanlarıdır**, karıştırılmamalı.

### Origin / Referer Header Tablosu

| Endpoint | Origin | Referer |
|---|---|---|
| `GET /Ulasim/line-schedule` | `https://ulasim.sakarya.bel.tr` | `https://ulasim.sakarya.bel.tr/` |
| `GET /VehicleTracking` | `https://sakus.sakarya.bel.tr` | `https://sakus.sakarya.bel.tr/` |
| `GET /Ulasim/route-and-busstops/{lineId}` | `https://ulasim.sakarya.bel.tr` (doğrulandı) | `https://ulasim.sakarya.bel.tr/` |

### Diğer Standart Headerlar (önerilen)
```
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0
Accept: application/json, text/plain, */*
Accept-Language: en-US,en;q=0.9
Accept-Encoding: gzip, deflate, br, zstd
Connection: keep-alive
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-site
```

---

## 1. Hat Güzergahı ve Durak Bilgisi

```
GET /Ulasim/route-and-busstops/{lineId}
```

### Açıklama
Belirtilen hat (lineId) için her iki yöndeki (gidiş/dönüş) güzergah geometrisini (polyline) ve duraklarını döner.

### Path Parametreleri
| Parametre | Tip | Açıklama | Örnek |
|---|---|---|---|
| `lineId` | integer | Hattın benzersiz ID'si (örn: M1 hattı için `50`) | `50` |

### Örnek İstek
```
GET https://sbbpublicapi.sakarya.bel.tr/api/v1/Ulasim/route-and-busstops/50
Origin: https://ulasim.sakarya.bel.tr
Referer: https://ulasim.sakarya.bel.tr/
```

### Response Şeması

```json
{
  "lineId": "integer — Hat ID",
  "lineName": "string — Hat adı (örn: 'GAR MEYDANI - KORUCUK')",
  "lineDetail": "string|null — Ek hat açıklaması",
  "typeValueId": "integer — Hat tipi referans ID (örn: 6904)",
  "lineNumber": "string — Hat numarası/kodu (örn: 'M1')",
  "routes": [
    {
      "routeId": "integer — Yön bazlı rota ID (gidiş ve dönüş için ayrı ID)",
      "routeName": "string — Rota adı (örn: 'Gar Meydanı -Korucuk')",
      "routeGeometry": {
        "type": "'MultiLineString' — GeoJSON geometri tipi",
        "coordinates": "number[][][] — [lng, lat] koordinat dizisi"
      },
      "busStops": [
        {
          "id": "integer — Durak benzersiz ID",
          "order": "integer — Güzergah üzerindeki sıra numarası (1'den başlar)",
          "name": "string — Durak adı (örn: 'M1 - GAR MEYDANI')",
          "busStopGeometry": {
            "type": "'Point'",
            "coordinates": "[lng, lat] — Durağın konumu"
          },
          "description": "string|null",
          "busStopTypeName": "string — Durak tipi adı (örn: 'KAPALI DURAK')",
          "busStopTypeId": "integer",
          "isSmartStop": "boolean — Elektronik tabela vb. olan akıllı durak mı",
          "busStopNumber": "string|null"
        }
      ],
      "routeTypeId": "integer — Yön kodu. M1 örneğinde: 220 = gidiş (802), 221 = dönüş (803). ⚠️ Bu paternin tüm hatlarda geçerli olup olmadığı doğrulanmadı, sadece M1 üzerinden gözlemlendi.",
      "startLocation": "string — Başlangıç noktası adı",
      "endLocation": "string — Bitiş noktası adı"
    }
  ],
  "ekentLineIntegrationId": "integer|null — E-kent sistemi entegrasyon ID'si (varsa)"
}
```

### Notlar
- `routes` dizisi genellikle **2 eleman** içerir: gidiş ve dönüş.
- `busStops` dizisindeki `order`, durağın `routeGeometry` üzerindeki sırasıdır.

---

## 2. Canlı Araç Takip (Vehicle Tracking)

```
GET /VehicleTracking?AsisId={asisId}
```

### Açıklama
Belirtilen hat için o anda yolda olan tüm araçların canlı konum, hız, yön ve sıradaki durağa tahmini varış (ETA) bilgilerini döner.

### Query Parametreleri
| Parametre | Tip | Açıklama | Örnek |
|---|---|---|---|
| `AsisId` | integer | Hattın "Asis" entegrasyon ID'si (line listesindeki `asisIntegrationId` alanına karşılık gelir; `lineId`'den farklıdır — M1 için `lineId=50`, `AsisId=250`) | `250` |

### Örnek İstek
```
GET https://sbbpublicapi.sakarya.bel.tr/api/v1/VehicleTracking?AsisId=250
Origin: https://sakus.sakarya.bel.tr
Referer: https://sakus.sakarya.bel.tr/
```

### Response Şeması (Array)

```json
[
  {
    "busNumber": "integer — Araç/otobüs numarası (filo içi)",
    "lineNumber": "string — Hat kodu (örn: 'M1')",
    "location": {
      "type": "'Point'",
      "coordinates": "[lng, lat] — Aracın anlık konumu"
    },
    "trackingId": "integer — Bu takip kaydının benzersiz ID'si",
    "lineId": "integer — Hat ID (route-and-busstops endpoint'i ile eşleşir)",
    "speed": "integer — Anlık hız (km/sa) ✅ doğrulandı",
    "lineName": "string — Hat tam adı",
    "nextStopId": "integer — Sıradaki durağın ID'si (busStops.id ile eşleşir)",
    "nextStopName": "string — Sıradaki durağın adı",
    "atStopId": "integer|null — Araç şu an bir durakta bekliyorsa o durağın ID'si",
    "atStopName": "string|null",
    "status": "string — Gözlemlenen değerler: 'CRUISE' (seyirde), 'APPROACH' (durağa yaklaşıyor). Başka değerler olabilir, doğrulanmadı.",
    "routeName": "string — Hangi yöndeki rotada olduğu",
    "routeId": "integer — Rota ID (route-and-busstops'taki routeId ile eşleşir)",
    "distNextStopMeter": "float — Sıradaki durağa kalan mesafe (metre)",
    "headingDegree": "float — Aracın pusula yönü (derece, 0-360)",
    "etaS": "float — Sıradaki durağa tahmini varış süresi (saniye)",
    "nhatNo": "integer — Asis entegrasyon ID'si (AsisId parametresiyle aynı değer döner)",
    "plate": "string — Araç plakası",
    "startLocation": "string — Rotanın başlangıç noktası",
    "endLocation": "string — Rotanın bitiş noktası"
  }
]
```

### Notlar
- Bu endpoint **anlık (real-time) veri** döner; cache edilmemeli.
- `etaS` saniye cinsindendir; dakikaya çevirmek için `/60`.

---

## 3. Hat Sefer Tarifesi (Schedule)

```
GET /Ulasim/line-schedule?date={date}&lineId={lineId}
```

### Açıklama
Belirtilen hat ve tarih için tüm seferlerin (trip) planlanan kalkış/varış saatlerini, yön bazında listeler.

### Query Parametreleri
| Parametre | Tip | Açıklama | Örnek |
|---|---|---|---|
| `date` | ISO 8601 datetime (UTC) | Sorgulanan **yerel (TR) günün 00:00'ı**, UTC'ye çevrilmiş hali. Bkz. aşağıdaki formül. | `2026-06-21T21:00:00.000Z` |
| `lineId` | integer | Hat ID'si | `50` |

#### `date` Hesaplama Formülü ✅ Doğrulandı
TR saat dilimi UTC+3 olduğundan:

```
date = (istenen_gün'ün 00:00 TR saati) - 3 saat (UTC'ye çevir)
     = önceki takvim günü, 21:00:00.000Z
```

**Örnek:** 21 Haziran 2026 (Pazar) için sefer tarifesi istemek için:
```
date = 2026-06-20T21:00:00.000Z
```
(URL-encoded: `2026-06-20T21%3A00%3A00.000Z`)

### Örnek İstek
```
GET https://sbbpublicapi.sakarya.bel.tr/api/v1/Ulasim/line-schedule?date=2026-06-20T21%3A00%3A00.000Z&lineId=50
Origin: https://ulasim.sakarya.bel.tr
Referer: https://ulasim.sakarya.bel.tr/
```

### Response Şeması

```json
{
  "lineId": "integer",
  "lineName": "string",
  "lineNumber": "string",
  "schedules": [
    {
      "routeId": "integer — Yön (gidiş/dönüş) ID'si",
      "routeName": "string",
      "routeDetail": [
        {
          "dayParameterValueId": "integer — Gün tipi referansı (bkz. tablo aşağıda)",
          "startTime": "string (HH:mm:ss) — Seferin kalkış saati",
          "endTime": "string (HH:mm:ss) — Seferin tahmini bitiş/varış saati",
          "tripNumber": "integer — Sefer sıra numarası (gidiş ve dönüş seferleri birlikte/iç içe numaralandırılmış, muhtemelen araç rotasyonunu takip ediyor)",
          "description": "string|null — Sefere özel not"
        }
      ]
    }
  ]
}
```

### Gün Tipi Referans Tablosu (`dayParameterValueId`) ✅ Doğrulandı
| Değer | Gün |
|---|---|
| `222` | Hafta içi |
| `223` | Cumartesi |
| `224` | Pazar |

### Notlar
- Sefer süresi standart **30 dakika**; bazı son seferlerde **35 dakika** (örn. 22:30→23:05).
- `tripNumber`, gidiş ve dönüş seferlerini birlikte ardışık numaralandırır — filo/araç rotasyon takibi için kullanışlı olabilir.

---

## Hat Listesi Referansı (Örnek)

```json
{
  "id": 50,
  "name": "GAR MEYDANI - KORUCUK",
  "asisIntegrationId": 250,
  "lineNumber": "M1",
  "busTypeColor": "#f04646",
  "slug": "m1-gar-meydani-korucuk-50"
}
```

> Bu yapı muhtemelen bir "tüm hatları listele" endpoint'inden geliyor (henüz tespit edilmedi). `id` → `lineId` parametresi, `asisIntegrationId` → `AsisId` parametresi olarak kullanılır.

---

## Açık / Doğrulanmamış Noktalar

1. **`routeTypeId` (220/221) paterni**: Sadece M1 hattından gözlemlendi (gidiş=220, dönüş=221). Diğer hatlarla doğrulanmadı.
2. **`status` alanının tam değer kümesi**: `CRUISE`, `APPROACH` dışında değer olup olmadığı bilinmiyor (önemsiz kabul edildi).
3. **Hat listesi endpoint'i**: Yukarıdaki `id/name/asisIntegrationId/...` yapısının geldiği endpoint henüz dokümante edilmedi.
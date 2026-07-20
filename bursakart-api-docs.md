
# Bursa Kart API Dokümantasyonu

Base URL: `https://bursakartapi.abys-web.com/api/static`

---

## İstek Başlıkları (Request Headers)

Tüm endpoint'lere yapılan isteklerde aşağıdaki başlıklar kullanılır:

```
Host: bursakartapi.abys-web.com
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0
Accept: */*
Accept-Language: en-US,en;q=0.9
Accept-Encoding: gzip, deflate, br, zstd
Access-Control-Request-Method: POST
Access-Control-Request-Headers: content-type
Referer: https://www.bursakart.com.tr/
Origin: https://www.bursakart.com.tr
Connection: keep-alive
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: cross-site
Sec-GPC: 1
Priority: u=4
TE: trailers
```

> **Not:** API, `https://www.bursakart.com.tr` origin'inden CORS ile çağrılmaktadır. İstekler `cross-site` modda yapılır.

---

## 1. Araç Canlı Konum

Hat numarasına göre o hatta aktif sefer yapan otobüslerin anlık konum ve yolcu bilgilerini döner.

**Endpoint**

```
POST /realtimedata
```

**Request Body**

| Alan        | Tip    | Açıklama                          |
| ----------- | ------ | ----------------------------------- |
| `keyword` | string | Hat kodu (örn.`"617"`,`"31A"`) |

**Örnek İstek**

```json
{
  "keyword": "617"
}
```

**Örnek Yanıt**

```json
{
  "version": 1,
  "statusCode": 200,
  "message": "Success",
  "result": [
    {
      "state": 1,
      "plaka": "16 M 06067",
      "enlem": 40.08408167,
      "boylam": 29.51137333,
      "renk": "00FF00",
      "hiz": 2,
      "mesafe": 124432,
      "surucu": "",
      "gunlukYolcu": 283,
      "seferYolcu": 10,
      "durakYolcu": 10,
      "maxHiz": 48,
      "yon": 0,
      "editDate": "0001-01-01T00:00:00",
      "imageUrl": "images/icon/green_bus.gif",
      "klimaVarMi": 0,
      "engelliUygunMu": 0,
      "hatkodu": "617",
      "validatorNo": 6167,
      "istikamet": "G"
    }
  ]
}
```

**Yanıt Alanları**

| Alan               | Tip    | Açıklama                                             |
| ------------------ | ------ | ------------------------------------------------------ |
| `state`          | int    | Araç durumu (`1`= aktif)                            |
| `plaka`          | string | Araç plakası                                         |
| `enlem`          | float  | Enlem (latitude)                                       |
| `boylam`         | float  | Boylam (longitude)                                     |
| `renk`           | string | Araç ikon rengi (HEX)                                 |
| `hiz`            | int    | Anlık hız (km/s)                                     |
| `mesafe`         | int    | Toplam kat edilen mesafe (metre)                       |
| `surucu`         | string | Sürücü adı (boş olabilir)                         |
| `gunlukYolcu`    | int    | Günlük toplam yolcu sayısı                         |
| `seferYolcu`     | int    | Mevcut seferdeki yolcu sayısı                        |
| `durakYolcu`     | int    | Son durактaki yolcu sayısı                        |
| `maxHiz`         | int    | Sefer içindeki maksimum hız (km/s)                   |
| `yon`            | int    | Yön bilgisi                                           |
| `editDate`       | string | Son güncelleme tarihi                                 |
| `imageUrl`       | string | Araç ikon görseli yolu                               |
| `klimaVarMi`     | int    | Klima durumu (`0`= yok,`1`= var)                   |
| `engelliUygunMu` | int    | Engelli erişim uygunluğu (`0`= hayır,`1`= evet) |
| `hatkodu`        | string | Hat kodu                                               |
| `validatorNo`    | int    | Validator (doğrulayıcı) cihaz numarası             |
| `istikamet`      | string | Sefer istikameti (`G`= Gidiş,`D`= Dönüş)       |

---

## 2. Hat Rota Koordinatları

Hat ID'sine göre hattın gidiş ve dönüş güzergah koordinatlarını döner.

**Endpoint**

```
POST /routecoordinate
```

**Request Body**

| Alan        | Tip    | Açıklama               |
| ----------- | ------ | ------------------------ |
| `keyword` | string | Hat ID (örn.`"1107"`) |

> **Not:** `keyword` değeri hat kodu değil, hat ID'sidir.

**Örnek İstek**

```json
{
  "keyword": "1107"
}
```

**Örnek Yanıt**

```json
{
  "version": 1,
  "statusCode": 200,
  "message": "Success",
  "result": [
    {
      "latitude": "40.17806",
      "logitude": "29.12634",
      "sequence": 0,
      "route": "1107",
      "routeDirection": "G"
    },
    {
      "latitude": "40.2544298675",
      "logitude": "28.9591998607",
      "sequence": 0,
      "route": "1107",
      "routeDirection": "D"
    }
  ]
}
```

**Yanıt Alanları**

| Alan               | Tip    | Açıklama                                                              |
| ------------------ | ------ | ----------------------------------------------------------------------- |
| `latitude`       | string | Enlem (latitude)                                                        |
| `logitude`       | string | Boylam (longitude) — API'den `logitude`olarak gelir (yazım hatası) |
| `sequence`       | int    | Koordinat sıra numarası                                               |
| `route`          | string | Hat ID                                                                  |
| `routeDirection` | string | Güzergah yönü (`G`= Gidiş,`D`= Dönüş)                        |

---

## 3. Hat Durak Listesi ve Konumları

Hat numarasına göre hattın tüm durak bilgilerini, konumlarını ve yön bilgilerini döner.

**Endpoint**

```
POST /routestat
```

**Request Body**

| Alan          | Tip | Açıklama                    |
| ------------- | --- | ----------------------------- |
| `routeCode` | int | Hat numarası (örn.`1107`) |

**Örnek İstek**

```json
{
  "routeCode": 1107
}
```

**Örnek Yanıt**

```json
{
  "version": 1,
  "statusCode": 200,
  "message": "Success",
  "result": [
    {
      "stopId": 5933,
      "stopName": "SİTELER HAREKET MERKEZİ 2",
      "sequence": 1,
      "latitude": "40.17806",
      "longitude": "29.12634",
      "direction": "G"
    },
    {
      "stopId": 1074,
      "stopName": "EMEK 2",
      "sequence": 1,
      "latitude": "40.25443",
      "longitude": "28.9592",
      "direction": "D"
    }
  ]
}
```

**Yanıt Alanları**

| Alan          | Tip    | Açıklama                                       |
| ------------- | ------ | ------------------------------------------------ |
| `stopId`    | int    | Durak benzersiz ID'si                            |
| `stopName`  | string | Durak adı                                       |
| `sequence`  | int    | Duraktaki sıra numarası                        |
| `latitude`  | string | Durak enlemi                                     |
| `longitude` | string | Durak boylamı                                   |
| `direction` | string | Güzergah yönü (`G`= Gidiş,`D`= Dönüş) |

---

## 4. Durağa Göre Sefer Saatleri

Belirli bir hat ve durağın gidiş veya dönüş yönüne göre hafta içi, cumartesi ve pazar sefer saatlerini döner.

**Endpoint**

```
POST /schedulebystop
```

**Request Body**

| Alan               | Tip    | Açıklama                                           |
| ------------------ | ------ | ---------------------------------------------------- |
| `direction`      | string | Güzergah yönü (`"G"`= Gidiş,`"D"`= Dönüş) |
| `routeId`        | int    | Hat ID (örn.`1107`)                               |
| `stopSequenceNo` | int    | Durak sıra numarası                                |
| `weekday`        | int    | Gün filtresi (`0`= tümü)                        |

**Örnek İstek — Gidiş (`G`)**

```json
{
  "direction": "G",
  "routeId": 1107,
  "stopSequenceNo": 0,
  "weekday": 0
}
```

**Örnek Yanıt — Gidiş (`G`)**

Gidiş yönünde sonuç `haftaIci`, `cumartesi` ve `pazar` olarak ayrı ayrı döner:

```json
{
  "version": 1,
  "statusCode": 200,
  "message": "Success!",
  "result": {
    "haftaIci": {
      "days": [1, 2, 3, 4, 5],
      "routeId": 1107,
      "routeCode": "31A",
      "stopTimes": [
        "06:40", "06:50", "06:55", "07:05", "07:15", "07:30", "07:45", "07:55",
        "08:15", "08:40", "09:10", "09:40", "10:10", "10:40", "11:10", "11:40",
        "12:10", "12:40", "13:10", "13:40", "14:10", "14:40", "15:10", "15:30",
        "15:45", "16:00", "16:15", "16:35", "17:00", "17:25", "17:50", "18:15",
        "18:40", "19:10", "19:40", "20:20", "21:00", "21:45", "22:30", "23:20"
      ]
    },
    "cumartesi": {
      "days": [6],
      "routeId": 1107,
      "routeCode": "31A",
      "stopTimes": [
        "06:30", "06:50", "06:55", "07:00", "07:30", "08:00", "08:30", "09:00",
        "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00",
        "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00",
        "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00",
        "21:45", "22:30", "23:15"
      ]
    },
    "pazar": {
      "days": [7],
      "routeId": 1107,
      "routeCode": "31A",
      "stopTimes": [
        "06:30", "06:45", "06:50", "06:55", "07:00", "07:30", "08:00", "08:30",
        "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
        "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
        "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30",
        "21:00", "21:45", "22:30", "23:15"
      ]
    }
  }
}
```

**Örnek İstek — Dönüş (`D`)**

```json
{
  "direction": "D",
  "routeId": 1107,
  "stopSequenceNo": 0,
  "weekday": 0
}
```

**Örnek Yanıt — Dönüş (`D`)**

Dönüş yönünde cumartesi ve pazar ayrı gelmez; `haftaSonu` olarak birleşik döner:

```json
{
  "version": 1,
  "statusCode": 200,
  "message": "Success!",
  "result": {
    "haftaIci": {
      "days": [1, 2, 3, 4, 5],
      "routeId": 1107,
      "routeCode": "31A",
      "stopTimes": [
        "06:30", "06:50", "07:10", "07:25", "07:40", "07:55", "08:10", "08:30",
        "08:55", "09:20", "09:50", "10:20", "10:50", "11:20", "11:50", "12:20",
        "12:50", "13:20", "13:50", "14:20", "14:50", "15:10", "15:30", "15:50",
        "16:10", "16:30", "16:50", "17:10", "17:30", "17:50", "18:15", "18:40",
        "19:10", "19:45", "20:20", "21:00", "21:45", "22:30", "23:15"
      ]
    },
    "haftaSonu": {
      "days": [6, 7],
      "routeId": 1107,
      "routeCode": "31A",
      "stopTimes": [
        "06:30", "06:45", "06:50", "07:25", "07:50", "08:20", "08:45", "09:15",
        "09:45", "10:15", "10:45", "11:15", "11:45", "12:15", "12:45", "13:15",
        "13:45", "14:15", "14:45", "15:15", "15:45", "16:15", "16:45", "17:15",
        "17:45", "18:15", "18:45", "19:15", "19:45", "20:15", "20:45", "21:15",
        "21:45", "22:30", "23:15"
      ]
    }
  }
}
```

**Yanıt Alanları (`result` içindeki her grup)**

| Alan          | Tip      | Açıklama                                                     |
| ------------- | -------- | -------------------------------------------------------------- |
| `days`      | int[]    | Bu gruba ait gün numaraları (1=Pzt, 2=Sal, ... 6=Cmt, 7=Paz) |
| `routeId`   | int      | Hat ID                                                         |
| `routeCode` | string   | Hat kodu                                                       |
| `stopTimes` | string[] | Sefer saatleri listesi (`HH:mm`formatında)                  |

**Gidiş / Dönüş Yönüne Göre Yanıt Yapısı Farkı**

| Yön     | `direction` | Yanıt grupları                                        |
| -------- | ------------- | ------------------------------------------------------- |
| Gidiş   | `"G"`       | `haftaIci`,`cumartesi`,`pazar`(ayrı ayrı)       |
| Dönüş | `"D"`       | `haftaIci`,`haftaSonu`(cumartesi + pazar birleşik) |

---

## Genel Yanıt Yapısı

Tüm endpoint'ler aynı genel yapıyı kullanır:

| Alan           | Tip    | Açıklama                             |
| -------------- | ------ | -------------------------------------- |
| `version`    | int    | API versiyonu                          |
| `statusCode` | int    | HTTP durum kodu (`200`= başarılı) |
| `message`    | string | Durum mesajı (`"Success"`)          |
| `result`     | array  | Sonuç verisi                          |

---

## Notlar

* `istikamet` / `routeDirection` / `direction` alanlarında `G`  **Gidiş** , `D` **Dönüş** yönünü ifade eder.
* `/routecoordinate` endpoint'indeki `logitude` alanı API'den bu şekilde gelmektedir (yazım hatası, `longitude` değil).
* `/realtimedata` ve `/routestat` endpoint'lerinde `keyword` string, `/routestat`'ta ise `routeCode` integer tipindedir.

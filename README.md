# TransitJSON (Spec v1.0)

TransitJSON, toplu taşıma verilerini (statik tarifeler, duraklar, rotalar ve canlı araç konumları) JSON formatında hafif, kolay okunabilir ve esnek bir şekilde temsil etmek için geliştirilmiş modern bir veri standardıdır.

## Şema Yapısı (v1.0)

| Şema | Zorunlu | Açıklama | $ref Bağlantıları |
|------|---------|----------|-------------------|
| **common** | - | Ortak tip tanımları (`trip_type`, `day_type`, `lat`/`lon`, `hex_color`, `currency_code` vb.) | Tüm şemalar buraya referans verir |
| **metadata** | **Evet** | Veri setinin yayıncı, geçerlilik ve TransitJSON versiyon üst bilgisi | common |
| **country** | Hayır | Ülke bilgisi | common |
| **city** | Hayır | Şehir bilgisi | common, country.code |
| **agency** | **Evet** | İşletmeci/Ajans bilgisi | common, city.code |
| **routes** | **Evet** | Hat listesi | common, agency.id |
| **shape** | Hayır | Hat rotası coğrafi çizgisi | common |
| **stops** | **Evet** | Fiziksel duraklar (bağımsız, `route_ids` ile çoklu hat desteği) | common |
| **trips** | **Evet** | Sefer saatleri ve gün tipleri (birden çok kalkış saati desteği) | common |
| **stop_time** | Hayır | Durakların saat bazlı varış/kalkış detayları | common |
| **vehicles** | Canlı Konum API | Canlı araç konumu, hızı ve yönü | common |
| **fare** | Hayır | Bilet tarifesi ve ücret kuralları (hat bazlı fiyatlandırma dahil) | common |

## Sürüm Geçmişi

- **v1.0** — İlk sürüm
  - Tüm field'lar `snake_case` formatında
  - Ortak tipler `common.schema.json#$defs` altında toplandı
  - `stops` artık bağımsız, `route_ids` ile çoklu hat desteği
  - `trips.departure_times` dizi olarak tanımlandı
  - `routes.car_type` enum'u genişletildi
  - Tüm `$id` değerleri URL formatında

---

**Notlar:**

- *vehicles* harici tüm diğer veriler statik JSON dosyası olarak sunulabilir.
- `shape`, `stops`, `trips`, `stop_time`, `vehicles` gidiş (`outbound`), dönüş (`inbound`) ve ring (`loop`) sefer parametrelerini `common.schema.json#$defs/trip_type` üzerinden destekler.
- `transitJsonVersion` alanı en güncel spesifikasyon sürümünü (şu an `1.0`) belirtmek için metadata şemasında zorunludur.

# TransitJSON (Spec v1.0)

TransitJSON, toplu taşıma verilerini (statik tarifeler, duraklar, rotalar ve canlı araç konumları) JSON formatında hafif, kolay okunabilir ve esnek bir şekilde temsil etmek için geliştirilmiş modern bir veri standardıdır.

## Şema Yapısı (v1.0)

* **metadata** - **Zorunlu**, Veri setinin yayıncı, geçerlilik ve TransitJSON versiyon üst bilgisini tutar.
* **country** - Opsiyonel, Ülke üst bilgisi.
* **city** - Opsiyonel, Şehir bilgisi (Ülke ile ref).
* **agency** - Zorunlu, İşletmeci/Ajans bilgisi (Şehir ile ref).
* **routes** - Zorunlu, Hat Listesi (Ajans ile ref, ayrıca sortOrder, status ve directions yön bilgilerini barındırır).
* **shape** - Opsiyonel, Hat rotası coğrafi çizgisi (Routes ile ref).
* **stops** - Zorunlu, Fiziksel duraklar (Bağımsız koordinatlar ve wheelchairAccessible içerir).
* **trips** - Zorunlu, Sefer saatleri ve gün tipleri (Routes ile ref).
* **stop_time** - Opsiyonel, Durakların saat bazlı varış/kalkış detayları (Trips ve Stops ile ref).
* **vehicles** - Canlı Konum API, Canlı araç konumu, hızı ve yönü (Routes ve Trips ile ref).
* **fare** - Opsiyonel, Bilet tarifesi ve ücret kuralları.

---

**Notlar:**

* *vehicles* harici tüm diğer veriler statik JSON dosyası olarak sunulabilir.
* `shape`, `stops`, `trips`, `stop_time`, `vehicles` gidiş (`outbound`), dönüş (`inbound`) ve ring (`loop`) sefer parametrelerini destekler.
* `transitJsonVersion` alanı en güncel spesifikasyon sürümünü (şu an `1.0`) belirtmek için metadata şemasında zorunludur.
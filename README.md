# TransitJSON (Spec v1.0)

TransitJSON, toplu taşıma verilerini (statik tarifeler, duraklar, rotalar ve canlı araç konumları) JSON formatında hafif, kolay okunabilir ve esnek bir şekilde temsil etmek için geliştirilmiş modern bir veri standardıdır.

Detaylı format spesifikasyonu: [`TransitJSON-README.md`](TransitJSON-README.md) · JSON Schema: [`schema/`](schema/)

**shapes.json:** Rota geometrisi encoded polyline değil; doğrudan `{lat, lon}` koordinat dizisidir (`coordinates`).

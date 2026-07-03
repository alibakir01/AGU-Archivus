# BULUT RAG Doğruluk Raporu (Voyage + Pinecone)

- Toplam soru: **50**
- Retrieval (kod bağlamda): **45/50** → **%90.0**
- Cevap doğruluk (keyword): **50/50** → **%100.0**
- Birleşik: **45/50** → **%90.0**
- **LLM-as-judge ortalama: 4.68/5.0** (50 skorlu)
- Judge kabul (≥3/5): **47/50** → **%94.0**
- Ortalama süre: **4.31s**

## Bölüm Bazlı
| Bölüm | N | Retrieval % | KW % | Judge Ort |
|---|---:|---:|---:|---:|
| bilgisayar | 25 | %84 | %100 | 4.56/5 |
| ekonomi | 20 | %100 | %100 | 4.95/5 |
| isletme | 5 | %80 | %100 | 4.20/5 |

## Düşük Skorlu Vakalar (judge < 3) — 3 adet

### `comp_009` (bilgisayar) — **0/5**
**Soru:** COMP 102 dersinin ön şartı nedir?
**Hakem:** Cevap COMP 102'nin ön koşulunu belirtmemiştir.
**Cevap:** _Bilgisayar Mühendisliği 2023, 2021 ve 2016 müfredatlarına göre COMP 102 dersine rastlanmamıştır. Ancak COMP 101 ve COMP 112 gibi dersler mevcuttur. 

COMP 101 ve COMP 112 derslerinin ön şartı ve detayları verilmiştir ancak COMP 102 için bilgi bulunamamıştır. 

İlgili bölüm web sayfasına/yönergeye bakmanızı tavsiye ederim._

### `comp_003` (bilgisayar) — **1/5**
**Soru:** COMP 201 nedir, hangi konuları içerir?
**Hakem:** Cevap COMP 201 dersinin adını/içeriğini belirtmemiştir.
**Cevap:** _2023 Bilgisayar Mühendisliği müfredatı hakkında bilgi veremem, ancak 2016 müfredatına göre;

COMP 201 Yazılım Mühendisliği dersinin içeriği hakkında bilgi bulunmamaktadır. 

2021 Bilgisayar Mühendisliği müfredatına göre; 

COMP 202 Yazılım Mühendisliği dersi 4. dönemde (2. sınıf Bahar) Teorik: 3, Lab: 0, Kredi: 3, AKTS: 7. Ön şartı: COMP 101 dir.

2016 Bilgisayar Mühendisliği müfredatına göre; 

C_

### `ba_004` (isletme) — **1/5**
**Soru:** BA 101 nedir?
**Hakem:** Cevap yüzeyseldir, çünkü sadece 'bilmiyorum' demekte ve daha fazla bilgi için bir kaynak önermektedir, ancak BA 101 dersinin adını ve özelliklerini belirtmemektedir.
**Cevap:** _Merhaba! BA 101 hakkında bilgi veremiyorum çünkü İşletme 2025 Müfredatı'nda böyle bir ders bulunmuyor. 

Derslerle ilgili daha detaylı bilgi için 2025 İşletme Müfredatı'na veya İşletme Bölümü web sayfasına bakmanızı tavsiye ederim._

"""
GPA / CGPA hesaplayıcı — müfredat verisinden ders listesi yükler ve
kullanıcı girdilerinden ortalama hesaplar. Tekrar dersi (latest-grade-wins),
müfredat dışı ders, Pass/Fail dersleri destekler.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"

# 11-li harf sistemi (4.0 üzerinden)
# AGÜ resmi katsayılar (Lisans Eğitim-Öğretim ve Sınav Yönetmeliği not tablosu):
# A- = 3.67, B+ = 3.33 ... (yuvarlanmış 3.7/3.3 DEĞİL — ⅓'lük kesirler)
GRADE_PTS: dict[str, float] = {
    "A":  4.00, "A-": 3.67,
    "B+": 3.33, "B":  3.00, "B-": 2.67,
    "C+": 2.33, "C":  2.00, "C-": 1.67,
    "D+": 1.33, "D":  1.00,
    "F":  0.00,
}
GRADE_OPTIONS: list[str] = [
    "—", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F"
]
PASSING: set[str] = {"A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D"}
FAILING: set[str] = {"F"}

# AGÜ Onur eşikleri (yönetmelik kontrol edilmeli — geçici varsayılan)
ONOR_THRESHOLD = 3.00
YUKSEK_ONOR_THRESHOLD = 3.50

# Default Pass/Fail (GPA'ya katılmaz, kullanıcı toggle edebilir)
DEFAULT_PF_PATTERNS = [
    r"\bSTAJ",                       # Staj, Stajı, Stajları (Türkçe ekler)
    r"\bINTERNSHIP\b",              # ME 311/411, ECON 499
    r"\bPRACTICE\b",               # Summer Practice, Workplace Practice
    r"\bTRAINING\b",               # IE 197/297/397 Summer Training
    r"\bWORKPLACE\s*EXPERIENCE\b",
    r"^CP\s*\d+",                  # CP 100 Kariyer Planlama
]

EXTRA_TYPES = ["None", "Tekrar/Yükseltme", "Yatay geçiş", "Eski müfredat (intibak)", "Yaz okulu", "Diğer"]


def _to_int(v, default: int = 0) -> int:
    try:
        return int(float(str(v).strip()))
    except (ValueError, TypeError, AttributeError):
        return default


def _jsonl_signature() -> tuple:
    """processed/*.jsonl dosyalarının (ad, mtime) imzası. Dosya değişince cache
    tazelenir — böylece ingest sonrası app'i yeniden başlatmaya gerek kalmaz."""
    sig = []
    for p in sorted(PROCESSED_DIR.glob("*.jsonl")):
        try:
            sig.append((p.name, p.stat().st_mtime_ns))
        except OSError:
            pass
    return tuple(sig)


_mufredat_cache: dict = {"sig": None, "data": ()}


def _all_mufredat_chunks() -> tuple[dict, ...]:
    """Tüm processed/*.jsonl içinden tip='mufredat' kayıtları (mtime-duyarlı cache)."""
    sig = _jsonl_signature()
    if _mufredat_cache["sig"] == sig:
        return _mufredat_cache["data"]
    rows = []
    for jsonl in sorted(PROCESSED_DIR.glob("*.jsonl")):
        try:
            with jsonl.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ch = json.loads(line)
                    except Exception:
                        continue
                    md = ch.get("metadata", {})
                    if md.get("tip") == "mufredat":
                        rows.append(md)
        except Exception:
            continue
    _mufredat_cache["sig"] = sig
    _mufredat_cache["data"] = tuple(rows)
    return _mufredat_cache["data"]


def available_curricula(bolum: str) -> list[str]:
    """Bir bölüm için seçilebilir müfredat yıllarını döndür (sıralı)."""
    years: set[str] = set()
    for md in _all_mufredat_chunks():
        if md.get("bolum") == bolum:
            y = md.get("mufredat_yili")
            if y:
                years.add(str(y))
    return sorted(years)


def load_courses(bolum: str, mufredat_yili: str) -> list[dict]:
    """Belirli bölüm + müfredat yılına ait derslerin tekil listesi.
    Eksik kredi/AKTS, aynı dersin genel katalogdaki dolu kaydından tamamlanır
    (ör. MATH 101 bir bölümde boş girilmişse başka bölümdeki 5 kredi'den alınır).
    Staj/uygulama gibi doğal 0-kredili (Pass/Fail) dersler zenginleştirilmez."""
    catalog = all_courses_catalog()
    rows: list[dict] = []
    seen_counts: dict[str, int] = {}
    for md in _all_mufredat_chunks():
        if md.get("bolum") != bolum:
            continue
        if str(md.get("mufredat_yili")) != str(mufredat_yili):
            continue
            
        base_kod = (md.get("ders_kodu") or "").strip()
        if not base_kod:
            continue
        # Geçerli ders kodu en az bir HARF içerir (ör. "COMP 101"). Sadece rakamdan
        # oluşanlar (ör. tablo toplam satırından sızan "143") çöptür, atla.
        if not re.search(r"[A-Za-z]", base_kod):
            continue

        donem = _to_int(md.get("donem"), 99)
        
        # Seçmeli/Havuz dersleri (kodunda X geçenler) her dönem farklı sayılır
        if "X" in base_kod.upper():
            sezon = "Güz" if donem % 2 != 0 else "Bahar"
            kod_prefix = f"{base_kod} ({sezon})"
            seen_counts[kod_prefix] = seen_counts.get(kod_prefix, 0) + 1
            if seen_counts[kod_prefix] > 1:
                kod = f"{kod_prefix}-{seen_counts[kod_prefix]}"
            else:
                kod = kod_prefix
        else:
            kod = base_kod
            if kod in seen_counts:
                continue
            seen_counts[kod] = 1
            
        kredi = _to_int(md.get("kredi"), 0)
        akts = _to_int(md.get("akts"), 0)
        ders_adi = md.get("ders_adi", "")
        # Eksik kredi/AKTS'yi katalogdan tamamla (havuz X'li dersler ve doğal
        # 0-kredili staj/uygulama dersleri hariç)
        if (kredi == 0 or akts == 0) and "X" not in base_kod.upper() \
                and not is_default_pf(base_kod, ders_adi):
            cat = catalog.get(base_kod.upper())
            if cat:
                if kredi == 0:
                    kredi = _to_int(cat.get("kredi"), 0)
                if akts == 0:
                    akts = _to_int(cat.get("akts"), 0)

        rows.append({
            "ders_kodu": kod,
            "ders_adi": ders_adi,
            "kredi": kredi,
            "akts": akts,
            "donem": donem,
        })
    rows.sort(key=lambda r: (r["donem"], r["ders_kodu"]))
    return rows


# Catalog'a dahil edilecek chunk tipleri (zorunlu + seçmeli + katalog kayıtları)
CATALOG_TIPS = {
    "mufredat",
    "secmeli_ders",       # malzeme teknik seçmeli
    "secmeli_havuz",      # EE/IE seçmeli havuz dersleri
    "teknik_secmeli",     # comp/ee teknik seçmeli
    "glb_ortak_secmeli",  # GLB ortak seçmeli
    "ders_katalog",       # ders kataloglarından
    "syllabus",           # IE staj syllabus'ları
}


_catalog_cache: dict = {"sig": None, "data": None}


def all_courses_catalog() -> dict[str, dict]:
    """Tüm bölümlerin tüm müfredat + seçmeli + katalog kayıtlarındaki dersler.
    Anahtar: DERS_KODU (büyük harf). Aynı kod birden fazla yerde varsa daha
    zengin bilgi (kredi/AKTS dolu olan) tercih edilir. Placeholder kodlar
    (içinde 'X' olanlar — örn. MSNETX1, GLB 1XX) hariç tutulur.
    (mtime-duyarlı cache — ingest sonrası app restart gerekmez.)"""
    sig = _jsonl_signature()
    if _catalog_cache["sig"] == sig and _catalog_cache["data"] is not None:
        return _catalog_cache["data"]
    catalog: dict[str, dict] = {}
    for jsonl in sorted(PROCESSED_DIR.glob("*.jsonl")):
        try:
            with jsonl.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ch = json.loads(line)
                    except Exception:
                        continue
                    md = ch.get("metadata", {})
                    if md.get("tip") not in CATALOG_TIPS:
                        continue
                    kod = (md.get("ders_kodu") or "").strip().upper()
                    if not kod or "X" in kod:
                        continue
                    # Geçerli kod en az bir harf içerir; sadece rakamsa (tablo
                    # toplam satırı sızıntısı, ör. "143") çöptür → atla.
                    if not re.search(r"[A-Za-z]", kod):
                        continue
                    kredi = _to_int(md.get("kredi"), 0)
                    akts = _to_int(md.get("akts"), 0)
                    cur = catalog.get(kod)
                    # İlk kayıt veya mevcut kayıt eksikse (kredi=0/AKTS=0) zenginiyle değiştir
                    if cur is None:
                        catalog[kod] = {
                            "ders_kodu": kod,
                            "ders_adi": md.get("ders_adi", ""),
                            "kredi": kredi,
                            "akts": akts,
                            "bolum": md.get("bolum", ""),
                            "tip": md.get("tip", ""),
                        }
                    else:
                        if (cur.get("kredi", 0) == 0 and kredi > 0) or \
                           (cur.get("akts", 0) == 0 and akts > 0):
                            catalog[kod] = {
                                "ders_kodu": kod,
                                "ders_adi": cur.get("ders_adi") or md.get("ders_adi", ""),
                                "kredi": max(cur.get("kredi", 0), kredi),
                                "akts": max(cur.get("akts", 0), akts),
                                "bolum": cur.get("bolum") or md.get("bolum", ""),
                                "tip": cur.get("tip") or md.get("tip", ""),
                            }
        except Exception:
            continue
    _catalog_cache["sig"] = sig
    _catalog_cache["data"] = catalog
    return catalog


def is_default_pf(ders_kodu: str, ders_adi: str) -> bool:
    text = f"{(ders_kodu or '').upper()} {(ders_adi or '').upper()}"
    return any(re.search(p, text) for p in DEFAULT_PF_PATTERNS)


def courses_for_year(bolum: str, mufredat_yili: str, sinif: int, donem: int = 0) -> list[dict]:
    """1-4 arası bir sınıf için o sınıfa ait dersleri (donem 2*sinif-1 ve 2*sinif)
    döndürür. sinif=0 → tüm dersler. donem != 0 ise sadece o dönemi döndürür."""
    courses = load_courses(bolum, mufredat_yili)
    if sinif == 0 and donem == 0:
        return courses
    if donem != 0:
        return [c for c in courses if c.get("donem") == donem]
    target_donems = {sinif * 2 - 1, sinif * 2}
    return [c for c in courses if c.get("donem") in target_donems]


def compute_combined(prev_cgpa: float, prev_credits: int, entries: list[dict]) -> dict:
    """Bu dönemin ortalamasını ve önceki CGPA ile birleşik yeni CGPA'yı döndürür.

    AGÜ MADDE 30: GNO = Σ(AKTS × katsayı) / Σ(AKTS) — ağırlık KREDİ değil AKTS'dir.
    Bu yüzden prev_credits parametresi = ÖNCEKİ TOPLAM AKTS.

    entries: [{ders_kodu, kredi, akts, not, pf, eski_not?}]
    - Aynı ders_kodu birden fazla geçerse SON girdi kullanılır.
    - pf=True olanlar ortalama hesabına KATILMAZ ama sayıma/AKTS'ye girer.
    - eski_not GEÇERLİ bir harf notu ise ders TEKRAR/YÜKSELTME sayılır: GNO'da
      ders TEK kez yer alır; eski notun katkısı çıkar, yeni not girer, AKTS
      denominatöre TEKRAR eklenmez (AGÜ: son alınan not geçerli).
    """
    by_code: dict[str, dict] = {}
    for e in entries:
        kod = (e.get("ders_kodu") or "").strip().upper()
        if kod:
            by_code[kod] = e

    # Dönem ortalaması — bu dönem alınan HER ders (yeni + tekrar), yeni notuyla, AKTS ağırlıklı
    term_pts = 0.0
    term_w = 0            # dönem ortalaması denominatörü (AKTS)
    # CGPA katkısı
    cum_pts_add = 0.0     # yeni derslerin puanı
    cum_w_add = 0         # yeni derslerin AKTS'si (kümülatif denominatöre eklenir)
    retake_delta = 0.0    # tekrar derslerinin (yeni-eski) puan düzeltmesi
    sem_akts_earned = 0   # bu dönem YENİ kazanılan AKTS (geçilen, tekrar olmayan)
    sem_passed = 0
    sem_failed = 0

    for kod, e in by_code.items():
        not_ = (e.get("not") or "").strip()
        if not_ in ("", "—"):
            continue
        akts = _to_int(e.get("akts"), 0)
        pf = bool(e.get("pf"))
        eski_not = (e.get("eski_not") or "").strip()
        is_retake = eski_not in GRADE_PTS

        if not pf and not_ in GRADE_PTS:
            new_pts = GRADE_PTS[not_] * akts
            term_pts += new_pts          # dönem: bu ders bu dönem alındı
            term_w += akts
            if is_retake:                # kümülatif: eski çıkar, yeni gir; AKTS eklenmez
                retake_delta += new_pts - GRADE_PTS[eski_not] * akts
            else:
                cum_pts_add += new_pts
                cum_w_add += akts

        if not_ in PASSING:
            sem_passed += 1
            if not is_retake:            # tekrar dersinin AKTS'si zaten kazanılmıştı
                sem_akts_earned += akts
        elif not_ in FAILING:
            sem_failed += 1

    sem_gpa = (term_pts / term_w) if term_w > 0 else 0.0

    prev_w = max(0, prev_credits)
    total_w = prev_w + cum_w_add
    if total_w > 0:
        new_cgpa = (max(0.0, prev_cgpa) * prev_w + cum_pts_add + retake_delta) / total_w
    else:
        new_cgpa = prev_cgpa

    if new_cgpa >= YUKSEK_ONOR_THRESHOLD:
        onor = "🥇 Yüksek Onur"
    elif new_cgpa >= ONOR_THRESHOLD:
        onor = "🥈 Onur"
    else:
        onor = ""

    return {
        "sem_gpa": round(sem_gpa, 2),
        "sem_credits": term_w,           # dönem ortalaması ağırlığı (AKTS)
        "sem_akts": sem_akts_earned,     # bu dönem yeni kazanılan AKTS
        "sem_passed": sem_passed,
        "sem_failed": sem_failed,
        "new_cgpa": round(new_cgpa, 2),
        "prev_cgpa": round(max(0.0, prev_cgpa), 2),
        "prev_credits": prev_w,          # önceki toplam AKTS
        "total_credits": total_w,        # yeni toplam AKTS
        "course_count": len(by_code),
        "onor": onor,
    }


def compute_gpa(entries: list[dict]) -> dict:
    """entries: list of {ders_kodu, kredi, akts, not, pf}.
    AGÜ MADDE 30: ortalama AKTS ağırlıklı — Σ(AKTS × katsayı) / Σ(AKTS).
    Aynı ders_kodu birden fazla geçerse SON girdi kazanır (tekrar dersi mantığı).
    pf=True ise ortalamaya KATILMAZ ama kazanılan kredi/AKTS sayılır.
    """
    by_code: dict[str, dict] = {}
    for e in entries:
        kod = (e.get("ders_kodu") or "").strip().upper()
        if not kod:
            continue
        by_code[kod] = e  # last-write-wins

    gpa_pts_sum = 0.0
    gpa_cred_sum = 0        # ortalama denominatörü — AKTS
    earned_credits = 0
    earned_akts = 0
    passed = 0
    failed = 0

    for kod, e in by_code.items():
        not_ = (e.get("not") or "").strip()
        if not_ in ("", "—"):
            continue
        kredi = _to_int(e.get("kredi"), 0)
        akts = _to_int(e.get("akts"), 0)
        pf = bool(e.get("pf"))
        is_pass = not_ in PASSING

        if not pf and not_ in GRADE_PTS:
            gpa_pts_sum += GRADE_PTS[not_] * akts   # ağırlık: AKTS
            gpa_cred_sum += akts

        if is_pass:
            earned_credits += kredi
            earned_akts += akts
            passed += 1
        elif not_ in FAILING:
            failed += 1

    gpa = (gpa_pts_sum / gpa_cred_sum) if gpa_cred_sum > 0 else 0.0

    if gpa >= YUKSEK_ONOR_THRESHOLD:
        onor = "🥇 Yüksek Onur"
    elif gpa >= ONOR_THRESHOLD:
        onor = "🥈 Onur"
    else:
        onor = ""

    return {
        "gpa": round(gpa, 2),
        "gpa_credits": gpa_cred_sum,
        "earned_credits": earned_credits,
        "earned_akts": earned_akts,
        "passed_count": passed,
        "failed_count": failed,
        "course_count": len(by_code),
        "onor": onor,
    }

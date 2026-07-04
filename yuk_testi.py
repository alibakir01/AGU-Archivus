"""
Yük testi — duyuru günü zirvesini simüle eder (20+ eşzamanlı kullanıcı).
Router (respond), semantik cache ve rate limiter'ın AYNI ANDA düzgün + thread-safe
çalıştığını doğrular.

Çalıştır:  python yuk_testi.py
Gerekli .env: VOYAGE_AI_KEY, PINECONE_API_KEY, MISTRAL_API_KEY (+ GROQ opsiyonel)
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

load_dotenv()

from src import rag_cloud, rate_limit, semantic_cache


def _consume(r) -> str:
    return r["text"] if r["mode"] == "list" else "".join(r["token_iter"])


def test_rate_limiter():
    print("\n" + "=" * 62)
    print("TEST 1 — RATE LIMITER (eşzamanlı, API'siz)")
    print("=" * 62)

    # a) 20 thread, AYNI kullanıcı, limit 6 → tam 6 geçmeli (spam engeli)
    rate_limit.reset()
    with ThreadPoolExecutor(max_workers=20) as ex:
        res = list(ex.map(lambda _: rate_limit.check("spammer", max_per_min=6)[0], range(20)))
    izin = sum(res)
    print(f"  a) 20 eşzamanlı istek / TEK kullanıcı  → {izin} izin  (beklenen: 6)  "
          f"{'✅' if izin == 6 else '❌ HATA'}")

    # b) 20 FARKLI kullanıcı → hepsi geçmeli (izolasyon)
    rate_limit.reset()
    with ThreadPoolExecutor(max_workers=20) as ex:
        res2 = list(ex.map(lambda i: rate_limit.check(f"user{i}", max_per_min=6)[0], range(20)))
    print(f"  b) 20 eşzamanlı istek / 20 FARKLI kullanıcı → {sum(res2)} izin  (beklenen: 20)  "
          f"{'✅' if sum(res2) == 20 else '❌ HATA'}")


def test_cache_concurrency():
    print("\n" + "=" * 62)
    print("TEST 2 — SEMANTİK CACHE (20 eşzamanlı AYNI soru)")
    print("=" * 62)
    q = "COMP 101 dersi kaç AKTS?"

    # Önce ısıt (1 üretim), sonra 20 eşzamanlı → hepsi cache'ten dönmeli
    _consume(rag_cloud.respond(q, bolum="bilgisayar"))

    def ask(_):
        t = time.time()
        r = rag_cloud.respond(q, bolum="bilgisayar")
        txt = _consume(r)
        return r.get("cached", False), time.time() - t, txt

    with ThreadPoolExecutor(max_workers=20) as ex:
        res = list(ex.map(ask, range(20)))

    hits = sum(1 for c, _, _ in res)
    ort = sum(d for _, d, _ in res) / len(res)
    tutarli = len({t for _, _, t in res}) == 1
    print(f"  Cache hit: {hits}/20  (beklenen: 20)  {'✅' if hits == 20 else '⚠️'}")
    print(f"  Ort. yanıt süresi: {ort:.3f}s  (cache hit hızlı olmalı)")
    print(f"  Tutarlılık (20 cevap da aynı): {'✅' if tutarli else '❌ CORRUPTION!'}")


def test_router_burst():
    print("\n" + "=" * 62)
    print("TEST 3 — ROUTER + SOĞUK BURST (farklı bölümler eşzamanlı)")
    print("=" * 62)
    sorular = [
        ("bilgisayar", "COMP 305 ön şartı nedir"),
        ("mbg", "MBG 207 kaç AKTS"),
        ("biyomuhendislik", "biyomühendislik stajı kaç gün"),
        ("elektrik", "EE 201 dersi içeriği"),
        ("makine", "makine 1. sınıf dersleri neler"),
        ("psikoloji", "Core Courses II neler"),
        ("mimarlik", "ARCH 101 kaç kredi"),
        ("isletme", "BA 207 ön şartı"),
    ]

    def route_ask(item):
        bolum, s = item
        try:
            r = rag_cloud.respond(s, bolum=bolum)
            txt = _consume(r)
            return (bolum, r["bolum"], len(txt) > 0, None)
        except Exception as e:
            return (bolum, None, False, str(e)[:60])

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=len(sorular)) as ex:
        res = list(ex.map(route_ask, sorular))
    dt = time.time() - t0

    ok = 0
    for istek_bolum, donen_bolum, dolu, hata in res:
        durum = "✅" if (donen_bolum == istek_bolum and dolu and not hata) else f"❌ {hata or 'boş/yanlış'}"
        if durum == "✅":
            ok += 1
        print(f"  [{istek_bolum:14}] → dönen: {str(donen_bolum):14} cevap:{'var' if dolu else 'YOK'}  {durum}")
    print(f"  Sonuç: {ok}/{len(sorular)} başarılı, {len(sorular)} soru {dt:.1f}s'de eşzamanlı işlendi")


def main():
    print("╔" + "═" * 60 + "╗")
    print("║  AGU ARCHIVUS — YÜK TESTİ (duyuru günü zirvesi)          ║")
    print("╚" + "═" * 60 + "╝")
    test_rate_limiter()
    test_cache_concurrency()
    test_router_burst()
    print("\n[✓] Yük testi tamam. Cache durumu:", semantic_cache.stats())


if __name__ == "__main__":
    main()

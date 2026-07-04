"""
Semantik cache ön-ısıtma — her bölümün öneri sorularını (SUGGESTIONS, 13×4=52)
önceden cevaplayıp embedding'leriyle birlikte data/answer_cache.json'a yazar.

Bulut açılışında rag_cloud/semantic_cache bu dosyayı yükler → en sık tıklanan
sorular ilk kullanıcıdan itibaren ANINDA gelir (retrieval + LLM harcamadan).

Çalıştır (deploy'dan önce, yerelde):
    python prewarm_cache.py
Gerekli .env: VOYAGE_AI_KEY, PINECONE_API_KEY, MISTRAL_API_KEY (+ opsiyonel GROQ)

NOT: Üretilen data/answer_cache.json repoya COMMIT edilmeli (bulut okuyabilsin).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

# Cache'i üretim sırasında DEVRE DIŞI bırak — respond() temiz (cache'siz) cevap
# üretsin; biz sonucu manuel kaydedelim. (semantic_cache import'tan ÖNCE.)
os.environ["SEM_CACHE"] = "0"

from dotenv import load_dotenv

load_dotenv()

from src import rag_cloud
from src.ui_theme import SUGGESTIONS

OUT = Path(__file__).resolve().parent / "data" / "answer_cache.json"


def main():
    for key in ("VOYAGE_AI_KEY", "PINECONE_API_KEY"):
        if not os.getenv(key):
            raise SystemExit(f"[HATA] {key} .env'de tanımlı değil.")

    records: list[dict] = []
    toplam = sum(len(v) for v in SUGGESTIONS.values())
    i = 0
    for bolum, sugs in SUGGESTIONS.items():
        for _icon, soru in sugs:
            i += 1
            try:
                r = rag_cloud.respond(soru, bolum=bolum)
                cevap = r["text"] if r["mode"] == "list" else "".join(r["token_iter"])
                # Yalnız LLM cevaplarını ısıt (liste modu zaten deterministik/hızlı)
                if r["mode"] != "llm" or not (cevap or "").strip():
                    print(f"  [{i}/{toplam}] [{bolum}] atlandı (liste modu): {soru[:45]}")
                    continue
                emb = rag_cloud.embed_question(soru)
                records.append({
                    "bolum": bolum, "question": soru, "answer": cevap, "embedding": emb,
                })
                print(f"  [{i}/{toplam}] [{bolum}] ✓ {soru[:45]}")
            except Exception as e:
                print(f"  [{i}/{toplam}] [{bolum}] HATA ({e}): {soru[:45]}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OK] {len(records)} soru ısıtıldı -> {OUT}")
    print("     Bu dosyayı repoya commit et; bulut açılışta yükleyip cache'ler.")


if __name__ == "__main__":
    main()

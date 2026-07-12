"""
Semantik answer cache — soru embedding'i kayıtlı bir soruyla yüksek benzerlikte
ise cevabı hazırdan döner (retrieval + LLM atlanır → hız + token tasarrufu).

Sadece BULUT yolu (rag_cloud) için. Bölüm başına bellek-içi depo + kalıcı
ön-ısıtma dosyası (data/answer_cache.json — prewarm_cache.py üretir).

Güvenlik:
  - Kıyas SADECE aynı bölüm içinde (COMP sorusu MBG cache'iyle karışmaz).
  - Yüksek eşik (varsayılan 0.96 kosinüs) → yalnız neredeyse aynı sorular hit alır.
  - TTL (varsayılan 24s) → müfredat değişirse bayat cevap takılıp kalmaz.
  - Süreç yeniden başlayınca bellek sıfırlanır; ön-ısıtma dosyası tekrar yüklenir.
"""
from __future__ import annotations

import json
import math
import os
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_PREWARM_FILE = ROOT / "data" / "answer_cache.json"

_THRESHOLD = float(os.getenv("SEM_CACHE_THRESHOLD", "0.96"))
_TTL = int(os.getenv("SEM_CACHE_TTL", str(24 * 3600)))       # saniye
_MAX_PER_BOLUM = int(os.getenv("SEM_CACHE_MAX", "500"))
_ENABLED = os.getenv("SEM_CACHE", "1").strip().lower() not in ("0", "false", "off", "no")

_lock = threading.Lock()
# bolum -> {"embs": [np.ndarray(d,) normalize], "q": [str], "a": [str], "ts": [float]}
_store: dict[str, dict] = {}
_loaded = False


def enabled() -> bool:
    return _ENABLED


def threshold() -> float:
    return _THRESHOLD


def _normalize(vec) -> list[float]:
    """Vektörü birim uzunluğa getir (saf Python — numpy YOK; ABI/segfault riski yok).
    Böylece kosinüs benzerliği = normalize edilmiş vektörlerin nokta çarpımı."""
    v = [float(x) for x in vec]
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v] if n > 0 else v


def _ensure_loaded() -> None:
    global _loaded
    if _loaded:
        return
    with _lock:
        if _loaded:
            return
        if _PREWARM_FILE.exists():
            try:
                data = json.loads(_PREWARM_FILE.read_text(encoding="utf-8"))
                for rec in data:
                    _add_locked(rec["bolum"], rec["embedding"], rec["question"],
                                rec["answer"], ts=time.time())
            except Exception:
                pass
        _loaded = True


def _add_locked(bolum: str, emb, question: str, answer: str, ts: float) -> None:
    e = _store.setdefault(bolum, {"embs": [], "q": [], "a": [], "ts": []})
    e["embs"].append(_normalize(emb))
    e["q"].append(question)
    e["a"].append(answer)
    e["ts"].append(ts)
    # Bölüm başına sınır: en eskiyi at (FIFO)
    if len(e["q"]) > _MAX_PER_BOLUM:
        for key in ("embs", "q", "a", "ts"):
            e[key].pop(0)


def lookup(bolum: str, emb, threshold: float | None = None) -> str | None:
    """Aynı bölümde benzerlik >= eşik olan kayıtlı cevabı döndür; yoksa None."""
    if not _ENABLED or not bolum:
        return None
    _ensure_loaded()
    thr = _THRESHOLD if threshold is None else threshold
    with _lock:
        e = _store.get(bolum)
        if not e or not e["q"]:
            return None
        q = _normalize(emb)
        # Kosinüs = normalize edilmiş vektörlerin nokta çarpımı (saf Python)
        best_sim = -2.0
        best_i = -1
        for i, v in enumerate(e["embs"]):
            s = 0.0
            for a, b in zip(v, q):
                s += a * b
            if s > best_sim:
                best_sim = s
                best_i = i
        if best_i >= 0 and best_sim >= thr and (time.time() - e["ts"][best_i]) <= _TTL:
            return e["a"][best_i]
    return None


def add(bolum: str, emb, question: str, answer: str) -> None:
    """Yeni (soru, cevap) çiftini cache'e ekle (bellek-içi)."""
    if not _ENABLED or not bolum or not (answer or "").strip():
        return
    _ensure_loaded()
    with _lock:
        _add_locked(bolum, emb, question, answer, ts=time.time())


def stats() -> dict:
    _ensure_loaded()
    with _lock:
        return {b: len(e["q"]) for b, e in _store.items()}

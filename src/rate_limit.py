"""
Basit sunucu-içi sliding-window rate limit — kullanıcı başına dakikada N istek.

Streamlit'ten bağımsız (test edilebilir). Tek süreçte modül-global sözlükte tutulur;
Streamlit Community Cloud tek process çalıştırdığı için tüm oturumlar bunu paylaşır.
Amaç: bir öğrenci hızlı hızlı spam yapıp ortak API kotasını (Mistral/Groq/Voyage/
Pinecone) tüketmesin.

NOT: Bellek-içi olduğu için process yeniden başlayınca sıfırlanır; kalıcı/dağıtık
bir çözüm değildir — "basit" koruma amaçlıdır.
"""
from __future__ import annotations

import threading
import time

_WINDOW_S = 60.0          # kayan pencere (saniye)
_MAX_KEYS = 5000          # bellek koruması: bundan fazla farklı anahtar olursa temizle

_lock = threading.Lock()
_hits: dict[str, list[float]] = {}


def check(client_id: str, max_per_min: int = 6) -> tuple[bool, int]:
    """Bir isteği değerlendirir.

    Dönüş: (izin_var_mi, kalan_saniye)
      - izin_var_mi True ise istek KAYDEDİLİR (sayaca eklenir).
      - engellendiyse kalan_saniye = pencerenin boşalmasına kaç saniye kaldığı.
    """
    now = time.time()
    with _lock:
        if len(_hits) > _MAX_KEYS:          # nadir; basit temizlik
            _hits.clear()
        ts = [t for t in _hits.get(client_id, ()) if now - t < _WINDOW_S]
        if len(ts) >= max_per_min:
            retry = int(_WINDOW_S - (now - ts[0])) + 1
            _hits[client_id] = ts           # eski (temizlenmiş) listeyi geri yaz
            return False, max(retry, 1)
        ts.append(now)
        _hits[client_id] = ts
        return True, 0


def reset(client_id: str | None = None) -> None:
    """Test/yönetim için sayaçları sıfırla (None ise tümü)."""
    with _lock:
        if client_id is None:
            _hits.clear()
        else:
            _hits.pop(client_id, None)

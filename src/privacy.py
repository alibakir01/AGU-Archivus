"""
Kullanıcı girdisindeki kişisel bilgileri (TC kimlik no, öğrenci no, telefon,
e-posta adresi) maskeler.

Basit yaklaşım:
  - 7+ haneli ardışık rakam dizileri gizlenir (TC 11, öğrenci no ~8-10, telefon
    10-11 hane). Müfredat sorularındaki yıl (4 hane: 2023), ders kodu (2-3 hane:
    101), AKTS (1-2 hane) etkilenmez.
  - E-posta adresleri gizlenir (yerel kısım ve alan adı ●'lenir, @ korunur).

Maskeleme LLM'e gönderilmeden, ekranda gösterilmeden ve feedback'e kaydedilmeden
ÖNCE uygulanır — yani kişisel veri hiçbir yere sızmaz.

Sınırlama: aralıklı yazılan numaraları ("123 456 789 01") tek parça saymaz;
"basit" koruma amaçlıdır, tam bir DLP değildir.
"""
from __future__ import annotations

import re

# 7+ ardışık rakam: TC / öğrenci no / telefon / IBAN parçası vb.
_LONG_DIGITS_RE = re.compile(r"\b\d{7,}\b")
# E-posta adresi
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def _mask_email(m: re.Match) -> str:
    """E-postayı gizle ama @ işaretini koru: 'ali@gmail.com' -> '●●●@●●●●●●●●●'."""
    s = m.group()
    at = s.find("@")
    local = "●" * max(len(s[:at]), 3)
    domain = "●" * max(len(s[at + 1:]), 3)
    return f"{local}@{domain}"


def mask_personal_info(text: str) -> str:
    """Metindeki e-posta ve uzun rakam dizilerini ● ile maskeler."""
    if not text:
        return text
    # Önce e-posta (içindeki rakamlar ayrıca maskelenmesin diye)
    text = _EMAIL_RE.sub(_mask_email, text)
    text = _LONG_DIGITS_RE.sub(lambda m: "●" * len(m.group()), text)
    return text


def has_personal_info(text: str) -> bool:
    """Metinde maskelenecek bir bilgi (e-posta veya uzun rakam) var mı? (UI uyarısı için)."""
    return bool(text) and bool(_EMAIL_RE.search(text) or _LONG_DIGITS_RE.search(text))

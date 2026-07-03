"""
Feedback'i Google Sheets'e ekler — bulutta KALICI depo (dosya sistemi geçici olduğu
için JSONL kullanılamaz). Streamlit'ten bağımsız (test edilebilir).

Kimlik: Google service account JSON (string) + hedef E-Tablo ID'si.
Kurulum eksikse ASLA exception fırlatmaz; sessizce False döner.

Kurulum özeti (bir kez):
  1) Google Cloud'da proje aç → "Google Sheets API"yi etkinleştir.
  2) Service Account oluştur → JSON anahtar indir.
  3) Bir Google E-Tablo aç, service account e-postasına (client_email) "Editör" paylaş.
  4) JSON'u ve E-Tablo ID'sini Streamlit Secrets'a koy (bkz. secrets.toml.example).
"""
from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache

_HEADER = ["ts", "rating", "bolum", "soru", "cevap", "yorum"]
_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


@lru_cache(maxsize=4)
def _worksheet(creds_json: str, sheet_id: str):
    """gspread worksheet (ilk sekme). creds_json: service account JSON string.
    lru_cache sayesinde yetkilendirme oturum boyunca bir kez yapılır."""
    import gspread
    from google.oauth2.service_account import Credentials

    info = json.loads(creds_json)
    creds = Credentials.from_service_account_info(info, scopes=_SCOPES)
    gc = gspread.authorize(creds)
    ws = gc.open_by_key(sheet_id).sheet1
    # Başlık satırı yoksa ekle (boş tabloya bir kez)
    try:
        if not ws.get_all_values():
            ws.append_row(_HEADER, value_input_option="RAW")
    except Exception:
        pass
    return ws


def log_feedback(
    creds_json: str | None,
    sheet_id: str | None,
    *,
    rating: str,
    bolum: str = "",
    question: str = "",
    answer: str = "",
    comment: str = "",
) -> bool:
    """Feedback satırını E-Tabloya ekler. Başarılıysa True; kurulum yoksa/hata olursa False."""
    if not creds_json or not sheet_id:
        return False
    try:
        ws = _worksheet(creds_json, sheet_id)
        row = [
            datetime.now().isoformat(timespec="seconds"),
            rating,
            bolum or "",
            (question or "")[:1000],
            (answer or "")[:2000],
            (comment or "")[:1000],
        ]
        ws.append_row(row, value_input_option="RAW")
        return True
    except Exception:
        return False

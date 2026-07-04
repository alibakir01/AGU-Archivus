"""
AGÜ Öğrenci Asistanı — bulut arayüzü (Streamlit Community Cloud).

Görsel tema app.py'den (assets/app_style.css + src/ui_theme.py); backend hafif
bulut yolu (src/rag_cloud.py: Voyage + Pinecone, torch YOK). GPA: src/gpa.py.

Çalıştır (yerel):  streamlit run streamlit_app.py
"""
import base64
import json
import os
from pathlib import Path

import streamlit as st

# --------------------------------------------------------------------------- #
# Anahtar köprüsü: Streamlit Cloud secrets.toml -> os.environ (rag_cloud'dan ÖNCE)
# --------------------------------------------------------------------------- #
_KEYS = ["VOYAGE_AI_KEY", "PINECONE_API_KEY", "MISTRAL_API_KEY", "MISTRAL_MODEL",
         "MISTRAL_MODEL_FALLBACK", "GROQ_API_KEY", "GROQ_FAST_LANE_TOKENS",
         "OPENROUTER_API_KEY", "LLM_PROVIDER", "OPENROUTER_MODEL",
         "RATE_LIMIT_PER_MIN", "MAINTENANCE_MODE", "MAINTENANCE_MESSAGE",
         "SEM_CACHE", "SEM_CACHE_THRESHOLD", "SEM_CACHE_TTL"]
try:
    for _k in _KEYS:
        if _k in st.secrets and not os.getenv(_k):
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass

from dotenv import load_dotenv

load_dotenv()

import pandas as pd

from src import feedback_store, gpa, privacy, rag_cloud, rate_limit, ui_theme

# Rate limit: kullanıcı başına dakikada kaç soru (env ile ayarlanabilir)
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "6"))


def _feedback_config() -> tuple[str | None, str | None]:
    """Google Sheets feedback için (creds_json, sheet_id). Yoksa (None, None)."""
    creds_json = None
    sheet_id = os.getenv("FEEDBACK_SHEET_ID")
    try:
        # Yöntem A: [gcp_service_account] TOML tablosu (alan alan)
        if "gcp_service_account" in st.secrets:
            creds_json = json.dumps(dict(st.secrets["gcp_service_account"]))
        # Yöntem B (kolay): JSON dosyasının tüm içeriği tek alanda
        elif "FEEDBACK_GCP_CREDS" in st.secrets:
            creds_json = str(st.secrets["FEEDBACK_GCP_CREDS"])
        if not sheet_id and "FEEDBACK_SHEET_ID" in st.secrets:
            sheet_id = str(st.secrets["FEEDBACK_SHEET_ID"])
    except Exception:
        pass
    if not creds_json:  # yerel/env alternatifi
        creds_json = os.getenv("FEEDBACK_GCP_CREDS")
    return creds_json, sheet_id


def _log_feedback(m: dict, rating: str, comment: str = "") -> bool:
    creds_json, sheet_id = _feedback_config()
    return feedback_store.log_feedback(
        creds_json, sheet_id,
        rating=rating, bolum=m.get("bolum", ""),
        question=m.get("question", ""), answer=m.get("content", ""),
        comment=comment,
    )


def _render_rating(idx: int, m: dict) -> None:
    """Asistan mesajı altına 👍/👎 + (👎 için) yorum kutusu."""
    if m.get("rating"):
        st.caption(f"{'👍' if m['rating'] == 'up' else '👎'} Geri bildirimin için teşekkürler.")
        return
    st.caption("Bu cevap yardımcı oldu mu?")
    cols = st.columns([1, 1, 8])
    if cols[0].button("👍", key=f"up-{idx}", help="Bu cevap işime yaradı"):
        m["rating"] = "up"
        _log_feedback(m, "up")
        st.rerun()
    if cols[1].button("👎", key=f"down-{idx}", help="Bu cevap yetersiz / yanlış"):
        st.session_state[f"_down_{idx}"] = True
    if st.session_state.get(f"_down_{idx}"):
        comment = st.text_input(
            "Neyin eksik/yanlış olduğunu yazar mısın? (opsiyonel)",
            key=f"cmt-{idx}", placeholder="Örn: ön şartı yanlış söyledi",
        )
        if st.button("Gönder", key=f"send-{idx}", type="primary"):
            m["rating"] = "down"
            _log_feedback(m, "down", comment or "")
            st.session_state.pop(f"_down_{idx}", None)
            st.rerun()


def _client_id() -> str:
    """Kullanıcı kimliği: önce IP (refresh'e dayanıklı), yoksa oturum bazlı kimlik."""
    try:
        headers = st.context.headers  # Streamlit >= 1.37
        ip = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for")
        if ip:
            return ip.split(",")[0].strip()
    except Exception:
        pass
    # IP alınamazsa (yerel/eski sürüm) oturuma özel rastgele kimlik
    if "_client_uid" not in st.session_state:
        import uuid
        st.session_state["_client_uid"] = uuid.uuid4().hex
    return st.session_state["_client_uid"]

# --------------------------------------------------------------------------- #
# Sayfa + tema
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="AGÜ Öğrenci Asistanı", page_icon="🎓",
                   layout="wide", initial_sidebar_state="expanded")

# --------------------------------------------------------------------------- #
# Bakım modu / kill switch — Secrets'ta MAINTENANCE_MODE="1" yapıp Reboot deyince
# kullanıcılar hata/stack trace yerine kibar bir "bakımdayız" ekranı görür.
# Kapatmak için MAINTENANCE_MODE="0" (ya da sil) + Reboot. En erken noktada çalışır.
# --------------------------------------------------------------------------- #
if os.getenv("MAINTENANCE_MODE", "").strip().lower() in ("1", "true", "on", "yes", "evet"):
    _msg = os.getenv("MAINTENANCE_MESSAGE") or "Bakımdayız, birazdan döneriz 🙂"
    st.markdown(
        '<div style="text-align:center;max-width:520px;margin:12vh auto 0;padding:2rem 1.5rem;">'
        '<div style="font-size:3.4rem;line-height:1;">🛠️</div>'
        f'<h2 style="margin:1rem 0 .4rem;color:#B21E55;">{_msg}</h2>'
        '<p style="opacity:.7;font-size:1rem;">AGU Archivus şu an kısa bir bakımda. '
        'Lütfen birazdan tekrar dene.</p></div>',
        unsafe_allow_html=True,
    )
    st.stop()

# Tema: aydınlık (VARSAYILAN) veya koyu. Sidebar'daki toggle session_state'i günceller.
theme = st.session_state.get("theme", "light")
st.markdown(ui_theme.global_css(), unsafe_allow_html=True)
st.markdown(ui_theme.theme_css(theme), unsafe_allow_html=True)

# Tema switch — sağ üstte sabit, küçük kayan bar (CSS ile konumlanır)
with st.container(key="theme_switch"):
    _dark = st.toggle("🌙" if theme == "dark" else "☀️", value=(theme == "dark"))
if ("dark" if _dark else "light") != theme:
    st.session_state["theme"] = "dark" if _dark else "light"
    st.rerun()

_LOGO_PATH = Path(__file__).parent / "assets" / "agu_logo.png"
try:
    LOGO_DATA_URI = "data:image/png;base64," + base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")
except Exception:
    LOGO_DATA_URI = ""

# Anahtar kontrolü
if not os.getenv("VOYAGE_AI_KEY") or not os.getenv("PINECONE_API_KEY"):
    st.error("VOYAGE_AI_KEY / PINECONE_API_KEY tanımlı değil. Streamlit Cloud → Settings → Secrets'a ekle.")
    st.stop()

# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
_BOLUM_IDS = list(rag_cloud.BOLUM_ADI_MAP.keys())
LEVEL_TO_K = {"Kısa": 4, "Dengeli": 8, "Kapsamlı": 14}
LEVEL_INFO = {
    "Kısa": "Net, tek bilgi soruları için (örn. COMP 101 kaç kredi?)",
    "Dengeli": "Günlük kullanım için ideal — çoğu soruya uyar.",
    "Kapsamlı": "Karşılaştırma / geniş konu soruları için.",
}

with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-logo">
            <img src="{LOGO_DATA_URI}" alt="AGÜ" class="agu-logo" />
            <h2>AGU Archivus</h2>
            <span>Yapay Zeka Asistanı</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="display:flex;align-items:center;gap:7px;font-weight:700;margin-bottom:2px;">'
        '<svg width="17" height="17" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
        '<g stroke="#3a3a3a" stroke-width="1.4" stroke-linejoin="round">'
        '<rect x="1.6" y="2" width="20.8" height="5.6" rx="1.6" fill="#F5C877"/>'
        '<rect x="1.6" y="9.2" width="20.8" height="5.6" rx="1.6" fill="#A6D98A"/>'
        '<rect x="1.6" y="16.4" width="20.8" height="5.6" rx="1.6" fill="#ABE4F5"/></g>'
        '<g fill="#EF5F5F" stroke="#3a3a3a" stroke-width="0.9" stroke-linejoin="round">'
        '<path d="M6.4 3.5 L8.8 4.8 L6.4 6.1 Z"/><path d="M6.4 10.7 L8.8 12 L6.4 13.3 Z"/>'
        '<path d="M6.4 17.9 L8.8 19.2 L6.4 20.5 Z"/></g>'
        '<g stroke="#3a3a3a" stroke-width="1.3" stroke-linecap="round">'
        '<line x1="11" y1="4.2" x2="19.5" y2="4.2"/><line x1="11" y1="5.6" x2="17" y2="5.6"/>'
        '<line x1="11" y1="11.4" x2="19.5" y2="11.4"/><line x1="11" y1="12.8" x2="17" y2="12.8"/>'
        '<line x1="11" y1="18.6" x2="19.5" y2="18.6"/><line x1="11" y1="20" x2="17" y2="20"/></g>'
        '</svg><span>Bölüm Seçimi</span></div>',
        unsafe_allow_html=True,
    )
    bolum_id = st.selectbox(
        "Bölüm Seçimi",
        options=_BOLUM_IDS,
        format_func=lambda b: rag_cloud.BOLUM_ADI_MAP[b],
        index=0,
        label_visibility="collapsed",
    )
    bolum_secim = rag_cloud.BOLUM_ADI_MAP[bolum_id]
    bolum_icon = ui_theme.BOLUM_SVG.get(bolum_id, "")

    # Bölüm değiştiyse sohbeti ve GPA state'ini sıfırla
    if st.session_state.get("_active_bolum") != bolum_id:
        st.session_state["_active_bolum"] = bolum_id
        st.session_state["messages"] = []
        for kk in [x for x in st.session_state.keys() if isinstance(x, str) and x.startswith("gpa_")]:
            del st.session_state[kk]

    st.markdown(
        f"""
        <div class="info-card">
            <strong>{bolum_icon} {bolum_secim}</strong><br>
            Müfredat, ders içerikleri, staj yönergesi ve daha fazlası hakkında soru sorabilirsin.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown(
        '<div style="display:flex;align-items:center;gap:7px;font-weight:700;">'
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="#E6105A" '
        'xmlns="http://www.w3.org/2000/svg">'
        '<circle cx="12" cy="4.3" r="2.6"/>'
        '<rect x="9.6" y="8.4" width="4.8" height="12.8" rx="2.2"/>'
        '</svg><span>Cevap Detay Seviyesi</span></div>',
        unsafe_allow_html=True,
    )
    detail_level = st.select_slider("detay", options=["Kısa", "Dengeli", "Kapsamlı"],
                                    value="Dengeli", label_visibility="collapsed")
    st.markdown(
        f'<div class="detail-card"><strong>Ayar: {detail_level}</strong><br>'
        f'<span style="opacity:0.8;">{LEVEL_INFO[detail_level]}</span></div>',
        unsafe_allow_html=True,
    )
    top_k = LEVEL_TO_K[detail_level]

    st.divider()
    if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

    st.markdown(
        '<div style="text-align:center; opacity:0.5; font-size:0.75rem; margin-top:18px; line-height:1.5;">'
        'Abdullah Gül Üniversitesi<br>Bölümleri</div>',
        unsafe_allow_html=True,
    )

# --------------------------------------------------------------------------- #
# Hero
# --------------------------------------------------------------------------- #
st.markdown(
    f"""
    <div class="hero">
        <div class="pill">✨ AKILLI ASİSTAN</div>
        <h1>Merhaba! {bolum_icon} {bolum_secim}</h1>
        <p>Müfredat, ders içerikleri, ön şartlar ve staj süreçleri hakkında doğal dilde sorular sor — anında Türkçe cevap al.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

chat_tab, gpa_tab = st.tabs([":material/rate_review: Asistan", ":material/school: GPA Hesaplayıcı"])

# ============================ ASİSTAN ============================
with chat_tab:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Boş sohbette karşılama + öneri çipleri (bekleyen soru yokken)
    if not st.session_state["messages"] and "pending_q" not in st.session_state:
        st.markdown(
            '<div class="welcome"><h3>'
            '<svg viewBox="0 0 24 24" width="1.05em" height="1.05em" fill="none" stroke="currentColor" '
            'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
            'style="vertical-align:-0.18em;margin-right:7px;">'
            '<path d="M2 5.5A2.5 2.5 0 0 1 4.5 3H12a2.5 2.5 0 0 1 2.5 2.5v5A2.5 2.5 0 0 1 12 13H8l-3 3v-3H4.5A2.5 2.5 0 0 1 2 10.5z"/>'
            '<path d="M5 6.6h6"/><path d="M5 9.2h4"/>'
            '<path d="M20 3.2a1.7 1.7 0 0 1 2.4 2.4l-7.6 7.6-3.2 .8 .8-3.2z"/>'
            '<path d="M18.7 4.5l2.4 2.4"/>'
            '</svg>Sormak istediğin bir şey var mı?</h3>'
            '<p>Aşağıdaki örneklerden birini seç ya da kendi sorunu yaz.</p></div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(2)
        for i, (icon, text) in enumerate(ui_theme.SUGGESTIONS.get(bolum_id, [])):
            with cols[i % 2]:
                if st.button(f"{icon}  {text}", key=f"sug_{i}", use_container_width=True):
                    st.session_state["pending_q"] = text
                    st.rerun()

    # Geçmişi çiz (asistan mesajlarının altına 👍/👎 feedback)
    for _idx, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m["role"] == "assistant" and not m.get("_no_rating"):
                _render_rating(_idx, m)

    # Bekleyen soruyu (yazılan ya da öneri) geçmişin ALTINDA işle
    soru = st.session_state.pop("pending_q", None)
    if soru:
        # Gizlilik: TC/öğrenci no gibi kişisel bilgileri LLM'e/feedback'e/ekrana
        # gitmeden ÖNCE maskele
        _had_pii = privacy.has_personal_info(soru)
        soru = privacy.mask_personal_info(soru)
        st.session_state.messages.append({"role": "user", "content": soru})
        with st.chat_message("user"):
            st.markdown(soru)
            if _had_pii:
                st.caption("🔒 Güvenliğin için girdiğin kişisel bilgi(ler) otomatik gizlendi.")

        # Rate limit: bir öğrenci spam yapıp ortak kotayı tüketmesin
        _allowed, _retry = rate_limit.check(_client_id(), max_per_min=RATE_LIMIT_PER_MIN)
        if not _allowed:
            uyari = (
                f"⏳ Çok hızlısın! Dakikada en fazla **{RATE_LIMIT_PER_MIN} soru** "
                f"sorabilirsin. Lütfen **{_retry} saniye** sonra tekrar dene."
            )
            with st.chat_message("assistant"):
                st.warning(uyari)
            # rate-limit uyarısına feedback butonu koyma
            st.session_state.messages.append({"role": "assistant", "content": uyari, "_no_rating": True})
            st.stop()

        with st.chat_message("assistant"):
            # "Düşünme" göstergesi — retrieval sürerken kullanıcı boş ekran görmesin
            _status = st.empty()
            _status.markdown(
                '<div style="display:flex;align-items:center;gap:8px;'
                'opacity:0.75;font-size:0.95rem;">'
                '<span class="thinking-dot">●</span> '
                '<em>Dökümanlar analiz ediliyor…</em></div>'
                '<style>.thinking-dot{animation:pulse 1.2s ease-in-out infinite;'
                'color:#FFB800;}@keyframes pulse{0%,100%{opacity:0.3}50%{opacity:1}}</style>',
                unsafe_allow_html=True,
            )
            try:
                r = rag_cloud.respond(soru, bolum=bolum_id, k=top_k)
                _status.empty()  # analiz bitti — stream başlıyor
                if r["mode"] == "list":
                    st.markdown(r["text"])
                    cevap = r["text"]
                else:
                    cevap = st.write_stream(r["token_iter"])
                st.caption(f"📚 {r['n']} kaynak · {rag_cloud.BOLUM_ADI_MAP.get(r['bolum'], 'AGÜ')}")
            except Exception as e:
                _status.empty()
                cevap = f"Bir hata oluştu: {e}"
                st.error(cevap)
        # Feedback için soru + bölümü mesajla sakla; rerun ile geçmişte 👍/👎 ile çizilir
        st.session_state.messages.append({
            "role": "assistant", "content": cevap,
            "question": soru, "bolum": bolum_id,
        })
        st.rerun()

    # Mesaj kutusu HER ZAMAN en altta — yazılan soru pending'e gidip rerun ile altta işlenir
    if prompt := st.chat_input("Örn: 2023 girişliyim 3. dönem hangi dersler var?"):
        st.session_state["pending_q"] = prompt
        st.rerun()

    # Kalıcı uyarı — mesaj kutusunun hemen altında
    st.markdown(
        '<div class="chat-disclaimer">AGU Archivus bir yapay zeka asistanıdır, hata yapabilir.<br>'
        '🔒 Lütfen TC kimlik no, öğrenci no gibi <b>kişisel bilgilerinizi girmeyin</b>.</div>',
        unsafe_allow_html=True,
    )

# ============================ GPA HESAPLAYICI ============================
with gpa_tab:
    st.markdown(
        '<div style="display:flex;align-items:center;gap:9px;margin:0.2rem 0 0.4rem;">'
        '<svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor" '
        'xmlns="http://www.w3.org/2000/svg">'
        '<path d="M16 8C16 10.21 14.21 12 12 12C9.79 12 8 10.21 8 8L8.11 7.06L5 5.5L12 '
        '2L19 5.5V10.5H18V6L15.89 7.06L16 8M12 14C16.42 14 20 15.79 20 18V20H4V18C4 '
        '15.79 7.58 14 12 14Z"/></svg>'
        '<span style="font-size:1.5rem;font-weight:700;">GPA Hesaplayıcı</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        f"**Aktif bölüm:** {bolum_secim} · Sınıfını seç, bu dönem aldığın derslere harf notunu gir, "
        "geçmiş ortalamanı yaz — yeni Genel Ortalamanı (CGPA) hesaplayalım."
    )

    cur_years = gpa.available_curricula(bolum_id)
    if not cur_years:
        st.warning("Bu bölüm için henüz müfredat verisi yüklenmemiş.")
    else:
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            sel_year = st.selectbox("📚 Müfredat yılı", cur_years, index=len(cur_years) - 1, key=f"gpa_year_{bolum_id}")
        with sc2:
            SINIF_LABELS = {1: "1. Sınıf", 2: "2. Sınıf", 3: "3. Sınıf", 4: "4. Sınıf", 0: "Tüm sınıflar"}
            sel_sinif = st.selectbox("🎓 Sınıf", options=[1, 2, 3, 4, 0], index=0,
                                     format_func=lambda x: SINIF_LABELS[x], key=f"gpa_sinif_{bolum_id}")
        with sc3:
            if sel_sinif == 0:
                donem_opts, donem_labels = [0], {0: "Tüm Dönemler"}
            else:
                d1, d2 = sel_sinif * 2 - 1, sel_sinif * 2
                donem_opts = [0, d1, d2]
                donem_labels = {0: "İki Dönem de", d1: f"{d1}. Dönem (Güz)", d2: f"{d2}. Dönem (Bahar)"}
            sel_donem = st.selectbox("📅 Dönem", options=donem_opts, index=0,
                                     format_func=lambda x: donem_labels[x], key=f"gpa_donem_{bolum_id}")

        st.markdown("#### Geçmiş Akademik Bilgi")
        gc1, gc2 = st.columns(2)
        with gc1:
            prev_cgpa = st.number_input("Geçmiş Genel Ortalaman (önceki CGPA)", min_value=0.0, max_value=4.0,
                                        value=0.0, step=0.01, key=f"gpa_prev_cgpa_{bolum_id}",
                                        help="Bu döneme girmeden önceki kümülatif ortalaman. İlk dönemse 0.00 bırak.")
        with gc2:
            prev_credits = st.number_input("Önceki Toplam AKTS", min_value=0, max_value=300, value=0, step=1,
                                           key=f"gpa_prev_cred_{bolum_id}",
                                           help="Şimdiye kadar aldığın derslerin toplam AKTS'si "
                                                "(GNO AKTS ağırlıklı hesaplanır — AGÜ yönetmeliği).")

        st.markdown("---")

        df_key = f"gpa_df_{bolum_id}_{sel_year}_{sel_sinif}_{sel_donem}"
        if df_key not in st.session_state:
            courses = gpa.courses_for_year(bolum_id, sel_year, sel_sinif, sel_donem)
            st.session_state[df_key] = pd.DataFrame([
                {"Dönem": c["donem"], "Ders Kodu": c["ders_kodu"], "Ders Adı": c["ders_adi"],
                 "Kredi": c["kredi"], "AKTS": c["akts"], "Not": "—",
                 "P/F": gpa.is_default_pf(c["ders_kodu"], c["ders_adi"])}
                for c in courses
            ])

        sinif_label = SINIF_LABELS[sel_sinif]
        donem_label = donem_labels[sel_donem] if sel_donem != 0 else ""
        st.markdown(f"##### Bu Dönem Dersleri — {sinif_label}{(' (' + donem_label + ')') if donem_label else ''}")
        if st.session_state[df_key].empty:
            st.info("Bu sınıf için müfredatta ders bulunamadı.")
            edited = st.session_state[df_key]
        else:
            edited = st.data_editor(
                st.session_state[df_key],
                column_config={
                    "Dönem": st.column_config.NumberColumn(width="small", disabled=True),
                    "Ders Kodu": st.column_config.TextColumn(width="small", disabled=True),
                    "Ders Adı": st.column_config.TextColumn(width="medium", disabled=True),
                    "Kredi": st.column_config.NumberColumn(width="small", disabled=True),
                    "AKTS": st.column_config.NumberColumn(width="small", disabled=True),
                    "Not": st.column_config.SelectboxColumn(options=gpa.GRADE_OPTIONS, width="small",
                                                            help="Bu dönem aldığın harf notu. Almadıysan '—' bırak."),
                    "P/F": st.column_config.CheckboxColumn(width="small",
                                                           help="Pass/Fail dersi (GPA'ya katılmaz; AKTS sayılır)."),
                },
                use_container_width=True, hide_index=True, num_rows="fixed", key=f"editor_{df_key}",
            )

        extra_key = f"gpa_extras_{bolum_id}"
        if extra_key not in st.session_state:
            st.session_state[extra_key] = pd.DataFrame(
                columns=["Ders Kodu", "Ders Adı", "Kredi", "AKTS", "Eski Not", "Not", "Tip", "P/F"])

        with st.expander("➕ Ders ekle (tekrar/yükseltme, yatay geçiş, yaz okulu...)"):
            catalog = gpa.all_courses_catalog()
            code_options = [""] + sorted(catalog.keys())

            def _fmt_option(c: str) -> str:
                if not c:
                    return "— ders ara veya kod yaz —"
                info = catalog[c]
                return f"{c} — {info['ders_adi']} ({info['kredi']} kredi · {info['akts']} AKTS)"

            ec1, ec2 = st.columns([5, 1])
            with ec1:
                sel_code = st.selectbox("🔎 Ders ara (kod veya isim ile filtrele)", options=code_options,
                                        format_func=_fmt_option, index=0, key=f"gpa_extra_search_{bolum_id}")
            with ec2:
                st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
                if st.button("➕ Ekle", key=f"gpa_extra_add_{bolum_id}", use_container_width=True) and sel_code:
                    c = catalog[sel_code]
                    existing = st.session_state[extra_key]
                    already = ("Ders Kodu" in existing.columns
                               and (existing["Ders Kodu"].astype(str).str.upper() == c["ders_kodu"]).any())
                    if not already:
                        new_row = pd.DataFrame([{
                            "Ders Kodu": c["ders_kodu"], "Ders Adı": c["ders_adi"], "Kredi": c["kredi"],
                            "AKTS": c["akts"], "Eski Not": "—", "Not": "—", "Tip": "Yatay geçiş",
                            "P/F": gpa.is_default_pf(c["ders_kodu"], c["ders_adi"])}])
                        st.session_state[extra_key] = pd.concat([existing, new_row], ignore_index=True)
                        st.rerun()

            st.caption("Aradığın dersi seç → **➕ Ekle** → kredi/AKTS otomatik dolar. Yeni harf notunu seç. "
                       "**Tekrar/yükseltme** için: **Tip**'i `Tekrar/Yükseltme` yap + **Eski Not**'u seç "
                       "(Eski Not yalnızca bu Tip'te hesaba katılır).")

            edited_extras = st.data_editor(
                st.session_state[extra_key],
                column_config={
                    "Ders Kodu": st.column_config.TextColumn(width="small"),
                    "Ders Adı": st.column_config.TextColumn(width="medium"),
                    "Kredi": st.column_config.NumberColumn(min_value=0, max_value=15, default=3, width="small"),
                    "AKTS": st.column_config.NumberColumn(min_value=0, max_value=30, default=5, width="small"),
                    "Eski Not": st.column_config.SelectboxColumn(options=gpa.GRADE_OPTIONS, default="—", width="small",
                                                                 help="Tekrar/yükseltmede ESKİ notun. Sadece Tip=Tekrar/Yükseltme'de kullanılır."),
                    "Not": st.column_config.SelectboxColumn(options=gpa.GRADE_OPTIONS, default="—", width="small",
                                                            help="Bu dönem aldığın YENİ not."),
                    "Tip": st.column_config.SelectboxColumn(options=gpa.EXTRA_TYPES, width="medium"),
                    "P/F": st.column_config.CheckboxColumn(width="small"),
                },
                use_container_width=True, hide_index=True, num_rows="dynamic", key=f"editor_{extra_key}",
            )

        bc1, bc2 = st.columns([1, 1])
        do_calc = bc1.button("🎯 Yeni CGPA Hesapla", type="primary", use_container_width=True)
        if bc2.button("🔄 Notları Sıfırla", use_container_width=True):
            for k in list(st.session_state.keys()):
                if isinstance(k, str) and (k.startswith("gpa_df_") or k.startswith("editor_gpa_df_")
                                           or k == extra_key or k == f"editor_{extra_key}"):
                    st.session_state.pop(k, None)
            st.rerun()

        if do_calc:
            entries: list[dict] = []
            if hasattr(edited, "iterrows"):
                for _, row in edited.iterrows():
                    grade = str(row.get("Not", "—") or "—").strip()
                    if grade in ("", "—", "nan"):
                        continue
                    entries.append({"ders_kodu": str(row["Ders Kodu"]), "kredi": int(row["Kredi"] or 0),
                                    "akts": int(row["AKTS"] or 0), "not": grade, "pf": bool(row.get("P/F"))})
            for _, row in edited_extras.iterrows():
                kod = str(row.get("Ders Kodu", "") or "").strip()
                grade = str(row.get("Not", "—") or "—").strip()
                if not kod or grade in ("", "—", "nan"):
                    continue
                tip = str(row.get("Tip", "") or "").strip()
                eski = str(row.get("Eski Not", "—") or "—").strip()
                # Eski Not YALNIZCA Tip=Tekrar/Yükseltme seçilince dikkate alınır
                eski = eski if (tip == "Tekrar/Yükseltme" and eski not in ("", "—", "nan")) else ""
                entries.append({
                    "ders_kodu": kod,
                    "kredi": int(row["Kredi"] or 0) if pd.notna(row.get("Kredi")) else 0,
                    "akts": int(row["AKTS"] or 0) if pd.notna(row.get("AKTS")) else 0,
                    "not": grade, "eski_not": eski, "pf": bool(row.get("P/F"))})

            if not entries:
                st.warning("Hiç not girilmemiş. En az bir derse harf notu seç.")
            else:
                if prev_cgpa > 0 and int(prev_credits) == 0:
                    st.error("⚠️ Geçmiş CGPA girdin ama 'Önceki Toplam AKTS' = 0. Doğru hesap için ikisini de gir.")
                result = gpa.compute_combined(prev_cgpa, int(prev_credits), entries)
                st.markdown("---")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("🎯 Yeni CGPA", f"{result['new_cgpa']:.2f} / 4.00",
                          delta=f"{result['new_cgpa'] - result['prev_cgpa']:+.2f}" if result['prev_credits'] > 0 else None)
                m2.metric("📅 Bu Dönem GPA", f"{result['sem_gpa']:.2f}")
                m3.metric("✅ Geçen / ❌ Kalan", f"{result['sem_passed']} / {result['sem_failed']}")
                m4.metric("📊 Toplam AKTS", result['total_credits'],
                          delta=f"+{result['total_credits'] - result['prev_credits']} yeni" if result['total_credits'] > result['prev_credits'] else None)

                with st.expander("🧮 Hesap detayı"):
                    st.markdown(
                        "**GNO, AKTS ağırlıklı hesaplanır** (AGÜ MADDE 30): "
                        "`GNO = Σ(AKTS × katsayı) / Σ(AKTS)`\n\n"
                        f"- Geçmiş: **{result['prev_cgpa']:.2f}** GNO × **{result['prev_credits']}** AKTS\n"
                        f"- Yeni toplam: **{result['total_credits']}** AKTS → **Yeni CGPA {result['new_cgpa']:.2f}**\n\n"
                        "> Tekrar/yükseltme derslerinde eski not çıkarılıp yeni not eklenir; "
                        "dersin AKTS'si toplamda **tek** sayılır."
                    )
                if result["onor"]:
                    thr = gpa.YUKSEK_ONOR_THRESHOLD if "Yüksek" in result["onor"] else gpa.ONOR_THRESHOLD
                    st.success(f"**{result['onor']}** kategorisindesin! (CGPA ≥ {thr:.2f})")
                elif result["new_cgpa"] > 0:
                    delta = gpa.ONOR_THRESHOLD - result["new_cgpa"]
                    if delta > 0:
                        st.info(f"Onur eşiğine **{delta:.2f}** puan kaldı (3.00).")

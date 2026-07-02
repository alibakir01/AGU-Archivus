"""app.py görsel temasından çıkarılan paylaşılan UI parçaları (CSS assets/app_style.css'te)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def global_css() -> str:
    p = ROOT / "assets" / "app_style.css"
    return p.read_text(encoding="utf-8") if p.exists() else ""


# Okunabilirlik iyileştirmeleri — HER İKİ temada uygulanır
_READABILITY_CSS = """
<style>
  [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
  [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
  [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
      font-size: 1rem !important;
      line-height: 1.68 !important;
  }
  [data-testid="stMarkdownContainer"] li { margin-bottom: 4px !important; }
  [data-testid="stMarkdownContainer"] h2 { margin-top: 0.6em !important; font-size: 1.4rem !important; }
  [data-testid="stMarkdownContainer"] h3 { margin-top: 0.5em !important; font-size: 1.15rem !important; }
  [data-testid="stMarkdownContainer"] strong { font-weight: 700 !important; }

  /* Kalıcı uyarı — mesaj kutusunun hemen altında (Python'da chat_input'tan sonra basılır) */
  .chat-disclaimer {
      text-align: center;
      font-size: 0.82rem;
      color: #8b909b !important;
      opacity: 0.9;
      padding: 7px 8px 2px;
      line-height: 1.35;
  }

  /* Material Symbols ikonları: base CSS'teki 'font-family: Inter !important' popover/menu
     içinde ikon fontunu ezip ligature'ları ham yazıya çeviriyordu (tablo sütun menüsündeki
     'content_copy', 'arrow_upward' gibi üst üste binen yazılar). İkon fontunu geri getir. */
  [data-testid="stIconMaterial"],
  [data-baseweb="popover"] [data-testid="stIconMaterial"],
  [data-baseweb="menu"] [data-testid="stIconMaterial"],
  span[class*="material-symbols"], span[class*="material-icons"] {
      font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
      font-weight: normal !important; font-style: normal !important;
      letter-spacing: normal !important; text-transform: none !important;
      white-space: nowrap !important; word-wrap: normal !important; direction: ltr !important;
  }

  /* Primary buton (Yeni CGPA Hesapla) — bordo zeminde yazı HER ZAMAN beyaz */
  .stButton button[kind="primary"], .stButton button[kind="primary"] * { color: #FFFFFF !important; }
  .stButton button[kind="primary"] svg { fill: #FFFFFF !important; }

  /* Tema switch — sağ üstte sabit; araç çubuğunun ALTINDA (tıklama engellenmesin) */
  .st-key-theme_switch {
      position: fixed !important;
      top: 3.1rem; right: 0.9rem; z-index: 1000000 !important;
      width: auto !important; min-width: 0 !important;
      background: rgba(140,140,150,0.22);
      border: 1px solid rgba(140,140,150,0.35);
      border-radius: 999px;
      padding: 7px 14px !important;
      pointer-events: auto !important;
      box-shadow: 0 3px 12px -4px rgba(0,0,0,0.3);
      overflow: visible !important;
  }
  .st-key-theme_switch * { pointer-events: auto !important; }
  .st-key-theme_switch [data-testid="stElementContainer"],
  .st-key-theme_switch [data-testid="stVerticalBlock"] { width: auto !important; gap: 0 !important; }
  .st-key-theme_switch label { margin: 0 !important; display: flex !important; align-items: center !important; }
  /* Yardım ikonu (?) gizle — sadeleşsin */
  .st-key-theme_switch [data-testid="stTooltipIcon"] { display: none !important; }
</style>
"""

# AYDINLIK TEMA — sadece "light" seçilince enjekte edilen override katmanı.
# Çalışan koyu CSS'e dokunulmaz; risk aydınlık moda izole.
_LIGHT_CSS = """
<style>
  /* ===== AYDINLIK TEMA (yumuşak, göz yormayan sıcak beyaz) ===== */
  .stApp {
      background:
          radial-gradient(1000px 480px at 12% -8%, rgba(194,24,91,0.045), transparent 60%),
          linear-gradient(180deg, #F5F6F8 0%, #ECEEF2 100%) !important;
  }
  /* Metin — güçlü kontrast ama saf siyah değil (daha az yorucu) */
  .stApp, .stApp p, .stApp li, .stApp label, .stApp span,
  [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
  [data-testid="stMarkdownContainer"] li, [data-testid="stMarkdownContainer"] span,
  [data-testid="stChatMessage"], [data-testid="stChatMessage"] * {
      color: #1c2330 !important;
  }
  h1, h2, h3, h4, h5, h6 { color: #141a24 !important; }
  [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: #606877 !important; }

  /* HERO — açık zeminde soluk kalmasın diye ZENGİN opak bordo gradient */
  .hero {
      background: linear-gradient(135deg, #7B1E3A 0%, #B21E55 52%, #E0507A 100%) !important;
      border: 1px solid rgba(0,0,0,0.06) !important;
      box-shadow: 0 12px 34px -14px rgba(178,30,85,0.5) !important;
  }
  .hero p { color: rgba(255,255,255,0.94) !important; }
  .hero .pill { color: #FFE9C4 !important; background: rgba(255,255,255,0.15) !important; }

  /* Sidebar */
  [data-testid="stSidebar"] {
      background: #FFFFFF !important;
      border-right: 1px solid #E6E8EE !important;
  }
  [data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
  [data-testid="stSidebar"] label, [data-testid="stSidebar"] div { color: #1c2330 !important; }
  /* Logo başlığı beyazda kayboluyordu → bordo gradient */
  [data-testid="stSidebar"] .sidebar-logo h2 {
      background: linear-gradient(90deg, #7B1E3A, #C2185B) !important;
      -webkit-background-clip: text !important; background-clip: text !important;
      -webkit-text-fill-color: transparent !important;
  }
  [data-testid="stSidebar"] .sidebar-logo { border-bottom: 1px solid #EAECF1 !important; }
  [data-testid="stSidebar"] .sidebar-logo span { color: #8a90a0 !important; opacity: 1 !important; }

  /* Vurgular: bordo (altın beyazda okunmaz) */
  .info-card strong, .detail-card strong, [data-testid="stExpander"] summary { color: #B21E55 !important; }

  /* Kartlar — beyaz + yumuşak gölge */
  .info-card {
      background: #FFFFFF !important; border: 1px solid #EADCE3 !important;
      box-shadow: 0 1px 3px rgba(16,24,40,0.05) !important; color: #333a48 !important; }
  .detail-card {
      background: #FFF7E8 !important; border-left: 3px solid #FFB800 !important; color: #4a4230 !important; }
  .welcome { color: #3a4150 !important; opacity: 1 !important; }

  /* Selectbox (kapalı görünüm) — sadece sidebar değil, TÜM alanlar (GPA sekmesi dahil) */
  [data-baseweb="select"] > div {
      background: #FFFFFF !important; border: 1px solid #DADCE3 !important; }
  [data-baseweb="select"] > div * { color: #1c2330 !important; }
  [data-baseweb="select"] svg { fill: #5a6172 !important; }
  [data-baseweb="popover"], [data-baseweb="menu"], [data-baseweb="select-dropdown"],
  [data-baseweb="popover"] [role="listbox"], [data-baseweb="popover"] ul {
      background: #FFFFFF !important; border: 1px solid #E1E3EA !important;
      box-shadow: 0 10px 30px -8px rgba(16,24,40,0.18) !important; }
  [data-baseweb="popover"] [role="option"], [data-baseweb="menu"] li, [data-baseweb="select-dropdown"] li,
  [data-baseweb="popover"] [role="option"] *, [data-baseweb="menu"] li * { color: #1c2330 !important; }
  [data-baseweb="popover"] [role="option"]:hover, [data-baseweb="menu"] li:hover { background: #FBEFF3 !important; }
  [data-baseweb="popover"] [role="option"]:hover * { color: #7B1E3A !important; }
  [data-baseweb="popover"] [role="option"][aria-selected="true"] { background: #F6E3EC !important; }

  /* Chat balonu — beyaz + gölge */
  [data-testid="stChatMessage"] {
      background: #FFFFFF !important; border: 1px solid #E6E8EE !important;
      box-shadow: 0 1px 3px rgba(16,24,40,0.05) !important; }
  [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
      background: linear-gradient(135deg, #FBEFF3, #FDF6EE) !important; border-color: #EFD9E2 !important; }

  /* Alt bar + chat input — koyu kalıyordu, aydınlığa çevir */
  [data-testid="stBottom"], [data-testid="stBottom"] > div,
  [data-testid="stBottomBlockContainer"] { background: transparent !important; }
  [data-testid="stChatInput"] {
      background: #FFFFFF !important; border: 1px solid #DADCE3 !important;
      box-shadow: 0 2px 10px -4px rgba(16,24,40,0.12) !important; }
  [data-testid="stChatInput"] textarea { color: #1c2330 !important; }
  [data-testid="stChatInput"] textarea::placeholder { color: #9aa0ac !important; }

  /* Expander — gövde + BAŞLIK (summary koyu kalıyordu) */
  [data-testid="stExpander"] { background: #FFFFFF !important; border: 1px solid #E6E8EE !important; }
  [data-testid="stExpander"] details,
  [data-testid="stExpander"] summary,
  [data-testid="stExpander"] > details > summary,
  [data-testid="stExpanderHeader"] {
      background: #FFFFFF !important; color: #1c2330 !important; }
  [data-testid="stExpander"] summary:hover { background: #F7F8FA !important; }
  [data-testid="stExpander"] summary p, [data-testid="stExpander"] summary span { color: #1c2330 !important; }

  /* Yardım (?) ikonu — açık zeminde nötr gri, hover'da bordo.
     NOT: Yeni Streamlit'te ikon SVG değil Material Symbols FONT ikonu
     (span[data-testid="stIconMaterial"]) — bu yüzden svg'ye ek olarak
     span/color da hedeflenmeli; genel '.stApp span' koyu metin kuralını ezmek
     için buradaki kurallar ondan sonra gelir. */
  [data-testid="stTooltipHoverTarget"],
  [data-testid="stTooltipHoverTarget"] *,
  [data-testid="stTooltipIcon"],
  [data-testid="stTooltipIcon"] *,
  [data-testid="stTooltipHoverTarget"] [data-testid="stIconMaterial"] {
      color: #A6ACB8 !important; fill: #A6ACB8 !important; opacity: 1 !important; }
  [data-testid="stTooltipHoverTarget"] svg,
  [data-testid="stTooltipHoverTarget"] svg * { stroke: none !important; }
  [data-testid="stTooltipHoverTarget"]:hover,
  [data-testid="stTooltipHoverTarget"]:hover *,
  [data-testid="stTooltipIcon"]:hover,
  [data-testid="stTooltipIcon"]:hover * {
      color: #B21E55 !important; fill: #B21E55 !important; }

  /* Tooltip balonu — DIŞ katman (BaseWeb) beyaz kartın kendisi olsun; içerik şeffaf.
     (Önceki yaklaşım iç kutuyu beyaz yapıyordu, dış koyu katman kalın siyah çerçeve
     gibi görünüyordu.) */
  div[data-baseweb="tooltip"], div[role="tooltip"] {
      background: #FFFFFF !important; color: #2a3140 !important;
      border: 1px solid #E6E8EE !important; border-left: 3px solid #C2185B !important;
      border-radius: 12px !important;
      box-shadow: 0 12px 34px -12px rgba(16,24,40,0.28) !important; }
  div[data-baseweb="tooltip"] > div, div[role="tooltip"] > div {
      background: transparent !important; }
  [data-testid="stTooltipContent"] {
      background: transparent !important; color: #2a3140 !important;
      border: none !important; box-shadow: none !important;
      padding: 11px 15px !important; font-size: 0.9rem !important; line-height: 1.5 !important; }
  [data-testid="stTooltipContent"] * {
      color: #2a3140 !important; background: transparent !important; border: none !important; box-shadow: none !important; }

  /* Butonlar (öneri çipleri = secondary) — primary'ye dokunma */
  .stButton button[kind="secondary"] {
      background: #FFFFFF !important; border: 1px solid #E1E3EA !important; color: #1c2330 !important;
      box-shadow: 0 1px 2px rgba(16,24,40,0.04) !important; }
  .stButton button[kind="secondary"]:hover {
      border-color: rgba(178,30,85,0.45) !important; background: #FDF6F8 !important; }

  /* Bölüm SVG ikonu beyaz stroke → aydınlıkta görünmez; info-card'da bordo yap
     (hero koyu bordo zeminde kaldığı için orada beyaz kalır) */
  .info-card .bolum-icon svg { stroke: #B21E55 !important; }

  /* Seçili dropdown öğesi: base CSS beyaz zorluyordu → bordo (açık zeminde okunur) */
  [data-baseweb="popover"] [role="option"][aria-selected="true"],
  [data-baseweb="popover"] [role="option"][aria-selected="true"] *,
  [data-baseweb="popover"] [role="option"][aria-checked="true"],
  [data-baseweb="popover"] [role="option"][aria-checked="true"] *,
  [data-baseweb="menu"] li[aria-selected="true"],
  [data-baseweb="menu"] li[aria-selected="true"] * { color: #7B1E3A !important; }

  /* Chat input SİYAH kalıyordu — tüm iç katmanları aydınlığa çevir */
  [data-testid="stBottom"], [data-testid="stBottom"] > div,
  [data-testid="stBottomBlockContainer"] { background: transparent !important; }
  [data-testid="stChatInput"],
  [data-testid="stChatInput"] > div,
  [data-testid="stChatInput"] [data-baseweb="base-input"],
  [data-testid="stChatInput"] [data-baseweb="textarea"] {
      background: #FFFFFF !important; border-color: #DADCE3 !important; }
  [data-testid="stChatInput"] textarea { background: transparent !important; color: #1c2330 !important; }
  [data-testid="stChatInput"] button svg { fill: #7B1E3A !important; }

  /* Number input / diğer baseweb girişleri (GPA sekmesi) */
  .stNumberInput [data-baseweb="input"], .stNumberInput input,
  [data-baseweb="input"], [data-baseweb="base-input"] {
      background: #FFFFFF !important; color: #1c2330 !important; border-color: #DADCE3 !important; }
  .stNumberInput button { background: #F1F3F7 !important; color: #1c2330 !important; }
  /* −/+ ikonları beyaz SVG → koyu yap (stroke EKLEME, yoksa kalınlaşır — sadece fill) */
  .stNumberInput button svg, .stNumberInput button svg * { fill: #1c2330 !important; stroke: none !important; }

  /* GPA tablosu: glide-canvas hücreleri CSS ile renklenemez (Streamlit sınırı).
     En azından çerçeveyi aydınlığa uydur — koyu tablo temiz bir kart içinde dursun. */
  [data-testid="stDataFrame"], [data-testid="stDataFrameResizable"],
  [data-testid="stDataEditor"], [data-testid="stDataEditorResizable"] {
      border: 1px solid #DADCE3 !important; border-radius: 12px !important;
      overflow: hidden !important; box-shadow: 0 1px 4px rgba(16,24,40,0.06) !important; }

  ::-webkit-scrollbar-thumb { background: rgba(16,24,40,0.18) !important; }
</style>
"""


def theme_css(theme: str) -> str:
    """Okunabilirlik (her zaman) + aydınlık override (theme='light' ise)."""
    css = _READABILITY_CSS
    if theme == "light":
        css += _LIGHT_CSS
    return css

SUGGESTIONS = {'bilgisayar': [('📚', '2023 girişliyim 3. dönem hangi dersler var?'),
                ('🔢', 'COMP 101 dersi kaç AKTS?'),
                ('🧩', 'COMP 305 dersinin ön şartı nedir?'),
                ('📋', 'Staj yönergesi maddeleri neler?')],
 'makine': [('📚', '2024 girişliyim 4. dönem dersleri neler?'),
            ('⚙️', 'ME 201 dersi kaç kredi?'),
            ('🧩', 'ME 301 ön şartı var mı?'),
            ('📋', 'Makine müfredatı 2025 nasıl?')],
 'endustri': [('📚', '2022 girişli 2. sınıf dersleri neler?'),
              ('📊', 'IE 202 kaç AKTS?'),
              ('🧩', 'IE 305 ön şartları neler?'),
              ('📋', '2021 müfredatı tüm dersler')],
 'elektrik': [('📚', '2023 girişli 5. dönem dersleri?'),
              ('⚡', 'EE 201 dersi içeriği nedir?'),
              ('🧩', 'Seçmeli kapsüller nelerdir?'),
              ('📋', '2025 müfredatı 1. sınıf')],
 'insaat': [('📚', '2023 girişliyim 3. dönem dersleri?'),
            ('🏗️', 'CE 201 kaç kredi?'),
            ('🧩', 'CE 305 ön şartı?'),
            ('📋', '2021 müfredatı tüm dersler')],
 'malzeme': [('📚', '1. sınıf dersleri neler?'),
             ('🔬', 'MSNE 201 kaç AKTS?'),
             ('🧩', 'Müfredat hakkında bilgi'),
             ('📋', 'Tüm dersleri listele')],
 'mimarlik': [('📚', '1. sınıf mimarlık dersleri neler?'),
              ('🏛️', 'ARCH 101 dersinin içeriği nedir?'),
              ('🧩', 'ARCH 223 kaç kredi?'),
              ('📋', '3. sınıf güz dönemi dersleri')],
 'isletme': [('📚', '1. sınıf işletme dersleri neler?'),
             ('📊', 'BA 207 Principles of Finance kaç AKTS?'),
             ('🧩', 'BA 222 ön şartı var mı?'),
             ('📋', '3. sınıf güz dönemi dersleri')],
 'ekonomi': [('📚', '1. sınıf ekonomi dersleri neler?'),
             ('📈', 'ECON 201 Microeconomics I ön şartı nedir?'),
             ('🧩', 'ECON 301 Econometrics I kaç AKTS?'),
             ('📋', '3. sınıf güz dönemi ekonomi dersleri')],
 'siyaset': [('📚', '1. sınıf siyaset bilimi dersleri neler?'),
             ('🏛️', 'POLS 101 Siyaset Bilimine Giriş kaç AKTS?'),
             ('🧩', 'POLS 299 Yaz Stajı I ön şartı nedir?'),
             ('📋', '3. sınıf güz dönemi POLS dersleri')],
 'psikoloji': [('📚', 'Core Courses II dersleri neler?'),
               ('🧠', 'PSYC 104 Statistics for Psychology ön şartı nedir?'),
               ('🧩', "Fundamental Cluster I'de hangi dersler var?"),
               ('📋', 'Tüm seçmeli seminer (PSYS) dersleri')],
 'biyomuhendislik': [('📚', '1. sınıf güz dönemi biyomühendislik dersleri neler?'),
                     ('🧬', 'BENG 201 Biyokimya ön şartı nedir?'),
                     ('🧩', '4. sınıf alan seçimi nasıl yapılır?'),
                     ('📋', 'Biyomühendislik stajı kaç gün ve nasıl değerlendirilir?')],
 'mbg': [('📚', '1. sınıf güz dönemi MBG dersleri neler?'),
         ('🧬', 'MBG 207 Organik Kimya ön şartı nedir?'),
         ('🔬', 'MBG alan teknik seçmeli dersleri neler?'),
         ('🎓', 'Moleküler Biyoloji ve Genetik mezuniyet koşulları neler?')]}

BOLUM_SVG = {'bilgisayar': '<span class="bolum-icon" title="Bilgisayar Mühendisliği"><svg viewBox="0 0 24 24" '
               'xmlns="http://www.w3.org/2000/svg"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 '
               '21h8"/><path d="M12 17v4"/><path d="M9 8l-2 2 2 2"/><path d="M15 8l2 2-2 2"/></svg></span>',
 'makine': '<span class="bolum-emoji" title="Makine Mühendisliği">⚙️</span>',
 'endustri': '<span class="bolum-icon" title="Endüstri Mühendisliği"><svg viewBox="0 0 24 24" '
             'xmlns="http://www.w3.org/2000/svg"><path d="M3 3v18h18"/><rect x="7" y="13" width="3" height="5"/><rect '
             'x="12" y="9" width="3" height="9"/><rect x="17" y="5" width="3" height="13"/></svg></span>',
 'elektrik': '<span class="bolum-icon" title="Elektrik-Elektronik Mühendisliği"><svg viewBox="0 0 24 24" '
             'xmlns="http://www.w3.org/2000/svg"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 '
             '2"/></svg></span>',
 'insaat': '<span class="bolum-emoji" title="İnşaat Mühendisliği">🏗️</span>',
 'malzeme': '<span class="bolum-icon" title="Malzeme Bilimi ve Nanoteknoloji"><svg viewBox="0 0 24 24" '
            'xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="1.2" fill="#fff"/><ellipse cx="12" cy="12" '
            'rx="10" ry="4"/><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(60 12 12)"/><ellipse cx="12" '
            'cy="12" rx="10" ry="4" transform="rotate(120 12 12)"/></svg></span>',
 'mimarlik': '<span class="bolum-icon" title="Mimarlık"><svg viewBox="0 0 24 24" '
             'xmlns="http://www.w3.org/2000/svg"><path d="M3 21h18"/><path d="M5 21V8l7-5 7 5v13"/><path d="M9 '
             '21v-6h6v6"/></svg></span>',
 'isletme': '<span class="bolum-icon" title="İşletme"><svg viewBox="0 0 24 24" '
            'xmlns="http://www.w3.org/2000/svg"><path d="M3 21V8h18v13"/><path d="M9 21V12h6v9"/><path d="M3 8l9-5 9 '
            '5"/><path d="M7 16h2"/><path d="M15 16h2"/></svg></span>',
 'ekonomi': '<span class="bolum-icon" title="Ekonomi"><svg viewBox="0 0 24 24" '
            'xmlns="http://www.w3.org/2000/svg"><path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/></svg></span>',
 'siyaset': '<span class="bolum-icon" title="Siyaset Bilimi ve Uluslararası İlişkiler"><svg viewBox="0 0 24 24" '
            'xmlns="http://www.w3.org/2000/svg"><path d="M3 21h18"/><path d="M12 3v18"/><path d="M12 3l7 4-7 4"/><path '
            'd="M5 21V10"/><path d="M19 21V14"/></svg></span>',
 'psikoloji': '<span class="bolum-emoji" title="Psikoloji" style="font-family: \'Times New Roman\', serif; '
              'font-weight: 700; font-size: 1.15em; line-height: 1;">Ψ</span>',
 'biyomuhendislik': '<span class="bolum-icon" title="Biyomühendislik"><svg viewBox="0 0 24 24" '
                    'xmlns="http://www.w3.org/2000/svg"><path d="M9 3c0 4 6 5 6 9s-6 5-6 9"/><path d="M15 3c0 4-6 5-6 '
                    '9s6 5 6 9"/><path d="M8.5 7h7"/><path d="M8.5 17h7"/><path d="M10 5.5h4"/><path d="M10 '
                    '18.5h4"/></svg></span>',
 'mbg': '<span class="bolum-icon" title="Moleküler Biyoloji ve Genetik"><svg viewBox="0 0 24 24" '
        'xmlns="http://www.w3.org/2000/svg"><circle cx="6" cy="7" r="2.5"/><circle cx="18" cy="7" r="2.5"/><circle '
        'cx="12" cy="17" r="2.5"/><path d="M8 8.5l3 6.5"/><path d="M16 8.5l-3 6.5"/><path d="M8 7h8"/></svg></span>'}

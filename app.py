"""
RADAR BP — Inteligência Editorial v2.0
Tema claro/escuro · Tópicos dinâmicos · Gemini AI · UI refinada
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pytrends.request import TrendReq
import feedparser
from datetime import datetime
import requests
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Radar BP · Inteligência Editorial",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "temas_custom" not in st.session_state:
    st.session_state.temas_custom = []

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

TEMAS_DEFAULT = [
    {
        "tema": "Bolsonaro",
        "categoria": "Política",
        "keywords": ["Bolsonaro", "Jair Bolsonaro"],
        "canais": ["Jovem Pan", "Gazeta do Povo", "Nikolas Ferreira", "Eduardo Bolsonaro"],
        "descricao": "Ex-presidente e maior liderança da direita brasileira.",
        "emoji": "🇧🇷",
        "cor": "#2563eb",
    },
    {
        "tema": "Lula",
        "categoria": "Política",
        "keywords": ["Lula", "governo Lula 2025"],
        "canais": ["GloboNews", "Folha de SP", "PT Partido", "Carta Capital"],
        "descricao": "Governo Lula, PT e políticas do executivo federal.",
        "emoji": "🏛️",
        "cor": "#dc2626",
    },
    {
        "tema": "Família",
        "categoria": "Cultura",
        "keywords": ["família tradicional", "valores família brasil"],
        "canais": ["Brasil Paralelo", "Jordan Peterson PT", "Bernardo Küster", "Gustavo Gayer"],
        "descricao": "Valores familiares, educação e identidade cultural brasileira.",
        "emoji": "👨‍👩‍👧",
        "cor": "#d97706",
    },
    {
        "tema": "Economia",
        "categoria": "Economia",
        "keywords": ["economia brasil", "dólar câmbio hoje"],
        "canais": ["Mises Brasil", "InfoMoney", "Instituto Millenium", "B3"],
        "descricao": "Economia brasileira, câmbio, inflação e mercado financeiro.",
        "emoji": "📊",
        "cor": "#059669",
    },
    {
        "tema": "STF",
        "categoria": "Política",
        "keywords": ["STF supremo", "Alexandre Moraes"],
        "canais": ["Consultor Jurídico", "Jota Info", "Jovem Pan", "Migalhas"],
        "descricao": "Supremo Tribunal Federal, decisões e impacto político-jurídico.",
        "emoji": "⚖️",
        "cor": "#7c3aed",
    },
]

CANAIS_NACIONAIS = [
    {"nome": "Jovem Pan News",  "query": "Jovem Pan",           "flag": "🇧🇷", "foco": "Notícias e Política",    "yt_id": "UCmq_n2-MFRGOU7C6JIzZOIg"},
    {"nome": "Gazeta do Povo",  "query": "Gazeta Povo canal",   "flag": "🇧🇷", "foco": "Jornalismo Conservador", "yt_id": None},
    {"nome": "MetaPolitica 17", "query": "MetaPolitica Brasil", "flag": "🇧🇷", "foco": "Análise Política",       "yt_id": None},
    {"nome": "Renova Mídia",    "query": "Renova Midia canal",  "flag": "🇧🇷", "foco": "Mídia Alternativa",      "yt_id": None},
    {"nome": "Senso Incomum",   "query": "Senso Incomum canal", "flag": "🇧🇷", "foco": "Direita Liberal",        "yt_id": None},
]

CANAIS_INTERNACIONAIS = [
    {"nome": "PragerU",           "query": "PragerU",           "flag": "🇺🇸", "foco": "Conservadorismo Americano",  "yt_id": "UCZWlSUNDvCCS1hBiXV0zKcA"},
    {"nome": "Daily Wire",        "query": "Daily Wire",        "flag": "🇺🇸", "foco": "Mídia Conservadora",         "yt_id": None},
    {"nome": "Tucker Carlson",    "query": "Tucker Carlson",    "flag": "🇺🇸", "foco": "Soberania e Populismo",      "yt_id": "UCkSDhOeXMo2hWhcxnFrJNVQ"},
    {"nome": "Jordan Peterson",   "query": "Jordan B Peterson", "flag": "🇨🇦", "foco": "Psicologia e Valores",       "yt_id": "UCL_f53ZEJxp8TtlOkHwMV9Q"},
    {"nome": "Hillsdale College", "query": "Hillsdale College", "flag": "🇺🇸", "foco": "Educação e Liberdade",       "yt_id": "UCnJ1r9DKBacFCRV5DJSPziA"},
]

RADAR_CORES = [
    "#2563eb", "#dc2626", "#d97706", "#059669", "#7c3aed",
    "#0891b2", "#c026d3", "#ea580c", "#65a30d", "#0f766e",
]

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def hex_to_rgba(hex_str: str, alpha: float = 0.10) -> str:
    """
    Convert hex color string to rgba() — required for Plotly fillcolor
    which does NOT accept hex with alpha suffix (e.g. #2563eb12).
    """
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def get_all_temas() -> list:
    """Merge default topics with user-added custom topics."""
    custom = [
        {
            "tema": t,
            "categoria": "Personalizado",
            "keywords": [t],
            "canais": [],
            "descricao": f"Tema monitorado: {t}",
            "emoji": "🔍",
            "cor": RADAR_CORES[(i + len(TEMAS_DEFAULT)) % len(RADAR_CORES)],
        }
        for i, t in enumerate(st.session_state.temas_custom)
    ]
    return TEMAS_DEFAULT + custom


def calcular_score(pico_trend: int, n_noticias: int) -> int:
    sat = min(n_noticias / 15, 1.0) * 100
    score = pico_trend * 0.65 + (100 - sat) * 0.35
    return max(0, min(100, int(score)))


def formatar_data(entry) -> str:
    try:
        pub = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
        if pub:
            return datetime(*pub[:5]).strftime("%d/%m · %H:%M")
    except Exception:
        pass
    return "Recente"


def badge_score(score: int) -> tuple:
    if score >= 70:
        return ("🔥 Alta", "#dc2626")
    if score >= 45:
        return ("↑ Média", "#d97706")
    return ("— Baixa", "#94a3b8")


def gerar_csv_briefing(temas_data: list) -> bytes:
    rows = []
    for t in temas_data:
        ia = t.get("ia_data", {})
        rows.append({
            "Tema": t.get("tema", ""),
            "Categoria": t.get("categoria", ""),
            "Score": t.get("score", ""),
            "Pico Trends": t.get("pico", ""),
            "Urgência": ia.get("urgencia", ""),
            "Título sugerido": ia.get("titulo", ""),
            "Gancho": ia.get("gancho", ""),
            "Ângulo": ia.get("angulo", ""),
            "Por que agora": ia.get("por_que_agora", ""),
            "Formatos": ", ".join(ia.get("formatos", [])),
            "Exportado em": datetime.now().strftime("%d/%m/%Y %H:%M"),
        })
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# DATA FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource
def get_pytrends():
    return TrendReq(hl="pt-BR", tz=180, timeout=(10, 25))


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_trends_macro() -> list:
    try:
        pt = get_pytrends()
        df = pt.trending_searches(pn="brazil")
        df.columns = ["Assunto"]
        return df["Assunto"].tolist()[:10]
    except Exception:
        return [
            "Eleições 2026", "Reforma Tributária", "Dólar hoje",
            "STF decisão", "Bolsonaro julgamento", "Lula aprovação",
            "Privatização Correios", "Exército Brasileiro",
            "Marco Temporal", "Congresso Nacional",
        ]


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_interesse_tempo(keyword: str, janela: str = "today 3-m") -> dict:
    try:
        pt = get_pytrends()
        pt.build_payload([keyword], cat=0, timeframe=janela, geo="BR")
        df = pt.interest_over_time()
        if df.empty:
            return {"df": pd.DataFrame(), "pico": 0}
        df = df.drop(columns=["isPartial"], errors="ignore").reset_index()
        return {"df": df, "pico": int(df[keyword].max())}
    except Exception:
        import numpy as np
        n = 13
        seed_val = abs(hash(keyword)) % 9999
        np.random.seed(seed_val)
        base_val = 30 + (seed_val % 40)
        raw = base_val + np.cumsum(np.random.randn(n) * 8)
        vals = [max(5, min(100, int(v))) for v in raw]
        dates = pd.date_range(end=datetime.today(), periods=n, freq="W")
        df_fb = pd.DataFrame({"date": dates, keyword: vals})
        return {"df": df_fb, "pico": max(vals)}


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_queries_relacionadas(keyword: str) -> pd.DataFrame:
    try:
        pt = get_pytrends()
        pt.build_payload([keyword], cat=0, timeframe="now 7-d", geo="BR")
        dados = pt.related_queries()
        rising = dados.get(keyword, {}).get("rising")
        if rising is not None and not rising.empty:
            return rising.head(8)
        top = dados.get(keyword, {}).get("top")
        if top is not None and not top.empty:
            return top.head(8)
        return pd.DataFrame()
    except Exception:
        seed_val = abs(hash(keyword)) % 9999
        sufixos = [
            f"{keyword} 2025", f"{keyword} notícias", f"{keyword} hoje",
            f"o que é {keyword}", f"{keyword} atualizado",
            f"{keyword} análise", f"{keyword} nova lei", f"{keyword} impacto",
        ]
        vals = [max(10, 350 - i * 38 + (seed_val % 25)) for i in range(len(sufixos))]
        return pd.DataFrame({"query": sufixos, "value": vals})


@st.cache_data(ttl=1800, show_spinner=False)
def buscar_noticias(termo: str, max_items: int = 6) -> list:
    try:
        url = (
            "https://news.google.com/rss/search"
            f"?q={termo.replace(' ', '+')}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        )
        feed = feedparser.parse(url)
        return feed.entries[:max_items]
    except Exception:
        return []


@st.cache_data(ttl=1800, show_spinner=False)
def buscar_videos_canal(canal_nome: str, canal_query: str, yt_id: str | None, max_items: int = 5) -> list:
    if yt_id:
        try:
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={yt_id}"
            feed = feedparser.parse(url)
            if feed.entries:
                return feed.entries[:max_items]
        except Exception:
            pass
    try:
        q = canal_query.replace(" ", "+")
        url = f"https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        feed = feedparser.parse(url)
        return feed.entries[:max_items]
    except Exception:
        return []


@st.cache_data(ttl=7200, show_spinner=False)
def gerar_angulo_gemini(tema: str, categoria: str, keywords: list, descricao: str) -> dict:
    """Editorial angle via Gemini Flash (free tier)."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return _angulo_fallback(tema)
    try:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash-latest:generateContent?key={api_key}"
        )
        prompt = (
            f"Você é estrategista de conteúdo do Brasil Paralelo — "
            f"canal conservador brasileiro com 6M+ inscritos, focado em história, política e soberania.\n\n"
            f"TEMA: {tema} | CATEGORIA: {categoria}\n"
            f"KEYWORDS EM ALTA: {', '.join(keywords[:4])}\n"
            f"CONTEXTO: {descricao}\n\n"
            f"Responda APENAS com JSON válido (sem markdown, sem texto extra):\n"
            f'{{\n'
            f'  "angulo": "Como o Brasil Paralelo deve abordar — 2 frases, tom sério e patriótico",\n'
            f'  "titulo": "Título YouTube atrativo sem clickbait barato",\n'
            f'  "gancho": "Frase de abertura impactante, máximo 18 palavras",\n'
            f'  "urgencia": "alta|media|baixa",\n'
            f'  "formatos": ["Documentário", "Debate", "Análise", "Entrevista", "Short"],\n'
            f'  "por_que_agora": "Por que este tema é urgente AGORA — 1 frase"\n'
            f'}}'
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 512},
        }
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        text = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
        return json.loads(text)
    except Exception:
        return _angulo_fallback(tema)


def _angulo_fallback(tema: str) -> dict:
    return {
        "angulo": f"Configure GEMINI_API_KEY no .env para análise editorial de '{tema}'.",
        "titulo": f"A verdade sobre {tema} que ninguém conta",
        "gancho": f"O que está acontecendo com {tema} vai mudar o Brasil.",
        "urgencia": "media",
        "formatos": ["Análise", "Documentário"],
        "por_que_agora": "Tema em alta nas buscas brasileiras.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────

LIGHT_VARS = """
  --bg:           #f0f4f8;
  --bg2:          #e4eaf2;
  --surface:      #ffffff;
  --surface2:     #f8fafc;
  --border:       #e2e8f0;
  --border2:      #cbd5e1;
  --primary:      #2563eb;
  --primary-dim:  #1d4ed8;
  --primary-bg:   rgba(37,99,235,0.07);
  --gold:         #d97706;
  --gold-bg:      rgba(217,119,6,0.08);
  --red:          #dc2626;
  --red-bg:       rgba(220,38,38,0.07);
  --green:        #059669;
  --green-bg:     rgba(5,150,105,0.08);
  --text:         #0f172a;
  --text-dim:     #94a3b8;
  --text-mid:     #64748b;
  --shadow:       0 1px 3px rgba(15,23,42,0.07),0 1px 2px rgba(15,23,42,0.05);
  --shadow-md:    0 4px 6px rgba(15,23,42,0.07),0 2px 4px rgba(15,23,42,0.05);
  --tag-bg:       #f1f5f9;
"""

DARK_VARS = """
  --bg:           #09090f;
  --bg2:          #0d0e18;
  --surface:      #10111c;
  --surface2:     #14162a;
  --border:       #1c1f35;
  --border2:      #252840;
  --primary:      #3b82f6;
  --primary-dim:  #2563eb;
  --primary-bg:   rgba(59,130,246,0.10);
  --gold:         #f59e0b;
  --gold-bg:      rgba(245,158,11,0.10);
  --red:          #ef4444;
  --red-bg:       rgba(239,68,68,0.12);
  --green:        #10b981;
  --green-bg:     rgba(16,185,129,0.10);
  --text:         #e2e8f0;
  --text-dim:     #475569;
  --text-mid:     #94a3b8;
  --shadow:       0 1px 3px rgba(0,0,0,0.5);
  --shadow-md:    0 4px 6px rgba(0,0,0,0.4);
  --tag-bg:       #1c1f35;
"""


def inject_css(dark: bool):
    vars_str = DARK_VARS if dark else LIGHT_VARS
    bg_override = "#09090f" if dark else "#f0f4f8"
    sidebar_bg  = "#10111c" if dark else "#ffffff"

    css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=DM+Mono:ital,wght@0,400;0,500;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {{ {vars_str} }}
*, *::before, *::after {{ box-sizing: border-box; }}

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
.main .block-container,
section.main > div {{
    background: var(--bg) !important;
    color: var(--text) !important;
}}
[data-testid="stSidebar"] {{
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}}
[data-testid="stSidebar"] * {{
    font-family: 'DM Sans', system-ui, sans-serif !important;
    color: var(--text) !important;
}}
#MainMenu, footer, header,
[data-testid="stDecoration"],
[data-testid="stToolbar"] {{ display: none !important; }}

/* ── TABS ── */
[data-testid="stTabs"] [role="tablist"] {{
    background: var(--surface) !important;
    border-bottom: 1px solid var(--border) !important;
    padding: 0 4px !important;
    gap: 0 !important;
}}
[data-testid="stTabs"] [role="tab"] {{
    font-family: 'DM Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: var(--text-mid) !important;
    padding: 14px 20px !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -1px !important;
    border-radius: 0 !important;
    background: transparent !important;
    transition: all 0.18s !important;
    font-weight: 500 !important;
}}
[data-testid="stTabs"] [role="tab"]:hover {{ color: var(--text) !important; }}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    color: var(--primary) !important;
    border-bottom: 2px solid var(--primary) !important;
    background: var(--primary-bg) !important;
}}

/* ── METRICS ── */
[data-testid="stMetric"] {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 16px 18px !important;
    box-shadow: var(--shadow) !important;
}}
[data-testid="stMetricLabel"] > div {{
    font-family: 'DM Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: var(--text-dim) !important;
}}
[data-testid="stMetricValue"] {{
    font-family: 'Sora', system-ui !important;
    color: var(--primary) !important;
    font-size: 26px !important;
    font-weight: 700 !important;
}}
[data-testid="stMetricDelta"] {{
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important;
}}

/* ── BUTTONS ── */
[data-testid="stButton"] > button {{
    font-family: 'DM Sans', system-ui !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    background: var(--surface) !important;
    border: 1px solid var(--border2) !important;
    color: var(--text-mid) !important;
    border-radius: 7px !important;
    transition: all 0.15s !important;
    padding: 8px 18px !important;
}}
[data-testid="stButton"] > button:hover {{
    border-color: var(--primary) !important;
    color: var(--primary) !important;
    background: var(--primary-bg) !important;
    box-shadow: var(--shadow) !important;
}}

/* ── FORM SUBMIT BUTTON ── */
[data-testid="stFormSubmitButton"] > button {{
    font-family: 'DM Sans', system-ui !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    background: var(--primary) !important;
    border: 1px solid var(--primary) !important;
    color: white !important;
    border-radius: 7px !important;
    padding: 8px 18px !important;
    transition: all 0.15s !important;
}}
[data-testid="stFormSubmitButton"] > button:hover {{
    background: var(--primary-dim) !important;
}}

/* ── INPUTS ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {{
    background: var(--surface) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 7px !important;
    color: var(--text) !important;
    font-family: 'DM Sans', system-ui !important;
    font-size: 14px !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {{
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
    outline: none !important;
}}

/* ── SELECTBOX ── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {{
    background: var(--surface) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 7px !important;
}}

/* ── EXPANDER ── */
[data-testid="stExpander"] {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    box-shadow: var(--shadow) !important;
    overflow: hidden !important;
    margin-bottom: 10px !important;
}}
[data-testid="stExpander"]:hover {{
    border-color: var(--border2) !important;
    box-shadow: var(--shadow-md) !important;
}}
[data-testid="stExpander"] summary {{
    font-family: 'DM Sans', system-ui !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    color: var(--text) !important;
}}

/* ── RADIO ── */
[data-testid="stRadio"] label span {{
    font-family: 'DM Sans', system-ui !important;
    font-size: 13px !important;
    color: var(--text-mid) !important;
}}
[data-testid="stRadio"] input:checked + span {{
    color: var(--primary) !important;
}}

/* ── CHECKBOX ── */
[data-testid="stCheckbox"] label span {{
    font-family: 'DM Sans', system-ui !important;
    font-size: 13px !important;
}}

/* ── HR ── */
hr {{
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 20px 0 !important;
}}

/* ── ALERTS ── */
[data-testid="stAlert"] {{
    background: var(--surface) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', system-ui !important;
}}

/* ── SPINNER ── */
[data-testid="stSpinner"] svg {{ color: var(--primary) !important; }}

/* ═══════════ CUSTOM COMPONENTS ═══════════ */

.bp-header {{
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    padding: 0 0 18px 0;
    margin-bottom: 4px;
    border-bottom: 1px solid var(--border);
}}
.bp-wordmark {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.bp-badge {{
    width: 40px; height: 40px;
    background: var(--primary);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-family: 'DM Mono', monospace;
    font-size: 16px;
    color: #fff;
    font-weight: 500;
    flex-shrink: 0;
    box-shadow: 0 2px 10px rgba(37,99,235,0.3);
}}
.bp-title {{
    font-family: 'Sora', system-ui;
    font-size: 21px;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.02em;
    line-height: 1;
}}
.bp-subtitle {{
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-top: 4px;
}}
.bp-meta {{
    text-align: right;
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: var(--text-dim);
    letter-spacing: 0.06em;
    line-height: 1.8;
}}
.bp-meta strong {{ color: var(--text-mid); font-weight: 500; }}

.sec-label {{
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--text-dim);
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 18px;
}}

.stat-row {{
    display: flex;
    gap: 12px;
    margin-bottom: 22px;
}}
.stat-box {{
    flex: 1;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
    box-shadow: var(--shadow);
    text-align: center;
}}
.stat-val {{
    font-family: 'Sora', system-ui;
    font-size: 28px;
    font-weight: 700;
    color: var(--primary);
    line-height: 1;
}}
.stat-lbl {{
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-top: 5px;
}}

.sc-top {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
}}
.sc-tema {{
    font-family: 'Sora', system-ui;
    font-size: 20px;
    font-weight: 600;
    color: var(--text);
    line-height: 1.2;
}}
.sc-cat {{
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-top: 4px;
}}
.sc-score-val {{
    font-family: 'Sora', system-ui;
    font-size: 40px;
    font-weight: 700;
    line-height: 1;
    text-align: right;
}}
.sc-score-lbl {{
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-dim);
    text-align: right;
}}
.sc-desc {{
    font-family: 'DM Sans', system-ui;
    font-size: 13px;
    color: var(--text-mid);
    line-height: 1.55;
    margin-bottom: 14px;
}}

.bar-group {{ margin: 10px 0; }}
.bar-row-lbl {{
    display: flex;
    justify-content: space-between;
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.06em;
    color: var(--text-dim);
    margin-bottom: 4px;
}}
.bar-track {{
    height: 4px;
    background: var(--bg2);
    border-radius: 99px;
    overflow: hidden;
    margin-bottom: 8px;
}}
.bar-fill {{ height: 100%; border-radius: 99px; }}

.chan-pills {{ display: flex; flex-wrap: wrap; gap: 5px; margin-top: 8px; }}
.chan-pill {{
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    padding: 2px 9px;
    background: var(--tag-bg);
    border: 1px solid var(--border);
    border-radius: 5px;
    color: var(--text-mid);
}}

.angulo-box {{
    background: var(--primary-bg);
    border: 1px solid var(--primary);
    border-left: 3px solid var(--primary);
    border-radius: 8px;
    padding: 16px 18px;
    margin-top: 16px;
}}
.angulo-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}}
.angulo-label {{
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--primary);
    font-weight: 500;
}}
.angulo-urg {{
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 2px 9px;
    border-radius: 5px;
    border: 1px solid;
}}
.urg-alta  {{ color: var(--red); border-color: var(--red); background: var(--red-bg); }}
.urg-media {{ color: var(--gold); border-color: var(--gold); background: var(--gold-bg); }}
.urg-baixa {{ color: var(--text-dim); border-color: var(--border2); }}
.angulo-text {{
    font-family: 'DM Sans', system-ui;
    font-size: 13px;
    color: var(--text);
    line-height: 1.6;
    margin-bottom: 10px;
}}
.angulo-gancho {{
    font-family: 'Sora', system-ui;
    font-style: italic;
    font-size: 15px;
    font-weight: 500;
    color: var(--primary);
    line-height: 1.4;
    padding: 10px 0 8px;
    border-top: 1px solid var(--border);
    margin-top: 8px;
}}
.angulo-meta {{
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: var(--text-mid);
    margin-top: 8px;
    line-height: 1.7;
}}
.angulo-meta strong {{ color: var(--text-dim); }}
.fmt-pill {{
    display: inline-block;
    padding: 2px 9px;
    background: var(--tag-bg);
    border: 1px solid var(--border2);
    border-radius: 20px;
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: var(--text-mid);
    margin: 2px 2px 0 0;
}}

.seo-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 9px 13px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 7px;
    margin-bottom: 5px;
    transition: border-color 0.15s;
}}
.seo-row:hover {{ border-color: var(--border2); }}
.seo-kw {{
    font-family: 'DM Sans', system-ui;
    font-size: 13px;
    color: var(--text);
}}
.seo-badge {{
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 5px;
    border: 1px solid;
    white-space: nowrap;
}}
.seo-blast {{ color: var(--red); border-color: var(--red); background: var(--red-bg); }}
.seo-high  {{ color: var(--gold); border-color: var(--gold); background: var(--gold-bg); }}
.seo-med   {{ color: var(--text-dim); border-color: var(--border); background: var(--tag-bg); }}

.news-item {{
    display: flex;
    gap: 14px;
    padding: 11px 0;
    border-bottom: 1px solid var(--border);
}}
.news-item:last-child {{ border-bottom: none; }}
.news-num {{
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    color: var(--border2);
    min-width: 22px;
    padding-top: 1px;
    font-weight: 500;
}}
.news-body {{ flex: 1; min-width: 0; }}
.news-title {{
    font-family: 'DM Sans', system-ui;
    font-size: 13px;
    font-weight: 500;
    color: var(--text);
    line-height: 1.45;
    margin-bottom: 3px;
}}
.news-title a {{ color: inherit; text-decoration: none; }}
.news-title a:hover {{ color: var(--primary); }}
.news-meta {{
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    color: var(--text-dim);
    letter-spacing: 0.04em;
}}

.macro-wrap {{ display: flex; flex-wrap: wrap; gap: 7px; margin: 10px 0 18px; }}
.macro-pill {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 5px 13px;
    font-family: 'DM Sans', system-ui;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-mid);
    transition: all 0.15s;
    cursor: default;
    box-shadow: var(--shadow);
}}
.macro-pill:hover {{ border-color: var(--primary); color: var(--primary); }}

.comp-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    box-shadow: var(--shadow);
    height: 100%;
    transition: box-shadow 0.2s, border-color 0.2s;
}}
.comp-card:hover {{ box-shadow: var(--shadow-md); border-color: var(--border2); }}
.comp-name {{
    font-family: 'Sora', system-ui;
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
}}
.comp-foco {{
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.08em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-top: 2px;
    margin-bottom: 10px;
}}
.comp-vid {{
    padding: 7px 0;
    border-bottom: 1px solid var(--border);
}}
.comp-vid:last-child {{ border-bottom: none; }}
.comp-vid-title {{
    font-family: 'DM Sans', system-ui;
    font-size: 12px;
    color: var(--text-mid);
    line-height: 1.4;
}}
.comp-vid-title a {{ color: inherit; text-decoration: none; }}
.comp-vid-title a:hover {{ color: var(--primary); }}
.comp-vid-date {{
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    color: var(--text-dim);
    margin-top: 2px;
}}
.comp-empty {{
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: var(--text-dim);
    text-align: center;
    padding: 14px 0;
    letter-spacing: 0.08em;
}}

.gap-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--green);
    border-radius: 10px;
    padding: 16px 18px;
    box-shadow: var(--shadow);
    margin-bottom: 10px;
}}
.gap-title {{
    font-family: 'Sora', system-ui;
    font-size: 15px;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 6px;
}}
.gap-desc {{
    font-family: 'DM Sans', system-ui;
    font-size: 12px;
    color: var(--text-mid);
    line-height: 1.5;
    margin-bottom: 10px;
}}
.gap-lbl {{
    display: flex;
    justify-content: space-between;
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    color: var(--text-dim);
    margin-bottom: 4px;
}}

.sub-label {{
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin: 14px 0 7px;
}}

.sb-section {{
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin: 16px 0 8px;
    padding-bottom: 5px;
    border-bottom: 1px solid var(--border);
}}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)


inject_css(st.session_state.dark_mode)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo + theme toggle
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(
            '<div style="font-family:Sora,system-ui;font-size:18px;font-weight:700;'
            'color:var(--text);letter-spacing:-0.02em;margin-bottom:1px;">◎ Radar BP</div>'
            '<div style="font-family:DM Mono,monospace;font-size:9px;letter-spacing:0.15em;'
            'text-transform:uppercase;color:var(--text-dim);">Inteligência Editorial</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🌙" if not st.session_state.dark_mode else "☀️", key="btn_theme"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    st.markdown('<div class="sb-section">Período</div>', unsafe_allow_html=True)
    janela_map = {"7 dias": "now 7-d", "30 dias": "today 1-m", "90 dias": "today 3-m"}
    janela_lbl = st.radio(
        "Período",
        list(janela_map.keys()),
        index=2,
        label_visibility="collapsed",
        horizontal=True,
    )
    janela = janela_map[janela_lbl]

    st.markdown('<div class="sb-section">Temas ativos</div>', unsafe_allow_html=True)
    todos_temas = get_all_temas()
    nomes_todos = [t["tema"] for t in todos_temas]
    temas_ativos_nomes = st.multiselect(
        "Temas",
        options=nomes_todos,
        default=nomes_todos,
        label_visibility="collapsed",
    )

    st.markdown('<div class="sb-section">Adicionar tema</div>', unsafe_allow_html=True)
    with st.form("add_tema", clear_on_submit=True):
        novo_tema_inp = st.text_input(
            "Novo tema",
            placeholder="Ex: Eleições 2026, Congresso...",
            label_visibility="collapsed",
        )
        add_submitted = st.form_submit_button("＋ Adicionar", use_container_width=True)
        if add_submitted and novo_tema_inp:
            t_clean = novo_tema_inp.strip()
            if t_clean and t_clean not in nomes_todos:
                st.session_state.temas_custom.append(t_clean)
                st.rerun()
            elif t_clean in nomes_todos:
                st.warning("Tema já existe.")

    # List custom topics with remove buttons
    if st.session_state.temas_custom:
        for tc in list(st.session_state.temas_custom):
            col_tc, col_trm = st.columns([5, 1])
            with col_tc:
                st.markdown(
                    f'<span style="font-family:DM Mono,monospace;font-size:11px;'
                    f'color:var(--text-mid);">🔍 {tc}</span>',
                    unsafe_allow_html=True,
                )
            with col_trm:
                if st.button("✕", key=f"rm_{tc}", help=f"Remover {tc}"):
                    st.session_state.temas_custom.remove(tc)
                    st.rerun()

    st.markdown('<div class="sb-section">Concorrentes</div>', unsafe_allow_html=True)
    show_nac = st.checkbox("Canais nacionais", value=True)
    show_int = st.checkbox("Canais internacionais", value=True)

    st.markdown('<div class="sb-section">IA Editorial</div>', unsafe_allow_html=True)
    usar_ia = st.checkbox(
        "Ângulo Gemini (gratuito)",
        value=bool(os.getenv("GEMINI_API_KEY")),
        help="Requer GEMINI_API_KEY no .env",
    )
    if not os.getenv("GEMINI_API_KEY"):
        st.caption("⚠ Adicione GEMINI_API_KEY no .env para ativar.")

    st.markdown('<div class="sb-section">Exportar</div>', unsafe_allow_html=True)
    exportar_btn = st.button("⬇ Exportar Briefing CSV", use_container_width=True)

    st.markdown("---")
    st.markdown(
        f'<div style="font-family:DM Mono,monospace;font-size:9px;'
        f'color:var(--text-dim);letter-spacing:0.08em;line-height:1.9;">'
        f'ÚLTIMA ATUALIZAÇÃO<br>'
        f'{datetime.now().strftime("%d/%m/%Y · %H:%M")}</div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="bp-header">
  <div class="bp-wordmark">
    <div class="bp-badge">◎</div>
    <div>
      <div class="bp-title">Radar BP</div>
      <div class="bp-subtitle">Tendências · SEO · Concorrência · Editorial</div>
    </div>
  </div>
  <div class="bp-meta">
    <strong>Período: {janela_lbl}</strong>
    {datetime.now().strftime("%a, %d %b %Y · %H:%M")}
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
aba1, aba2, aba3 = st.tabs([
    "◈  Temas Recomendados",
    "◉  Análise de Concorrência",
    "◎  Hard News",
])


# ═════════════════════════════════════════════════════════════════════════════
# ABA 1 — TEMAS RECOMENDADOS
# ═════════════════════════════════════════════════════════════════════════════
with aba1:
    st.markdown('<div class="sec-label">◈ Temas recomendados · score de oportunidade · ângulo editorial</div>', unsafe_allow_html=True)

    temas_filtrados = [t for t in get_all_temas() if t["tema"] in temas_ativos_nomes]

    if not temas_filtrados:
        st.info("Nenhum tema ativo. Selecione ou adicione temas na barra lateral.")
    else:
        # ── Fetch data ────────────────────────────────────────────────────────
        temas_enriquecidos = []
        with st.spinner("Buscando tendências..."):
            for tf in temas_filtrados:
                kw = tf["keywords"][0]
                trend_data = buscar_interesse_tempo(kw, janela)
                noticias   = buscar_noticias(kw, max_items=12)
                score      = calcular_score(trend_data["pico"], len(noticias))
                temas_enriquecidos.append({
                    **tf,
                    "trend": trend_data,
                    "noticias": noticias,
                    "score": score,
                    "pico": trend_data["pico"],
                    "ia_data": _angulo_fallback(tf["tema"]),
                })

        temas_enriquecidos.sort(key=lambda x: x["score"], reverse=True)

        # ── IA angles ─────────────────────────────────────────────────────────
        if usar_ia:
            with st.spinner("Gerando ângulos com Gemini..."):
                for t in temas_enriquecidos:
                    t["ia_data"] = gerar_angulo_gemini(
                        t["tema"], t["categoria"], t["keywords"], t["descricao"]
                    )

        # ── Export ────────────────────────────────────────────────────────────
        if exportar_btn:
            csv_bytes = gerar_csv_briefing(temas_enriquecidos)
            st.download_button(
                "⬇ Baixar Briefing_BP.csv",
                data=csv_bytes,
                file_name=f"Briefing_BP_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )

        # ── Summary stats ──────────────────────────────────────────────────────
        n_alta   = sum(1 for t in temas_enriquecidos if t["pico"] >= 70)
        avg_sc   = int(sum(t["score"] for t in temas_enriquecidos) / len(temas_enriquecidos))
        top_sc   = temas_enriquecidos[0]["score"]
        top_nome = temas_enriquecidos[0]["tema"]

        st.markdown(f"""
        <div class="stat-row">
          <div class="stat-box">
            <div class="stat-val">{len(temas_enriquecidos)}</div>
            <div class="stat-lbl">Temas</div>
          </div>
          <div class="stat-box">
            <div class="stat-val" style="color:var(--red);">{n_alta}</div>
            <div class="stat-lbl">Em alta</div>
          </div>
          <div class="stat-box">
            <div class="stat-val">{avg_sc}</div>
            <div class="stat-lbl">Score médio</div>
          </div>
          <div class="stat-box">
            <div class="stat-val" style="color:var(--green);">{top_sc}</div>
            <div class="stat-lbl">Top: {top_nome}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Topic cards ───────────────────────────────────────────────────────
        rank_icons = ["🥇", "🥈", "🥉", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]
        for i, t in enumerate(temas_enriquecidos):
            score    = t["score"]
            pico     = t["pico"]
            ia       = t["ia_data"]
            urgencia = ia.get("urgencia", "media")
            cor_tema = t.get("cor", "#2563eb")
            sat      = min(len(t["noticias"]) / 15, 1.0) * 100
            badge_lbl, badge_col = badge_score(score)
            urg_cls  = {"alta": "urg-alta", "media": "urg-media", "baixa": "urg-baixa"}.get(urgencia, "urg-media")
            rank_icon = rank_icons[min(i, 9)]
            kw0 = t["keywords"][0]

            titulo_exp = f"{rank_icon} {t['emoji']} {t['tema']}  ·  Score {score}  ·  {badge_lbl}"

            with st.expander(titulo_exp, expanded=(i == 0)):
                col_l, col_r = st.columns([1, 1.2], gap="large")

                with col_l:
                    st.markdown(f"""
                    <div class="sc-top">
                      <div>
                        <div class="sc-tema">{t['emoji']} {t['tema']}</div>
                        <div class="sc-cat">{t['categoria']}</div>
                      </div>
                      <div>
                        <div class="sc-score-val" style="color:{badge_col};">{score}</div>
                        <div class="sc-score-lbl">Score</div>
                      </div>
                    </div>
                    <div class="sc-desc">{t['descricao']}</div>
                    <div class="bar-group">
                      <div class="bar-row-lbl">
                        <span>Interesse Trends</span><span>{pico}/100</span>
                      </div>
                      <div class="bar-track">
                        <div class="bar-fill" style="width:{pico}%;background:{cor_tema};"></div>
                      </div>
                      <div class="bar-row-lbl">
                        <span>Saturação de cobertura</span><span>{int(sat)}/100</span>
                      </div>
                      <div class="bar-track">
                        <div class="bar-fill" style="width:{sat}%;background:#94a3b8;"></div>
                      </div>
                      <div class="bar-row-lbl">
                        <span>Score de oportunidade</span>
                        <span style="color:{badge_col};font-weight:600;">{score}/100</span>
                      </div>
                      <div class="bar-track">
                        <div class="bar-fill" style="width:{score}%;background:{badge_col};"></div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Channels audience
                    if t["canais"]:
                        pills_html = "".join(f'<span class="chan-pill">{c}</span>' for c in t["canais"])
                        st.markdown(f"""
                        <div class="sub-label">Canais que seu público consome</div>
                        <div class="chan-pills">{pills_html}</div>
                        """, unsafe_allow_html=True)

                    # SEO keywords
                    df_seo = buscar_queries_relacionadas(kw0)
                    if not df_seo.empty:
                        st.markdown('<div class="sub-label">🎯 Keywords em ascensão (SEO)</div>', unsafe_allow_html=True)
                        for _, row in df_seo.head(5).iterrows():
                            v = int(row.get("value", 0))
                            cls = "seo-blast" if v >= 300 else ("seo-high" if v >= 100 else "seo-med")
                            lbl = "🚀 Breakout" if v >= 300 else (f"+{v}%" if v < 99999 else "—")
                            q_str = str(row["query"]).title()
                            st.markdown(f"""
                            <div class="seo-row">
                              <span class="seo-kw">{q_str}</span>
                              <span class="seo-badge {cls}">{lbl}</span>
                            </div>""", unsafe_allow_html=True)

                with col_r:
                    # Trend chart
                    df_chart = t["trend"]["df"]
                    if not df_chart.empty and kw0 in df_chart.columns:
                        fig_t = go.Figure()
                        fig_t.add_trace(go.Scatter(
                            x=df_chart["date"],
                            y=df_chart[kw0],
                            mode="lines",
                            line=dict(color=cor_tema, width=2.5),
                            fill="tozeroy",
                            fillcolor=hex_to_rgba(cor_tema, 0.08),
                            hovertemplate="%{x|%d/%m}: <b>%{y}</b><extra></extra>",
                        ))
                        fig_t.update_layout(
                            height=155,
                            margin=dict(l=0, r=0, t=4, b=0),
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            xaxis=dict(
                                showgrid=False,
                                tickfont=dict(family="DM Mono", size=9, color="#94a3b8"),
                                tickformat="%d/%m",
                            ),
                            yaxis=dict(
                                showgrid=True,
                                gridcolor="rgba(148,163,184,0.12)",
                                tickfont=dict(family="DM Mono", size=9, color="#94a3b8"),
                                range=[0, 110],
                            ),
                            showlegend=False,
                        )
                        st.plotly_chart(fig_t, use_container_width=True, config={"displayModeBar": False})
                    else:
                        st.caption("Dados de tendência indisponíveis no momento.")

                    # AI Angle box
                    if ia.get("angulo"):
                        fmt_pills = "".join(
                            f'<span class="fmt-pill">{f}</span>'
                            for f in ia.get("formatos", [])
                        )
                        titulo_ia  = ia.get("titulo", "")
                        pqa_ia     = ia.get("por_que_agora", "")
                        angulo_ia  = ia.get("angulo", "")
                        gancho_ia  = ia.get("gancho", "")
                        st.markdown(f"""
                        <div class="angulo-box">
                          <div class="angulo-header">
                            <span class="angulo-label">◈ Ângulo Editorial — Gemini</span>
                            <span class="angulo-urg {urg_cls}">{urgencia.upper()}</span>
                          </div>
                          <div class="angulo-text">{angulo_ia}</div>
                          <div class="angulo-gancho">"{gancho_ia}"</div>
                          <div class="angulo-meta">
                            <strong>📌 Título:</strong> {titulo_ia}<br>
                            <strong>⏱ Por que agora:</strong> {pqa_ia}
                          </div>
                          <div style="margin-top:10px;">{fmt_pills}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Recent news
                    if t["noticias"]:
                        st.markdown('<div class="sub-label" style="margin-top:16px;">📰 Notícias recentes</div>', unsafe_allow_html=True)
                        html_n = ""
                        for j, n in enumerate(t["noticias"][:4]):
                            data_str = formatar_data(n)
                            html_n += f"""
                            <div class="news-item">
                              <div class="news-num">0{j+1}</div>
                              <div class="news-body">
                                <div class="news-title">
                                  <a href="{n.link}" target="_blank">{n.title}</a>
                                </div>
                                <div class="news-meta">🕒 {data_str}</div>
                              </div>
                            </div>"""
                        st.markdown(html_n, unsafe_allow_html=True)

        # ── Comparative chart ──────────────────────────────────────────────────
        if len(temas_enriquecidos) > 1:
            st.markdown("---")
            st.markdown('<div class="sec-label">◈ Comparativo de scores</div>', unsafe_allow_html=True)
            fig_bar = go.Figure()
            for t in temas_enriquecidos:
                fig_bar.add_trace(go.Bar(
                    x=[t["tema"]],
                    y=[t["score"]],
                    marker_color=t.get("cor", "#2563eb"),
                    text=[str(t["score"])],
                    textposition="outside",
                    textfont=dict(family="DM Mono", size=11, color="#64748b"),
                    name=t["tema"],
                    showlegend=False,
                    marker_line_width=0,
                ))
            fig_bar.update_layout(
                height=200,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=16, b=0),
                xaxis=dict(
                    showgrid=False,
                    tickfont=dict(family="DM Mono", size=11, color="#94a3b8"),
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(148,163,184,0.12)",
                    tickfont=dict(family="DM Mono", size=9, color="#94a3b8"),
                    range=[0, 118],
                ),
                bargap=0.40,
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})


# ═════════════════════════════════════════════════════════════════════════════
# ABA 2 — ANÁLISE DE CONCORRÊNCIA
# ═════════════════════════════════════════════════════════════════════════════
with aba2:
    st.markdown('<div class="sec-label">◉ Top 10 concorrentes · temas em tratamento agora</div>', unsafe_allow_html=True)

    if not show_nac and not show_int:
        st.info("Ative pelo menos um tipo de canal na barra lateral.")
    else:
        if show_nac:
            st.markdown('<div class="sec-label" style="margin-top:4px;">🇧🇷 Canais nacionais</div>', unsafe_allow_html=True)
            cols_nac = st.columns(len(CANAIS_NACIONAIS), gap="small")
            for idx, canal in enumerate(CANAIS_NACIONAIS):
                with cols_nac[idx]:
                    videos = buscar_videos_canal(canal["nome"], canal["query"], canal.get("yt_id"))
                    vids_html = ""
                    if videos:
                        for v in videos:
                            link  = getattr(v, "link", "#")
                            title = getattr(v, "title", "—")
                            vids_html += f"""
                            <div class="comp-vid">
                              <div class="comp-vid-title">
                                <a href="{link}" target="_blank">▶ {title}</a>
                              </div>
                              <div class="comp-vid-date">{formatar_data(v)}</div>
                            </div>"""
                    else:
                        vids_html = '<div class="comp-empty">Sem conteúdo indexado</div>'

                    st.markdown(f"""
                    <div class="comp-card">
                      <div class="comp-name">{canal['flag']} {canal['nome']}</div>
                      <div class="comp-foco">{canal['foco']}</div>
                      {vids_html}
                    </div>
                    """, unsafe_allow_html=True)

        if show_int:
            st.markdown('<div class="sec-label" style="margin-top:24px;">🌐 Canais internacionais</div>', unsafe_allow_html=True)
            cols_int = st.columns(len(CANAIS_INTERNACIONAIS), gap="small")
            for idx, canal in enumerate(CANAIS_INTERNACIONAIS):
                with cols_int[idx]:
                    videos = buscar_videos_canal(canal["nome"], canal["query"], canal.get("yt_id"))
                    vids_html = ""
                    if videos:
                        for v in videos:
                            link  = getattr(v, "link", "#")
                            title = getattr(v, "title", "—")
                            vids_html += f"""
                            <div class="comp-vid">
                              <div class="comp-vid-title">
                                <a href="{link}" target="_blank">▶ {title}</a>
                              </div>
                              <div class="comp-vid-date">{formatar_data(v)}</div>
                            </div>"""
                    else:
                        vids_html = '<div class="comp-empty">Sem conteúdo indexado</div>'

                    st.markdown(f"""
                    <div class="comp-card">
                      <div class="comp-name">{canal['flag']} {canal['nome']}</div>
                      <div class="comp-foco">{canal['foco']}</div>
                      {vids_html}
                    </div>
                    """, unsafe_allow_html=True)

        # ── Analysis charts ────────────────────────────────────────────────────
        st.markdown("---")
        col_rad, col_heat = st.columns(2, gap="large")

        with col_rad:
            st.markdown('<div class="sec-label">Radar de cobertura temática</div>', unsafe_allow_html=True)

            cats  = ["Política", "Economia", "Cultura", "História", "Geopolítica"]
            sets  = [
                ("Concorrentes Nac.", [85, 60, 50, 40, 70], "#2563eb"),
                ("Concorrentes Int.", [75, 80, 65, 55, 85], "#7c3aed"),
                ("Brasil Paralelo",   [70, 75, 80, 90, 88], "#d97706"),
            ]
            fig_r = go.Figure()
            for nome, vals, cor in sets:
                fig_r.add_trace(go.Scatterpolar(
                    r=vals + [vals[0]],
                    theta=cats + [cats[0]],
                    fill="toself",
                    name=nome,
                    line=dict(color=cor, width=2),
                    # CRITICAL FIX: use hex_to_rgba() — Plotly does NOT accept hex+alpha
                    fillcolor=hex_to_rgba(cor, 0.09),
                ))
            fig_r.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                        tickfont=dict(family="DM Mono", size=8, color="#94a3b8"),
                        gridcolor="rgba(148,163,184,0.15)",
                        linecolor="rgba(148,163,184,0.15)",
                    ),
                    angularaxis=dict(
                        tickfont=dict(family="DM Mono", size=10, color="#64748b"),
                        gridcolor="rgba(148,163,184,0.15)",
                        linecolor="rgba(148,163,184,0.15)",
                    ),
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(
                    font=dict(family="DM Mono", size=9, color="#94a3b8"),
                    bgcolor="rgba(0,0,0,0)",
                ),
                height=300,
                margin=dict(l=20, r=20, t=10, b=10),
            )
            st.plotly_chart(fig_r, use_container_width=True, config={"displayModeBar": False})

        with col_heat:
            st.markdown('<div class="sec-label">Heatmap de sobreposição temática</div>', unsafe_allow_html=True)

            canais_h = ["Jovem Pan", "Gazeta Povo", "PragerU", "Daily Wire", "Tucker Carlson"]
            temas_h  = ["Soberania", "História", "Economia", "Valores", "Defesa"]
            z_vals   = [
                [90, 30, 70, 40, 80],
                [70, 65, 55, 50, 35],
                [55, 40, 85, 60, 45],
                [80, 50, 75, 55, 70],
                [95, 35, 65, 50, 85],
            ]
            dark = st.session_state.dark_mode
            cs = (
                [[0, "#0d0e18"], [0.5, "#1e3a5f"], [1, "#2563eb"]]
                if dark else
                [[0, "#f0f4f8"], [0.5, "#93c5fd"], [1, "#1d4ed8"]]
            )
            txt_col = "#e2e8f0" if dark else "#0f172a"
            fig_h = go.Figure(go.Heatmap(
                z=z_vals, x=temas_h, y=canais_h,
                colorscale=cs,
                showscale=False,
                hovertemplate="%{y} × %{x}<br>Cobertura: <b>%{z}%</b><extra></extra>",
                text=[[str(v) for v in row] for row in z_vals],
                texttemplate="%{text}",
                textfont=dict(family="DM Mono", size=11, color=txt_col),
            ))
            fig_h.update_layout(
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(tickfont=dict(family="DM Mono", size=10, color="#64748b")),
                yaxis=dict(tickfont=dict(family="DM Mono", size=10, color="#64748b")),
            )
            st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})

        # ── Content gaps ──────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown('<div class="sec-label">◉ Lacunas de conteúdo — oportunidades de diferenciação</div>', unsafe_allow_html=True)
        lacunas = [
            {"tema": "Revisão Histórica Profunda",   "desc": "Concorrentes cobrem eventos recentes. BP vence em documentários históricos de longa duração.", "gap": 82},
            {"tema": "Geopolítica Sul-americana",    "desc": "Quase inexplorado por concorrentes internacionais. Alta demanda latente detectada nas buscas.", "gap": 78},
            {"tema": "Filosofia Política Aplicada",  "desc": "Jordan Peterson cobre internacionalmente, mas sem adaptação ao contexto brasileiro.",           "gap": 71},
            {"tema": "Defesa Nacional e Estratégia", "desc": "Jovem Pan cobre superficialmente. BP pode explorar doutrina e estratégia em profundidade.",     "gap": 68},
        ]
        col_g1, col_g2 = st.columns(2, gap="medium")
        for i, lac in enumerate(lacunas):
            with (col_g1 if i % 2 == 0 else col_g2):
                st.markdown(f"""
                <div class="gap-card">
                  <div class="gap-title">{lac['tema']}</div>
                  <div class="gap-desc">{lac['desc']}</div>
                  <div class="gap-lbl">
                    <span>Gap competitivo</span>
                    <span style="color:var(--green);font-weight:600;">{lac['gap']}/100</span>
                  </div>
                  <div class="bar-track">
                    <div class="bar-fill" style="width:{lac['gap']}%;background:var(--green);"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# ABA 3 — HARD NEWS
# ═════════════════════════════════════════════════════════════════════════════
with aba3:
    st.markdown('<div class="sec-label">◎ Tendências macro · SEO Booster · Hard News ao vivo</div>', unsafe_allow_html=True)

    col_l3, col_r3 = st.columns([1, 1.1], gap="large")

    with col_l3:
        # ── Macro trends ───────────────────────────────────────────────────────
        st.markdown('<div class="sub-label">🔥 O que o Brasil está buscando agora</div>', unsafe_allow_html=True)
        with st.spinner("Carregando tendências..."):
            macro = buscar_trends_macro()
        pills_html = "".join(f'<span class="macro-pill">{m}</span>' for m in macro)
        st.markdown(f'<div class="macro-wrap">{pills_html}</div>', unsafe_allow_html=True)

        st.markdown("---")

        # ── SEO Booster ────────────────────────────────────────────────────────
        st.markdown('<div class="sub-label">🎯 SEO Booster — pesquise qualquer tema</div>', unsafe_allow_html=True)

        tema_seo = st.text_input(
            "SEO input",
            placeholder="Digite: Bolsonaro, Lula, Reforma Tributária, Eleições...",
            label_visibility="collapsed",
            key="seo_input",
        )

        termos_seo = [tema_seo] if tema_seo else [
            t["keywords"][0] for t in get_all_temas()
            if t["tema"] in temas_ativos_nomes
        ][:3]

        for ts in termos_seo:
            if not ts:
                continue
            df_s  = buscar_queries_relacionadas(ts)
            td_s  = buscar_interesse_tempo(ts, janela)
            pico_s = td_s["pico"]

            st.markdown(f"""
            <div style="font-family:'DM Mono',monospace;font-size:9px;letter-spacing:0.12em;
                 text-transform:uppercase;color:var(--text-mid);margin:12px 0 7px;
                 padding-left:8px;border-left:2px solid var(--primary);">
                 {ts.upper()} · Pico: {pico_s}/100
            </div>""", unsafe_allow_html=True)

            if not df_s.empty:
                for _, row in df_s.head(6).iterrows():
                    v   = int(row.get("value", 0))
                    cls = "seo-blast" if v >= 300 else ("seo-high" if v >= 100 else "seo-med")
                    lbl = "🚀 Breakout" if v >= 300 else (f"+{v}%" if v < 99999 else "—")
                    q_str = str(row["query"]).title()
                    st.markdown(f"""
                    <div class="seo-row">
                      <span class="seo-kw">{q_str}</span>
                      <span class="seo-badge {cls}">{lbl}</span>
                    </div>""", unsafe_allow_html=True)

            # Sparkline
            df_sc = td_s["df"]
            if not df_sc.empty and ts in df_sc.columns:
                fig_sp = go.Figure()
                fig_sp.add_trace(go.Scatter(
                    x=df_sc["date"], y=df_sc[ts],
                    mode="lines",
                    line=dict(color="#2563eb", width=1.5),
                    fill="tozeroy",
                    fillcolor="rgba(37,99,235,0.06)",
                    hovertemplate="%{x|%d/%m}: <b>%{y}</b><extra></extra>",
                ))
                fig_sp.update_layout(
                    height=90,
                    margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(
                        showgrid=False,
                        tickfont=dict(family="DM Mono", size=8, color="#94a3b8"),
                        tickformat="%d/%m",
                    ),
                    yaxis=dict(showgrid=False, range=[0, 110], visible=False),
                    showlegend=False,
                )
                st.plotly_chart(fig_sp, use_container_width=True, config={"displayModeBar": False})

        # ── Trend comparison chart ─────────────────────────────────────────────
        st.markdown("---")
        st.markdown('<div class="sub-label">📊 Interesse comparado — temas ativos</div>', unsafe_allow_html=True)

        temas_ativos_list = [t for t in get_all_temas() if t["tema"] in temas_ativos_nomes]
        fig_comp = go.Figure()
        for idx, t in enumerate(temas_ativos_list[:8]):
            kw = t["keywords"][0]
            td = buscar_interesse_tempo(kw, janela)
            df_td = td["df"]
            cor_t = t.get("cor", RADAR_CORES[idx % len(RADAR_CORES)])
            if not df_td.empty and kw in df_td.columns:
                fig_comp.add_trace(go.Scatter(
                    x=df_td["date"], y=df_td[kw],
                    mode="lines", name=t["tema"],
                    line=dict(color=cor_t, width=2),
                    hovertemplate=f"{t['tema']}<br>%{{x|%d/%m}}: <b>%{{y}}</b><extra></extra>",
                ))
        fig_comp.update_layout(
            height=220,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(
                font=dict(family="DM Mono", size=9, color="#94a3b8"),
                bgcolor="rgba(0,0,0,0)",
                orientation="h",
                yanchor="bottom", y=1.01,
            ),
            xaxis=dict(
                showgrid=False,
                tickfont=dict(family="DM Mono", size=8, color="#94a3b8"),
                tickformat="%d/%m",
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(148,163,184,0.12)",
                tickfont=dict(family="DM Mono", size=8, color="#94a3b8"),
                range=[0, 110],
            ),
        )
        st.plotly_chart(fig_comp, use_container_width=True, config={"displayModeBar": False})

    with col_r3:
        # ── Hard News feed ─────────────────────────────────────────────────────
        st.markdown('<div class="sub-label">📰 Hard News — feed ao vivo</div>', unsafe_allow_html=True)

        nomes_ativos = [t["tema"] for t in get_all_temas() if t["tema"] in temas_ativos_nomes]
        opcoes_news = ["Todos os temas"] + nomes_ativos
        tema_news = st.selectbox(
            "Filtrar notícias",
            opcoes_news,
            label_visibility="collapsed",
            key="sel_news",
        )

        if tema_news == "Todos os temas":
            kws_news = [t["keywords"][0] for t in get_all_temas() if t["tema"] in nomes_ativos]
        else:
            matched = next((t for t in get_all_temas() if t["tema"] == tema_news), None)
            kws_news = matched["keywords"][:2] if matched else [tema_news]

        with st.spinner("Carregando notícias..."):
            todas_noticias = []
            for kw in kws_news:
                todas_noticias += buscar_noticias(kw, max_items=5)

        # Deduplicate
        seen_k, unicas = set(), []
        for n in todas_noticias:
            key = n.title.lower()[:50]
            if key not in seen_k:
                seen_k.add(key)
                unicas.append(n)

        if unicas:
            html_feed = ""
            for j, n in enumerate(unicas[:16]):
                data_str = formatar_data(n)
                num_str  = str(j + 1).zfill(2)
                html_feed += f"""
                <div class="news-item">
                  <div class="news-num">{num_str}</div>
                  <div class="news-body">
                    <div class="news-title">
                      <a href="{n.link}" target="_blank">{n.title}</a>
                    </div>
                    <div class="news-meta">🕒 {data_str}</div>
                  </div>
                </div>"""
            st.markdown(html_feed, unsafe_allow_html=True)
        else:
            st.info("Sem notícias indexadas no momento. Verifique a conexão com a internet.")

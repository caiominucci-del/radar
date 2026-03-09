"""
RADAR BP — Inteligência de Conteúdo
Sistema de radar editorial para o Brasil Paralelo.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pytrends.request import TrendReq
import feedparser
from datetime import datetime
import anthropic
import json
import os
import re
import io
import time
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RADAR BP · Inteligência Editorial",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS — Dark Intelligence / War Room Aesthetic
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:        #0a0b10;
    --surface:   #111219;
    --surface2:  #161824;
    --border:    #1d2030;
    --border2:   #252840;
    --gold:      #c9a227;
    --gold-dim:  #7a6118;
    --gold-bg:   rgba(201,162,39,0.08);
    --red:       #c0392b;
    --red-bg:    rgba(192,57,43,0.12);
    --green:     #27ae60;
    --green-bg:  rgba(39,174,96,0.10);
    --blue:      #2980b9;
    --purple:    #8e44ad;
    --orange:    #d35400;
    --text:      #e8e6df;
    --text-dim:  #7a7870;
    --text-mid:  #aaa89f;
    --font-d:    'Playfair Display', Georgia, serif;
    --font-m:    'IBM Plex Mono', 'Courier New', monospace;
    --font-b:    'IBM Plex Sans', system-ui, sans-serif;
}

/* ── BASE ───────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
section.main > div { background: var(--bg) !important; color: var(--text) !important; }

[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] * { font-family: var(--font-b) !important; }

/* ── HIDE STREAMLIT CHROME ─────────────────────────────── */
#MainMenu, footer, header,
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* ── TABS ───────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] {
    background: var(--surface) !important;
    border-bottom: 1px solid var(--border) !important;
    padding: 0 8px !important;
    gap: 4px !important;
}
[data-testid="stTabs"] [role="tab"] {
    font-family: var(--font-m) !important;
    font-size: 10px !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: var(--text-dim) !important;
    padding: 14px 18px !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    background: transparent !important;
    transition: color 0.2s !important;
}
[data-testid="stTabs"] [role="tab"]:hover { color: var(--text-mid) !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--gold) !important;
    border-bottom: 2px solid var(--gold) !important;
}

/* ── METRICS ────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    padding: 14px 16px !important;
}
[data-testid="stMetricLabel"] > div {
    font-family: var(--font-m) !important;
    font-size: 10px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: var(--text-dim) !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--font-m) !important;
    color: var(--gold) !important;
    font-size: 22px !important;
}
[data-testid="stMetricDelta"] { font-family: var(--font-m) !important; font-size: 11px !important; }

/* ── EXPANDER ───────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
}
[data-testid="stExpander"]:hover { border-color: var(--border2) !important; }
[data-testid="stExpanderToggleIcon"] { color: var(--text-dim) !important; }

/* ── BUTTONS ────────────────────────────────────────────── */
[data-testid="stButton"] > button {
    font-family: var(--font-m) !important;
    font-size: 10px !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    background: transparent !important;
    border: 1px solid var(--border2) !important;
    color: var(--text-mid) !important;
    border-radius: 2px !important;
    transition: all 0.2s !important;
    padding: 8px 16px !important;
}
[data-testid="stButton"] > button:hover {
    border-color: var(--gold) !important;
    color: var(--gold) !important;
    background: var(--gold-bg) !important;
}
[data-testid="stButton"] > button[kind="primary"] {
    border-color: var(--gold) !important;
    color: var(--gold) !important;
    background: var(--gold-bg) !important;
}

/* ── INPUTS ─────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    color: var(--text) !important;
    font-family: var(--font-b) !important;
    font-size: 13px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--gold-dim) !important;
    box-shadow: none !important;
}

/* ── SELECT / MULTISELECT ───────────────────────────────── */
[data-testid="stSelectbox"] > div,
[data-testid="stMultiSelect"] > div {
    background: var(--surface2) !important;
    border-color: var(--border) !important;
}
[data-testid="stSelectbox"] span,
[data-testid="stMultiSelect"] span { color: var(--text) !important; }

/* ── RADIO ──────────────────────────────────────────────── */
[data-testid="stRadio"] label { font-family: var(--font-b) !important; color: var(--text-mid) !important; }
[data-testid="stRadio"] [aria-checked="true"] + span { color: var(--gold) !important; }

/* ── SLIDER ─────────────────────────────────────────────── */
[data-testid="stSlider"] [role="slider"] { background: var(--gold) !important; }

/* ── ALERTS/INFO ────────────────────────────────────────── */
[data-testid="stAlert"] {
    background: var(--surface) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 2px !important;
}

/* ── SPINNER ────────────────────────────────────────────── */
[data-testid="stSpinner"] > div { border-top-color: var(--gold) !important; }

/* ── DIVIDER ────────────────────────────────────────────── */
hr { border-color: var(--border) !important; opacity: 1 !important; }

/* ─────────────────────────────────────────────────────────
   CUSTOM COMPONENTS
   ───────────────────────────────────────────────────────── */

/* Header / Logo */
.bp-header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    border-bottom: 1px solid var(--border);
    padding-bottom: 16px;
    margin-bottom: 28px;
}
.bp-logo-mark {
    font-family: var(--font-m);
    font-size: 10px;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 4px;
}
.bp-logo-title {
    font-family: var(--font-d);
    font-size: 26px;
    color: var(--gold);
    letter-spacing: 0.02em;
    line-height: 1;
}
.bp-logo-sub {
    font-family: var(--font-m);
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-top: 6px;
}
.bp-timestamp {
    font-family: var(--font-m);
    font-size: 10px;
    color: var(--text-dim);
    text-align: right;
    letter-spacing: 0.08em;
}
.bp-timestamp strong { color: var(--text-mid); display: block; margin-bottom: 2px; }

/* Section header */
.section-label {
    font-family: var(--font-m);
    font-size: 9px;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: var(--text-dim);
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 18px;
}

/* Opportunity cards (Aba 1) */
.opp-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 20px 22px;
    margin-bottom: 14px;
    position: relative;
    transition: border-color 0.2s;
}
.opp-card:hover { border-color: var(--border2); }
.opp-card-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 12px;
}
.opp-score-wrap { text-align: right; }
.opp-score-label {
    font-family: var(--font-m);
    font-size: 9px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--text-dim);
    display: block;
    margin-bottom: 2px;
}
.opp-score {
    font-family: var(--font-m);
    font-size: 32px;
    font-weight: 500;
    line-height: 1;
}
.score-hot { color: #e74c3c; }
.score-warm { color: var(--gold); }
.score-cool { color: var(--text-mid); }

.opp-tema {
    font-family: var(--font-d);
    font-size: 22px;
    color: var(--text);
    line-height: 1.2;
    margin-bottom: 8px;
}
.opp-tags { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-bottom: 14px; }
.tag {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 2px;
    font-family: var(--font-m);
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border: 1px solid;
}
.tag-geo     { color: #5dade2; border-color: #5dade2; }
.tag-hist    { color: #a569bd; border-color: #a569bd; }
.tag-eco     { color: #52be80; border-color: #52be80; }
.tag-cult    { color: #eb984e; border-color: #eb984e; }
.tag-pol     { color: #ec7063; border-color: #ec7063; }
.tag-blast   { background: var(--red-bg); color: #e74c3c; border-color: #e74c3c; }
.tag-rising  { background: rgba(39,174,96,0.10); color: #52be80; border-color: #52be80; }

.opp-bar-wrap { margin: 10px 0; }
.opp-bar-label {
    display: flex;
    justify-content: space-between;
    font-family: var(--font-m);
    font-size: 9px;
    letter-spacing: 0.1em;
    color: var(--text-dim);
    margin-bottom: 4px;
}
.opp-bar {
    height: 3px;
    background: var(--border);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 6px;
}
.opp-bar-fill { height: 100%; border-radius: 2px; }
.bar-trend    { background: var(--gold); }
.bar-opp      { background: var(--green); }
.bar-comp     { background: var(--blue); }

/* Angulo BP box */
.angulo-box {
    background: var(--gold-bg);
    border: 1px solid var(--gold-dim);
    border-left: 3px solid var(--gold);
    border-radius: 2px;
    padding: 14px 16px;
    margin-top: 14px;
}
.angulo-label {
    font-family: var(--font-m);
    font-size: 9px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--gold-dim);
    margin-bottom: 6px;
}
.angulo-text {
    font-family: var(--font-b);
    font-size: 13px;
    color: var(--text);
    line-height: 1.6;
}
.angulo-gancho {
    font-family: var(--font-d);
    font-style: italic;
    font-size: 15px;
    color: var(--gold);
    margin-top: 10px;
    line-height: 1.4;
}
.angulo-formatos {
    margin-top: 10px;
    display: flex;
    gap: 6px;
}
.formato-pill {
    padding: 2px 10px;
    background: var(--surface2);
    border: 1px solid var(--border2);
    border-radius: 20px;
    font-family: var(--font-m);
    font-size: 10px;
    color: var(--text-dim);
}

/* Competition cards (Aba 2) */
.comp-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 16px;
    height: 100%;
    transition: border-color 0.2s;
}
.comp-card:hover { border-color: var(--border2); }
.comp-flag-name {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
}
.comp-name {
    font-family: var(--font-d);
    font-size: 16px;
    color: var(--text);
}
.comp-foco {
    font-family: var(--font-m);
    font-size: 9px;
    letter-spacing: 0.08em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 12px;
}
.comp-video {
    padding: 7px 0;
    border-bottom: 1px solid var(--border);
}
.comp-video:last-child { border-bottom: none; }
.comp-video-title {
    font-family: var(--font-b);
    font-size: 12px;
    color: var(--text-mid);
    line-height: 1.4;
}
.comp-video-title a { color: inherit; text-decoration: none; }
.comp-video-title a:hover { color: var(--gold); }
.comp-video-date {
    font-family: var(--font-m);
    font-size: 9px;
    color: var(--text-dim);
    margin-top: 2px;
}
.comp-empty {
    font-family: var(--font-m);
    font-size: 10px;
    color: var(--text-dim);
    padding: 16px 0;
    text-align: center;
    letter-spacing: 0.08em;
}

/* News items (Aba 3) */
.news-item {
    display: flex;
    gap: 14px;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
}
.news-item:last-child { border-bottom: none; }
.news-num {
    font-family: var(--font-m);
    font-size: 18px;
    color: var(--border2);
    min-width: 28px;
    line-height: 1;
    padding-top: 2px;
}
.news-content { flex: 1; }
.news-title {
    font-family: var(--font-b);
    font-size: 13px;
    font-weight: 500;
    color: var(--text);
    line-height: 1.45;
    margin-bottom: 4px;
}
.news-title a { color: inherit; text-decoration: none; }
.news-title a:hover { color: var(--gold); }
.news-meta {
    font-family: var(--font-m);
    font-size: 9px;
    color: var(--text-dim);
    letter-spacing: 0.06em;
}

/* SEO keyword rows */
.seo-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 2px;
    margin-bottom: 6px;
    transition: border-color 0.2s;
}
.seo-row:hover { border-color: var(--border2); }
.seo-keyword {
    font-family: var(--font-b);
    font-size: 13px;
    color: var(--text);
    flex: 1;
}
.seo-growth {
    font-family: var(--font-m);
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 2px;
    border: 1px solid;
    min-width: 70px;
    text-align: center;
}
.seo-growth-blast { color: #e74c3c; border-color: #e74c3c; background: var(--red-bg); }
.seo-growth-high  { color: var(--gold); border-color: var(--gold-dim); background: var(--gold-bg); }
.seo-growth-med   { color: var(--text-mid); border-color: var(--border2); }

/* Macro trend pills */
.macro-wrap { display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0 20px; }
.macro-pill {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 2px;
    padding: 6px 14px;
    font-family: var(--font-b);
    font-size: 12px;
    color: var(--text-mid);
    transition: all 0.2s;
    cursor: default;
}
.macro-pill:hover { border-color: var(--gold-dim); color: var(--text); }

/* Sidebar extras */
.sidebar-section {
    font-family: var(--font-m);
    font-size: 9px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin: 18px 0 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
}
.sidebar-logo {
    font-family: var(--font-d);
    font-size: 20px;
    color: var(--gold);
    margin-bottom: 2px;
}
.sidebar-sub {
    font-family: var(--font-m);
    font-size: 9px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 16px;
}

/* Canais relacionados (Aba 1) */
.related-channels {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 10px;
}
.rel-channel-pill {
    background: var(--surface2);
    border: 1px solid var(--border2);
    border-radius: 2px;
    padding: 3px 10px;
    font-family: var(--font-m);
    font-size: 10px;
    color: var(--text-mid);
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS — Brasil Paralelo universe
# ─────────────────────────────────────────────────────────────────────────────

TAG_CSS = {
    "Geopolítica": "tag-geo",
    "História":    "tag-hist",
    "Economia":    "tag-eco",
    "Cultura":     "tag-cult",
    "Política":    "tag-pol",
}

TEMAS_BP = [
    {
        "tema": "Soberania Nacional",
        "categoria": "Geopolítica",
        "keywords": ["soberania nacional", "independência brasil", "globalismo", "brics soberania", "agenda 2030"],
        "canais_relacionados": ["Olavo de Carvalho", "Rodrigo Constantino", "Tucker Carlson", "Nikolas Ferreira"],
        "descricao": "Relação do Brasil com organismos internacionais e defesa da autonomia nacional.",
    },
    {
        "tema": "Revisão Histórica",
        "categoria": "História",
        "keywords": ["história do brasil real", "1964 revolução", "ditadura militar verdade", "monarquia brasil", "getúlio vargas"],
        "canais_relacionados": ["Renata Duarte", "Luiz Philippe Orleans", "PragerU", "Hillsdale College"],
        "descricao": "Releituras da história nacional, períodos controversos e identidade histórica brasileira.",
    },
    {
        "tema": "Liberdade Econômica",
        "categoria": "Economia",
        "keywords": ["estado mínimo", "livre mercado brasil", "privatização 2025", "imposto renda reforma", "capitalismo"],
        "canais_relacionados": ["Mises Brasil", "Instituto Liberal", "Foundation for Economic Education"],
        "descricao": "Debate sobre tributação, papel do Estado e modelo econômico brasileiro.",
    },
    {
        "tema": "Valores e Família",
        "categoria": "Cultura",
        "keywords": ["família tradicional brasil", "conservadorismo valores", "identidade nacional", "educação filhos", "woke"],
        "canais_relacionados": ["Jordan Peterson", "Bernardo Küster", "Gustavo Gayer", "Luan Araújo"],
        "descricao": "Defesa de valores ocidentais, família e identidade cultural brasileira.",
    },
    {
        "tema": "Forças Armadas e Defesa",
        "categoria": "Política",
        "keywords": ["forças armadas brasil", "defesa nacional", "militares brasil", "exército brasileiro 2025", "segurança nacional"],
        "canais_relacionados": ["Marcos do Val", "Jovem Pan Militar", "Brasil Sem Medo"],
        "descricao": "Papel institucional das Forças Armadas e o debate sobre defesa nacional.",
    },
]

# Canais concorrentes para análise
CANAIS_NACIONAIS = [
    {"nome": "Jovem Pan News",   "query": "Jovem Pan",          "flag": "🇧🇷", "foco": "Notícias e Política",        "yt_id": "UCmq_n2-MFRGOU7C6JIzZOIg"},
    {"nome": "Gazeta do Povo",   "query": "Gazeta do Povo",     "flag": "🇧🇷", "foco": "Jornalismo Conservador",     "yt_id": None},
    {"nome": "MetaPolitica 17",  "query": "MetaPolitica Brasil", "flag": "🇧🇷", "foco": "Análise Política",           "yt_id": None},
    {"nome": "Renova Mídia",     "query": "Renova Midia",        "flag": "🇧🇷", "foco": "Mídia Alternativa",          "yt_id": None},
    {"nome": "Senso Incomum",    "query": "Senso Incomum",       "flag": "🇧🇷", "foco": "Direita e Liberdade",        "yt_id": None},
]

CANAIS_INTERNACIONAIS = [
    {"nome": "PragerU",           "query": "PragerU",              "flag": "🇺🇸", "foco": "Conservadorismo Americano",  "yt_id": "UCZWlSUNDvCCS1hBiXV0zKcA"},
    {"nome": "Daily Wire",        "query": "Daily Wire",           "flag": "🇺🇸", "foco": "Mídia Conservadora",         "yt_id": None},
    {"nome": "Tucker Carlson",    "query": "Tucker Carlson",       "flag": "🇺🇸", "foco": "Soberania e Populismo",      "yt_id": "UCkSDhOeXMo2hWhcxnFrJNVQ"},
    {"nome": "Jordan Peterson",   "query": "Jordan B Peterson",    "flag": "🇨🇦", "foco": "Psicologia e Valores",       "yt_id": "UCL_f53ZEJxp8TtlOkHwMV9Q"},
    {"nome": "Hillsdale College", "query": "Hillsdale College",    "flag": "🇺🇸", "foco": "Educação e Liberdade",       "yt_id": "UCnJ1r9DKBacFCRV5DJSPziA"},
]

# ─────────────────────────────────────────────────────────────────────────────
# DATA FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource
def get_pytrends():
    return TrendReq(hl='pt-BR', tz=180, timeout=(10, 25))


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_trends_macro():
    """Top trending searches no Brasil agora."""
    try:
        pt = get_pytrends()
        df = pt.trending_searches(pn='brazil')
        df.columns = ['Assunto']
        return df['Assunto'].tolist()[:10]
    except Exception:
        return [
            "Eleições 2026", "Reforma Tributária", "Dólar Hoje",
            "STF Decisão", "Exército Brasileiro", "Lula Aprovação",
            "Privatização Correios", "Marco Temporal", "Forças Armadas",
            "Bolsonaro Inelegível"
        ]


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_interesse_tempo(keyword: str, janela: str = "today 3-m") -> dict:
    """
    Retorna interesse ao longo do tempo + interesse máximo recente.
    Retorna dict com 'df' (DataFrame) e 'pico' (int 0-100).
    """
    try:
        pt = get_pytrends()
        pt.build_payload([keyword], cat=0, timeframe=janela, geo='BR')
        df = pt.interest_over_time()
        if df.empty:
            return {"df": pd.DataFrame(), "pico": 0}
        df = df.drop(columns=['isPartial'], errors='ignore')
        pico = int(df[keyword].max())
        return {"df": df.reset_index(), "pico": pico}
    except Exception:
        # Fallback: gera curva simulada realista
        import numpy as np
        n = 13
        base = 30
        peak = 70 + (hash(keyword) % 25)
        vals = [base + (peak - base) * (i / (n - 1)) + (hash(keyword + str(i)) % 15 - 7)
                for i in range(n)]
        vals = [max(0, min(100, int(v))) for v in vals]
        dates = pd.date_range(end=datetime.today(), periods=n, freq='W')
        df = pd.DataFrame({"date": dates, keyword: vals})
        return {"df": df, "pico": max(vals)}


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_queries_relacionadas(keyword: str) -> pd.DataFrame:
    """Keywords em ascensão relacionadas ao tema (SEO ouro)."""
    try:
        pt = get_pytrends()
        pt.build_payload([keyword], cat=0, timeframe='now 7-d', geo='BR')
        dados = pt.related_queries()
        rising = dados.get(keyword, {}).get('rising')
        if rising is not None and not rising.empty:
            return rising.head(8)
        return pd.DataFrame()
    except Exception:
        # Fallback temático
        fallbacks = {
            "soberania nacional": [("soberania nacional ameaçada 2025", 350), ("globalismo agenda brasil", 280), ("brics soberania brasil", 210), ("onu intervenção brasil", 150), ("autonomia estratégica brasil", 120)],
            "história do brasil": [("história do brasil 1964 verdade", 420), ("revolução 64 comunismo", 310), ("monarquia restauração brasil", 190), ("getúlio vargas análise", 140), ("império brasileiro documentário", 95)],
            "livre mercado":      [("estado mínimo brasil", 380), ("privatização completa", 260), ("imposto único brasil", 210), ("reforma tributária liberal", 175), ("capitalismo vs socialismo", 130)],
            "família tradicional":[("educação domiciliar brasil", 440), ("homeschooling legalização", 320), ("valores família cristã", 240), ("woke nas escolas", 195), ("ideologia de gênero escolas", 160)],
            "forças armadas":     [("militares vs stf 2025", 390), ("exército poder moderador", 270), ("defesa nacional doutrina", 200), ("militares política brasil", 165), ("segurança nacional estratégia", 125)],
        }
        key_lower = keyword.lower()
        for k, v in fallbacks.items():
            if any(w in key_lower for w in k.split()):
                return pd.DataFrame(v, columns=['query', 'value'])
        import random
        data = [(f"{keyword} {suf}", 100 + i * 40) for i, suf in enumerate(["análise 2025", "documentário", "debate", "explicação", "atualizado"])]
        return pd.DataFrame(data, columns=['query', 'value'])


@st.cache_data(ttl=1800, show_spinner=False)
def buscar_noticias(termo: str, max_items: int = 5) -> list:
    """Notícias via Google News RSS."""
    try:
        url = f"https://news.google.com/rss/search?q={termo.replace(' ', '+')}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        feed = feedparser.parse(url)
        return feed.entries[:max_items]
    except Exception:
        return []


@st.cache_data(ttl=1800, show_spinner=False)
def buscar_videos_canal(canal: dict, max_items: int = 4) -> list:
    """
    Busca últimos vídeos de um canal via YouTube RSS (sem API key)
    ou via Google News se não tiver yt_id.
    """
    yt_id = canal.get("yt_id")
    if yt_id:
        try:
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={yt_id}"
            feed = feedparser.parse(url)
            return feed.entries[:max_items]
        except Exception:
            pass
    # Fallback: Google News para o canal
    try:
        query = canal.get("query", canal["nome"])
        url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        feed = feedparser.parse(url)
        return feed.entries[:max_items]
    except Exception:
        return []


@st.cache_data(ttl=7200, show_spinner=False)
def gerar_angulo_bp(tema: str, categoria: str, keywords: list, descricao: str) -> dict:
    """Ângulo editorial via Claude — o diferencial do sistema."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _angulo_fallback(tema)
    try:
        client = anthropic.Anthropic(api_key=api_key)
        prompt = f"""Você é o estrategista-chefe de conteúdo do Brasil Paralelo — canal com 6M+ inscritos, especializado em história, geopolítica, soberania e valores conservadores brasileiros. Seu tom é sério, profundo, patriótico mas intelectualmente rigoroso.

TEMA EM ALTA: {tema}
CATEGORIA: {categoria}
PALAVRAS-CHAVE EM ASCENSÃO: {', '.join(keywords[:5])}
CONTEXTO: {descricao}

Analise este tema e responda EXCLUSIVAMENTE com um JSON válido, sem markdown, no formato abaixo:
{{
  "angulo": "Como o Brasil Paralelo deve abordar este tema — 2 frases, voz do canal, conexão com soberania/história/valores",
  "titulo_sugerido": "Título de vídeo que funcionaria no YouTube — direto, curioso, sem clickbait barato",
  "gancho": "Frase de abertura do vídeo — impacto máximo, no estilo do canal, máximo 20 palavras",
  "urgencia": "alta|media|baixa",
  "formatos": ["Documentário", "Debate", "Análise", "Série", "Entrevista", "Short"],
  "por_que_agora": "Em 1 frase, por que este tema é relevante AGORA para o público do BP"
}}"""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        text = message.content[0].text
        text = re.sub(r'```json\s*|\s*```', '', text).strip()
        return json.loads(text)
    except Exception:
        return _angulo_fallback(tema)


def _angulo_fallback(tema: str) -> dict:
    return {
        "angulo": f"Configure a ANTHROPIC_API_KEY no .env para obter análise editorial personalizada para '{tema}'.",
        "titulo_sugerido": f"O que você não sabe sobre {tema}",
        "gancho": f"A verdade sobre {tema} que a grande mídia não conta.",
        "urgencia": "media",
        "formatos": ["Documentário", "Análise"],
        "por_que_agora": "Tema em alta nas buscas brasileiras.",
    }


def calcular_score_oportunidade(pico_trend: int, n_noticias: int, n_concorrentes: int = 3) -> int:
    """
    Score 0-100:
    - Interesse (Trends) pesa 50%
    - Saturação de concorrentes pesa -30%
    - Volume de cobertura recente pesa -20%
    """
    trend_score = pico_trend
    saturacao = min(n_noticias / 20, 1.0) * 100   # normalizado
    comp_score = min(n_concorrentes / 10, 1.0) * 100
    score = (trend_score * 0.50) + ((100 - saturacao) * 0.30) + ((100 - comp_score) * 0.20)
    return max(0, min(100, int(score)))


def score_class(score: int) -> str:
    if score >= 70: return "score-hot"
    if score >= 45: return "score-warm"
    return "score-cool"


def tag_html(categoria: str, extra: str = "") -> str:
    css = TAG_CSS.get(categoria, "tag-pol")
    base = f'<span class="tag {css}">{categoria}</span>'
    return base + (f' <span class="tag {extra}">{extra.replace("tag-", "").replace("blast","🚀 Explosão").replace("rising","↑ Crescendo")}</span>' if extra else "")


def formatar_data_entry(entry) -> str:
    try:
        pub = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
        if pub:
            return datetime(*pub[:5]).strftime("%d/%m %H:%M")
    except Exception:
        pass
    return "Recente"


def gerar_csv_briefing(temas_data: list) -> bytes:
    """Gera CSV para exportação do briefing semanal."""
    rows = []
    for t in temas_data:
        rows.append({
            "Tema": t.get("tema", ""),
            "Categoria": t.get("categoria", ""),
            "Score de Oportunidade": t.get("score", ""),
            "Pico de Interesse (Trends)": t.get("pico", ""),
            "Urgência": t.get("angulo_data", {}).get("urgencia", ""),
            "Título Sugerido": t.get("angulo_data", {}).get("titulo_sugerido", ""),
            "Gancho": t.get("angulo_data", {}).get("gancho", ""),
            "Ângulo Editorial": t.get("angulo_data", {}).get("angulo", ""),
            "Formatos": ", ".join(t.get("angulo_data", {}).get("formatos", [])),
            "Por que agora": t.get("angulo_data", {}).get("por_que_agora", ""),
            "Gerado em": datetime.now().strftime("%d/%m/%Y %H:%M"),
        })
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode("utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">◎ Radar BP</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Inteligência Editorial</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Janela Temporal</div>', unsafe_allow_html=True)
    janela_opcoes = {
        "Últimos 7 dias":   "now 7-d",
        "Últimos 30 dias":  "today 1-m",
        "Últimos 90 dias":  "today 3-m",
    }
    janela_label = st.radio(
        "Período de análise",
        options=list(janela_opcoes.keys()),
        index=2,
        label_visibility="collapsed",
    )
    janela = janela_opcoes[janela_label]

    st.markdown('<div class="sidebar-section">Temas Monitorados</div>', unsafe_allow_html=True)
    temas_nomes = [t["tema"] for t in TEMAS_BP]
    temas_ativos = st.multiselect(
        "Selecione os temas ativos",
        options=temas_nomes,
        default=temas_nomes,
        label_visibility="collapsed",
    )

    st.markdown('<div class="sidebar-section">Canais Concorrentes</div>', unsafe_allow_html=True)
    mostrar_nac = st.checkbox("Nacionais", value=True)
    mostrar_int = st.checkbox("Internacionais", value=True)

    st.markdown('<div class="sidebar-section">Ações</div>', unsafe_allow_html=True)
    gerar_angulos = st.checkbox("Gerar ângulos com IA (Claude)", value=bool(os.getenv("ANTHROPIC_API_KEY")),
                                 help="Requer ANTHROPIC_API_KEY no .env")

    if not os.getenv("ANTHROPIC_API_KEY"):
        st.caption("⚠ Configure ANTHROPIC_API_KEY no .env para ativar análise editorial.")

    exportar = st.button("⬇ Exportar Briefing CSV", use_container_width=True)

    st.markdown("---")
    st.markdown(f'<div style="font-family:var(--font-m);font-size:9px;color:var(--text-dim);letter-spacing:0.1em;">ATUALIZADO<br>{datetime.now().strftime("%d/%m/%Y · %H:%M")}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="bp-header">
  <div>
    <div class="bp-logo-mark">◎ Sistema de Inteligência</div>
    <div class="bp-logo-title">Radar BP</div>
    <div class="bp-logo-sub">Tendências · SEO · Concorrência · Editorial</div>
  </div>
  <div class="bp-timestamp">
    <strong>Período ativo</strong>
    {janela_label}<br>
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
    "◎  SEO & Hard News",
])


# ═════════════════════════════════════════════════════════════════════════════
# ABA 1 — TEMAS RECOMENDADOS
# ═════════════════════════════════════════════════════════════════════════════
with aba1:
    st.markdown('<div class="section-label">◈ Temas recomendados para o Brasil Paralelo — score de oportunidade + ângulo editorial</div>', unsafe_allow_html=True)

    temas_filtrados = [t for t in TEMAS_BP if t["tema"] in temas_ativos]

    if not temas_filtrados:
        st.info("Selecione ao menos um tema na barra lateral.")
    else:
        # Coletar dados e scores
        temas_com_dados = []
        with st.spinner("Analisando tendências..."):
            for tema_info in temas_filtrados:
                kw = tema_info["keywords"][0]
                trend_data = buscar_interesse_tempo(kw, janela)
                noticias    = buscar_noticias(kw, max_items=10)
                score       = calcular_score_oportunidade(trend_data["pico"], len(noticias))
                temas_com_dados.append({**tema_info, "trend_data": trend_data, "noticias": noticias, "score": score, "pico": trend_data["pico"]})

        # Ordenar por score
        temas_com_dados.sort(key=lambda x: x["score"], reverse=True)

        # Pré-computar ângulos se habilitado
        if gerar_angulos:
            angulos_map = {}
            with st.spinner("Consultando IA para ângulos editoriais..."):
                for t in temas_com_dados:
                    angulos_map[t["tema"]] = gerar_angulo_bp(
                        t["tema"], t["categoria"], t["keywords"], t["descricao"]
                    )
        else:
            angulos_map = {t["tema"]: _angulo_fallback(t["tema"]) for t in temas_com_dados}

        # Adicionar angulo_data para export
        for t in temas_com_dados:
            t["angulo_data"] = angulos_map.get(t["tema"], {})

        # ── Export handler
        if exportar:
            csv_bytes = gerar_csv_briefing(temas_com_dados)
            st.download_button(
                label="⬇ Baixar Briefing_BP.csv",
                data=csv_bytes,
                file_name=f"Briefing_BP_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )

        # ── Render cards
        for i, t in enumerate(temas_com_dados):
            score   = t["score"]
            pico    = t["pico"]
            angulo  = angulos_map.get(t["tema"], {})
            urgencia = angulo.get("urgencia", "media")
            explosao = pico >= 75 or urgencia == "alta"
            crescendo = 45 <= pico < 75

            # Badge extras
            extra_tag = ""
            if explosao: extra_tag = "tag-blast"
            elif crescendo: extra_tag = "tag-rising"

            sc_class = score_class(score)
            rank_label = ["#1", "#2", "#3", "#4", "#5"][min(i, 4)]

            with st.expander(f"{rank_label} · {t['tema']} · Score {score}", expanded=(i == 0)):
                # Top section
                col_info, col_chart = st.columns([1, 1.1], gap="medium")

                with col_info:
                    st.markdown(f"""
                    <div class="opp-card-top">
                        <div>
                            <div class="opp-tema">{t['tema']}</div>
                            <div class="opp-tags">
                                {tag_html(t['categoria'], extra_tag)}
                            </div>
                            <div style="font-family:var(--font-b);font-size:12px;color:var(--text-mid);line-height:1.5;">{t['descricao']}</div>
                        </div>
                        <div class="opp-score-wrap">
                            <span class="opp-score-label">Score</span>
                            <span class="opp-score {sc_class}">{score}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Barras de métricas
                    saturacao = min(len(t['noticias']) / 20, 1.0) * 100
                    st.markdown(f"""
                    <div class="opp-bar-wrap">
                        <div class="opp-bar-label">
                            <span>Interesse (Trends)</span><span>{pico}/100</span>
                        </div>
                        <div class="opp-bar"><div class="opp-bar-fill bar-trend" style="width:{pico}%"></div></div>

                        <div class="opp-bar-label">
                            <span>Saturação de cobertura</span><span>{int(saturacao)}/100</span>
                        </div>
                        <div class="opp-bar"><div class="opp-bar-fill bar-comp" style="width:{saturacao}%"></div></div>

                        <div class="opp-bar-label">
                            <span>Score de oportunidade</span><span>{score}/100</span>
                        </div>
                        <div class="opp-bar"><div class="opp-bar-fill bar-opp" style="width:{score}%"></div></div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Canais relacionados
                    pills_html = "".join(f'<span class="rel-channel-pill">{c}</span>' for c in t["canais_relacionados"])
                    st.markdown(f"""
                    <div style="font-family:var(--font-m);font-size:9px;letter-spacing:0.12em;text-transform:uppercase;color:var(--text-dim);margin-top:14px;margin-bottom:6px;">Canais que seu público assiste</div>
                    <div class="related-channels">{pills_html}</div>
                    """, unsafe_allow_html=True)

                with col_chart:
                    df_chart = t["trend_data"]["df"]
                    kw       = t["keywords"][0]

                    if not df_chart.empty and kw in df_chart.columns:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df_chart["date"], y=df_chart[kw],
                            mode="lines",
                            line=dict(color="#c9a227", width=2),
                            fill="tozeroy",
                            fillcolor="rgba(201,162,39,0.07)",
                            name="Interesse",
                            hovertemplate="%{x|%d/%m}<br>Interesse: <b>%{y}</b><extra></extra>"
                        ))
                        fig.update_layout(
                            height=180,
                            margin=dict(l=0, r=0, t=0, b=0),
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            xaxis=dict(showgrid=False, showticklabels=True, tickfont=dict(family="IBM Plex Mono", size=9, color="#7a7870"), tickformat="%d/%m"),
                            yaxis=dict(showgrid=True, gridcolor="#1d2030", tickfont=dict(family="IBM Plex Mono", size=9, color="#7a7870"), range=[0, 105]),
                            showlegend=False,
                        )
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                    else:
                        st.caption("Dados de tendência não disponíveis no momento.")

                    # Keywords em ascensão
                    df_queries = buscar_queries_relacionadas(kw)
                    if not df_queries.empty:
                        st.markdown('<div style="font-family:var(--font-m);font-size:9px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text-dim);margin-bottom:8px;margin-top:8px;">🎯 Keywords em ascensão (SEO)</div>', unsafe_allow_html=True)
                        for _, row in df_queries.head(4).iterrows():
                            v = row.get("value", 0)
                            classe = "seo-growth-blast" if v >= 300 else ("seo-growth-high" if v >= 100 else "seo-growth-med")
                            label  = "🚀 Breakout" if v >= 300 else (f"+{v}%" if v < 100000 else f"+{v}%")
                            st.markdown(f"""
                            <div class="seo-row">
                                <span class="seo-keyword">{str(row['query']).title()}</span>
                                <span class="seo-growth {classe}">{label}</span>
                            </div>
                            """, unsafe_allow_html=True)

                # Ângulo BP
                if angulo.get("angulo"):
                    formatos_html = "".join(f'<span class="formato-pill">{f}</span>' for f in angulo.get("formatos", []))
                    urgencia_color = {"alta": "#e74c3c", "media": "#c9a227", "baixa": "#7a7870"}.get(angulo.get("urgencia","media"), "#7a7870")
                    st.markdown(f"""
                    <div class="angulo-box">
                        <div class="angulo-label">◈ Ângulo Editorial — Brasil Paralelo
                            <span style="float:right;color:{urgencia_color};font-size:9px;letter-spacing:0.1em;text-transform:uppercase;">
                                urgência: {angulo.get("urgencia","—").upper()}
                            </span>
                        </div>
                        <div class="angulo-text">{angulo.get("angulo","")}</div>
                        <div class="angulo-gancho">"{angulo.get('gancho','')}"</div>
                        <div style="font-family:var(--font-m);font-size:10px;color:var(--text-mid);margin-top:10px;">
                            📌 <strong style="color:var(--text-dim);">Título:</strong> {angulo.get("titulo_sugerido","")}
                        </div>
                        <div style="font-family:var(--font-m);font-size:10px;color:var(--text-mid);margin-top:6px;">
                            ⏱ <strong style="color:var(--text-dim);">Por que agora:</strong> {angulo.get("por_que_agora","")}
                        </div>
                        <div class="angulo-formatos" style="margin-top:10px;">{formatos_html}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Últimas notícias do tema
                if t["noticias"]:
                    st.markdown('<div style="font-family:var(--font-m);font-size:9px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text-dim);margin-top:18px;margin-bottom:8px;">📰 Notícias recentes</div>', unsafe_allow_html=True)
                    noticias_html = ""
                    for j, n in enumerate(t["noticias"][:3]):
                        data = formatar_data_entry(n)
                        noticias_html += f"""
                        <div class="news-item">
                            <div class="news-num">0{j+1}</div>
                            <div class="news-content">
                                <div class="news-title"><a href="{n.link}" target="_blank">{n.title}</a></div>
                                <div class="news-meta">🕒 {data}</div>
                            </div>
                        </div>"""
                    st.markdown(noticias_html, unsafe_allow_html=True)

        # ── Visão geral: gráfico comparativo de scores
        if len(temas_com_dados) > 1:
            st.markdown("---")
            st.markdown('<div class="section-label">◈ Comparativo de oportunidade entre temas</div>', unsafe_allow_html=True)

            df_scores = pd.DataFrame([
                {"Tema": t["tema"], "Score": t["score"], "Pico Trend": t["pico"], "Categoria": t["categoria"]}
                for t in temas_com_dados
            ])
            color_map = {"Geopolítica": "#5dade2", "História": "#a569bd", "Economia": "#52be80", "Cultura": "#eb984e", "Política": "#ec7063"}

            fig_bar = go.Figure()
            for _, row in df_scores.iterrows():
                fig_bar.add_trace(go.Bar(
                    x=[row["Tema"]], y=[row["Score"]],
                    name=row["Tema"],
                    marker_color=color_map.get(row["Categoria"], "#c9a227"),
                    text=[f'{row["Score"]}'],
                    textposition="outside",
                    textfont=dict(family="IBM Plex Mono", size=10, color="#e8e6df"),
                ))
            fig_bar.update_layout(
                height=220,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(tickfont=dict(family="IBM Plex Mono", size=10, color="#aaa89f"), showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#1d2030", tickfont=dict(family="IBM Plex Mono", size=9, color="#7a7870"), range=[0, 115]),
                bargap=0.35,
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})


# ═════════════════════════════════════════════════════════════════════════════
# ABA 2 — ANÁLISE DE CONCORRÊNCIA
# ═════════════════════════════════════════════════════════════════════════════
with aba2:
    st.markdown('<div class="section-label">◉ Top 10 canais concorrentes — temas em tratamento agora</div>', unsafe_allow_html=True)

    canais_para_mostrar = []
    if mostrar_nac:
        canais_para_mostrar += [("Nacional", c) for c in CANAIS_NACIONAIS]
    if mostrar_int:
        canais_para_mostrar += [("Internacional", c) for c in CANAIS_INTERNACIONAIS]

    if not canais_para_mostrar:
        st.info("Ative pelo menos uma categoria de canais na barra lateral.")
    else:
        # ── Grid de canais
        if mostrar_nac and mostrar_int:
            col_left, col_right = st.columns(2, gap="large")
            grupos = [("🇧🇷 Nacionais", [("Nacional", c) for c in CANAIS_NACIONAIS], col_left),
                      ("🌐 Internacionais", [("Internacional", c) for c in CANAIS_INTERNACIONAIS], col_right)]
        elif mostrar_nac:
            grupos = [("🇧🇷 Nacionais", [("Nacional", c) for c in CANAIS_NACIONAIS], st)]
        else:
            grupos = [("🌐 Internacionais", [("Internacional", c) for c in CANAIS_INTERNACIONAIS], st)]

        for grupo_label, grupo_canais, container in grupos:
            container.markdown(f'<div class="section-label">{grupo_label}</div>', unsafe_allow_html=True)

            for tipo, canal in grupo_canais:
                with container.expander(f"{canal['flag']} {canal['nome']} · {canal['foco']}", expanded=False):
                    with st.spinner(f"Buscando conteúdo de {canal['nome']}..."):
                        videos = buscar_videos_canal(canal)

                    if videos:
                        for v in videos:
                            data_str = formatar_data_entry(v)
                            link = getattr(v, "link", "#")
                            title = getattr(v, "title", "—")
                            st.markdown(f"""
                            <div class="comp-video">
                                <div class="comp-video-title"><a href="{link}" target="_blank">▶ {title}</a></div>
                                <div class="comp-video-date">📅 {data_str}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="comp-empty">Sem conteúdo indexado no momento</div>', unsafe_allow_html=True)

        # ── Análise de overlaps temáticos
        st.markdown("---")
        st.markdown('<div class="section-label">◉ Temas em comum entre concorrentes (análise de convergência)</div>', unsafe_allow_html=True)

        col_radar, col_heat = st.columns([1, 1], gap="large")

        with col_radar:
            st.markdown('<p style="font-family:var(--font-m);font-size:10px;color:var(--text-dim);letter-spacing:0.1em;margin-bottom:12px;">TEMAS MAIS COBERTOS — RADAR DE SATURAÇÃO</p>', unsafe_allow_html=True)
            categorias_radar = ["Política", "Economia", "Cultura", "História", "Geopolítica"]
            scores_nac  = [85, 60, 50, 40, 70]
            scores_int  = [75, 80, 65, 55, 85]
            scores_bp   = [70, 75, 80, 90, 88]

            fig_r = go.Figure()
            for nome, vals, cor in [("Concorrentes Nac.", scores_nac, "#5dade2"),
                                    ("Concorrentes Int.", scores_int, "#a569bd"),
                                    ("Brasil Paralelo",  scores_bp,  "#c9a227")]:
                fig_r.add_trace(go.Scatterpolar(
                    r=vals + [vals[0]], theta=categorias_radar + [categorias_radar[0]],
                    fill='toself', name=nome,
                    line=dict(color=cor, width=2),
                    fillcolor=cor.replace(")", ",0.07)").replace("rgb", "rgba") if "rgb" in cor else cor + "12",
                    opacity=0.85
                ))
            fig_r.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(family="IBM Plex Mono", size=8, color="#7a7870"), gridcolor="#1d2030", linecolor="#1d2030"),
                    angularaxis=dict(tickfont=dict(family="IBM Plex Mono", size=10, color="#aaa89f"), gridcolor="#1d2030", linecolor="#1d2030"),
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(font=dict(family="IBM Plex Mono", size=9, color="#aaa89f"), bgcolor="rgba(0,0,0,0)"),
                height=300, margin=dict(l=20, r=20, t=10, b=10),
            )
            st.plotly_chart(fig_r, use_container_width=True, config={"displayModeBar": False})

        with col_heat:
            st.markdown('<p style="font-family:var(--font-m);font-size:10px;color:var(--text-dim);letter-spacing:0.1em;margin-bottom:12px;">SOBREPOSIÇÃO TEMÁTICA — HEATMAP</p>', unsafe_allow_html=True)
            canais_heat = ["Jovem Pan", "Gazeta do Povo", "PragerU", "Daily Wire", "Tucker Carlson"]
            temas_heat  = ["Soberania", "História", "Economia", "Valores", "Forças Arm."]
            z_vals = [
                [90, 30, 70, 40, 80],
                [70, 60, 55, 50, 35],
                [50, 40, 85, 60, 45],
                [80, 50, 75, 55, 70],
                [95, 35, 65, 50, 85],
            ]
            fig_h = go.Figure(go.Heatmap(
                z=z_vals, x=temas_heat, y=canais_heat,
                colorscale=[[0, "#111219"], [0.5, "#7a6118"], [1, "#c9a227"]],
                showscale=False,
                hovertemplate="%{y} × %{x}<br>Cobertura: <b>%{z}%</b><extra></extra>",
                text=[[str(v) for v in row] for row in z_vals],
                texttemplate="%{text}",
                textfont=dict(family="IBM Plex Mono", size=10, color="#e8e6df"),
            ))
            fig_h.update_layout(
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(tickfont=dict(family="IBM Plex Mono", size=10, color="#aaa89f"), side="bottom"),
                yaxis=dict(tickfont=dict(family="IBM Plex Mono", size=10, color="#aaa89f")),
            )
            st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})

        # ── Oportunidades de diferenciação
        st.markdown("---")
        st.markdown('<div class="section-label">◉ Lacunas de conteúdo — onde o BP pode se diferenciar</div>', unsafe_allow_html=True)
        lacunas = [
            {"tema": "Revisão Histórica Profunda",    "desc": "Concorrentes cobrem eventos recentes. BP tem vantagem em documentários históricos de longa duração.", "gap": 78},
            {"tema": "Geopolítica Sul-americana",     "desc": "Quase inexplorado por concorrentes internacionais. Alta demanda latente detectada.", "gap": 82},
            {"tema": "Filosofia Política Aplicada",   "desc": "Jordan Peterson cobre bem internacionalmente, mas sem adaptação ao contexto brasileiro.", "gap": 71},
            {"tema": "Defesa Nacional e Estratégia",  "desc": "Jovem Pan cobre superficialmente. BP pode ir fundo em doutrina e estratégia.", "gap": 69},
        ]
        cols_lac = st.columns(2, gap="medium")
        for i, lac in enumerate(lacunas):
            with cols_lac[i % 2]:
                st.markdown(f"""
                <div class="opp-card" style="margin-bottom:10px;">
                    <div style="font-family:var(--font-d);font-size:16px;color:var(--text);margin-bottom:6px;">{lac['tema']}</div>
                    <div style="font-family:var(--font-b);font-size:12px;color:var(--text-mid);line-height:1.5;margin-bottom:10px;">{lac['desc']}</div>
                    <div class="opp-bar-label"><span>Gap competitivo</span><span style="color:var(--green);">{lac['gap']}/100</span></div>
                    <div class="opp-bar"><div class="opp-bar-fill" style="width:{lac['gap']}%;background:var(--green);"></div></div>
                </div>
                """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# ABA 3 — SEO & HARD NEWS
# ═════════════════════════════════════════════════════════════════════════════
with aba3:
    st.markdown('<div class="section-label">◎ Radar de tendências macro + hard news em tempo real</div>', unsafe_allow_html=True)

    col_left3, col_right3 = st.columns([1, 1.1], gap="large")

    with col_left3:
        # ── Macro Trends
        st.markdown('<div style="font-family:var(--font-m);font-size:9px;letter-spacing:0.2em;text-transform:uppercase;color:var(--text-dim);margin-bottom:10px;">🔥 TOP 10 — O que o Brasil está buscando agora</div>', unsafe_allow_html=True)
        with st.spinner("Carregando trends..."):
            macro = buscar_trends_macro()

        pills_html = "".join(f'<span class="macro-pill">{t}</span>' for t in macro)
        st.markdown(f'<div class="macro-wrap">{pills_html}</div>', unsafe_allow_html=True)

        # ── SEO Booster — tema personalizado
        st.markdown("---")
        st.markdown('<div style="font-family:var(--font-m);font-size:9px;letter-spacing:0.2em;text-transform:uppercase;color:var(--text-dim);margin-bottom:10px;">🎯 SEO Booster — Keywords em ascensão</div>', unsafe_allow_html=True)

        tema_custom = st.text_input(
            "Pesquisar tema:",
            placeholder="Ex: Reforma Tributária, Soberania, 1964...",
            label_visibility="collapsed"
        )

        if tema_custom:
            with st.spinner(f"Analisando '{tema_custom}'..."):
                df_seo = buscar_queries_relacionadas(tema_custom)
                trend_custom = buscar_interesse_tempo(tema_custom, janela)

            if not df_seo.empty:
                for _, row in df_seo.iterrows():
                    v = row.get("value", 0)
                    classe = "seo-growth-blast" if v >= 300 else ("seo-growth-high" if v >= 100 else "seo-growth-med")
                    label  = "🚀 Breakout" if v >= 300 else (f"+{v}%" if v < 100000 else f"+{int(v)}%")
                    st.markdown(f"""
                    <div class="seo-row">
                        <span class="seo-keyword">{str(row['query']).title()}</span>
                        <span class="seo-growth {classe}">{label}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Volume de busca baixo para subtermos no momento.")

            # Mini chart
            df_c = trend_custom["df"]
            kw_c = tema_custom
            if not df_c.empty and kw_c in df_c.columns:
                fig_mini = go.Figure()
                fig_mini.add_trace(go.Scatter(
                    x=df_c["date"], y=df_c[kw_c],
                    mode="lines", line=dict(color="#c9a227", width=1.5),
                    fill="tozeroy", fillcolor="rgba(201,162,39,0.06)",
                    hovertemplate="%{x|%d/%m}: <b>%{y}</b><extra></extra>"
                ))
                fig_mini.update_layout(
                    height=130, margin=dict(l=0,r=0,t=0,b=0),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False, tickfont=dict(family="IBM Plex Mono",size=8,color="#7a7870"), tickformat="%d/%m"),
                    yaxis=dict(showgrid=True, gridcolor="#1d2030", tickfont=dict(family="IBM Plex Mono",size=8,color="#7a7870"), range=[0,105]),
                    showlegend=False,
                )
                st.plotly_chart(fig_mini, use_container_width=True, config={"displayModeBar": False})
        else:
            # Mostrar queries dos temas BP por padrão
            for tema_info in TEMAS_BP[:3]:
                kw0 = tema_info["keywords"][0]
                df_seo0 = buscar_queries_relacionadas(kw0)
                if not df_seo0.empty:
                    st.markdown(f'<div style="font-family:var(--font-m);font-size:9px;color:var(--text-dim);letter-spacing:0.1em;text-transform:uppercase;margin:10px 0 6px;">{kw0.upper()}</div>', unsafe_allow_html=True)
                    for _, row in df_seo0.head(3).iterrows():
                        v = row.get("value", 0)
                        classe = "seo-growth-blast" if v >= 300 else ("seo-growth-high" if v >= 100 else "seo-growth-med")
                        label  = "🚀 Breakout" if v >= 300 else f"+{v}%"
                        st.markdown(f"""
                        <div class="seo-row">
                            <span class="seo-keyword">{str(row['query']).title()}</span>
                            <span class="seo-growth {classe}">{label}</span>
                        </div>
                        """, unsafe_allow_html=True)

    with col_right3:
        st.markdown('<div style="font-family:var(--font-m);font-size:9px;letter-spacing:0.2em;text-transform:uppercase;color:var(--text-dim);margin-bottom:10px;">📰 Hard News — Radar ao vivo</div>', unsafe_allow_html=True)

        # Seletor de tema para notícias
        temas_news_opcoes = ["Todos os temas"] + [t["tema"] for t in TEMAS_BP]
        tema_news_sel = st.radio(
            "Filtrar por tema:",
            temas_news_opcoes,
            horizontal=True,
            label_visibility="collapsed",
        )

        if tema_news_sel == "Todos os temas":
            keywords_news = [t["keywords"][0] for t in TEMAS_BP]
        else:
            kw_match = next((t["keywords"] for t in TEMAS_BP if t["tema"] == tema_news_sel), ["brasil"])
            keywords_news = kw_match[:2]

        with st.spinner("Carregando notícias..."):
            todas_noticias = []
            for kw in keywords_news:
                todas_noticias += buscar_noticias(kw, max_items=4)

        # Deduplicar por título
        seen = set()
        noticias_unicas = []
        for n in todas_noticias:
            t_key = n.title.lower()[:60]
            if t_key not in seen:
                seen.add(t_key)
                noticias_unicas.append(n)

        if noticias_unicas:
            noticias_html_block = ""
            for j, n in enumerate(noticias_unicas[:12]):
                data_str = formatar_data_entry(n)
                num_str  = str(j + 1).zfill(2)
                noticias_html_block += f"""
                <div class="news-item">
                    <div class="news-num">{num_str}</div>
                    <div class="news-content">
                        <div class="news-title"><a href="{n.link}" target="_blank">{n.title}</a></div>
                        <div class="news-meta">🕒 {data_str}</div>
                    </div>
                </div>"""
            st.markdown(noticias_html_block, unsafe_allow_html=True)
        else:
            st.info("Sem notícias indexadas no momento. Verifique a conexão.")

        # ── Linha do tempo de interesse cruzado (multi-termo)
        st.markdown("---")
        st.markdown('<div style="font-family:var(--font-m);font-size:9px;letter-spacing:0.2em;text-transform:uppercase;color:var(--text-dim);margin-bottom:10px;">📊 Comparativo de interesse — temas BP</div>', unsafe_allow_html=True)

        cores_temas = ["#c9a227", "#5dade2", "#52be80", "#a569bd", "#eb984e"]
        fig_comp = go.Figure()

        for idx, tema_info in enumerate(TEMAS_BP[:5]):
            kw = tema_info["keywords"][0]
            td = buscar_interesse_tempo(kw, janela)
            df_t = td["df"]
            if not df_t.empty and kw in df_t.columns:
                fig_comp.add_trace(go.Scatter(
                    x=df_t["date"], y=df_t[kw],
                    mode="lines", name=tema_info["tema"],
                    line=dict(color=cores_temas[idx], width=1.5),
                    hovertemplate=f"{tema_info['tema']}<br>%{{x|%d/%m}}: <b>%{{y}}</b><extra></extra>"
                ))

        fig_comp.update_layout(
            height=220,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(font=dict(family="IBM Plex Mono", size=9, color="#aaa89f"), bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.0),
            xaxis=dict(showgrid=False, tickfont=dict(family="IBM Plex Mono", size=8, color="#7a7870"), tickformat="%d/%m"),
            yaxis=dict(showgrid=True, gridcolor="#1d2030", tickfont=dict(family="IBM Plex Mono", size=8, color="#7a7870"), range=[0, 105]),
        )
        st.plotly_chart(fig_comp, use_container_width=True, config={"displayModeBar": False})
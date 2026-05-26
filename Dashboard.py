import streamlit as st
import geopandas as gpd
import pydeck as pdk
import pandas as pd
import numpy as np
import json
import base64
import warnings
import math
from pathlib import Path

warnings.filterwarnings('ignore')
APP_DIR = Path(__file__).resolve().parent

# ════════════════════════════════════════════════════════
# 0. SESSION STATE
# ════════════════════════════════════════════════════════
for k, v in [
    ('cena_atual', 0),
    ('foco_historia', 0),
    ('metrica_cena2', 'PIB Municipal'),
    ('ano_pib', 2023),
    ('ano_gini', 2010),
    ('ano_va', 2021),
    ('recorte_cena2', 'Sul inteiro'),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ════════════════════════════════════════════════════════
# 1. PAGE CONFIG
# ════════════════════════════════════════════════════════
st.set_page_config(
    layout="wide",
    page_title="Sul do Brasil · Narrativa Econômica",
    page_icon="🗺️",
    initial_sidebar_state="collapsed"
)

# ════════════════════════════════════════════════════════
# 2. ESTILOS GLOBAIS
# ════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Reset & Fundo ── */
header, footer, [data-testid="stDecoration"] { display: none !important; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
    margin: 0 !important; padding: 0 !important;
    overflow: hidden !important; background: transparent !important;
}
.block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }

[data-testid="stAppViewContainer"]::before {
    content: ''; position: fixed; inset: 0;
    background:
        radial-gradient(ellipse 80% 60% at 15% 85%, rgba(14,116,144,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 55% 45% at 85% 10%, rgba(245,158,11,0.08) 0%, transparent 55%);
    pointer-events: none; z-index: 1;
}

/* ── Mapa fullscreen ── */
[data-testid="stDeckGlJsonChart"],
[data-testid="stDeckGlJsonChart"] iframe {
    position: fixed !important; top: 0 !important; left: 0 !important;
    width: 100vw !important; height: 100vh !important;
    z-index: 0 !important; border: none !important;
}

/* ══════════════════════════════════════════════════════
   NAV SIDEBAR — esquerda, aparece ao hover
══════════════════════════════════════════════════════ */
div[data-testid="stVerticalBlock"]:has(#nav-anchor):not(:has(#right-anchor)):not(:has([data-testid="stDeckGlJsonChart"])) {
    position: fixed !important;
    left: -208px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 238px !important;
    background: linear-gradient(145deg, rgba(15,23,42,0.74), rgba(15,23,42,0.48)) !important;
    backdrop-filter: blur(30px) saturate(170%) !important;
    -webkit-backdrop-filter: blur(30px) saturate(170%) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    border-left: 0 !important;
    border-radius: 0 22px 22px 0 !important;
    z-index: 10001 !important;
    transition: left 0.32s cubic-bezier(0.4,0,0.2,1) !important;
    box-shadow: 10px 0 44px rgba(2,6,23,0.38), inset -1px 0 0 rgba(255,255,255,0.10) !important;
    padding: 18px 10px 18px 8px !important;
    overflow: hidden !important;
    max-height: 96vh !important;
    overflow-y: auto !important;
    scrollbar-width: none !important;
}
div[data-testid="stVerticalBlock"]:has(#nav-anchor):not(:has(#right-anchor)):not(:has([data-testid="stDeckGlJsonChart"])):hover {
    left: 0 !important;
}

/* Aba visível (28px à esquerda) — linha decorativa */
div[data-testid="stVerticalBlock"]:has(#nav-anchor):not(:has(#right-anchor)):not(:has([data-testid="stDeckGlJsonChart"]))::after {
    content: '';
    position: absolute;
    right: 4px;
    top: 50%;
    transform: translateY(-50%);
    width: 3px;
    height: 46px;
    border-radius: 99px;
    background: rgba(14,116,144,0.72);
    box-shadow: 0 0 18px rgba(14,116,144,0.45);
    transition: opacity 0.3s;
}
div[data-testid="stVerticalBlock"]:has(#nav-anchor):not(:has(#right-anchor)):not(:has([data-testid="stDeckGlJsonChart"])):hover::after {
    opacity: 0;
}

/* Botões do nav — tema escuro */
div[data-testid="stVerticalBlock"]:has(#nav-anchor) .stButton > button {
    width: 100% !important;
    background: linear-gradient(145deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06)) !important;
    border: 1px solid rgba(255,255,255,0.16) !important;
    color: rgba(255,255,255,0.84) !important;
    font-weight: 600 !important;
    font-size: 0.76rem !important;
    padding: 7px 10px !important;
    border-radius: 11px !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.03em !important;
}
div[data-testid="stVerticalBlock"]:has(#nav-anchor) .stButton > button:hover {
    background: rgba(14,116,144,0.30) !important;
    border-color: rgba(14,116,144,0.55) !important;
    color: #ffffff !important;
    transform: translateX(3px) !important;
    box-shadow: 0 4px 14px rgba(14,116,144,0.25) !important;
}

/* Radio do nav — tema escuro */
div[data-testid="stVerticalBlock"]:has(#nav-anchor) .stRadio { gap: 3px !important; }
div[data-testid="stVerticalBlock"]:has(#nav-anchor) .stRadio > div { gap: 3px !important; flex-direction: column !important; }
div[data-testid="stVerticalBlock"]:has(#nav-anchor) .stRadio > div > label {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 7px !important;
    padding: 6px 10px !important;
    color: rgba(255,255,255,0.72) !important;
    font-size: 0.74rem !important;
    line-height: 1.18 !important;
    transition: all 0.18s !important;
}
div[data-testid="stVerticalBlock"]:has(#nav-anchor) .stRadio > div > label:hover {
    background: rgba(14,116,144,0.22) !important;
    color: #fff !important;
}
div[data-testid="stVerticalBlock"]:has(#nav-anchor) .stRadio > div > label:has(input:checked) {
    background: rgba(14,116,144,0.38) !important;
    border-color: rgba(14,116,144,0.7) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
}
div[data-testid="stVerticalBlock"]:has(#nav-anchor) .stRadio > div > label > div:first-child { display: none !important; }
div[data-testid="stVerticalBlock"]:has(#nav-anchor) .stRadio > label { display: none !important; }
div[data-testid="stVerticalBlock"]:has(#nav-anchor) hr {
    border: none !important;
    border-top: 1px solid rgba(255,255,255,0.10) !important;
    margin: 10px 0 !important;
}

/* ══════════════════════════════════════════════════════
   PAINEL DIREITO — cards de informação
══════════════════════════════════════════════════════ */
div[data-testid="stVerticalBlock"]:has(#right-anchor):not(:has(#nav-anchor)):not(:has([data-testid="stDeckGlJsonChart"])) {
    position: fixed !important;
    right: 16px !important;
    top: 20px !important;
    width: 330px !important;
    max-height: 94vh !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    z-index: 7500 !important;
    scrollbar-width: thin !important;
    scrollbar-color: rgba(14,116,144,0.3) transparent !important;
    background: transparent !important;
}
div[data-testid="stVerticalBlock"]:has(#right-anchor)::-webkit-scrollbar { width: 3px; }
div[data-testid="stVerticalBlock"]:has(#right-anchor)::-webkit-scrollbar-thumb {
    background: rgba(14,116,144,0.35); border-radius: 4px;
}
div[data-testid="stVerticalBlock"]:has(#right-anchor) .stRadio {
    background: linear-gradient(145deg, rgba(255,255,255,0.86), rgba(255,255,255,0.58)) !important;
    border: 1px solid rgba(255,255,255,0.74) !important;
    border-radius: 18px !important;
    padding: 12px 12px 10px !important;
    box-shadow: 0 18px 48px rgba(15,23,42,0.16), inset 0 1px 0 rgba(255,255,255,0.82) !important;
    backdrop-filter: blur(24px) saturate(165%) !important;
    -webkit-backdrop-filter: blur(24px) saturate(165%) !important;
}
div[data-testid="stVerticalBlock"]:has(#right-anchor) .stRadio > div {
    gap: 7px !important;
}
div[data-testid="stVerticalBlock"]:has(#right-anchor) .stRadio > div > label {
    background: rgba(255,255,255,0.76) !important;
    border: 1px solid rgba(148,163,184,0.36) !important;
    border-radius: 11px !important;
    padding: 9px 12px !important;
    color: #0f172a !important;
    font-size: 0.88rem !important;
    font-weight: 800 !important;
}
div[data-testid="stVerticalBlock"]:has(#right-anchor) .stRadio > div > label p {
    color: #0f172a !important;
    font-size: 0.88rem !important;
    font-weight: 800 !important;
}
div[data-testid="stVerticalBlock"]:has(#right-anchor) .stRadio > div > label:has(input:checked) {
    background: rgba(14,116,144,0.22) !important;
    border-color: rgba(14,116,144,0.52) !important;
    color: #0f172a !important;
}
div[data-testid="stVerticalBlock"]:has(#right-anchor) .stRadio > div > label > div:first-child {
    transform: scale(1.08);
}

* { font-family: 'DM Sans', sans-serif !important; box-sizing: border-box; }
h1,h2,h3 { font-family: 'Playfair Display', serif !important; }

.control-heading {
    background: linear-gradient(145deg, rgba(15,23,42,0.82), rgba(15,23,42,0.58));
    color: rgba(255,255,255,0.88);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 18px;
    padding: 14px 16px;
    margin-bottom: 10px;
    box-shadow: 0 18px 48px rgba(15,23,42,0.20);
    backdrop-filter: blur(24px) saturate(165%);
    -webkit-backdrop-filter: blur(24px) saturate(165%);
}
.control-heading-kicker {
    font-size: 0.62rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: rgba(125,211,252,0.86);
    font-weight: 800;
    margin-bottom: 5px;
}
.control-heading-title {
    font-family: 'Playfair Display', serif !important;
    font-size: 1.18rem;
    line-height: 1.15;
    font-weight: 700;
}
.presentation-legend {
    position: fixed;
    left: 50%;
    bottom: 24px;
    transform: translateX(-50%);
    z-index: 7600;
    pointer-events: none;
    width: min(820px, calc(100vw - 420px));
    border-radius: 20px;
    padding: 16px 18px;
    background: linear-gradient(145deg, rgba(255,255,255,0.76), rgba(255,255,255,0.38));
    border: 1px solid rgba(255,255,255,0.76);
    box-shadow: 0 22px 58px rgba(15,23,42,0.18), inset 0 1px 0 rgba(255,255,255,0.84);
    backdrop-filter: blur(24px) saturate(165%);
    -webkit-backdrop-filter: blur(24px) saturate(165%);
}
.presentation-legend.dark {
    background: linear-gradient(145deg, rgba(15,23,42,0.78), rgba(15,23,42,0.48));
    border-color: rgba(255,255,255,0.18);
    color: #e2e8f0;
}
.legend-kicker {
    font-size: 0.70rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: rgba(71,85,105,0.92);
    font-weight: 800;
    margin-bottom: 10px;
}
.presentation-legend.dark .legend-kicker { color: rgba(186,230,253,0.92); }
.legend-row {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 9px;
    font-size: 0.92rem;
    color: #334155;
    font-weight: 700;
}
.presentation-legend.dark .legend-item { color: #e2e8f0; }
.legend-line {
    width: 46px;
    height: 8px;
    border-radius: 99px;
    flex-shrink: 0;
}
.legend-dot {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    flex-shrink: 0;
    box-shadow: 0 0 0 5px rgba(255,255,255,0.30);
}
.legend-gradient {
    height: 16px;
    border-radius: 999px;
    margin: 2px 0 8px;
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.35);
}
.legend-scale-labels {
    display: flex;
    justify-content: space-between;
    color: #334155;
    font-size: 0.88rem;
    font-weight: 800;
}
@media (max-width: 1200px) {
    .presentation-legend {
        width: min(720px, calc(100vw - 80px));
        left: calc(50% + 20px);
    }
}

/* Cards de apresentacao sobre o mapa - tema glassmorphism */
.roots-overlay {
    position: fixed;
    inset: 0;
    z-index: 7600;
    pointer-events: auto;
    cursor: default;
}
.roots-frame {
    position: absolute;
    left: 50%;
    top: 50%;
    width: min(100vw, 177.7778vh);
    height: min(100vh, 56.25vw);
    transform: translate(-50%, -50%);
    pointer-events: none;
}
.roots-pin {
    position: absolute;
    left: var(--pin-x);
    top: var(--pin-y);
    width: 22px;
    height: 22px;
    transform: translate(-50%, -50%);
    border-radius: 999px;
    border: 2px solid rgba(255,255,255,0.95);
    background: var(--accent);
    box-shadow:
        0 0 0 8px var(--accent-soft),
        0 12px 30px rgba(15,23,42,0.20);
    z-index: 4;
}
.roots-pin::after {
    content: '';
    position: absolute;
    inset: -12px;
    border: 1px solid var(--accent-soft);
    border-radius: 999px;
}
.roots-card {
    position: absolute;
    left: var(--card-x);
    top: var(--card-y);
    width: clamp(340px, 20.8vw, 410px);
    transform: translate(-50%, -50%) scale(var(--scale, 1));
    overflow: hidden;
    border-radius: 22px;
    background:
        linear-gradient(145deg, rgba(255,255,255,0.72), rgba(255,255,255,0.36));
    border: 1px solid rgba(255,255,255,0.78);
    backdrop-filter: blur(24px) saturate(165%);
    -webkit-backdrop-filter: blur(24px) saturate(165%);
    box-shadow:
        0 22px 60px rgba(15,23,42,0.22),
        inset 0 1px 0 rgba(255,255,255,0.82);
    opacity: 0.95;
    transition: transform 0.24s ease, opacity 0.24s ease, box-shadow 0.24s ease;
    z-index: 3;
}
.roots-card.is-active {
    opacity: 1;
    --scale: 1;
    box-shadow:
        0 26px 70px rgba(15,23,42,0.26),
        0 0 0 1px var(--accent-soft),
        inset 0 1px 0 rgba(255,255,255,0.88);
}
.roots-card::before {
    content: '';
    position: absolute;
    inset: 0 auto 0 0;
    width: 5px;
    background: var(--accent);
    opacity: 0.84;
    z-index: 2;
}
.roots-card-media {
    height: 102px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid rgba(255,255,255,0.58);
    background-size: cover;
    background-position: center;
    color: rgba(15,23,42,0.54);
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    text-align: center;
}
.roots-card-body { padding: 12px 14px 14px; }
.roots-card-kicker {
    font-size: 0.58rem;
    line-height: 1.2;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: rgba(71,85,105,0.88);
    font-weight: 700;
    margin-bottom: 4px;
}
.roots-card-title {
    font-family: 'Playfair Display', serif !important;
    font-size: 1.16rem;
    line-height: 1.12;
    color: #0f172a;
    font-weight: 700;
    margin-bottom: 7px;
}
.roots-card-text {
    font-size: 0.80rem;
    line-height: 1.48;
    color: #334155;
}
.roots-card-chip {
    display: inline-flex;
    margin-top: 9px;
    padding: 5px 9px;
    border-radius: 999px;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}
@media (max-width: 1400px) {
    .roots-card {
        width: 302px;
    }
    .roots-card-media { height: 90px; }
    .roots-card-text {
        font-size: 0.70rem;
        line-height: 1.34;
    }
    .roots-card-title { font-size: 1.0rem; }
    .roots-card-chip { font-size: 0.60rem; }
}
@media (max-aspect-ratio: 1.4) {
    .roots-frame {
        width: 100vw;
        height: 100vh;
    }
    .roots-card.root-norte_parana { --card-x: 31% !important; --card-y: 24% !important; }
    .roots-card.root-vale_itajai { --card-x: 69% !important; --card-y: 38% !important; }
    .roots-card.root-pampas_gauchos { --card-x: 31% !important; --card-y: 75% !important; }
    .roots-card.root-serra_gaucha { --card-x: 69% !important; --card-y: 72% !important; }
}

.integration-overlay {
    position: fixed;
    inset: 0;
    z-index: 7400;
    pointer-events: none;
}
.integration-frame {
    position: absolute;
    left: 50%;
    top: 50%;
    width: min(100vw, 177.7778vh);
    height: min(100vh, 56.25vw);
    transform: translate(-50%, -50%);
}
.integration-card {
    position: absolute;
    left: var(--card-x);
    top: var(--card-y);
    width: clamp(330px, 20vw, 395px);
    transform: translate(-50%, -50%);
    padding: 16px 18px 17px;
    border-radius: 22px;
    background: linear-gradient(145deg, rgba(255,255,255,0.72), rgba(255,255,255,0.36));
    border: 1px solid rgba(255,255,255,0.74);
    backdrop-filter: blur(24px) saturate(165%);
    -webkit-backdrop-filter: blur(24px) saturate(165%);
    box-shadow: 0 18px 48px rgba(15,23,42,0.18), inset 0 1px 0 rgba(255,255,255,0.82);
}
.integration-card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    width: 5px;
    height: 100%;
    border-radius: 22px 0 0 22px;
    background: var(--accent);
    box-shadow: 0 0 24px var(--accent-soft);
}
.integration-kicker {
    font-size: 0.62rem;
    line-height: 1.1;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: rgba(71,85,105,0.90);
    font-weight: 800;
    margin-bottom: 5px;
}
.integration-title {
    font-family: 'Playfair Display', serif !important;
    font-size: 1.16rem;
    line-height: 1.12;
    color: #0f172a;
    font-weight: 700;
    margin-bottom: 6px;
}
.integration-text {
    font-size: 0.84rem;
    line-height: 1.48;
    color: #334155;
}
.integration-chip {
    display: inline-flex;
    margin-top: 9px;
    padding: 5px 9px;
    border-radius: 999px;
    color: var(--accent);
    border: 1px solid var(--accent-soft);
    background: rgba(255,255,255,0.42);
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.02em;
}
.integration-card.paranagua { --card-x: 65%; --card-y: 22%; }
.integration-card.itajai { --card-x: 75%; --card-y: 45%; }
.integration-card.portoalegre { --card-x: 56%; --card-y: 75%; }
.integration-card.chapeco { --card-x: 31%; --card-y: 55%; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# 3. DADOS ESTÁTICOS
# ════════════════════════════════════════════════════════

REGIOES_HISTORICAS = [
    {
        "name": "Serra Gaúcha", "position": [-51.18, -29.17],
        "color": [220, 100, 35], "radius": 22000,
        "tema": "🍷 Colonização Italiana",
        "slug": "serra_gaucha",
        "texto": "Imigrantes italianos chegaram à Serra Gaúcha a partir de 1875 e consolidaram minifúndios policultores. O excedente agrícola, a vitivinicultura e depois a metal-mecânica formaram um polo de renda distribuída, cooperativismo forte e industrialização endógena.",
        "dado": "R$ 18 bi em produção agroindustrial",
        "nota": "Minifúndio, cooperativas e indústria local",
        "label_mapa": "Serra Gaucha\nCooperativas e industria local\nR$ 18 bi agroindustrial",
        "card_position": [-50.15, -29.35],
    },
    {
        "name": "Pampas Gaúchos", "position": [-54.50, -31.00],
        "color": [50, 150, 65], "radius": 38000,
        "tema": "🐄 Ciclo da Pecuária",
        "slug": "pampas_gauchos",
        "texto": "Os pampas gaúchos foram estruturados por estâncias pecuárias extensivas desde o século XVIII. A riqueza do couro e do charque integrou a região ao mercado interno, mas deixou uma herança fundiária concentrada que ajuda a explicar a estagnação relativa da Metade Sul.",
        "dado": "Rebanho de 14 milhões de bovinos",
        "nota": "Estâncias, charque e concentração fundiária",
        "label_mapa": "Pampas Gauchos\nEstancias e concentracao fundiaria\n14 milhoes de bovinos",
        "card_position": [-55.75, -30.15],
    },
    {
        "name": "Norte do Paraná", "position": [-52.00, -23.30],
        "color": [130, 55, 195], "radius": 22000,
        "tema": "☕ Erva-mate e Café",
        "slug": "norte_parana",
        "texto": "O Norte do Paraná sintetiza duas frentes: a infraestrutura financiada pela erva-mate e a colonização planejada ligada ao café no século XX. A geada e a crise cafeeira aceleraram a transição para grãos, mecanização e agroindústria.",
        "dado": "1º produtor nacional de café na déc. de 1960",
        "nota": "Da erva-mate e café à soja mecanizada",
        "label_mapa": "Norte do Parana\nCafe, mate e soja mecanizada\nLider no cafe nos anos 1960",
        "card_position": [-53.25, -24.10],
    },
    {
        "name": "Vale do Itajaí", "position": [-49.07, -26.92],
        "color": [25, 95, 200], "radius": 18000,
        "tema": "🏭 Colonização Alemã",
        "slug": "vale_itajai",
        "texto": "Colonizado por alemães e italianos ao longo dos rios, o Vale do Itajaí transformou isolamento em capacidade produtiva. A rota fluvial pelo Itajaí-Açu, somada à autossuficiência das colônias, deu origem ao polo têxtil e a uma rede industrial familiar.",
        "dado": "SC: maior PIB industrial per capita do Brasil",
        "nota": "Vales fluviais, têxtil e indústria familiar",
        "label_mapa": "Vale do Itajai\nTextil e industria familiar\nAlto PIB industrial per capita",
        "card_position": [-48.90, -26.15],
    },
]

# ── Ferrovias (redes reais ativas e históricas) ──────────────────────
FERROVIAS = [
    # EFPR — Curitiba ↔ Paranaguá (Rumo Malha Sul, ativa)
    {"path": [[-49.27,-25.43],[-49.17,-25.52],[-48.98,-25.52],[-48.83,-25.47],[-48.71,-25.43],[-48.51,-25.50]],
     "name": "EFPR – Curitiba ↔ Paranaguá"},
    # Rumo Malha Sul — Curitiba → Ponta Grossa → Guarapuava → Cascavel → Foz do Iguaçu
    {"path": [[-49.27,-25.43],[-49.73,-25.61],[-50.16,-25.09],[-51.07,-25.23],[-51.46,-25.39],[-52.88,-25.39],[-53.46,-24.96],[-54.58,-25.52]],
     "name": "Rumo – Curitiba ↔ Cascavel"},
    # Rumo Malha Sul — Porto Alegre → Santa Maria → Uruguaiana
    {"path": [[-51.22,-30.03],[-51.91,-29.69],[-52.89,-30.04],[-53.81,-29.68],[-55.53,-29.46],[-57.08,-29.76]],
     "name": "Rumo – Porto Alegre ↔ Uruguaiana"},
    # EFSPRG (histórica, parcialmente inativa) — Ponta Grossa → SC interior
    {"path": [[-50.16,-25.09],[-50.39,-26.18],[-49.80,-26.57],[-49.80,-27.22],[-49.10,-27.72]],
     "name": "EFSPRG – Ponta Grossa ↔ SC (histórica)"},
    # Ramal norte RS → conexão gaúcha interior
    {"path": [[-51.22,-30.03],[-51.55,-29.45],[-52.15,-28.70],[-52.40,-28.26],[-52.40,-27.61]],
     "name": "Ramal Norte RS (Passo Fundo)"},
]

# ── Rodovias (traçados reais com waypoints detalhados) ────────────────
RODOVIAS = [
    # BR-116 (Régis Bittencourt) — Curitiba ↔ Porto Alegre via interior serrano
    {"path": [[-49.27,-25.43],[-49.72,-25.77],[-49.80,-26.12],[-50.39,-26.18],[-51.01,-26.78],[-50.33,-27.82],[-51.17,-29.17],[-51.22,-30.03]],
     "name": "BR-116 (Interior – Curitiba ↔ Porto Alegre)"},
    # BR-101 — Litoral (Paranaguá → Joinville → Florianópolis → Porto Alegre)
    {"path": [[-48.51,-25.50],[-48.84,-26.30],[-49.07,-26.92],[-48.65,-27.60],[-48.62,-28.55],[-49.97,-29.89],[-51.22,-30.03]],
     "name": "BR-101 (Corredor Litorâneo)"},
    # BR-277 — Curitiba ↔ Foz do Iguaçu (corredor bioceânico)
    {"path": [[-49.27,-25.43],[-50.16,-25.09],[-51.46,-25.39],[-52.88,-25.39],[-53.46,-24.96],[-54.58,-25.52]],
     "name": "BR-277 (Curitiba ↔ Foz do Iguaçu)"},
    # BR-376 / BR-369 — Eixo Norte Paranaense (Curitiba → Londrina → Maringá)
    {"path": [[-49.27,-25.43],[-50.16,-25.09],[-51.02,-23.90],[-51.16,-23.31],[-51.93,-23.42]],
     "name": "BR-376 (Norte Paranaense)"},
    # BR-163 — Corredor do Mercosul (Foz → Chapecó → interior SC)
    {"path": [[-54.58,-25.52],[-53.46,-24.96],[-52.68,-26.86],[-52.37,-27.30],[-52.67,-28.29]],
     "name": "BR-163 (Corredor do Mercosul)"},
    # BR-290 / Freeway RS — Porto Alegre → Santa Maria → Uruguaiana
    {"path": [[-51.22,-30.03],[-52.89,-30.04],[-53.81,-29.68],[-55.53,-29.46],[-57.08,-29.76]],
     "name": "BR-290 (Freeway RS)"},
]

FERROVIA_DESCRICOES = [
    "Inaugurada no fim do seculo XIX, a EFPR venceu a Serra do Mar e ligou Curitiba ao Porto de Paranagua, primeiro grande salto logistico do mate e da madeira.",
    "A malha rumo ao oeste levou a logica exportadora para Guarapuava, Cascavel e Foz, conectando graos e fronteira ao eixo Curitiba-Paranagua.",
    "No RS, a ferrovia interior-Porto Alegre-Uruguaiana integrou pecuaria, arroz, graos e a porta do Mercosul.",
    "A Estrada de Ferro Sao Paulo-Rio Grande abriu o planalto catarinense, puxando madeira, colonizacao e a base agroindustrial do oeste.",
    "O ramal norte gaucho aproxima Passo Fundo e a Serra do sistema logistico de Porto Alegre, articulando graos e industria regional.",
]

RODOVIA_DESCRICOES = [
    "Eixo interiorano que costura Curitiba, planalto catarinense, Serra Gaucha e Porto Alegre, central para cargas industriais.",
    "Corredor litoraneo que aproxima os vales catarinenses dos portos e transforma o litoral em espinha dorsal industrial.",
    "Ligacao Curitiba-Foz: corredor bioceanico em potencial e via de escoamento do oeste paranaense.",
    "Eixo da frente cafeeira e depois da agroindustria do Norte do Parana, conectando Londrina e Maringa a Curitiba.",
    "Corredor do Mercosul: articula Foz, oeste catarinense e cadeias de carnes em direcao aos mercados regionais.",
    "No RS, a BR-290 organiza a relacao Porto Alegre-Santa Maria-Uruguaiana e a conexao rodoviaria com a Argentina.",
]

for rota, descricao in zip(FERROVIAS, FERROVIA_DESCRICOES):
    rota["tipo"] = "Ferrovia"
    rota["setor"] = "trilhos de escoamento interior-portos"
    rota["descricao"] = descricao

for rota, descricao in zip(RODOVIAS, RODOVIA_DESCRICOES):
    rota["tipo"] = "Rodovia"
    rota["setor"] = "corredor logistico, industrial e Mercosul"
    rota["descricao"] = descricao

POLOS_CENA1 = [
    {"name":"Curitiba",         "position":[-49.27,-25.43],"radius":38000,"color":[14,116,144],  "setor":"Automotivo · Serviços · Tecnologia"},
    {"name":"Porto Alegre",     "position":[-51.22,-30.03],"radius":34000,"color":[109,40,217],  "setor":"Indústria · Finanças · Porto"},
    {"name":"Joinville",        "position":[-48.84,-26.30],"radius":22000,"color":[245,158,11],  "setor":"Metal-mecânica · Têxtil"},
    {"name":"Florianópolis",    "position":[-48.55,-27.60],"radius":18000,"color":[16,185,129],  "setor":"Tecnologia · Turismo · Administração"},
    {"name":"Londrina",         "position":[-51.16,-23.31],"radius":18000,"color":[239,68,68],   "setor":"Agronegócio · Comércio Regional"},
    {"name":"Caxias do Sul",    "position":[-51.17,-29.17],"radius":16000,"color":[245,100,20],  "setor":"Metal-mecânica · Vitivinicultura"},
    {"name":"Blumenau",         "position":[-49.07,-26.92],"radius":15000,"color":[30,120,220],  "setor":"Têxtil · Tecnologia · Turismo"},
    {"name":"Maringá",          "position":[-51.93,-23.42],"radius":14000,"color":[200,50,100],  "setor":"Agronegócio · Educação"},
    {"name":"Chapecó",          "position":[-52.62,-27.10],"radius":13000,"color":[34,197,94],   "setor":"Agroindústria de carnes"},
    {"name":"Passo Fundo",      "position":[-52.40,-28.26],"radius":12000,"color":[251,191,36],  "setor":"Agronegócio · Educação"},
]

# Métricas disponíveis — chaves sem espaços para pydeck
POLO_DESCRICOES = {
    "Curitiba": "Centro financeiro do ciclo do mate e hoje hub automotivo/logistico ligado a Araucaria e Paranagua.",
    "Porto Alegre": "Polo comercial que cresceu com a navegacao Jacui-Guaiba e articulou a industria gaucha.",
    "Joinville": "Nucleo metal-mecanico conectado ao porto de Sao Francisco do Sul; base de motores e compressores.",
    "Florianópolis": "Polo de tecnologia e servicos, rota intangivel que reduz a dependencia do escoamento fisico.",
    "Londrina": "Marco da frente cafeeira do Norte do Parana e da transicao para graos e agroindustria.",
    "Caxias do Sul": "Serra Gaucha: cooperativas, vinho e metal-mecanica com base em pequena propriedade familiar.",
    "Blumenau": "Vale do Itajai: industria textil nascida do isolamento dos vales e do escoamento fluvial.",
    "Maringá": "Polo planejado da frente cafeeira, hoje agronegocio, servicos e educacao regional.",
    "Chapecó": "Oeste catarinense: carnes, cooperativas e agroindustria puxadas pela integracao ferroviaria/rodoviaria.",
    "Passo Fundo": "Norte gaucho: graos, maquinas e educacao, elo entre interior agricola e mercados metropolitanos.",
}

for polo in POLOS_CENA1:
    polo["tipo"] = "Polo regional"
    polo["descricao"] = POLO_DESCRICOES.get(polo["name"], "")

ROTAS_FLUVIAIS = [
    {"name":"Jacui-Guaiba", "tipo":"Rota fluvial",
     "setor":"excedentes agricolas e primeiras manufaturas",
     "descricao":"Bacia que levou producao dos vales ate Porto Alegre, formando o grande polo comercial gaucho.",
     "path":[[-52.4,-29.7],[-51.95,-29.8],[-51.55,-29.95],[-51.22,-30.03]]},
    {"name":"Itajai-Acu", "tipo":"Rota fluvial",
     "setor":"vale textil catarinense",
     "descricao":"O Itajai-Acu foi a via de escoamento que conectou Blumenau e Brusque ao litoral e ao polo textil.",
     "path":[[-49.75,-27.0],[-49.45,-26.95],[-49.07,-26.92],[-48.67,-26.91]]},
]

INTEGRACAO_LABELS = [
    {"position":[-48.50,-25.50], "offset":[20,-86], "color":[14,116,144,235],
     "label":"Paranagua\nerva-mate, madeira\ne ferrovia da Serra do Mar"},
    {"position":[-49.07,-26.92], "offset":[90,-70], "color":[25,95,200,235],
     "label":"Vale do Itajai\nrota fluvial + textil"},
    {"position":[-48.84,-26.30], "offset":[92,-82], "color":[245,158,11,235],
     "label":"Joinville / S. Francisco\nmetal-mecanica + porto"},
    {"position":[-51.22,-30.03], "offset":[-82,-82], "color":[109,40,217,235],
     "label":"Porto Alegre\nJacui-Guaiba + industria"},
    {"position":[-52.62,-27.10], "offset":[-78,-72], "color":[34,197,94,235],
     "label":"Chapeco\nmadeira, colonizacao\ne carnes"},
]

METRICAS_CENA2 = {
    "PIB Municipal":    {"base": "pib",  "anos": [2010, 2023], "ano_state": "ano_pib",  "chave": "pib_2023",  "paleta": "azul", "legenda": ["Menor PIB", "Maior PIB"]},
    "Índice de Gini":   {"base": "gini", "anos": [2000, 2010], "ano_state": "ano_gini", "chave": "gini_2010", "paleta": "roxo", "legenda": ["Mais igual", "Mais desigual"]},
    "VA Agropecuário (%)":  {"base": "va_agro",  "anos": [2010, 2021], "ano_state": "ano_va", "chave": "va_agro_2021",  "paleta": "verde", "legenda": ["Menor participação", "Maior participação"], "formato": "percentual"},
    "VA Indústria (%)":     {"base": "va_ind",   "anos": [2010, 2021], "ano_state": "ano_va", "chave": "va_ind_2021",   "paleta": "azul",  "legenda": ["Menor participação", "Maior participação"], "formato": "percentual"},
    "VA Serviços (%)":      {"base": "va_serv",  "anos": [2010, 2021], "ano_state": "ano_va", "chave": "va_serv_2021",  "paleta": "roxo",  "legenda": ["Menor participação", "Maior participação"], "formato": "percentual"},
    "Adm. Pública (%)": {"base": "va_pub_share", "anos": [2010, 2021], "ano_state": "ano_va", "chave": "va_pub_share_2021", "paleta": "ambar", "legenda": ["Menor participação", "Maior participação"], "formato": "percentual"},
}

if st.session_state.metrica_cena2 not in METRICAS_CENA2:
    st.session_state.metrica_cena2 = "PIB Municipal"


def get_metrica_cena2_config(metrica_label):
    cfg = METRICAS_CENA2.get(metrica_label, METRICAS_CENA2["PIB Municipal"]).copy()
    if "anos" in cfg:
        ano = st.session_state.get(cfg["ano_state"], cfg["anos"][-1])
        cfg["ano"] = ano
        cfg["chave"] = f"{cfg['base']}_{ano}"
    return cfg

ARCOS_EXPORTACAO = [
    {"start_lon":-48.50,"start_lat":-25.50,"end_lon":121.47,"end_lat":31.23,
     "color_s":[34,197,94,220],"color_t":[34,197,94,30],"width":9,
     "produto":"🌱 Complexo Soja","destino":"Xangai · China","volume":"12 mi ton/ano","porto":"Paranaguá"},
    {"start_lon":-52.10,"start_lat":-32.00,"end_lon":4.50,"end_lat":51.90,
     "color_s":[34,197,94,220],"color_t":[34,197,94,30],"width":6,
     "produto":"🥩 Carne Bovina","destino":"Rotterdam · UE","volume":"680 mil ton/ano","porto":"Rio Grande"},
    {"start_lon":-48.67,"start_lat":-26.91,"end_lon":139.69,"end_lat":35.69,
     "color_s":[34,197,94,220],"color_t":[34,197,94,30],"width":5,
     "produto":"🐔 Frango Processado","destino":"Tóquio · Japão","volume":"420 mil ton/ano","porto":"Itajaí"},
    {"start_lon":-48.50,"start_lat":-25.50,"end_lon":18.42,"end_lat":-33.92,
     "color_s":[34,197,94,200],"color_t":[34,197,94,30],"width":4,
     "produto":"🌲 Celulose","destino":"Cidade do Cabo · ZA","volume":"260 mil ton/ano","porto":"Paranaguá"},
    {"start_lon":-48.50,"start_lat":-25.50,"end_lon":55.30,"end_lat":25.20,
     "color_s":[34,197,94,200],"color_t":[34,197,94,30],"width":5,
     "produto":"🐔 Carne Halal","destino":"Dubai · Oriente Médio","volume":"180 mil ton/ano","porto":"Paranaguá"},
    {"start_lon":-49.27,"start_lat":-25.43,"end_lon":-46.63,"end_lat":-23.55,
     "color_s":[59,130,246,220],"color_t":[59,130,246,30],"width":7,
     "produto":"🚗 Indústria Automotiva","destino":"São Paulo · BR","volume":"R$ 45 bi/ano","porto":"Interno"},
    {"start_lon":-49.27,"start_lat":-25.43,"end_lon":-58.38,"end_lat":-34.61,
     "color_s":[59,130,246,220],"color_t":[59,130,246,30],"width":5,
     "produto":"⚙️ Autopeças & Máquinas","destino":"Buenos Aires · Mercosul","volume":"R$ 18 bi/ano","porto":"Terrestre"},
    {"start_lon":-48.55,"start_lat":-27.60,"end_lon":-122.41,"end_lat":37.78,
     "color_s":[168,85,247,200],"color_t":[168,85,247,30],"width":3,
     "produto":"💻 Software & TI","destino":"São Francisco · EUA","volume":"R$ 8 bi/ano","porto":"Digital"},
]

PORTOS = [
    {"name":"Porto de Paranaguá",            "position":[-48.50,-25.50],"color":[14,116,144],"radius":20000,"movimento":"R$ 48 bi/ano em exportações",
     "produto":"Porto exportador", "porto":"Paranaguá", "destino":"Ásia, Oriente Médio e rotas atlânticas", "volume":"R$ 48 bi/ano"},
    {"name":"Porto de Itajaí / Navegantes",  "position":[-48.67,-26.91],"color":[14,116,144],"radius":15000,"movimento":"R$ 28 bi/ano em exportações",
     "produto":"Porto exportador", "porto":"Itajaí / Navegantes", "destino":"Contêineres, carnes e indústria", "volume":"R$ 28 bi/ano"},
    {"name":"Porto de Rio Grande",           "position":[-52.10,-32.00],"color":[14,116,144],"radius":17000,"movimento":"R$ 32 bi/ano em exportações",
     "produto":"Porto exportador", "porto":"Rio Grande", "destino":"Atlântico, UE e grãos/carnes", "volume":"R$ 32 bi/ano"},
    {"name":"Porto de São Francisco do Sul", "position":[-48.63,-26.24],"color":[14,116,144],"radius":11000,"movimento":"R$ 15 bi/ano em exportações",
     "produto":"Porto exportador", "porto":"São Francisco do Sul", "destino":"Cargas industriais e agrícolas", "volume":"R$ 15 bi/ano"},
]

ROTA_GLOBAL_DESCRICOES = [
    "A soja sintetiza a funcao do Sul como plataforma agroexportadora: alto volume, baixa margem decisoria local e forte dependencia de preco internacional, cambio e demanda chinesa.",
    "A carne bovina sai por Rio Grande para mercados premium e regula a conexao entre pecuaria, frigorificos, controle sanitario e cadeias de distribuicao europeias.",
    "O frango processado revela a forca das cooperativas e agroindustrias catarinenses: tecnologia produtiva regional, mas demanda final e padroes comerciais definidos fora do territorio.",
    "A celulose conecta florestas plantadas, logistica portuaria e industria de base. E uma rota de escala, intensiva em terra, capital e infraestrutura.",
    "A carne halal mostra como a producao regional se adapta a nichos globais: certificacao religiosa, frigorificos especializados e rotas para o Oriente Medio.",
    "A industria automotiva conecta Curitiba e o eixo metropolitano ao comando empresarial e financeiro paulista, mostrando integracao nacional com hierarquia decisoria.",
    "Autopecas e maquinas desenham a ponte industrial do Mercosul: o Sul funciona como elo fabril entre Brasil, Argentina e cadeias regionais de montagem.",
    "Software e TI apontam a camada mais leve da globalizacao regional: servicos exportaveis, capital humano urbano e conexao direta com mercados de alto valor.",
]

for arco, descricao in zip(ARCOS_EXPORTACAO, ROTA_GLOBAL_DESCRICOES):
    arco["tipo"] = "Rota comercial"
    arco["descricao"] = descricao
    arco["width"] = max(arco.get("width", 4) + 1.5, 5.5)

for porto in PORTOS:
    porto["tipo"] = "Porto exportador"
    porto["descricao"] = (
        "Ponto de saida da producao regional. O porto concentra infraestrutura, alfandega, armazenagem "
        "e a passagem do territorio produtivo para os mercados nacionais e globais."
    )

PORTOS_CENA1 = []
for porto in PORTOS:
    item = porto.copy()
    item["tipo"] = "Porto"
    item["setor"] = item.get("movimento", "porta de escoamento regional")
    item["descricao"] = (
        "No mapa de integracao, o porto mostra onde trilhos, rodovias e vales industriais encontram o Atlantico."
    )
    item["color"] = [14,116,144]
    item["radius"] = int(item.get("radius", 12000) * 0.72)
    PORTOS_CENA1.append(item)

ESTADO_LABELS = [
    {"name":"PARANA", "uf":"PR", "position":[-52.1,-24.7]},
    {"name":"SANTA CATARINA", "uf":"SC", "position":[-50.4,-27.1]},
    {"name":"RIO GRANDE DO SUL", "uf":"RS", "position":[-53.0,-30.0]},
]

DIVISAS_ESTADUAIS = [
    {"name":"Divisa PR-SC", "path":[[-53.8,-25.95],[-52.9,-26.2],[-51.8,-26.1],[-50.8,-26.25],[-49.8,-26.2],[-48.9,-26.25]]},
    {"name":"Divisa SC-RS", "path":[[-53.8,-27.2],[-52.9,-27.4],[-51.9,-27.7],[-50.8,-28.0],[-49.8,-28.6],[-49.3,-29.0]]},
]

CENAS_CONFIG = [
    {"titulo":"Raízes",           "eixo":"Eixo 1 · Formação",    "icone":"🌱",
     "cor_acento":"#92400e","cor_bg":"rgba(245,158,11,0.07)","cor_borda":"rgba(245,158,11,0.28)",
     "intro":"Antes do PIB e dos portos, havia a terra. Clima subtropical, solos vermelhos e os pampas criaram ecossistemas econômicos distintos — moldados pela colonização europeia e pelo apagamento dos povos originários.",
     "mapa":"road"},
    {"titulo":"Integração",       "eixo":"Eixo 2 · Conexão",     "icone":"🛤️",
     "cor_acento":"#065f46","cor_bg":"rgba(16,185,129,0.06)","cor_borda":"rgba(16,185,129,0.25)",
     "intro":"Ferrovias e rodovias costuraram o território. Mas a integração veio com tensão: crescia o debate sobre autonomia regional frente à dependência do capital paulista e das decisões centralizadas em Brasília.",
     "mapa":"light"},
    {"titulo":"Desigualdades",    "eixo":"Eixo 3 · Raio-X",      "icone":"📊",
     "cor_acento":"#4c1d95","cor_bg":"rgba(109,40,217,0.06)","cor_borda":"rgba(109,40,217,0.22)",
     "intro":"O mapa revela o que o discurso 'Sul rico' esconde: litoral e capitais concentram riqueza enquanto interior e pampas exibem Gini elevado. Selecione o indicador para radiografar o território.",
     "mapa":"light"},
    {"titulo":"Tabuleiro Global", "eixo":"Eixo 4 · Conclusão",   "icone":"🌐",
     "cor_acento":"#0c4a6e","cor_bg":"rgba(14,116,144,0.07)","cor_borda":"rgba(14,116,144,0.26)",
     "intro":"Os arcos revelam a tese: soja e carne partem para a Ásia; autopeças circulam para o Sudeste e Mercosul. O Sul exporta matéria-prima e importa decisão. Cérebro ou músculo das cadeias globais?",
     "mapa":"dark"},
]

VIEW_STATES = [
    pdk.ViewState(latitude=-27.4, longitude=-52.0, zoom=5.2, pitch=0,  bearing=0,   transition_duration=2000),
    pdk.ViewState(latitude=-27.5, longitude=-51.5, zoom=5.8, pitch=0,  bearing=0,   transition_duration=2000),
    pdk.ViewState(latitude=-27.0, longitude=-51.0, zoom=6.2, pitch=45, bearing=5,   transition_duration=2000),
    pdk.ViewState(latitude=-26.0, longitude=-44.0, zoom=4.8, pitch=30, bearing=-10, transition_duration=2000),
]

# ════════════════════════════════════════════════════════
# 4. CARGA DE DADOS GEOESPACIAIS
# ════════════════════════════════════════════════════════
@st.cache_data
def carregar_geojson():
    """
    Carrega sul_master.geojson do mesmo diretório do script.
    Suporta colunas com nomes variados (IBGE, lowercase, etc.).
    Mapeia para chaves fixas usadas pelo dashboard: pib, gini, va_agro, va_ind, va_serv.
    """
    try:
        gdf = gpd.read_file("sul_master.geojson")
        gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.005)

        cols = gdf.columns.tolist()

        def find(opts):
            return next((c for c in opts if c in cols), None)

        # ── Nome do município (inclui name_muni do GeoJSON do usuário) ──
        col_mun = find([
            'name_muni','NM_MUN','NM_MUNICIP','NOME_MUN',
            'NOME','NAME','MUNICIPIO','MUNICÍPIO','nm_mun'
        ])
        if not col_mun:
            gdf['name_muni'] = [f"Município {i}" for i in range(len(gdf))]
            col_mun = 'name_muni'
        col_uf = find(['abbrev_state','SIGLA_UF','UF','sg_uf'])

        # ── Mapeamento de colunas para chaves fixas ──
        col_map = {
            'pib_2010':  find(['pib_2010','PIB_2010']),
            'pib_2023':  find(['pib_2023','PIB_2023','pib','PIB','pib_total','PIB_TOTAL','vl_pib','VL_PIB','pib_mun']),
            'gini_2000': find(['Índice de Gini 2000','indice_gini_2000','gini_2000','GINI_2000']),
            'gini_2010': find(['Índice de Gini 2010','indice_gini_2010','gini_2010','GINI_2010','gini','GINI','gini_coef','GINI_COEF']),
            'va_total_2010': find(['va_total_2010','VAB_TOTAL_2010']),
            'va_total_2021': find(['va_total_2021','VAB_TOTAL_2021']),
            'va_agro_2010':  find(['va_agro_2010','VA_AGRO_2010','vab_agropecuaria_2010','VAB_AGROPECUARIA_2010']),
            'va_agro_2021':  find(['va_agro_2021','VA_AGRO_2021','vab_agropecuaria_2021','VAB_AGROPECUARIA_2021']),
            'va_ind_2010':   find(['va_ind_2010','VA_IND_2010','vab_industria_2010','VAB_INDUSTRIA_2010']),
            'va_ind_2021':   find(['va_ind_2021','VA_IND_2021','vab_industria_2021','VAB_INDUSTRIA_2021']),
            'va_serv_2010':  find(['va_serv_2010','VA_SERV_2010','vab_servicos_2010','VAB_SERVICOS_2010']),
            'va_serv_2021':  find(['va_serv_2021','VA_SERV_2021','vab_servicos_2021','VAB_SERVICOS_2021']),
            'va_pub_share_2010': find(['va_pub_share_2010','PART_ADM_PUBLICA_2010']),
            'va_pub_share_2021': find(['va_pub_share_2021','PART_ADM_PUBLICA_2021']),
        }

        # ── Fallback com dados simulados se coluna não encontrada ──
        fallbacks = {
            'pib_2010':  (50_000, 1_600_000, False),
            'pib_2023':  (120_000, 4_000_000, False),
            'gini_2000': (0.38,   0.72,      True),
            'gini_2010': (0.34,   0.68,      True),
            'va_total_2010': (50_000, 1_200_000, False),
            'va_total_2021': (120_000, 3_200_000, False),
            'va_agro_2010':  (10_000, 800_000,   False),
            'va_agro_2021':  (20_000, 1_400_000, False),
            'va_ind_2010':   (5_000,  600_000,   False),
            'va_ind_2021':   (12_000, 1_200_000, False),
            'va_serv_2010':  (20_000, 1_200_000, False),
            'va_serv_2021':  (45_000, 2_400_000, False),
            'va_pub_share_2010': (5, 45, True),
            'va_pub_share_2021': (5, 45, True),
        }
        for chave, (lo, hi, is_float) in fallbacks.items():
            if not col_map[chave]:
                if is_float:
                    gdf[chave] = np.random.uniform(lo, hi, len(gdf))
                else:
                    gdf[chave] = np.random.randint(int(lo), int(hi), len(gdf))
                col_map[chave] = chave

        # ── Paleta de cores ──
        def interp_color(v, stops):
            v = 0.5 if pd.isna(v) else float(np.clip(v, 0, 1))
            for i in range(len(stops) - 1):
                p0, c0 = stops[i]
                p1, c1 = stops[i + 1]
                if v <= p1:
                    t = 0 if p1 == p0 else (v - p0) / (p1 - p0)
                    return [int(c0[j] + (c1[j] - c0[j]) * t) for j in range(3)] + [255]
            return stops[-1][1] + [255]

        def cor(v, paleta):
            if pd.isna(v):
                return [156, 170, 188, 238]
            if paleta == 'azul':
                return [int(186+(3-186)*v),   int(230+(105-230)*v), int(253+(161-253)*v), 255]
            elif paleta == 'verde':
                return [int(220+(22-220)*v),   int(252+(163-252)*v), int(231+(74-231)*v),  255]
            elif paleta == 'ambar':
                return [int(254+(180-254)*v),  int(243+(83-243)*v),  int(199+(9-199)*v),   255]
            elif paleta == 'gini':
                return interp_color(v, [
                    (0.00, [37, 99, 235]),
                    (0.28, [59, 130, 246]),
                    (0.50, [129, 140, 248]),
                    (0.74, [124, 119, 146]),
                    (1.00, [95, 90, 112]),
                ])
            else:
                return [int(237+(109-237)*v),  int(233+(40-233)*v),  int(254+(217-254)*v), 255]

        paletas = {
            'pib_2010':'azul','pib_2023':'azul',
            'gini_2000':'gini','gini_2010':'gini',
            'va_total_2010':'azul','va_total_2021':'azul',
            'va_agro_2010':'verde','va_agro_2021':'verde',
            'va_ind_2010':'azul','va_ind_2021':'azul',
            'va_serv_2010':'roxo','va_serv_2021':'roxo',
            'va_pub_share_2010':'ambar','va_pub_share_2021':'ambar'
        }

        for chave, real_col in col_map.items():
            serie = pd.to_numeric(
                gdf[real_col].astype(str).str.replace(',', '.', regex=False),
                errors='coerce'
            ).fillna(0)
            # Normalização: sqrt para valores absolutos, linear para índices/participações.
            serie_n = serie if chave.startswith(('gini', 'va_pub_share')) else np.sqrt(np.maximum(serie, 0))
            vmin, vmax = serie_n.min(), serie_n.quantile(0.99)
            norm = ((serie_n - vmin) / (vmax - vmin)).clip(0, 1) if vmax > vmin else pd.Series(0.5, index=gdf.index)
            gdf[f'color_{chave}'] = [cor(v, paletas[chave]) for v in norm]
            if chave.startswith('gini'):
                gdf[f'{chave}_fmt'] = serie.apply(lambda x: f"{x:.3f}".replace('.', ','))
            elif chave.startswith('va_pub_share'):
                gdf[f'{chave}_fmt'] = serie.apply(lambda x: f"{x:.2f}%".replace('.', ','))
            else:
                gdf[f'{chave}_fmt'] = serie.apply(lambda x: f"R$ {x:,.0f}".replace(',', '.'))

        series_raw = {}
        for chave, real_col in col_map.items():
            series_raw[chave] = pd.to_numeric(
                gdf[real_col].astype(str).str.replace(',', '.', regex=False),
                errors='coerce'
            )

        for ano in [2010, 2021]:
            total = series_raw.get(f'va_total_{ano}', pd.Series(0, index=gdf.index)).replace(0, np.nan)
            for setor in ['va_agro', 'va_ind', 'va_serv']:
                chave_setor = f'{setor}_{ano}'
                if chave_setor in series_raw:
                    series_raw[chave_setor] = (series_raw[chave_setor] / total * 100).replace([np.inf, -np.inf], np.nan).fillna(0)

        pib_shared = pd.concat([
            np.sqrt(np.maximum(series_raw.get('pib_2010', pd.Series(dtype=float)), 0)),
            np.sqrt(np.maximum(series_raw.get('pib_2023', pd.Series(dtype=float)), 0)),
        ])
        pib_vmin, pib_vmax = pib_shared.quantile(0.02), pib_shared.quantile(0.985)

        def normalizar_gini(serie):
            clean = serie.replace([np.inf, -np.inf], np.nan)
            valid_mask = clean.notna() & (clean > 0)
            valid = clean[valid_mask]
            if valid.nunique() < 2:
                return pd.Series(0.5, index=serie.index)

            lo, hi = valid.min(), valid.max()
            center = float(valid.mean())
            if not lo < center < hi:
                center = float(valid.median())

            clipped = clean.clip(lo, hi)
            base = clipped.fillna(center)
            lower_span = max(center - lo, 1e-9)
            upper_span = max(hi - center, 1e-9)

            below = ((center - base) / lower_span).clip(0, 1).pow(0.58)
            above = ((base - center) / upper_span).clip(0, 1).pow(0.58)
            centered = pd.Series(
                np.where(base >= center, 0.5 + 0.5 * above, 0.5 - 0.5 * below),
                index=serie.index,
            ).clip(0, 1)

            rank_norm = pd.Series(0.5, index=serie.index, dtype=float)
            ranks = clipped[valid_mask].rank(method='average', pct=True)
            if ranks.max() > ranks.min():
                rank_norm.loc[valid_mask] = ((ranks - ranks.min()) / (ranks.max() - ranks.min())).clip(0, 1)

            hybrid = (0.66 * rank_norm + 0.34 * centered).clip(0, 1)
            return (0.5 + (hybrid - 0.5) * 0.98).clip(0, 1)

        def normalizar(serie, chave):
            if chave.startswith('pib_'):
                serie_n = np.sqrt(np.maximum(serie.fillna(0), 0))
                norm = ((serie_n - pib_vmin) / (pib_vmax - pib_vmin)).clip(0, 1) if pib_vmax > pib_vmin else pd.Series(0.5, index=gdf.index)
                return norm.pow(0.92)
            if chave.startswith('gini'):
                return normalizar_gini(serie)
            if chave.startswith(('va_agro', 'va_ind', 'va_serv', 'va_pub_share')):
                vmin, vmax = serie.quantile(0.04), serie.quantile(0.96)
                norm = ((serie - vmin) / (vmax - vmin)).clip(0, 1) if vmax > vmin else pd.Series(0.5, index=gdf.index)
                return ((norm - 0.5) * 1.18 + 0.5).clip(0, 1)
            serie_n = np.sqrt(np.maximum(serie.fillna(0), 0))
            vmin, vmax = serie_n.min(), serie_n.quantile(0.99)
            return ((serie_n - vmin) / (vmax - vmin)).clip(0, 1) if vmax > vmin else pd.Series(0.5, index=gdf.index)

        for chave, serie in series_raw.items():
            norm = normalizar(serie, chave)
            gdf[f'color_{chave}'] = [
                cor(np.nan if pd.isna(valor) else v, paletas[chave])
                for valor, v in zip(serie, norm)
            ]
            if chave.startswith('gini'):
                gdf[f'{chave}_fmt'] = serie.apply(lambda x: "sem dado" if pd.isna(x) else f"{x:.3f}".replace('.', ','))
            elif chave.startswith(('va_agro', 'va_ind', 'va_serv', 'va_pub_share')):
                gdf[f'{chave}_fmt'] = serie.apply(lambda x: f"{x:.2f}%".replace('.', ','))
            else:
                gdf[f'{chave}_fmt'] = serie.apply(lambda x: f"R$ {x:,.0f}".replace(',', '.'))

        state_borders = None
        if col_uf:
            estados = gdf[[col_uf, 'geometry']].dissolve(by=col_uf).reset_index()
            state_borders = json.loads(estados.to_json())

        return json.loads(gdf.to_json()), col_mun, state_borders

    except Exception as e:
        st.warning(f"⚠️ sul_master.geojson não encontrado ou inválido: {e}")
        return None, 'name_muni', None


geojson_data, col_mun, state_borders_data = carregar_geojson()

RECORTES_CENA2 = {
    "Sul inteiro": None,
    "Paraná": "PR",
    "Santa Catarina": "SC",
    "Rio Grande do Sul": "RS",
}

VIEW_STATES_CENA2 = {
    "Sul inteiro": VIEW_STATES[2],
    "Paraná": pdk.ViewState(latitude=-24.9, longitude=-51.7, zoom=6.8, pitch=35, bearing=0, transition_duration=900),
    "Santa Catarina": pdk.ViewState(latitude=-27.2, longitude=-50.3, zoom=7.2, pitch=35, bearing=0, transition_duration=900),
    "Rio Grande do Sul": pdk.ViewState(latitude=-30.0, longitude=-53.2, zoom=6.5, pitch=35, bearing=0, transition_duration=900),
}

ROOTS_STATE_STYLE = {
    "PR": {"fill": [130, 55, 195, 42], "line": [130, 55, 195, 160]},
    "SC": {"fill": [25, 95, 200, 42], "line": [25, 95, 200, 165]},
    "RS": {"fill": [220, 100, 35, 38], "line": [50, 150, 65, 165]},
}


def get_geojson_cena2():
    recorte = st.session_state.get("recorte_cena2", "Sul inteiro")
    uf = RECORTES_CENA2.get(recorte)
    if not uf or not geojson_data:
        return geojson_data
    data = json.loads(json.dumps(geojson_data))
    data["features"] = [
        f for f in data.get("features", [])
        if f.get("properties", {}).get("abbrev_state") == uf
    ]
    return data


def get_state_borders_filtered():
    recorte = st.session_state.get("recorte_cena2", "Sul inteiro")
    uf = RECORTES_CENA2.get(recorte)
    if not uf or not state_borders_data:
        return state_borders_data
    data = json.loads(json.dumps(state_borders_data))
    data["features"] = [
        f for f in data.get("features", [])
        if f.get("properties", {}).get("abbrev_state") == uf
    ]
    return data


def get_estado_labels_cena2():
    recorte = st.session_state.get("recorte_cena2", "Sul inteiro")
    uf = RECORTES_CENA2.get(recorte)
    if not uf:
        return ESTADO_LABELS
    return [label for label in ESTADO_LABELS if label.get("uf") == uf]


def get_roots_state_data():
    if not state_borders_data:
        return None
    data = json.loads(json.dumps(state_borders_data))
    for feature in data.get("features", []):
        props = feature.setdefault("properties", {})
        uf = props.get("abbrev_state") or props.get("UF") or props.get("SIGLA_UF")
        style = ROOTS_STATE_STYLE.get(uf, {"fill": [14, 116, 144, 28], "line": [14, 116, 144, 120]})
        props["roots_fill_color"] = style["fill"]
        props["roots_line_color"] = style["line"]
    return data


roots_state_data = get_roots_state_data()

# ════════════════════════════════════════════════════════
# 5. LAYERS E TOOLTIP
# ════════════════════════════════════════════════════════
def get_cards_historicos_mapa():
    foco = st.session_state.get('foco_historia', 0)
    cards = []
    for i, r in enumerate(REGIOES_HISTORICAS):
        cor = r['color']
        is_active = (i == foco)
        cards.append({
            **r,
            "point_color": cor + [245],
            "halo_color": cor + [55 if is_active else 35],
            "halo_radius": 65000 if is_active else 48000,
            "point_radius": int(r["radius"] * (1.28 if is_active else 1.0)),
        })
    return cards


def get_layers(cena, metrica_label=None):
    if cena == 0:
        layers = []
        if roots_state_data:
            layers.append(pdk.Layer(
                "GeoJsonLayer", data=roots_state_data,
                opacity=1.0, stroked=False, filled=True, pickable=False,
                get_fill_color="properties.roots_fill_color",
            ))
        return layers

    elif cena == 1:
        layers = []
        if roots_state_data:
            layers.append(pdk.Layer(
                "GeoJsonLayer", data=roots_state_data,
                opacity=1.0, stroked=False, filled=True, pickable=False,
                get_fill_color="properties.roots_fill_color",
            ))
        layers += [
            pdk.Layer("PathLayer", data=FERROVIAS,
                get_path="path", get_color=[185,150,70,55],
                width_min_pixels=12.0, pickable=False),
            pdk.Layer("PathLayer", data=RODOVIAS,
                get_path="path", get_color=[70,165,70,45],
                width_min_pixels=10.5, pickable=False),
            pdk.Layer("PathLayer", data=ROTAS_FLUVIAIS,
                get_path="path", get_color=[14,116,144,75],
                width_min_pixels=11.0, pickable=False),
            pdk.Layer("PathLayer", data=ROTAS_FLUVIAIS,
                get_path="path", get_color=[14,116,144,190],
                width_min_pixels=4.2, pickable=True),
            # Ferrovias — cor âmbar / dourado
            pdk.Layer("PathLayer", data=FERROVIAS,
                get_path="path", get_color=[185,150,70,210],
                width_min_pixels=6.2, pickable=True),
            # Rodovias — cor verde
            pdk.Layer("PathLayer", data=RODOVIAS,
                get_path="path", get_color=[70,165,70,170],
                width_min_pixels=5.0, pickable=True),
            # Polos industriais
            pdk.Layer("ScatterplotLayer", data=POLOS_CENA1,
                get_position="position", get_fill_color="color", get_radius="radius",
                opacity=0.78, stroked=True, get_line_color=[255,255,255,190],
                line_width_min_pixels=2, pickable=True),
            pdk.Layer("ScatterplotLayer", data=PORTOS_CENA1,
                get_position="position", get_fill_color=[14,116,144,205], get_radius="radius",
                opacity=0.78, stroked=True, get_line_color=[255,255,255,230],
                line_width_min_pixels=2.4, pickable=True),
        ]
        return layers

    elif cena == 2:
        layers = []
        data_cena2 = get_geojson_cena2()
        if geojson_data and metrica_label:
            chave = get_metrica_cena2_config(metrica_label)['chave']
            layers.append(pdk.Layer(
                "GeoJsonLayer", data=data_cena2,
                opacity=1.0, stroked=True, filled=True, pickable=True,
                get_fill_color=f"properties.color_{chave}",
                get_line_color=[255,255,255,42],
                line_width_min_pixels=0.18,
                update_triggers={"get_fill_color": chave},
            ))
        layers.append(pdk.Layer(
            "TextLayer", data=get_estado_labels_cena2(),
            get_position="position", get_text="name",
            get_color=[15,23,42,120], get_size=15,
            size_units="pixels", size_min_pixels=12, size_max_pixels=18,
            billboard=True, pickable=False,
        ))
        layers.append(pdk.Layer(
            "ScatterplotLayer", data=POLOS_CENA1,
            get_position="position", get_fill_color=[15,23,42,220],
            get_radius=7000, opacity=0.95,
            stroked=True, get_line_color=[255,255,255,230], line_width_min_pixels=2,
            pickable=False,
        ))
        return layers

    elif cena == 3:
        layers = []
        # GeoJSON como fundo escuro para dar contexto geográfico
        if geojson_data:
            layers.append(pdk.Layer(
                "GeoJsonLayer", data=geojson_data,
                opacity=0.35, stroked=True, filled=True, pickable=False,
                get_fill_color=[20, 40, 70, 160],
                get_line_color=[60, 100, 140, 80],
                line_width_min_pixels=0.3,
            ))
        layers += [
            pdk.Layer("ArcLayer", data=ARCOS_EXPORTACAO,
                get_source_position=["start_lon","start_lat"],
                get_target_position=["end_lon","end_lat"],
                get_source_color="color_s", get_target_color="color_t",
                get_width="width", pickable=True, auto_highlight=True),
            pdk.Layer("ScatterplotLayer", data=PORTOS,
                get_position="position", get_fill_color="color", get_radius="radius",
                opacity=0.92, stroked=True, get_line_color=[255,255,255,220],
                line_width_min_pixels=2.5, pickable=True),
        ]
        return layers

    return []


def get_tooltip(cena, metrica_label=None):
    style = {
        "backgroundColor": "rgba(255,255,255,0.97)",
        "border": "1px solid rgba(203,213,225,0.8)",
        "borderRadius": "12px", "padding": "12px 16px",
        "boxShadow": "0 10px 30px rgba(15,23,42,0.16)",
        "fontFamily": "DM Sans,sans-serif", "color": "#0f172a",
        "maxWidth": "240px",
    }
    lbl = "<div style='font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.12em;margin-bottom:4px;'>"
    val = "<div style='font-size:15px;font-weight:700;color:#0f172a;margin-bottom:5px;'>"

    if cena == 0:
        return {}
    elif cena == 1:
        return {"html": f"{lbl}{{tipo}}</div>{val}{{name}}</div>"
                        f"<div style='font-size:11px;color:#0e7490;margin-bottom:6px;'>{{setor}}</div>"
                        f"<div style='font-size:12px;line-height:1.45;color:#475569;'>{{descricao}}</div>",
                "style": style}
    elif cena == 2:
        cfg = get_metrica_cena2_config(metrica_label) if metrica_label else get_metrica_cena2_config("PIB Municipal")
        chave = cfg['chave']
        ano_label = f" · {cfg['ano']}" if 'ano' in cfg else ""
        mun_key = f"{{{col_mun}}}"
        uf_key = "{abbrev_state}"
        dado_key = f"{{{chave}_fmt}}"
        return {"html": f"{lbl}Município · {uf_key}</div>{val}{mun_key}</div>"
                        f"<div style='font-size:12px;color:#64748b;margin-bottom:2px;'>{metrica_label or 'PIB Municipal'}{ano_label}</div>"
                        f"<div style='font-size:16px;font-weight:800;color:#0e7490;'>{dado_key}</div>",
                "style": style}
    elif cena == 3:
        style3 = {**style, "maxWidth": "360px", "padding": "14px 18px"}
        return {"html": f"{lbl}{{tipo}}</div>{val}{{produto}}</div>"
                        f"<div style='font-size:12px;color:#64748b;margin-bottom:2px;'>Porto/base: {{porto}}</div>"
                        f"<div style='font-size:12px;color:#64748b;margin-bottom:4px;'>Destino: {{destino}}</div>"
                        f"<div style='font-size:15px;font-weight:800;color:#0e7490;margin-bottom:8px;'>{{volume}}</div>"
                        f"<div style='font-size:12px;line-height:1.48;color:#475569;'>{{descricao}}</div>",
                "style": style3}
    return {}


# ════════════════════════════════════════════════════════
# 6. GERADOR DE HTML — PAINEL DIREITO
# ════════════════════════════════════════════════════════

def _cor_hex(rgb):
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


ROOTS_FRAME_WIDTH = 1920
ROOTS_FRAME_HEIGHT = 1080

ROOTS_CARD_LAYOUT = {
    "norte_parana": (39.60, 14.80),
    "vale_itajai": (68.38, 33.28),
    "pampas_gauchos": (32.79, 84.07),
    "serra_gaucha": (62.63, 73.84),
}


def _project_to_roots_frame(position):
    """Project lon/lat to the fixed 16:9 composition used in the roots scene."""
    lon, lat = position
    view = VIEW_STATES[0]
    world_size = 512 * (2 ** view.zoom)

    def project(lon_value, lat_value):
        siny = math.sin(math.radians(lat_value))
        siny = min(max(siny, -0.9999), 0.9999)
        x = (lon_value + 180.0) / 360.0 * world_size
        y = (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)) * world_size
        return x, y

    center_x, center_y = project(view.longitude, view.latitude)
    point_x, point_y = project(lon, lat)
    screen_x = ROOTS_FRAME_WIDTH / 2 + (point_x - center_x)
    screen_y = ROOTS_FRAME_HEIGHT / 2 + (point_y - center_y)
    return screen_x / ROOTS_FRAME_WIDTH * 100, screen_y / ROOTS_FRAME_HEIGHT * 100


ROOTS_IMAGE_FILES = {
    "serra_gaucha": "SERRA_GAUCHA.jpg",
    "pampas_gauchos": "PAMPAS_GAUCHOS.jpg",
    "norte_parana": "NORTE_PARANA.jpg",
    "vale_itajai": "VALE_ITAJAI.jpeg",
}


@st.cache_data
def carregar_imagens_raizes():
    imagens = {}
    for slug, filename in ROOTS_IMAGE_FILES.items():
        path = APP_DIR / filename
        if path.exists():
            mime = "image/jpeg" if path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            imagens[slug] = f"data:{mime};base64,{encoded}"
    return imagens


def _card_arrow():
    """Triângulo CSS apontando para a esquerda (→ mapa)"""
    return """<div style="position:absolute;left:-11px;top:28px;width:0;height:0;
        border-right:11px solid rgba(255,255,255,0.94);
        border-top:9px solid transparent;
        border-bottom:9px solid transparent;
        filter:drop-shadow(-2px 0 3px rgba(15,23,42,0.12));"></div>"""

def render_cena0_overlay():
    imagens = carregar_imagens_raizes()
    foco = st.session_state.get('foco_historia', 0)
    html = ['<div class="roots-overlay"><div class="roots-frame">']
    for i, r in enumerate(REGIOES_HISTORICAS):
        cor = _cor_hex(r['color'])
        pin_x, pin_y = _project_to_roots_frame(r['position'])
        card_x, card_y = ROOTS_CARD_LAYOUT.get(
            r['slug'],
            _project_to_roots_frame(r.get('card_position', r['position']))
        )
        active_cls = " is-active" if i == foco else ""
        tema = r['tema'].split(' ', 1)[1] if ' ' in r['tema'] else r['tema']
        texto_card = r['texto']
        img = imagens.get(r['slug'], "")
        media_style = (
            f"background-image:linear-gradient(180deg,rgba(15,23,42,0.04),rgba(15,23,42,0.26)),url('{img}');"
            if img else
            f"background:linear-gradient(135deg,rgba({r['color'][0]},{r['color'][1]},{r['color'][2]},0.28),rgba(255,255,255,0.40));"
        )
        html.append(f"""
<div class="roots-pin" style="--pin-x:{pin_x:.3f}%;--pin-y:{pin_y:.3f}%;--accent:{cor};--accent-soft:{cor}33;"></div>
<section class="roots-card root-{r['slug']}{active_cls}" style="--card-x:{card_x:.3f}%;--card-y:{card_y:.3f}%;--accent:{cor};--accent-soft:{cor}44;border-color:rgba({r['color'][0]},{r['color'][1]},{r['color'][2]},0.42);">
    <div class="roots-card-media" style="{media_style}"></div>
    <div class="roots-card-body">
        <div class="roots-card-kicker">{r['name']}</div>
        <div class="roots-card-title">{tema}</div>
        <div class="roots-card-text">{texto_card}</div>
        <div class="roots-card-chip" style="background:{cor}22;color:{cor};border:1px solid {cor}55;">
            {r['dado']}
        </div>
    </div>
</section>""")
    html.append("</div></div>")
    return "".join(html)

def render_cena0_cards(foco):
    html = ""
    for i, r in enumerate(REGIOES_HISTORICAS):
        is_active = (i == foco)
        cor = _cor_hex(r['color'])
        slug = r['slug']

        if is_active:
            # Card expandido com imagem placeholder + texto completo
            html += f"""
<div style="position:relative;background:rgba(255,255,255,0.94);border-radius:14px;
    margin-bottom:14px;
    backdrop-filter:blur(22px) saturate(180%);
    -webkit-backdrop-filter:blur(22px) saturate(180%);
    box-shadow:0 12px 40px rgba(15,23,42,0.20),0 2px 0 rgba(255,255,255,0.9) inset;
    border:1px solid rgba(255,255,255,0.92);
    overflow:visible;">
    {_card_arrow()}
    <!-- Imagem placeholder -->
    <div style="width:100%;height:110px;
        background:linear-gradient(135deg,rgba({r['color'][0]},{r['color'][1]},{r['color'][2]},0.12) 0%,rgba(241,245,249,0.9) 100%);
        border-radius:14px 14px 0 0;
        display:flex;align-items:center;justify-content:center;
        border-bottom:1px solid rgba(203,213,225,0.40);
        overflow:hidden;">
        <img src="app/static/{slug}.jpg"
             style="width:100%;height:100%;object-fit:cover;border-radius:14px 14px 0 0;"
             onerror="this.style.display='none'">
        <div style="position:absolute;text-align:center;color:{cor};font-size:0.68rem;line-height:1.8;pointer-events:none;">
            <div style="font-size:1.6rem;margin-bottom:2px;">📷</div>
            <span style="font-family:monospace;font-size:0.62rem;color:#94a3b8;
                background:rgba(255,255,255,0.8);padding:2px 6px;border-radius:4px;">
                {slug}.jpg
            </span>
        </div>
    </div>
    <!-- Conteúdo -->
    <div style="padding:13px 15px 14px;">
        <div style="font-size:0.60rem;text-transform:uppercase;letter-spacing:.13em;
            color:#94a3b8;margin-bottom:3px;">📍 {r['name']}</div>
        <div style="font-size:0.92rem;font-weight:700;color:#0f172a;margin-bottom:8px;
            font-family:'Playfair Display',serif;">{r['tema']}</div>
        <div style="font-size:0.78rem;color:#475569;line-height:1.58;margin-bottom:10px;">
            {r['texto']}
        </div>
        <div style="display:inline-block;background:{cor}1a;color:{cor};
            border:1px solid {cor}44;border-radius:6px;
            padding:4px 10px;font-size:0.70rem;font-weight:600;">
            📈 {r['dado']}
        </div>
    </div>
    <!-- Barra de cor acento -->
    <div style="position:absolute;top:0;left:0;width:4px;height:100%;
        background:{cor};border-radius:4px 0 0 4px;opacity:0.85;"></div>
</div>"""
        else:
            # Card compacto (pill)
            html += f"""
<div style="position:relative;background:rgba(255,255,255,0.78);border-radius:10px;
    margin-bottom:8px;padding:10px 14px;
    box-shadow:0 2px 12px rgba(15,23,42,0.09);
    border:1px solid rgba(203,213,225,0.55);
    border-left:3px solid {cor};">
    {_card_arrow()}
    <div style="font-size:0.72rem;font-weight:600;color:#334155;">{r['tema']}</div>
    <div style="font-size:0.65rem;color:#94a3b8;margin-top:2px;">{r['name']}</div>
</div>"""

    return html


def render_cena1_panel():
    return """
<div style="background:linear-gradient(145deg,rgba(255,255,255,0.72),rgba(255,255,255,0.36));
    backdrop-filter:blur(24px) saturate(165%);-webkit-backdrop-filter:blur(24px) saturate(165%);
    border-radius:18px;padding:16px;margin-bottom:12px;
    box-shadow:0 18px 48px rgba(15,23,42,0.18),inset 0 1px 0 rgba(255,255,255,0.82);
    border:1px solid rgba(255,255,255,0.74);">
    <div style="font-size:0.62rem;letter-spacing:.13em;color:#64748b;font-weight:600;
        text-transform:uppercase;margin-bottom:12px;">Como ler as rotas</div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <div style="width:30px;height:7px;background:rgba(185,150,70,0.85);border-radius:4px;flex-shrink:0;"></div>
        <span style="font-size:0.78rem;color:#334155;"><strong>Linhas âmbar</strong>: ferrovias de escoamento interior-portos</span>
    </div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <div style="width:30px;height:6px;background:rgba(70,165,70,0.8);border-radius:4px;flex-shrink:0;"></div>
        <span style="font-size:0.78rem;color:#334155;"><strong>Linhas verdes</strong>: rodovias estruturantes e corredores do Mercosul</span>
    </div>
    <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:13px;height:13px;border-radius:50%;background:rgba(14,116,144,0.85);flex-shrink:0;"></div>
        <span style="font-size:0.78rem;color:#334155;"><strong>Bolinhas</strong>: polos urbanos, industriais, logísticos ou agroindustriais</span>
    </div>
</div>
<div style="background:linear-gradient(145deg,rgba(255,255,255,0.68),rgba(255,255,255,0.34));
    backdrop-filter:blur(22px) saturate(165%);-webkit-backdrop-filter:blur(22px) saturate(165%);
    border-radius:18px;padding:14px;margin-bottom:12px;
    box-shadow:0 16px 42px rgba(15,23,42,0.14),inset 0 1px 0 rgba(255,255,255,0.78);
    border:1px solid rgba(255,255,255,0.70);">
    <div style="font-size:0.62rem;letter-spacing:.13em;color:#065f46;font-weight:600;
        text-transform:uppercase;margin-bottom:10px;">Notas para fala</div>
    <div style="border-left:3px solid rgba(70,165,70,0.85);padding-left:10px;margin-bottom:10px;">
        <div style="font-size:0.76rem;font-weight:800;color:#0f172a;">Corredor litoraneo</div>
        <div style="font-size:0.74rem;color:#475569;line-height:1.42;">BR-101, portos e industria catarinense encurtam o caminho ate o Atlantico.</div>
    </div>
    <div style="border-left:3px solid rgba(185,150,70,0.90);padding-left:10px;margin-bottom:10px;">
        <div style="font-size:0.76rem;font-weight:800;color:#0f172a;">Corredor interior</div>
        <div style="font-size:0.74rem;color:#475569;line-height:1.42;">Ferrovias e BR-116/277/290 puxam graos, carnes, madeira, maquinas e autopecas.</div>
    </div>
    <div style="border-left:3px solid rgba(14,116,144,0.85);padding-left:10px;">
        <div style="font-size:0.76rem;font-weight:800;color:#0f172a;">Leitura central</div>
        <div style="font-size:0.74rem;color:#475569;line-height:1.42;">A malha integra a regiao, mas tambem organiza dependencias: interior produz, portos escoam, centros financeiros comandam.</div>
    </div>
</div>
<div style="background:linear-gradient(145deg,rgba(245,158,11,0.16),rgba(255,255,255,0.28));
    backdrop-filter:blur(20px) saturate(160%);-webkit-backdrop-filter:blur(20px) saturate(160%);
    border:1px solid rgba(245,158,11,0.30);
    border-radius:18px;padding:14px;">
    <div style="font-size:0.62rem;letter-spacing:.13em;color:#92400e;font-weight:600;
        text-transform:uppercase;margin-bottom:8px;">Tensão Histórica</div>
    <p style="font-size:0.80rem;color:#334155;line-height:1.60;margin:0;">
        As ferrovias construídas no séc. XIX e XX seguiam a lógica do
        <strong>escoamento</strong> — conectavam o interior aos portos, e os portos a São Paulo e
        ao mercado externo. A integração era real, mas assimétrica: o Sul produzia,
        o Sudeste processava e financiava.
    </p>
</div>"""


def render_cena1_panel_compacto():
    return """
<div style="background:linear-gradient(145deg,rgba(255,255,255,0.70),rgba(255,255,255,0.34));
    backdrop-filter:blur(24px) saturate(165%);-webkit-backdrop-filter:blur(24px) saturate(165%);
    border-radius:18px;padding:16px;margin-bottom:12px;
    box-shadow:0 18px 48px rgba(15,23,42,0.16),inset 0 1px 0 rgba(255,255,255,0.82);
    border:1px solid rgba(255,255,255,0.74);">
    <div style="font-size:0.62rem;letter-spacing:.13em;color:#64748b;font-weight:700;
        text-transform:uppercase;margin-bottom:12px;">Como ler as rotas</div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <div style="width:30px;height:7px;background:rgba(185,150,70,0.88);border-radius:4px;flex-shrink:0;"></div>
        <span style="font-size:0.78rem;color:#334155;"><strong>Ambar</strong>: ferrovias e escoamento interior-portos</span>
    </div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <div style="width:30px;height:6px;background:rgba(70,165,70,0.82);border-radius:4px;flex-shrink:0;"></div>
        <span style="font-size:0.78rem;color:#334155;"><strong>Verde</strong>: rodovias estruturantes e Mercosul</span>
    </div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <div style="width:30px;height:5px;background:rgba(14,116,144,0.75);border-radius:4px;flex-shrink:0;"></div>
        <span style="font-size:0.78rem;color:#334155;"><strong>Azul</strong>: rotas fluviais historicas</span>
    </div>
    <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:13px;height:13px;border-radius:50%;background:rgba(14,116,144,0.85);flex-shrink:0;"></div>
        <span style="font-size:0.78rem;color:#334155;"><strong>Pontos</strong>: polos e portos; passe o mouse para a historia curta</span>
    </div>
</div>"""


def render_cena1_overlay():
    cards = [
        {
            "cls": "paranagua", "accent": "#0e7490", "kicker": "Porto + ferrovia",
            "title": "Paranagua",
            "text": "A Estrada de Ferro Curitiba-Paranagua venceu a Serra do Mar e transformou o porto em eixo do mate, da madeira e depois dos graos.",
            "chip": "Serra do Mar",
        },
        {
            "cls": "itajai", "accent": "#1d4ed8", "kicker": "Vale fluvial",
            "title": "Itajai-Acu",
            "text": "O rio conectou Blumenau, Brusque e o litoral. A circulacao fluvial ajudou a formar o polo textil e a rede industrial familiar catarinense.",
            "chip": "textil + portos",
        },
        {
            "cls": "portoalegre", "accent": "#6d28d9", "kicker": "Jacuí-Guaíba",
            "title": "Porto Alegre",
            "text": "Os excedentes dos vales desciam pelos rios ate a capital. Porto Alegre se consolidou como centro comercial, financeiro e industrial gaucho.",
            "chip": "rios + manufatura",
        },
        {
            "cls": "chapeco", "accent": "#16a34a", "kicker": "Interior integrado",
            "title": "Chapeco",
            "text": "Ferrovia, colonizacao e rodovias integraram o oeste catarinense, primeiro pela madeira e depois pela agroindustria de carnes.",
            "chip": "carnes + cooperativas",
        },
    ]
    html = ['<div class="integration-overlay"><div class="integration-frame">']
    for card in cards:
        html.append(f"""
<section class="integration-card {card['cls']}" style="--accent:{card['accent']};--accent-soft:{card['accent']}55;">
    <div class="integration-kicker">{card['kicker']}</div>
    <div class="integration-title">{card['title']}</div>
    <div class="integration-text">{card['text']}</div>
    <div class="integration-chip">{card['chip']}</div>
</section>""")
    html.append("</div></div>")
    return "".join(html)


def render_cena1_legend():
    return """
<div class="presentation-legend">
    <div class="legend-kicker">Como ler a integração</div>
    <div class="legend-row">
        <div class="legend-item"><span class="legend-line" style="background:rgba(185,150,70,0.92);"></span>Ferrovias: escoamento interior-portos</div>
        <div class="legend-item"><span class="legend-line" style="background:rgba(70,165,70,0.90);"></span>Rodovias: eixos estruturantes</div>
        <div class="legend-item"><span class="legend-line" style="background:rgba(14,116,144,0.86);"></span>Rios: vales produtivos</div>
        <div class="legend-item"><span class="legend-dot" style="background:rgba(14,116,144,0.95);"></span>Polos e portos</div>
    </div>
</div>"""


def render_cena2_panel(metrica):
    cfg = get_metrica_cena2_config(metrica)
    ano_label = f" · {cfg['ano']}" if 'ano' in cfg else ""
    if cfg.get('base') == 'gini':
        grad = "linear-gradient(to right, #2563eb 0%, #3b82f6 28%, #818cf8 50%, #7c7792 74%, #5f5a70 100%)"
    elif cfg['paleta'] == 'azul':
        grad = "linear-gradient(to right, #bae6fd, #0369a1)"
    elif cfg['paleta'] == 'verde':
        grad = "linear-gradient(to right, #d1fae5, #047857)"
    elif cfg['paleta'] == 'ambar':
        grad = "linear-gradient(to right, #fef3c7, #b45309)"
    else:
        grad = "linear-gradient(to right, #ede9fe, #5b21b6)"

    return f"""
<div style="background:linear-gradient(145deg,rgba(255,255,255,0.72),rgba(255,255,255,0.36));
    backdrop-filter:blur(24px) saturate(165%);-webkit-backdrop-filter:blur(24px) saturate(165%);
    border-radius:18px;padding:14px;margin-bottom:12px;box-shadow:0 18px 48px rgba(15,23,42,0.18);
    border:1px solid rgba(255,255,255,0.74);">
    <div style="font-size:0.62rem;letter-spacing:.12em;color:#64748b;font-weight:600;
        text-transform:uppercase;margin-bottom:10px;">Escala Cromática{ano_label}</div>
    <div style="height:8px;border-radius:99px;background:{grad};margin-bottom:6px;"></div>
    <div style="display:flex;justify-content:space-between;">
        <span style="font-size:0.68rem;color:#64748b;">{cfg['legenda'][0]}</span>
        <span style="font-size:0.68rem;color:#64748b;">{cfg['legenda'][1]}</span>
    </div>
</div>
<div style="background:linear-gradient(145deg,rgba(109,40,217,0.12),rgba(255,255,255,0.26));
    backdrop-filter:blur(20px) saturate(160%);-webkit-backdrop-filter:blur(20px) saturate(160%);
    border:1px solid rgba(109,40,217,0.22);
    border-radius:18px;padding:14px;">
    <div style="font-size:0.62rem;letter-spacing:.13em;color:#4c1d95;font-weight:600;
        text-transform:uppercase;margin-bottom:8px;">🔬 Análise</div>
    <p style="font-size:0.78rem;color:#334155;line-height:1.58;margin:0;">
        Passe o mouse sobre os municípios para ver <strong>cidade, estado e valor individual</strong>.
        Os rótulos suaves indicam PR, SC e RS sem poluir a leitura das cores.
        <br><br>
        A <strong>hiperconcentração</strong> em capitais e litoral coexiste
        com índices de pobreza que rivalizam com áreas deprimidas do país
        no interior e na Metade Sul gaúcha.
    </p>
</div>"""


def render_cena2_legend(metrica):
    cfg = get_metrica_cena2_config(metrica)
    ano_label = f" · {cfg['ano']}" if 'ano' in cfg else ""
    if cfg.get('base') == 'gini':
        grad = "linear-gradient(to right, #2563eb 0%, #3b82f6 28%, #818cf8 50%, #7c7792 74%, #5f5a70 100%)"
    elif cfg['paleta'] == 'azul':
        grad = "linear-gradient(to right, #bae6fd, #0369a1)"
    elif cfg['paleta'] == 'verde':
        grad = "linear-gradient(to right, #d1fae5, #047857)"
    elif cfg['paleta'] == 'ambar':
        grad = "linear-gradient(to right, #fef3c7, #b45309)"
    else:
        grad = "linear-gradient(to right, #ede9fe, #5b21b6)"
    recorte = st.session_state.get("recorte_cena2", "Sul inteiro")
    return f"""
<div class="presentation-legend">
    <div class="legend-kicker">{metrica}{ano_label} · {recorte}</div>
    <div class="legend-gradient" style="background:{grad};"></div>
    <div class="legend-scale-labels">
        <span>{cfg['legenda'][0]}</span>
        <span>{cfg['legenda'][1]}</span>
    </div>
</div>"""


def render_cena3_panel():
    return """
<div style="background:linear-gradient(145deg,rgba(255,255,255,0.72),rgba(255,255,255,0.36));
    backdrop-filter:blur(24px) saturate(165%);-webkit-backdrop-filter:blur(24px) saturate(165%);
    border-radius:18px;padding:14px;margin-bottom:12px;box-shadow:0 18px 48px rgba(15,23,42,0.18);
    border:1px solid rgba(255,255,255,0.74);">
    <div style="font-size:0.62rem;letter-spacing:.12em;color:#64748b;font-weight:600;
        text-transform:uppercase;margin-bottom:12px;">🧭 Fluxos de Exportação</div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <div style="width:26px;height:5px;border-radius:3px;background:rgba(34,197,94,0.85);flex-shrink:0;"></div>
        <span style="font-size:0.76rem;color:#334155;">Commodities agrícolas</span>
    </div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <div style="width:26px;height:5px;border-radius:3px;background:rgba(59,130,246,0.85);flex-shrink:0;"></div>
        <span style="font-size:0.76rem;color:#334155;">Integração industrial / Mercosul</span>
    </div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <div style="width:26px;height:5px;border-radius:3px;background:rgba(168,85,247,0.85);flex-shrink:0;"></div>
        <span style="font-size:0.76rem;color:#334155;">Serviços digitais / Tecnologia</span>
    </div>
    <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:13px;height:13px;border-radius:50%;background:rgba(14,116,144,0.85);flex-shrink:0;"></div>
        <span style="font-size:0.76rem;color:#334155;">Portos exportadores</span>
    </div>
</div>
<div style="background:linear-gradient(145deg,rgba(14,116,144,0.13),rgba(255,255,255,0.26));
    backdrop-filter:blur(20px) saturate(160%);-webkit-backdrop-filter:blur(20px) saturate(160%);
    border:1px solid rgba(14,116,144,0.25);
    border-radius:18px;padding:14px;">
    <div style="font-size:0.62rem;letter-spacing:.13em;color:#0c4a6e;font-weight:600;
        text-transform:uppercase;margin-bottom:8px;">🧠 A Tese Central</div>
    <p style="font-size:0.78rem;color:#334155;line-height:1.60;margin:0;">
        O Sul <strong>executa</strong> em escala global — planta, colhe, abate e embarca.
        Mas as decisões de preço, logística e financiamento são tomadas em
        Chicago, Amsterdã e Xangai.
        <br><br>
        O território é <strong>músculo</strong> de cadeias cujos
        <strong>cérebros estão fora</strong>.
    </p>
</div>"""


def render_cena3_legend():
    return """
<div class="presentation-legend dark">
    <div class="legend-kicker">Rotas comerciais e dependência externa</div>
    <div class="legend-row">
        <div class="legend-item"><span class="legend-line" style="background:rgba(34,197,94,0.92);"></span>Commodities agrícolas e carnes</div>
        <div class="legend-item"><span class="legend-line" style="background:rgba(59,130,246,0.92);"></span>Indústria e Mercosul</div>
        <div class="legend-item"><span class="legend-line" style="background:rgba(168,85,247,0.92);"></span>Serviços digitais</div>
        <div class="legend-item"><span class="legend-dot" style="background:rgba(14,116,144,0.95);"></span>Portos exportadores</div>
    </div>
</div>"""


def render_right_panel(cena, foco, metrica):
    if cena == 0:
        return ""
    elif cena == 1:
        return ""
    elif cena == 2:
        return ""
    elif cena == 3:
        return ""
    return ""


# ════════════════════════════════════════════════════════
# 7. NAV SIDEBAR — menu lateral esquerdo (hover)
# ════════════════════════════════════════════════════════
cena = st.session_state.cena_atual

nav_panel = st.container()
with nav_panel:
    st.markdown('<span id="nav-anchor"></span>', unsafe_allow_html=True)

    # Cabeçalho do menu
    st.markdown("""
    <div style="font-size:0.58rem;text-transform:uppercase;letter-spacing:.18em;
        color:rgba(14,116,144,0.85);font-weight:700;margin-bottom:14px;padding-left:4px;">
        Sul do Brasil
    </div>
    """, unsafe_allow_html=True)

    # Botões de cena
    for i, cfg in enumerate(CENAS_CONFIG):
        is_active = (st.session_state.cena_atual == i)
        label = f"{i+1:02d}  {cfg['titulo'].upper() if is_active else cfg['titulo']}"
        if st.button(label, key=f"nav_{i}", use_container_width=True):
            st.session_state.cena_atual = i
            st.rerun()

    # Sub-menu: recorte territorial (cena 2)
    if cena == 2:
        st.markdown("""
        <hr style="border:none;border-top:1px solid rgba(255,255,255,0.10);margin:12px 0 8px;">
        <div style="font-size:0.58rem;text-transform:uppercase;letter-spacing:.15em;
            color:rgba(109,40,217,0.75);font-weight:600;margin-bottom:8px;padding-left:4px;">
            Recorte
        </div>
        """, unsafe_allow_html=True)
        recortes = list(RECORTES_CENA2.keys())
        recorte_sel = st.radio(
            "recorte",
            recortes,
            index=recortes.index(st.session_state.recorte_cena2),
            label_visibility="collapsed",
            key="radio_recorte_cena2"
        )
        if recorte_sel != st.session_state.recorte_cena2:
            st.session_state.recorte_cena2 = recorte_sel
            st.rerun()

    # Barra de progresso no fundo do nav
    total = len(CENAS_CONFIG)
    pct = int((cena / (total - 1)) * 100)
    st.markdown(f"""
    <div style="margin-top:20px;padding:0 4px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
            <span style="font-size:0.56rem;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:.1em;">Progresso</span>
            <span style="font-size:0.56rem;color:rgba(255,255,255,0.45);">{cena+1}/{total}</span>
        </div>
        <div style="height:3px;background:rgba(255,255,255,0.10);border-radius:99px;">
            <div style="width:{pct}%;height:100%;background:linear-gradient(to right,#0e7490,#0369a1);
                border-radius:99px;transition:width .5s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# 8. PAINEL DIREITO — cards flutuantes
# ════════════════════════════════════════════════════════
right_panel = st.container()
with right_panel:
    st.markdown('<span id="right-anchor"></span>', unsafe_allow_html=True)
    if cena == 2:
        st.markdown("""
        <div class="control-heading">
            <div class="control-heading-kicker">Indicador</div>
            <div class="control-heading-title">Comparação temporal</div>
        </div>
        """, unsafe_allow_html=True)
        metricas = list(METRICAS_CENA2.keys())
        metrica_sel = st.radio(
            "indicador",
            metricas,
            index=metricas.index(st.session_state.metrica_cena2),
            label_visibility="collapsed",
            key="radio_metrica"
        )
        if metrica_sel != st.session_state.metrica_cena2:
            st.session_state.metrica_cena2 = metrica_sel
            st.rerun()

        cfg_ano = METRICAS_CENA2.get(st.session_state.metrica_cena2, {})
        if "anos" in cfg_ano:
            st.markdown("""
            <div class="control-heading" style="margin-top:10px;">
                <div class="control-heading-kicker">Ano</div>
                <div class="control-heading-title">Base de leitura</div>
            </div>
            """, unsafe_allow_html=True)
            ano_state = cfg_ano["ano_state"]
            anos = cfg_ano["anos"]
            if st.session_state.get(ano_state) not in anos:
                st.session_state[ano_state] = anos[-1]
            ano_sel = st.radio(
                "ano",
                anos,
                index=anos.index(st.session_state[ano_state]),
                format_func=lambda x: str(x),
                label_visibility="collapsed",
                horizontal=True,
                key=f"radio_ano_{cfg_ano['base']}"
            )
            if ano_sel != st.session_state[ano_state]:
                st.session_state[ano_state] = ano_sel
                st.rerun()
    else:
        st.markdown(
            render_right_panel(cena, st.session_state.foco_historia, st.session_state.metrica_cena2),
            unsafe_allow_html=True
        )

if cena == 0:
    st.markdown(render_cena0_overlay(), unsafe_allow_html=True)
elif cena == 1:
    st.markdown(render_cena1_overlay(), unsafe_allow_html=True)
    st.markdown(render_cena1_legend(), unsafe_allow_html=True)
elif cena == 2:
    st.markdown(render_cena2_legend(st.session_state.metrica_cena2), unsafe_allow_html=True)
elif cena == 3:
    st.markdown(render_cena3_legend(), unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# 9. RENDERIZAÇÃO DO MAPA
# ════════════════════════════════════════════════════════
metrica_ativa = st.session_state.metrica_cena2 if cena == 2 else None
layers  = get_layers(cena, metrica_ativa)
tooltip = get_tooltip(cena, metrica_ativa)
view    = VIEW_STATES_CENA2.get(st.session_state.get("recorte_cena2", "Sul inteiro"), VIEW_STATES[2]) if cena == 2 else VIEW_STATES[cena]
estilo  = CENAS_CONFIG[cena]['mapa']
controller_enabled = False

st.pydeck_chart(pdk.Deck(
    layers=layers,
    initial_view_state=view,
    map_style=estilo,
    tooltip=tooltip,
    views=[{"controller": controller_enabled}],
))

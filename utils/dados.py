import pandas as pd
import streamlit as st


def aplicar_estilo_global():
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #1a3a5c !important;
        }
        [data-testid="stSidebar"] * {
            color: #e8f0f7 !important;
        }
        [data-testid="stSidebarNav"]::before {
            content: "📊 RegDoc";
            display: block;
            font-size: 1.05rem;
            font-weight: 600;
            color: white !important;
            padding: 1.2rem 1rem 0.8rem 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.15);
            margin-bottom: 0.5rem;
        }
        [data-testid="stSidebarNav"] a {
            color: #b8cfe8 !important;
            font-size: 0.95rem !important;
            padding: 0.45rem 1rem !important;
            border-radius: 6px !important;
            margin: 2px 0.5rem !important;
            display: block !important;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background-color: rgba(255,255,255,0.15) !important;
            color: white !important;
            font-weight: 500 !important;
        }
        [data-testid="stSidebarNav"] a:hover {
            background-color: rgba(255,255,255,0.1) !important;
            color: white !important;
        }
        [data-testid="stSidebarCollapseButton"] svg {
            color: white !important;
            fill: white !important;
        }
        section[data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,0.15) !important;
        }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data
def carregar_municipal():
    df = pd.read_parquet("municipal_consolidado.parquet")
    df["CO_MUNICIPIO"] = df["CO_MUNICIPIO"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["ANO"] = df["ANO"].astype(int)
    df["NO_MUNICIPIO"] = df["NO_MUNICIPIO"].fillna("Não identificado")
    df["SG_UF"] = df["SG_UF"].fillna("??")
    return df


@st.cache_data
def carregar_escola():
    df = pd.read_parquet("escola_consolidado.parquet")
    df["CO_MUNICIPIO"] = df["CO_MUNICIPIO"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["CO_ENTIDADE"] = df["CO_ENTIDADE"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["ANO"] = df["ANO"].astype(int)
    df["NO_MUNICIPIO"] = df["NO_MUNICIPIO"].fillna("Não identificado")
    df["SG_UF"] = df["SG_UF"].fillna("??")
    df["NO_ENTIDADE"] = df["NO_ENTIDADE"].fillna("Escola não identificada")
    return df
@st.cache_data
def carregar_saeb():
    df = pd.read_parquet("saeb_escola_consolidado.parquet")
    df["CO_ENTIDADE"] = df["CO_ENTIDADE"].astype(str).str.replace(r"\.0$", "", regex=True)
    return df

def classificar_risco(ird, media_nacional):
    if pd.isna(ird) or pd.isna(media_nacional):
        return "Sem dados", "#aaa"
    if ird < media_nacional * 0.85:
        return "Alerta", "#c0392b"
    elif ird < media_nacional:
        return "Atenção", "#e67e22"
    elif ird < media_nacional * 1.1:
        return "Moderado", "#f1c40f"
    else:
        return "Favorável", "#27ae60"


def formatar_br(valor, casas=3):
    if pd.isna(valor):
        return "—"
    return f"{float(valor):.{casas}f}".replace(".", ",")

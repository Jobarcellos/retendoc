import pandas as pd
import streamlit as st


@st.cache_data
def carregar_dados():
    df = pd.read_parquet("municipal_consolidado.parquet")
    df["CO_MUNICIPIO"] = df["CO_MUNICIPIO"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["ANO"] = df["ANO"].astype(int)
    df["NO_MUNICIPIO"] = df["NO_MUNICIPIO"].fillna("Não identificado")
    df["SG_UF"] = df["SG_UF"].fillna("??")
    return df


def classificar_risco_atu(atu, media_nacional):
    """
    Classificação baseada no achado principal do modelo de EF:
    ATU é o único preditor robusto (β = -0,0085; p<0,001).
    Quanto maior ATU em relação à média, maior o risco.
    """
    if pd.isna(atu) or pd.isna(media_nacional):
        return "Sem dados", "#aaa"
    desvio = atu - media_nacional
    if desvio >= 5:
        return "Risco elevado", "#c0392b"
    elif desvio >= 2:
        return "Atenção", "#e67e22"
    elif desvio >= 0:
        return "Moderado", "#f1c40f"
    else:
        return "Favorável", "#27ae60"


def formatar_br(valor, casas=3):
    if pd.isna(valor):
        return "—"
    return f"{float(valor):.{casas}f}".replace(".", ",")


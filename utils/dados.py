import pandas as pd
import streamlit as st


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


def classificar_risco(atu, media_nacional):
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

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.dados import carregar_dados, formatar_br

st.set_page_config(page_title="Painel da Rede · RegDoc", layout="wide")

st.title("🗺️ Painel da Rede Nacional")
st.caption("Visão agregada do IRD por UF e ano · Escolas públicas de educação básica")

df = carregar_dados()

# ── Filtros ──────────────────────────────────────────────────────────────────
col_f1, col_f2 = st.columns([2, 1])

with col_f1:
    ufs = sorted(df["SG_UF"].dropna().unique())
    ufs_sel = st.multiselect(
        "Filtrar por UF (deixe vazio para Brasil inteiro)",
        options=ufs,
        default=[]
    )

with col_f2:
    anos_disp = sorted(df["ANO"].unique())
    ano_sel = st.selectbox("Ano de referência", anos_disp, index=len(anos_disp) - 2)

df_filtrado = df[df["ANO"] == ano_sel].copy()
if ufs_sel:
    df_filtrado = df_filtrado[df_filtrado["SG_UF"].isin(ufs_sel)]

# ── Métricas nacionais ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"### Indicadores nacionais — {ano_sel}")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("IRD médio",        formatar_br(df_filtrado["IRD"].mean()))
m2.metric("ATU média",        formatar_br(df_filtrado["ATU"].mean(), 1))
m3.metric("AFD média (%)",    formatar_br(df_filtrado["AFD"].mean(), 1))
m4.metric("IED médio (%)",    formatar_br(df_filtrado["IED"].mean(), 1))
m5.metric("Municípios",       f"{df_filtrado['CO_MUNICIPIO'].nunique():,}".replace(",", "."))

# ── IRD por UF ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### IRD médio por UF")

ird_uf = (
    df_filtrado.groupby("SG_UF")["IRD"]
    .mean()
    .reset_index()
    .sort_values("IRD", ascending=True)
)

fig_uf = px.bar(
    ird_uf,
    x="IRD",
    y="SG_UF",
    orientation="h",
    color="IRD",
    color_continuous_scale=["#c0392b", "#e67e22", "#f1c40f", "#27ae60"],
    labels={"IRD": "IRD médio", "SG_UF": "UF"},
    height=600
)
fig_uf.update_layout(coloraxis_showscale=False, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig_uf, use_container_width=True)

# ── Evolução temporal nacional ────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Evolução do IRD nacional (2013–2025)")

df_evolucao = df.copy()
if ufs_sel:
    df_evolucao = df_evolucao[df_evolucao["SG_UF"].isin(ufs_sel)]

ird_ano = df_evolucao.groupby("ANO")["IRD"].mean().reset_index()

fig_evo = px.line(
    ird_ano,
    x="ANO",
    y="IRD",
    markers=True,
    labels={"ANO": "Ano", "IRD": "IRD médio"},
    color_discrete_sequence=["#1a3a5c"]
)
fig_evo.update_layout(margin=dict(l=20, r=20, t=20, b=20))
fig_evo.update_traces(line_width=2.5, marker_size=7)
st.plotly_chart(fig_evo, use_container_width=True)

# ── Dispersão ATU × IRD ───────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### ATU × IRD — dispersão por município")
st.caption("ATU é o preditor mais robusto do modelo estimado (β = −0,0085; p < 0,001)")

df_disp = df_filtrado.dropna(subset=["ATU", "IRD"]).copy()

if len(df_disp) > 0:
    fig_scatter = px.scatter(
        df_disp,
        x="ATU",
        y="IRD",
        color="SG_UF",
        hover_name="NO_MUNICIPIO",
        hover_data={"SG_UF": True, "ATU": ":.1f", "IRD": ":.3f"},
        labels={"ATU": "Média de alunos por turma", "IRD": "IRD médio"},
        opacity=0.5,
        height=450
    )
    fig_scatter.update_traces(marker_size=4)
    fig_scatter.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.info("ATU não disponível para o ano e filtro selecionados.")


import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.dados import carregar_municipal, formatar_br, aplicar_estilo_global

st.set_page_config(page_title="Painel da Rede · RegDoc", layout="wide")

aplicar_estilo_global()
st.title("🗺️ Painel da Rede Nacional")
st.caption("Visão geral da regularidade dos professores por estado e município · 2013–2025")

df = carregar_municipal()

col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    ufs = sorted(df["SG_UF"].dropna().unique())
    ufs_sel = st.multiselect("Filtrar por estado (deixe vazio para Brasil inteiro)", options=ufs, default=[])
with col_f2:
    anos_disp = sorted(df["ANO"].unique())
    ano_sel = st.selectbox("Ano de referência", anos_disp, index=len(anos_disp) - 2)

df_filtrado = df[df["ANO"] == ano_sel].copy()
if ufs_sel:
    df_filtrado = df_filtrado[df_filtrado["SG_UF"].isin(ufs_sel)]

st.markdown("---")
st.markdown(f"### Situação nacional — {ano_sel}")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Regularidade média", formatar_br(df_filtrado["IRD"].mean()))
m2.metric("Alunos por turma", formatar_br(df_filtrado["ATU"].mean(), 1))
m3.metric("Formação adequada (%)", formatar_br(df_filtrado["AFD"].mean(), 1))
m4.metric("Sobrecarga (%)", formatar_br(df_filtrado["IED"].mean(), 1))
m5.metric("Municípios", f"{df_filtrado['CO_MUNICIPIO'].nunique():,}".replace(",", "."))

st.markdown("---")
st.markdown("### Regularidade dos professores por estado")

ird_uf = (
    df_filtrado.groupby("SG_UF")["IRD"]
    .mean().reset_index().sort_values("IRD", ascending=True)
)
fig_uf = px.bar(
    ird_uf, x="IRD", y="SG_UF", orientation="h",
    color="IRD",
    color_continuous_scale=["#c0392b", "#e67e22", "#f1c40f", "#27ae60"],
    labels={"IRD": "Regularidade média (0 a 5)", "SG_UF": "Estado"},
    height=600
)
fig_uf.update_layout(coloraxis_showscale=False, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig_uf, use_container_width=True)

st.markdown("---")
st.markdown("### Evolução da regularidade ao longo do tempo")

df_evo = df.copy()
if ufs_sel:
    df_evo = df_evo[df_evo["SG_UF"].isin(ufs_sel)]

ird_ano = df_evo.groupby("ANO")["IRD"].mean().reset_index()
fig_evo = px.line(
    ird_ano, x="ANO", y="IRD", markers=True,
    labels={"ANO": "Ano", "IRD": "Regularidade média (0 a 5)"},
    color_discrete_sequence=["#1a3a5c"]
)
fig_evo.update_layout(margin=dict(l=20, r=20, t=20, b=20))
fig_evo.update_traces(line_width=2.5, marker_size=7)
st.plotly_chart(fig_evo, use_container_width=True)

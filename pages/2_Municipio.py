import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.dados import carregar_municipal, formatar_br

st.set_page_config(page_title="Município · RegDoc", layout="wide")

st.title("🔍 Análise por Município")
st.caption("Evolução da regularidade dos professores e comparação com médias nacionais e estaduais")

df = carregar_municipal()

col1, col2 = st.columns([1, 2])
with col1:
    ufs = sorted(df["SG_UF"].dropna().unique())
    uf_sel = st.selectbox("Estado", ufs, index=ufs.index("ES") if "ES" in ufs else 0)
with col2:
    municipios_uf = (
        df[df["SG_UF"] == uf_sel][["CO_MUNICIPIO", "NO_MUNICIPIO"]]
        .drop_duplicates().sort_values("NO_MUNICIPIO")
    )
    municipio_label = st.selectbox("Município", municipios_uf["NO_MUNICIPIO"].tolist())

co_mun = municipios_uf[municipios_uf["NO_MUNICIPIO"] == municipio_label]["CO_MUNICIPIO"].iloc[0]
df_mun = df[df["CO_MUNICIPIO"] == co_mun].sort_values("ANO").copy()

if df_mun.empty:
    st.warning("Sem dados para este município.")
    st.stop()

ano_ref = st.selectbox("Ano de referência", sorted(df_mun["ANO"].unique()), index=len(df_mun["ANO"].unique()) - 2)

linha_atual = df_mun[df_mun["ANO"] == ano_ref].iloc[0]
media_ird_nac = df[df["ANO"] == ano_ref]["IRD"].mean()
media_ird_uf = df[(df["ANO"] == ano_ref) & (df["SG_UF"] == uf_sel)]["IRD"].mean()
media_atu_nac = df[df["ANO"] == ano_ref]["ATU"].mean()

ird = linha_atual["IRD"]
if pd.notna(ird):
    if ird >= media_ird_nac:
        cor = "#27ae60"; situacao = "Situação favorável"
    elif pd.notna(media_ird_uf) and ird >= media_ird_uf:
        cor = "#f39c12"; situacao = "Atenção"
    else:
        cor = "#c0392b"; situacao = "Alerta"
else:
    cor = "#aaa"; situacao = "Sem dados"

st.markdown("---")
st.markdown(f"### {municipio_label} · {uf_sel} · {ano_ref}")

col_ird, col_comp = st.columns([1, 2])
with col_ird:
    st.markdown(f"""
    <div style="background:{cor}22; border:2px solid {cor}; border-radius:12px;
         padding:1.5rem 2rem; text-align:center;">
        <p style="color:{cor}; margin:0; font-size:1rem;">Regularidade dos professores (0 a 5)</p>
        <p style="color:{cor}; margin:0; font-size:3.5rem; font-weight:bold;">{formatar_br(ird)}</p>
        <p style="color:{cor}; margin:0; font-size:1.2rem; font-weight:bold;">● {situacao}</p>
    </div>
    """, unsafe_allow_html=True)

with col_comp:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Média Brasil", formatar_br(media_ird_nac))
    c2.metric(f"Média {uf_sel}", formatar_br(media_ird_uf))
    c3.metric("Alunos por turma", formatar_br(linha_atual["ATU"], 1))
    c4.metric("Formação adequada (%)", formatar_br(linha_atual["AFD"], 1))

st.markdown("---")
st.markdown("### Evolução da regularidade dos professores")

ird_nac = df.groupby("ANO")["IRD"].mean().reset_index().rename(columns={"IRD": "Média Brasil"})
ird_uf_ano = df[df["SG_UF"] == uf_sel].groupby("ANO")["IRD"].mean().reset_index().rename(columns={"IRD": f"Média {uf_sel}"})
df_evo = df_mun[["ANO", "IRD"]].rename(columns={"IRD": municipio_label})
df_evo = df_evo.merge(ird_nac, on="ANO", how="left").merge(ird_uf_ano, on="ANO", how="left")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df_evo["ANO"], y=df_evo[municipio_label],
    name=municipio_label, line=dict(color=cor, width=3), mode="lines+markers", marker_size=8))
fig.add_trace(go.Scatter(x=df_evo["ANO"], y=df_evo["Média Brasil"],
    name="Média Brasil", line=dict(color="#aaa", dash="dash", width=1.5)))
fig.add_trace(go.Scatter(x=df_evo["ANO"], y=df_evo[f"Média {uf_sel}"],
    name=f"Média {uf_sel}", line=dict(color="#e67e22", dash="dot", width=1.5)))
fig.update_layout(height=380, margin=dict(l=20, r=20, t=20, b=20),
    legend=dict(orientation="h", y=-0.2),
    yaxis=dict(title="Regularidade (0 a 5)", range=[0, 5.2]),
    xaxis_title="Ano")
st.plotly_chart(fig, use_container_width=True)

st.markdown("### Série histórica completa")
df_tab = df_mun[["ANO", "IRD", "ATU", "AFD", "IED", "ICG"]].copy()
df_tab = df_tab.rename(columns={
    "ANO": "Ano", "IRD": "Regularidade (0-5)",
    "ATU": "Alunos/turma", "AFD": "Formação adequada (%)",
    "IED": "Sobrecarga (%)", "ICG": "Complexidade (1-6)"
})
for col in df_tab.columns[1:]:
    df_tab[col] = df_tab[col].apply(lambda x: formatar_br(x, 1))
st.dataframe(df_tab.set_index("Ano"), use_container_width=True)

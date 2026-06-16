import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.dados import carregar_dados, classificar_risco_atu, formatar_br

st.set_page_config(page_title="Município · RegDoc", layout="wide")

st.title("🔍 Análise por Município")
st.caption("Evolução temporal dos indicadores e comparação com médias nacionais e estaduais")

df = carregar_dados()

# ── Seleção do município ──────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    ufs = sorted(df["SG_UF"].dropna().unique())
    uf_sel = st.selectbox("UF", ufs, index=ufs.index("ES") if "ES" in ufs else 0)

with col2:
    municipios_uf = (
        df[df["SG_UF"] == uf_sel][["CO_MUNICIPIO", "NO_MUNICIPIO"]]
        .drop_duplicates()
        .sort_values("NO_MUNICIPIO")
    )
    municipio_label = st.selectbox(
        "Município",
        municipios_uf["NO_MUNICIPIO"].tolist()
    )

co_mun = municipios_uf[municipios_uf["NO_MUNICIPIO"] == municipio_label]["CO_MUNICIPIO"].iloc[0]
df_mun = df[df["CO_MUNICIPIO"] == co_mun].sort_values("ANO").copy()

if df_mun.empty:
    st.warning("Sem dados para este município.")
    st.stop()

# ── Ano de referência ─────────────────────────────────────────────────────────
ano_ref = st.selectbox(
    "Ano de referência para comparação",
    sorted(df_mun["ANO"].unique()),
    index=len(df_mun["ANO"].unique()) - 2
)

linha_atual = df_mun[df_mun["ANO"] == ano_ref].iloc[0]
media_nacional = df[df["ANO"] == ano_ref]["ATU"].mean()
media_uf = df[(df["ANO"] == ano_ref) & (df["SG_UF"] == uf_sel)]["ATU"].mean()
media_ird_nac = df[df["ANO"] == ano_ref]["IRD"].mean()
media_ird_uf = df[(df["ANO"] == ano_ref) & (df["SG_UF"] == uf_sel)]["IRD"].mean()

risco, cor_risco = classificar_risco_atu(linha_atual["ATU"], media_nacional)

# ── Métricas ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"### {municipio_label} · {uf_sel} · {ano_ref}")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(
    "IRD",
    formatar_br(linha_atual["IRD"]),
    delta=f"{linha_atual['IRD'] - media_ird_nac:+.3f} vs Brasil".replace(".", ",")
)
c2.metric(
    "ATU",
    formatar_br(linha_atual["ATU"], 1),
    delta=f"{linha_atual['ATU'] - media_nacional:+.1f} vs Brasil".replace(".", ","),
    delta_color="inverse"
)
c3.metric("AFD (%)", formatar_br(linha_atual["AFD"], 1))
c4.metric("IED (%)", formatar_br(linha_atual["IED"], 1))
c5.metric("ICG",     formatar_br(linha_atual["ICG"], 2))

# ── Classificação de risco ────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:{cor_risco}22; border-left: 5px solid {cor_risco};
     padding: 0.8rem 1.2rem; border-radius: 6px; margin: 1rem 0;">
    <strong style="color:{cor_risco}; font-size:1.1rem;">Classificação ATU: {risco}</strong><br>
    <span style="color:#333; font-size:0.9rem;">
    ATU do município: {formatar_br(linha_atual['ATU'], 1)} alunos/turma ·
    Média nacional: {formatar_br(media_nacional, 1)} ·
    Média {uf_sel}: {formatar_br(media_uf, 1)}<br>
    <em>Baseado no único preditor robusto do modelo estimado (β = −0,0085; p &lt; 0,001)</em>
    </span>
</div>
""", unsafe_allow_html=True)

# ── Evolução IRD ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Evolução do IRD")

ird_nac_ano = df.groupby("ANO")["IRD"].mean().reset_index().rename(columns={"IRD": "Brasil"})
ird_uf_ano = df[df["SG_UF"] == uf_sel].groupby("ANO")["IRD"].mean().reset_index().rename(columns={"IRD": uf_sel})

df_evo = df_mun[["ANO", "IRD"]].rename(columns={"IRD": municipio_label})
df_evo = df_evo.merge(ird_nac_ano, on="ANO", how="left")
df_evo = df_evo.merge(ird_uf_ano, on="ANO", how="left")

fig_ird = go.Figure()
fig_ird.add_trace(go.Scatter(
    x=df_evo["ANO"], y=df_evo[municipio_label],
    name=municipio_label, line=dict(color="#1a3a5c", width=3),
    mode="lines+markers", marker_size=8
))
fig_ird.add_trace(go.Scatter(
    x=df_evo["ANO"], y=df_evo["Brasil"],
    name="Média Brasil", line=dict(color="#aaa", dash="dash", width=1.5)
))
fig_ird.add_trace(go.Scatter(
    x=df_evo["ANO"], y=df_evo[uf_sel],
    name=f"Média {uf_sel}", line=dict(color="#e67e22", dash="dot", width=1.5)
))
fig_ird.update_layout(
    height=380,
    margin=dict(l=20, r=20, t=20, b=20),
    legend=dict(orientation="h", y=-0.15)
)
st.plotly_chart(fig_ird, use_container_width=True)

# ── Evolução ATU ──────────────────────────────────────────────────────────────
st.markdown("### Evolução da ATU (preditor principal)")

atu_nac = df.groupby("ANO")["ATU"].mean().reset_index().rename(columns={"ATU": "Brasil"})
df_atu = df_mun[["ANO", "ATU"]].rename(columns={"ATU": municipio_label})
df_atu = df_atu.merge(atu_nac, on="ANO", how="left")

fig_atu = go.Figure()
fig_atu.add_trace(go.Scatter(
    x=df_atu["ANO"], y=df_atu[municipio_label],
    name=municipio_label, line=dict(color="#c0392b", width=3),
    mode="lines+markers", marker_size=8
))
fig_atu.add_trace(go.Scatter(
    x=df_atu["ANO"], y=df_atu["Brasil"],
    name="Média Brasil", line=dict(color="#aaa", dash="dash", width=1.5)
))
fig_atu.update_layout(
    height=320,
    margin=dict(l=20, r=20, t=20, b=20),
    legend=dict(orientation="h", y=-0.15)
)
st.plotly_chart(fig_atu, use_container_width=True)

# ── Tabela histórica ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Série histórica completa")

df_tab = df_mun[["ANO", "IRD", "ATU", "AFD", "IED", "ICG"]].copy()
for col in ["IRD", "ATU", "AFD", "IED", "ICG"]:
    df_tab[col] = df_tab[col].apply(lambda x: formatar_br(x, 3 if col == "IRD" else 1))
df_tab = df_tab.rename(columns={
    "ANO": "Ano", "IRD": "IRD", "ATU": "ATU",
    "AFD": "AFD (%)", "IED": "IED (%)", "ICG": "ICG"
})
st.dataframe(df_tab.set_index("Ano"), use_container_width=True)


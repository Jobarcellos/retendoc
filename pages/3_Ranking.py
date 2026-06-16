import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.dados import carregar_dados, classificar_risco_atu, formatar_br

st.set_page_config(page_title="Ranking · RegDoc", layout="wide")

st.title("⚠️ Ranking de Atenção")
st.caption("Municípios priorizados pelo risco à regularidade docente · baseado em ATU (β = −0,0085; p < 0,001)")

df = carregar_dados()

# ── Filtros ──────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    anos_disp = sorted(df["ANO"].unique())
    ano_sel = st.selectbox("Ano", anos_disp, index=len(anos_disp) - 2)

with col2:
    ufs = ["Todas"] + sorted(df["SG_UF"].dropna().unique())
    uf_sel = st.selectbox("UF", ufs)

with col3:
    n_top = st.slider("Quantidade de municípios no ranking", 10, 100, 30)

# ── Preparar ranking ──────────────────────────────────────────────────────────
df_ano = df[df["ANO"] == ano_sel].copy()
if uf_sel != "Todas":
    df_ano = df_ano[df_ano["SG_UF"] == uf_sel]

media_nacional_atu = df[df["ANO"] == ano_sel]["ATU"].mean()
media_nacional_ird = df[df["ANO"] == ano_sel]["IRD"].mean()

df_rank = df_ano.dropna(subset=["ATU", "IRD"]).copy()
df_rank["RISCO"] = df_rank["ATU"].apply(
    lambda x: classificar_risco_atu(x, media_nacional_atu)[0]
)
df_rank["COR"] = df_rank["ATU"].apply(
    lambda x: classificar_risco_atu(x, media_nacional_atu)[1]
)

# Ordenar: maior ATU primeiro (maior risco)
df_rank = df_rank.sort_values("ATU", ascending=False)

# ── Resumo por faixa ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"### Distribuição de risco — {ano_sel}" + (f" · {uf_sel}" if uf_sel != "Todas" else " · Brasil"))

ordem = ["Risco elevado", "Atenção", "Moderado", "Favorável"]
cores = {"Risco elevado": "#c0392b", "Atenção": "#e67e22", "Moderado": "#f1c40f", "Favorável": "#27ae60"}

contagem = df_rank["RISCO"].value_counts().reindex(ordem, fill_value=0)
cols = st.columns(4)
for i, (faixa, qtd) in enumerate(contagem.items()):
    pct = qtd / len(df_rank) * 100 if len(df_rank) > 0 else 0
    cols[i].markdown(f"""
    <div style="background:{cores[faixa]}22; border-left:5px solid {cores[faixa]};
         padding:0.8rem 1rem; border-radius:6px; text-align:center;">
        <div style="font-size:1.8rem; font-weight:bold; color:{cores[faixa]};">{qtd}</div>
        <div style="font-size:0.85rem; color:#333;">{faixa}</div>
        <div style="font-size:0.8rem; color:#777;">{pct:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

# ── Gráfico dispersão IRD × ATU com cor por risco ─────────────────────────────
st.markdown("---")
st.markdown("### IRD × ATU por município")

fig = px.scatter(
    df_rank,
    x="ATU",
    y="IRD",
    color="RISCO",
    color_discrete_map=cores,
    hover_name="NO_MUNICIPIO",
    hover_data={"SG_UF": True, "ATU": ":.1f", "IRD": ":.3f", "RISCO": True, "COR": False},
    labels={"ATU": "ATU (alunos/turma)", "IRD": "IRD médio"},
    category_orders={"RISCO": ordem},
    opacity=0.7,
    height=420
)
fig.add_vline(
    x=media_nacional_atu,
    line_dash="dash",
    line_color="#555",
    annotation_text=f"Média ATU Brasil: {media_nacional_atu:.1f}",
    annotation_position="top right"
)
fig.add_hline(
    x=media_nacional_ird,
    line_dash="dot",
    line_color="#999",
    annotation_text=f"Média IRD Brasil: {media_nacional_ird:.3f}",
    annotation_position="bottom right"
)
fig.update_traces(marker_size=5)
fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)

# ── Tabela ranking ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"### Top {n_top} municípios — maior ATU (maior risco)")

df_tabela = df_rank.head(n_top)[
    ["NO_MUNICIPIO", "SG_UF", "IRD", "ATU", "AFD", "IED", "ICG", "RISCO"]
].copy()

df_tabela["IRD"] = df_tabela["IRD"].apply(lambda x: formatar_br(x, 3))
df_tabela["ATU"] = df_tabela["ATU"].apply(lambda x: formatar_br(x, 1))
df_tabela["AFD"] = df_tabela["AFD"].apply(lambda x: formatar_br(x, 1))
df_tabela["IED"] = df_tabela["IED"].apply(lambda x: formatar_br(x, 1))
df_tabela["ICG"] = df_tabela["ICG"].apply(lambda x: formatar_br(x, 2))

df_tabela = df_tabela.rename(columns={
    "NO_MUNICIPIO": "Município",
    "SG_UF": "UF",
    "AFD": "AFD (%)",
    "IED": "IED (%)",
    "RISCO": "Classificação"
})

st.dataframe(df_tabela, use_container_width=True, hide_index=True)

# ── Download ──────────────────────────────────────────────────────────────────
csv = df_tabela.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="📥 Baixar ranking completo (CSV)",
    data=csv,
    file_name=f"ranking_regdoc_{ano_sel}_{uf_sel}.csv",
    mime="text/csv"
)

st.markdown("---")
st.caption("""
**Nota metodológica:** A classificação de risco é baseada exclusivamente na ATU (média de alunos por turma),
único preditor robusto e teoricamente consistente identificado no modelo de Efeitos Fixos
(β = −0,0085; p < 0,001; painel 2013–2024, N = 66.840). Os demais indicadores (ICG, IED, AFD)
apresentaram sinais contraintuitivos ou instabilidade estatística nas especificações de robustez.
""")


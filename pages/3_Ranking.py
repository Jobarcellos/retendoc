import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.dados import carregar_municipal, classificar_risco, formatar_br

st.set_page_config(page_title="Ranking · RegDoc", layout="wide")

st.title("⚠️ Quais municípios precisam de atenção agora?")
st.caption("Municípios ordenados pelo risco à regularidade dos professores")

df = carregar_municipal()

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    anos_disp = sorted(df["ANO"].unique())
    ano_sel = st.selectbox("Ano", anos_disp, index=len(anos_disp) - 2)
with col2:
    ufs = ["Todos os estados"] + sorted(df["SG_UF"].dropna().unique())
    uf_sel = st.selectbox("Estado", ufs)
with col3:
    n_top = st.slider("Municípios no ranking", 10, 100, 30)

df_ano = df[df["ANO"] == ano_sel].copy()
if uf_sel != "Todos os estados":
    df_ano = df_ano[df_ano["SG_UF"] == uf_sel]

media_atu = df[df["ANO"] == ano_sel]["ATU"].mean()
media_ird = df[df["ANO"] == ano_sel]["IRD"].mean()

df_rank = df_ano.dropna(subset=["ATU", "IRD"]).copy()
df_rank["RISCO"] = df_rank["ATU"].apply(lambda x: classificar_risco(x, media_atu)[0])
df_rank["COR"] = df_rank["ATU"].apply(lambda x: classificar_risco(x, media_atu)[1])
df_rank = df_rank.sort_values("ATU", ascending=False)

st.markdown("---")
titulo = f"Situação em {ano_sel}"
titulo += f" · {uf_sel}" if uf_sel != "Todos os estados" else " · Brasil"
st.markdown(f"### {titulo}")

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

st.markdown("---")
st.markdown(f"### Top {n_top} municípios — maior risco")

df_tabela = df_rank.head(n_top)[["NO_MUNICIPIO","SG_UF","IRD","ATU","AFD","IED","ICG","RISCO"]].copy()
df_tabela["IRD"] = df_tabela["IRD"].apply(lambda x: formatar_br(x, 3))
df_tabela["ATU"] = df_tabela["ATU"].apply(lambda x: formatar_br(x, 1))
df_tabela["AFD"] = df_tabela["AFD"].apply(lambda x: formatar_br(x, 1))
df_tabela["IED"] = df_tabela["IED"].apply(lambda x: formatar_br(x, 1))
df_tabela["ICG"] = df_tabela["ICG"].apply(lambda x: formatar_br(x, 2))
df_tabela = df_tabela.rename(columns={
    "NO_MUNICIPIO": "Município", "SG_UF": "Estado",
    "IRD": "Regularidade", "ATU": "Alunos/turma",
    "AFD": "Formação (%)", "IED": "Sobrecarga (%)",
    "ICG": "Complexidade", "RISCO": "Situação"
})
st.dataframe(df_tabela, use_container_width=True, hide_index=True)

csv = df_tabela.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="📥 Baixar lista completa (CSV)",
    data=csv,
    file_name=f"ranking_regdoc_{ano_sel}_{uf_sel}.csv",
    mime="text/csv"
)

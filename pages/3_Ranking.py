import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.dados import carregar_municipal, formatar_br

st.set_page_config(page_title="Ranking · RegDoc", layout="wide")

st.title("⚠️ Quais municípios precisam de atenção agora?")
st.caption("Municípios ordenados pela menor regularidade dos professores")

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

media_ird = df[df["ANO"] == ano_sel]["IRD"].mean()
media_ird_uf = df[(df["ANO"] == ano_sel) & (df["SG_UF"] == uf_sel)]["IRD"].mean() if uf_sel != "Todos os estados" else media_ird

df_rank = df_ano.dropna(subset=["IRD"]).copy()

def classificar(ird):
    if pd.isna(ird):
        return "Sem dados", "#aaa"
    if ird < media_ird * 0.85:
        return "Alerta", "#c0392b"
    elif ird < media_ird:
        return "Atenção", "#e67e22"
    elif ird < media_ird * 1.1:
        return "Moderado", "#f1c40f"
    else:
        return "Favorável", "#27ae60"

df_rank["RISCO"] = df_rank["IRD"].apply(lambda x: classificar(x)[0])
df_rank["COR"]   = df_rank["IRD"].apply(lambda x: classificar(x)[1])
df_rank = df_rank.sort_values("IRD", ascending=True)

st.markdown("---")
titulo = f"Situação em {ano_sel}"
titulo += f" · {uf_sel}" if uf_sel != "Todos os estados" else " · Brasil"
st.markdown(f"### {titulo}")

ordem = ["Alerta", "Atenção", "Moderado", "Favorável"]
cores = {"Alerta": "#c0392b", "Atenção": "#e67e22", "Moderado": "#f1c40f", "Favorável": "#27ae60"}
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
st.markdown(f"### Top {n_top} municípios — menor regularidade dos professores")
st.caption(f"Média nacional de regularidade em {ano_sel}: {formatar_br(media_ird)} — municípios abaixo dessa média precisam de atenção")

df_tabela = df_rank.head(n_top)[["NO_MUNICIPIO","SG_UF","IRD","ATU","AFD","IED","ICG","RISCO"]].copy()
df_tabela["IRD"] = df_tabela["IRD"].apply(lambda x: formatar_br(x, 3))
df_tabela["ATU"] = df_tabela["ATU"].apply(lambda x: formatar_br(x, 1))
df_tabela["AFD"] = df_tabela["AFD"].apply(lambda x: formatar_br(x, 1))
df_tabela["IED"] = df_tabela["IED"].apply(lambda x: formatar_br(x, 1))
df_tabela["ICG"] = df_tabela["ICG"].apply(lambda x: formatar_br(x, 2))
df_tabela = df_tabela.rename(columns={
    "NO_MUNICIPIO": "Município",
    "SG_UF": "Estado",
    "IRD": "Regularidade",
    "ATU": "Alunos/turma",
    "AFD": "Formação (%)",
    "IED": "Esforço docente (%)",
    "ICG": "Complexidade",
    "RISCO": "Situação"
})
st.dataframe(df_tabela, use_container_width=True, hide_index=True)

csv = df_tabela.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="📥 Baixar lista completa (CSV)",
    data=csv,
    file_name=f"ranking_regdoc_{ano_sel}_{uf_sel}.csv",
    mime="text/csv"
)

st.markdown("---")
st.markdown("### Regularidade dos professores por estado")
st.caption("Comparação visual entre estados — barras mais à esquerda indicam menor regularidade")

ird_uf = (df_ano.groupby("SG_UF")["IRD"].mean().reset_index().sort_values("IRD", ascending=True))
fig = px.bar(
    ird_uf, x="IRD", y="SG_UF", orientation="h",
    color="IRD",
    color_continuous_scale=["#c0392b", "#e67e22", "#f1c40f", "#27ae60"],
    labels={"IRD": "Regularidade média (0 a 5)", "SG_UF": "Estado"},
    height=600
)
fig.add_vline(x=media_ird, line_dash="dash", line_color="#333",
    annotation_text=f"Média Brasil: {formatar_br(media_ird)}",
    annotation_position="top right")
fig.update_layout(coloraxis_showscale=False, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)

st.caption("""
Nota: A classificação de situação é baseada na regularidade dos professores (IRD).
Municípios com IRD abaixo de 85% da média nacional são classificados como Alerta;
entre 85% e 100% como Atenção; entre 100% e 110% como Moderado; acima de 110% como Favorável.
""")

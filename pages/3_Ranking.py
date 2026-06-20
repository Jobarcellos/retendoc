import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils.dados import carregar_municipal, formatar_br, aplicar_estilo_global

st.set_page_config(page_title="Ranking · RegDoc", layout="wide")

aplicar_estilo_global()

st.markdown("""
<style>
.tooltip-wrap { position:relative; display:inline-block; cursor:pointer; }
.tooltip-wrap .tip {
    visibility:hidden; opacity:0; width:320px; background:#1a3a5c; color:white;
    font-size:12px; line-height:1.6; border-radius:8px; padding:12px 16px;
    position:absolute; z-index:999; bottom:130%; left:50%; transform:translateX(-50%);
    transition:opacity 0.2s; pointer-events:none;
}
.tooltip-wrap:hover .tip { visibility:visible; opacity:1; }
.info-icon { display:inline-flex; align-items:center; justify-content:center;
    width:16px; height:16px; border-radius:50%; background:#1a3a5c;
    color:white; font-size:10px; font-weight:bold; cursor:help; }
</style>
""", unsafe_allow_html=True)

# ── Tooltips ───────────────────────────────────────────────────────────────────
TOOLTIP_IRD = (
    "O IRD — Indicador de Regularidade do Docente — mede se os mesmos professores "
    "continuam nas escolas de um ano para o outro. "
    "O valor do município é a média simples dos IRDs de todas as suas escolas. "
    "Escala de 0 a 5: abaixo de 2 = baixa regularidade; 2 a 3 = média-baixa; "
    "3 a 4 = média-alta; 4 a 5 = alta regularidade. "
    "Fonte: Nota Técnica INEP nº 11/2015."
)

TOOLTIP_CLASSIFICACAO = (
    "A classificação de situação é baseada na comparação do IRD do município "
    "com a média nacional do ano selecionado: "
    "Alerta = IRD abaixo de 85% da média nacional; "
    "Atenção = entre 85% e 100% da média; "
    "Moderado = entre 100% e 110% da média; "
    "Favorável = acima de 110% da média."
)

st.title("⚠️ Quais municípios precisam de atenção agora?")
st.caption("Municípios ordenados pela menor regularidade dos professores")

df = carregar_municipal()

# ── Filtros ────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    anos_disp = sorted(df["ANO"].unique())
    ano_sel = st.selectbox("Ano", anos_disp, index=len(anos_disp) - 1)
with col2:
    ufs = ["Todos os estados"] + sorted(df["SG_UF"].dropna().unique())
    uf_sel = st.selectbox("Estado", ufs)
with col3:
    n_top = st.slider("Municípios no ranking", 10, 100, 30)

df_ano = df[df["ANO"] == ano_sel].copy()
if uf_sel != "Todos os estados":
    df_ano = df_ano[df_ano["SG_UF"] == uf_sel]

media_ird     = df[df["ANO"] == ano_sel]["IRD"].mean()
media_ird_uf  = (df[(df["ANO"] == ano_sel) & (df["SG_UF"] == uf_sel)]["IRD"].mean()
                 if uf_sel != "Todos os estados" else media_ird)

df_rank = df_ano.dropna(subset=["IRD"]).copy()

def classificar(ird):
    if pd.isna(ird):         return "Sem dados", "#aaa"
    if ird < media_ird*0.85: return "Alerta",    "#c0392b"
    elif ird < media_ird:    return "Atenção",   "#e67e22"
    elif ird < media_ird*1.1:return "Moderado",  "#f1c40f"
    else:                    return "Favorável",  "#27ae60"

df_rank["RISCO"] = df_rank["IRD"].apply(lambda x: classificar(x)[0])
df_rank["COR"]   = df_rank["IRD"].apply(lambda x: classificar(x)[1])
df_rank = df_rank.sort_values("IRD", ascending=True)

# ── Painel de situação ─────────────────────────────────────────────────────────
st.markdown("---")
titulo = f"Situação em {ano_sel}"
titulo += f" · {uf_sel}" if uf_sel != "Todos os estados" else " · Brasil"
st.markdown(f"### {titulo}")

ordem = ["Alerta", "Atenção", "Moderado", "Favorável"]
cores = {"Alerta":"#c0392b","Atenção":"#e67e22","Moderado":"#f1c40f","Favorável":"#27ae60"}
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

# ── Contexto da média ──────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
ref_label = f"Média {uf_sel}" if uf_sel != "Todos os estados" else "Média nacional"
ref_valor = media_ird_uf if uf_sel != "Todos os estados" else media_ird

col_m1, col_m2 = st.columns(2)
col_m1.metric(
    label=f"Média nacional — {ano_sel}",
    value=formatar_br(media_ird),
    help="IRD médio de todos os municípios brasileiros no ano selecionado."
)
if uf_sel != "Todos os estados":
    col_m2.metric(
        label=f"Média {uf_sel} — {ano_sel}",
        value=formatar_br(media_ird_uf),
        delta=f"{media_ird_uf - media_ird:+.3f}".replace(".", ",") if pd.notna(media_ird_uf) else None,
        help=f"IRD médio dos municípios de {uf_sel} no ano selecionado."
    )

# ── Ranking ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"### Top {n_top} municípios — menor regularidade dos professores")
st.markdown(
    f"Média nacional de regularidade em {ano_sel}: **{formatar_br(media_ird)}** "
    f"<span class='tooltip-wrap'><span class='info-icon'>i</span>"
    f"<span class='tip'>{TOOLTIP_CLASSIFICACAO}</span></span> — "
    f"municípios abaixo dessa média precisam de atenção.",
    unsafe_allow_html=True
)

df_tabela = df_rank.head(n_top)[["NO_MUNICIPIO","SG_UF","IRD","ATU","AFD","IED","ICG","RISCO"]].copy()
df_tabela["IRD"] = df_tabela["IRD"].apply(lambda x: formatar_br(x, 3))
df_tabela["ATU"] = df_tabela["ATU"].apply(lambda x: formatar_br(x, 1))
df_tabela["AFD"] = df_tabela["AFD"].apply(lambda x: formatar_br(x, 1))
df_tabela["IED"] = df_tabela["IED"].apply(lambda x: formatar_br(x, 1))
df_tabela["ICG"] = df_tabela["ICG"].apply(lambda x: formatar_br(x, 2))
df_tabela = df_tabela.rename(columns={
    "NO_MUNICIPIO":"Município","SG_UF":"Estado",
    "IRD":"Regularidade","ATU":"Alunos/turma",
    "AFD":"Formação (%)","IED":"Esforço docente (%)","ICG":"Complexidade","RISCO":"Situação"
})
st.dataframe(df_tabela, use_container_width=True, hide_index=True)

col_dl1, col_dl2 = st.columns([1, 3])
with col_dl1:
    csv = df_tabela.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Baixar lista completa (CSV)",
        data=csv,
        file_name=f"ranking_regdoc_{ano_sel}_{uf_sel}.csv",
        mime="text/csv"
    )

# ── Gráfico por estado ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Regularidade dos professores por estado")
st.caption("Barras mais à esquerda indicam menor regularidade — estados que merecem atenção prioritária")

ird_uf = (df_ano.groupby("SG_UF")["IRD"].mean()
          .reset_index().sort_values("IRD", ascending=True))

fig = px.bar(
    ird_uf, x="IRD", y="SG_UF", orientation="h",
    color="IRD",
    color_continuous_scale=["#c0392b","#e67e22","#f1c40f","#27ae60"],
    labels={"IRD":"Regularidade média (0 a 5)","SG_UF":"Estado"},
    height=600
)
fig.add_vline(x=media_ird, line_dash="dash", line_color="#333",
    annotation_text=f"Média Brasil: {formatar_br(media_ird)}",
    annotation_position="top right")
fig.update_layout(coloraxis_showscale=False, margin=dict(l=20,r=20,t=20,b=20))
st.plotly_chart(fig, use_container_width=True)

# ── Nota metodológica ──────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("ℹ️ Como interpretar este ranking"):
    st.markdown(f"""
    **O que é o IRD?**
    O Indicador de Regularidade do Docente mede a permanência dos professores
    nas mesmas escolas ao longo de 5 anos consecutivos. Varia de 0 a 5.
    O valor do município é a média simples dos IRDs de todas as suas escolas.

    **Como os municípios são classificados?**
    A classificação é baseada na comparação com a média nacional de {ano_sel}
    ({formatar_br(media_ird)}):

    | Situação | Critério |
    |----------|---------|
    | 🔴 Alerta | IRD abaixo de 85% da média nacional |
    | 🟠 Atenção | IRD entre 85% e 100% da média nacional |
    | 🟡 Moderado | IRD entre 100% e 110% da média nacional |
    | 🟢 Favorável | IRD acima de 110% da média nacional |

    **Limitações importantes**
    - O ranking compara municípios sem controlar pelo nível socioeconômico (INSE)
      ou complexidade das escolas (ICG) — contextos diferentes podem explicar
      parte das diferenças observadas.
    - Municípios muito pequenos têm IRD mais volátil — a saída de poucos
      professores afeta muito o indicador.
    - Use o ranking como ponto de partida para investigação, não como
      diagnóstico definitivo.

    **Fonte:** Censo Escolar da Educação Básica — INEP/MEC.
    Nota Técnica nº 11/2015 e atualizações anuais.
    """)

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.dados import carregar_municipal, formatar_br, aplicar_estilo_global

st.set_page_config(page_title="Painel da Rede · RegDoc", layout="wide")
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
.tendencia-box { border-radius:8px; padding:0.8rem 1.2rem; margin:0.5rem 0 1rem 0;
    font-size:0.9rem; display:flex; align-items:flex-start; gap:0.8rem; }
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

TOOLTIP_ATU = (
    "ATU — Média de Alunos por Turma. "
    "Média de estudantes por turma nos municípios selecionados. "
    "Turmas superlotadas aumentam a sobrecarga docente e estão associadas "
    "a maior rotatividade de professores. "
    "Fonte: Censo Escolar/INEP."
)

TOOLTIP_AFD = (
    "AFD — Adequação da Formação Docente. "
    "Percentual de professores que lecionam na área em que se formaram. "
    "Quanto maior, mais qualificado e alinhado é o quadro docente. "
    "Fonte: Censo Escolar/INEP."
)

TOOLTIP_IED = (
    "IED — Indicador de Esforço Docente. "
    "Mede a complexidade da jornada — escolas, turnos e disciplinas simultâneas. "
    "Valores altos sugerem jornada fragmentada, o que pode reduzir "
    "o vínculo do professor com a escola. "
    "Fonte: Censo Escolar/INEP."
)

def tooltip_html(sigla, tip):
    return (
        f"<span class='tooltip-wrap'>"
        f"<span class='info-icon'>i</span>"
        f"<span class='tip'>{tip}</span>"
        f"</span>"
    )

st.title("🗺️ Painel da Rede Nacional")
st.caption("Visão geral da regularidade dos professores por estado e município · 2013–2025")

df = carregar_municipal()

# ── Filtros ────────────────────────────────────────────────────────────────────
col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    ufs = sorted(df["SG_UF"].dropna().unique())
    ufs_sel = st.multiselect(
        "Filtrar por estado (deixe vazio para Brasil inteiro)",
        options=ufs, default=[]
    )
with col_f2:
    anos_disp = sorted(df["ANO"].unique())
    ano_sel = st.selectbox("Ano de referência", anos_disp, index=len(anos_disp)-1)

df_filtrado = df[df["ANO"] == ano_sel].copy()
if ufs_sel:
    df_filtrado = df_filtrado[df_filtrado["SG_UF"].isin(ufs_sel)]

# ── Métricas nacionais ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"### Situação {'nacional' if not ufs_sel else '— ' + ', '.join(ufs_sel)} — {ano_sel}")

m1, m2, m3, m4, m5 = st.columns(5)

ird_medio = df_filtrado["IRD"].mean()
atu_medio = df_filtrado["ATU"].mean()
afd_medio = df_filtrado["AFD"].mean()
ied_medio = df_filtrado["IED"].mean()
n_mun     = df_filtrado["CO_MUNICIPIO"].nunique()

# Calcular municípios em alerta
media_nac = df[df["ANO"] == ano_sel]["IRD"].mean()
n_alerta  = int((df_filtrado["IRD"] < media_nac * 0.85).sum())

m1.markdown(
    f"<div style='text-align:center;'>"
    f"<p style='font-size:1.8rem;font-weight:bold;color:#1a3a5c;margin:0;'>{formatar_br(ird_medio)}</p>"
    f"<p style='font-size:0.8rem;color:#777;margin:0;'>Regularidade média "
    f"{tooltip_html('IRD', TOOLTIP_IRD)}</p></div>",
    unsafe_allow_html=True
)
m2.markdown(
    f"<div style='text-align:center;'>"
    f"<p style='font-size:1.8rem;font-weight:bold;color:#1a3a5c;margin:0;'>{formatar_br(atu_medio,1)}</p>"
    f"<p style='font-size:0.8rem;color:#777;margin:0;'>Alunos por turma "
    f"{tooltip_html('ATU', TOOLTIP_ATU)}</p></div>",
    unsafe_allow_html=True
)
m3.markdown(
    f"<div style='text-align:center;'>"
    f"<p style='font-size:1.8rem;font-weight:bold;color:#1a3a5c;margin:0;'>{formatar_br(afd_medio,1)}%</p>"
    f"<p style='font-size:0.8rem;color:#777;margin:0;'>Formação adequada "
    f"{tooltip_html('AFD', TOOLTIP_AFD)}</p></div>",
    unsafe_allow_html=True
)
m4.markdown(
    f"<div style='text-align:center;'>"
    f"<p style='font-size:1.8rem;font-weight:bold;color:#1a3a5c;margin:0;'>{formatar_br(ied_medio,1)}%</p>"
    f"<p style='font-size:0.8rem;color:#777;margin:0;'>Esforço docente "
    f"{tooltip_html('IED', TOOLTIP_IED)}</p></div>",
    unsafe_allow_html=True
)
m5.markdown(
    f"<div style='text-align:center;'>"
    f"<p style='font-size:1.8rem;font-weight:bold;color:#c0392b;margin:0;'>{n_alerta}</p>"
    f"<p style='font-size:0.8rem;color:#777;margin:0;'>Municípios em alerta</p></div>",
    unsafe_allow_html=True
)

# ── Gráfico por estado ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Regularidade dos professores por estado")
st.caption("Barras mais à esquerda = menor regularidade = maior atenção necessária")

ird_uf = (
    df_filtrado.groupby("SG_UF")["IRD"]
    .mean().reset_index().sort_values("IRD", ascending=True)
)

fig_uf = px.bar(
    ird_uf, x="IRD", y="SG_UF", orientation="h",
    color="IRD",
    color_continuous_scale=["#c0392b","#e67e22","#f1c40f","#27ae60"],
    labels={"IRD":"Regularidade média (0 a 5)","SG_UF":"Estado"},
    height=600
)
fig_uf.add_vline(
    x=media_nac, line_dash="dash", line_color="#333",
    annotation_text=f"Média Brasil: {formatar_br(media_nac)}",
    annotation_position="top right"
)
fig_uf.update_layout(coloraxis_showscale=False, margin=dict(l=20,r=20,t=20,b=20))
st.plotly_chart(fig_uf, use_container_width=True)

# ── Evolução temporal ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Evolução da regularidade ao longo do tempo")
st.caption("Série histórica 2013–2025 — acompanhe se a regularidade está melhorando ou piorando")

df_evo = df.copy()
if ufs_sel:
    df_evo = df_evo[df_evo["SG_UF"].isin(ufs_sel)]

ird_ano = df_evo.groupby("ANO")["IRD"].mean().reset_index()

# Sinalização de tendência na série nacional
anos   = ird_ano["ANO"].values.astype(float)
valores = ird_ano["IRD"].values
slope  = np.polyfit(anos - anos.mean(), valores, 1)[0]
variacao = valores[-1] - valores[0]

if slope <= -0.05:
    tend_icone="↘️"; tend_cor="#f39c12"; tend_bg="#fef9e7"
    tend_texto = f"Tendência de queda desde 2013 ({variacao:+.2f} pontos acumulados)."
elif slope < 0.05:
    tend_icone="➡️"; tend_cor="#7f8c8d"; tend_bg="#f0f4f8"
    tend_texto = f"Série estável desde 2013 (variação de {variacao:+.2f} pontos)."
else:
    tend_icone="↗️"; tend_cor="#27ae60"; tend_bg="#eafaf1"
    tend_texto = f"Tendência de melhora desde 2013 (+{variacao:.2f} pontos acumulados)."

fig_evo = px.line(
    ird_ano, x="ANO", y="IRD", markers=True,
    labels={"ANO":"Ano","IRD":"Regularidade média (0 a 5)"},
    color_discrete_sequence=["#1a3a5c"]
)
fig_evo.update_layout(margin=dict(l=20,r=20,t=20,b=20))
fig_evo.update_traces(line_width=2.5, marker_size=7)
st.plotly_chart(fig_evo, use_container_width=True)

st.markdown(
    f"<div class='tendencia-box' style='background:{tend_bg}; border-left:4px solid {tend_cor};'>"
    f"<span style='font-size:1.3rem;'>{tend_icone}</span>"
    f"<div><strong style='color:{tend_cor};'>Tendência histórica nacional</strong>"
    f"<br><span style='color:#333;'>{tend_texto}</span></div></div>",
    unsafe_allow_html=True
)

# ── Dispersão IRD × ATU ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Regularidade × Tamanho das turmas")
st.caption(
    "Cada ponto é um município. Municípios com turmas menores tendem a ter "
    "maior regularidade docente — mas o contexto socioeconômico também influencia."
)

df_disp = df_filtrado.dropna(subset=["IRD","ATU"]).copy()
df_disp["Situação"] = df_disp["IRD"].apply(
    lambda x: "Alerta" if x < media_nac*0.85
    else "Atenção" if x < media_nac
    else "Moderado" if x < media_nac*1.1
    else "Favorável"
)
cores_sit = {"Alerta":"#c0392b","Atenção":"#e67e22","Moderado":"#f1c40f","Favorável":"#27ae60"}

fig_disp = px.scatter(
    df_disp.sample(min(2000, len(df_disp)), random_state=42),
    x="ATU", y="IRD",
    color="Situação",
    color_discrete_map=cores_sit,
    hover_data={"NO_MUNICIPIO":True,"SG_UF":True,"IRD":":.2f","ATU":":.1f"},
    labels={"ATU":"Alunos por turma","IRD":"Regularidade (IRD)"},
    height=420,
    opacity=0.65
)
fig_disp.add_hline(
    y=media_nac, line_dash="dash", line_color="#333",
    annotation_text=f"Média Brasil IRD: {formatar_br(media_nac)}",
    annotation_position="top right"
)
fig_disp.update_layout(margin=dict(l=20,r=20,t=20,b=20),
    legend=dict(orientation="h", y=-0.2))
st.plotly_chart(fig_disp, use_container_width=True)
st.caption("Amostra de até 2.000 municípios para melhor performance visual.")

# ── Nota metodológica ──────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("ℹ️ Como interpretar este painel"):
    st.markdown(f"""
    **O que é o IRD?**
    O Indicador de Regularidade do Docente mede a permanência dos professores
    nas mesmas escolas ao longo de 5 anos consecutivos. Varia de 0 a 5.
    O valor do município é a média simples dos IRDs de todas as suas escolas.

    **Classificação de situação**

    | Situação | Critério |
    |----------|---------|
    | 🔴 Alerta | IRD abaixo de 85% da média nacional |
    | 🟠 Atenção | IRD entre 85% e 100% da média nacional |
    | 🟡 Moderado | IRD entre 100% e 110% da média nacional |
    | 🟢 Favorável | IRD acima de 110% da média nacional |

    **Gráfico de dispersão**
    Mostra a relação entre tamanho de turmas (ATU) e regularidade docente (IRD).
    Cada ponto é um município. A amostra exibe até 2.000 municípios para
    melhor performance visual — use os filtros de estado para ver todos os
    municípios de uma região específica.

    **Fonte:** Censo Escolar da Educação Básica — INEP/MEC.
    Nota Técnica nº 11/2015 e atualizações anuais.
    Dados públicos, uso gratuito e irrestrito.
    """)

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from utils.dados import carregar_escola, carregar_municipal, formatar_br, aplicar_estilo_global

st.set_page_config(page_title="Comparação de Escolas · RegDoc", layout="wide")
aplicar_estilo_global()

st.markdown("""
<style>
.tooltip-wrap { position:relative; display:inline-block; cursor:pointer; }
.tooltip-wrap .tip {
    visibility:hidden; opacity:0; width:320px; background:#1a3a5c; color:white;
    font-size:12px; font-weight:normal; line-height:1.6;
    border-radius:8px; padding:12px 16px;
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
TOOLTIPS = {
    "IRD": (
        "O IRD — Indicador de Regularidade do Docente — mede se os mesmos professores "
        "continuam na escola de um ano para o outro. "
        "Escala de 0 a 5: abaixo de 2 = baixa regularidade; 2 a 3 = média-baixa; "
        "3 a 4 = média-alta; 4 a 5 = alta regularidade. "
        "Fonte: Nota Técnica INEP nº 11/2015."
    ),
    "ATU": (
        "ATU — Média de Alunos por Turma. "
        "Média de estudantes por turma. Turmas superlotadas aumentam a sobrecarga "
        "e estão associadas a maior rotatividade docente. "
        "No radar, valores mais altos = turmas menores = situação mais favorável "
        "(escala invertida). Fonte: Censo Escolar/INEP."
    ),
    "AFD": (
        "AFD — Adequação da Formação Docente. "
        "Percentual de professores que lecionam na área em que se formaram. "
        "Quanto maior, mais qualificado é o quadro docente. "
        "Fonte: Censo Escolar/INEP."
    ),
    "IED": (
        "IED — Indicador de Esforço Docente. "
        "Mede a complexidade da jornada — escolas, turnos e disciplinas simultâneas. "
        "Atenção: NÃO indica duplo vínculo diretamente. "
        "No radar, valores mais altos = jornada menos fragmentada = mais favorável "
        "(escala invertida). Fonte: Censo Escolar/INEP."
    ),
    "ICG": (
        "ICG — Complexidade de Gestão da Escola. "
        "Combina porte, turnos, etapas e modalidades. Escala de 1 a 6. "
        "No radar, valores mais altos = menor complexidade = mais favorável "
        "(escala invertida). Fonte: Censo Escolar/INEP."
    ),
}

def tooltip_html(sigla):
    tip = TOOLTIPS.get(sigla, "")
    return (f"<span class='tooltip-wrap'>"
            f"<span class='info-icon'>i</span>"
            f"<span class='tip'>{tip}</span>"
            f"</span>")

st.title("📊 Comparação de Escolas")
st.caption("Compare múltiplas escolas — do mesmo município ou de municípios diferentes")

df_esc = carregar_escola()
df_mun = carregar_municipal()

# ── Seleção de escolas ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Selecione as escolas para comparar")
st.caption("Adicione até 5 escolas de qualquer estado e município")

if "escolas_selecionadas" not in st.session_state:
    st.session_state.escolas_selecionadas = []

col1, col2, col3, col4 = st.columns([1, 2, 3, 1])

with col1:
    ufs = sorted(df_esc["SG_UF"].dropna().unique())
    uf_add = st.selectbox("Estado", ufs, key="uf_add",
        index=ufs.index("ES") if "ES" in ufs else 0)

with col2:
    municipios = (df_esc[df_esc["SG_UF"] == uf_add][["CO_MUNICIPIO","NO_MUNICIPIO"]]
        .drop_duplicates().sort_values("NO_MUNICIPIO"))
    mun_add = st.selectbox("Município", municipios["NO_MUNICIPIO"].tolist(), key="mun_add")

co_mun_add = municipios[municipios["NO_MUNICIPIO"] == mun_add]["CO_MUNICIPIO"].iloc[0]

with col3:
    busca_add = st.text_input("Buscar escola", placeholder="Digite parte do nome...", key="busca_add")
    escolas_mun = df_esc[df_esc["CO_MUNICIPIO"] == co_mun_add][["CO_ENTIDADE","NO_ENTIDADE"]].drop_duplicates()
    if busca_add and len(busca_add) >= 3:
        escolas_mun = escolas_mun[escolas_mun["NO_ENTIDADE"].str.upper().str.contains(busca_add.upper(), na=False)]
    escolas_mun = escolas_mun.sort_values("NO_ENTIDADE")
    if not escolas_mun.empty:
        escola_add = st.selectbox("Escola", escolas_mun["NO_ENTIDADE"].tolist(), key="escola_add")
    else:
        st.warning("Nenhuma escola encontrada.")
        escola_add = None

with col4:
    anos_disp = sorted(df_esc["ANO"].unique())
    ano_comp = st.selectbox("Ano", anos_disp, index=len(anos_disp)-1, key="ano_comp")
    st.markdown("<br>", unsafe_allow_html=True)
    if escola_add and st.button("➕ Adicionar escola", use_container_width=True):
        co_esc_add = escolas_mun[escolas_mun["NO_ENTIDADE"] == escola_add]["CO_ENTIDADE"].iloc[0]
        entrada = {
            "CO_ENTIDADE": co_esc_add,
            "NO_ENTIDADE": escola_add,
            "NO_MUNICIPIO": mun_add,
            "SG_UF": uf_add,
            "ANO": ano_comp
        }
        if len(st.session_state.escolas_selecionadas) >= 5:
            st.warning("Máximo de 5 escolas atingido.")
        elif any(e["CO_ENTIDADE"] == co_esc_add and e["ANO"] == ano_comp
                 for e in st.session_state.escolas_selecionadas):
            st.warning("Esta escola já foi adicionada para este ano.")
        else:
            st.session_state.escolas_selecionadas.append(entrada)
            st.rerun()

# Lista de escolas selecionadas
if st.session_state.escolas_selecionadas:
    st.markdown("**Escolas selecionadas:**")
    cols_lista = st.columns(len(st.session_state.escolas_selecionadas))
    for i, esc in enumerate(st.session_state.escolas_selecionadas):
        with cols_lista[i]:
            st.markdown(f"""
            <div style="background:#f0f4f8; border-radius:8px; padding:0.6rem 0.8rem;
                 border-left:4px solid #1a3a5c; font-size:0.85rem;">
                <strong>{esc['NO_ENTIDADE'][:30]}...</strong><br>
                {esc['NO_MUNICIPIO']} · {esc['SG_UF']} · {esc['ANO']}
            </div>
            """, unsafe_allow_html=True)
            if st.button("✕ Remover", key=f"rem_{i}", use_container_width=True):
                st.session_state.escolas_selecionadas.pop(i)
                st.rerun()

if st.button("🗑️ Limpar todas", use_container_width=False):
    st.session_state.escolas_selecionadas = []
    st.rerun()

if len(st.session_state.escolas_selecionadas) < 2:
    st.info("Adicione pelo menos 2 escolas para comparar.")
    st.stop()

# ── Dados das escolas selecionadas ────────────────────────────────────────────
dados_comp = []
for esc in st.session_state.escolas_selecionadas:
    linha = df_esc[
        (df_esc["CO_ENTIDADE"] == esc["CO_ENTIDADE"]) &
        (df_esc["ANO"] == esc["ANO"])
    ]
    if not linha.empty:
        r = linha.iloc[0]
        media_nac = df_mun[df_mun["ANO"] == esc["ANO"]]["IRD"].mean()
        dados_comp.append({
            "Escola": esc["NO_ENTIDADE"][:25] + "..." if len(esc["NO_ENTIDADE"]) > 25 else esc["NO_ENTIDADE"],
            "Nome completo": esc["NO_ENTIDADE"],
            "Município": esc["NO_MUNICIPIO"],
            "UF": esc["SG_UF"],
            "Ano": esc["ANO"],
            "CO_ENTIDADE": esc["CO_ENTIDADE"],
            "IRD": r["IRD"],
            "ATU": r.get("ATU"),
            "AFD": r.get("AFD"),
            "IED": r.get("IED"),
            "ICG": r.get("ICG"),
            "Media_nac": media_nac
        })

if not dados_comp:
    st.warning("Sem dados disponíveis para as escolas selecionadas.")
    st.stop()

df_comp = pd.DataFrame(dados_comp)

def cor_ird(ird, media):
    if pd.isna(ird) or pd.isna(media): return "#aaa", "#f5f5f5"
    if ird >= media:        return "#27ae60", "#eafaf1"
    elif ird >= media*0.85: return "#f39c12", "#fef9e7"
    else:                   return "#c0392b", "#fdedec"

# ── Comparação lado a lado ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Comparação lado a lado")
st.caption(
    f"IRD — Regularidade dos professores (0 a 5) "
    + tooltip_html("IRD"),
    unsafe_allow_html=True
)

cols_cards = st.columns(len(dados_comp))
for i, d in enumerate(dados_comp):
    cor, bg = cor_ird(d["IRD"], d["Media_nac"])
    with cols_cards[i]:
        st.markdown(f"""
        <div style="background:{bg}; border:2px solid {cor}; border-radius:10px;
             padding:1rem; text-align:center; margin-bottom:0.5rem;">
            <p style="font-size:0.75rem; color:{cor}; margin:0; font-weight:bold;">
                {d['Escola']}
            </p>
            <p style="font-size:0.7rem; color:#777; margin:0.2rem 0;">
                {d['Município']} · {d['UF']} · {d['Ano']}
            </p>
            <p style="font-size:2rem; font-weight:bold; color:{cor}; margin:0.3rem 0;">
                {formatar_br(d['IRD'])}
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:#f7f9fc; border-radius:8px; padding:0.8rem; font-size:0.8rem;">
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span>Alunos/turma {tooltip_html('ATU')}</span>
                <strong>{formatar_br(d['ATU'],1)}</strong>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span>Formação (%) {tooltip_html('AFD')}</span>
                <strong>{formatar_br(d['AFD'],1)}{'%' if pd.notna(d['AFD']) else ''}</strong>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span>Esforço docente {tooltip_html('IED')}</span>
                <strong>{formatar_br(d['IED'],1)}{'%' if pd.notna(d['IED']) else ''}</strong>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span>Complexidade {tooltip_html('ICG')}</span>
                <strong>{formatar_br(d['ICG'],1)}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Comparação com média nacional ──────────────────────────────────────────────
st.markdown("---")
st.markdown("### Comparação com a média nacional")
st.caption("Barras coloridas mostram o IRD de cada escola em relação à média nacional")

anos_unicos  = list(set(d["Ano"] for d in dados_comp))
media_nac_ref = (df_mun[df_mun["ANO"] == anos_unicos[0]]["IRD"].mean()
                 if len(anos_unicos) == 1 else df_mun["IRD"].mean())

fig_bar = go.Figure()
for i, d in enumerate(dados_comp):
    cor, _ = cor_ird(d["IRD"], d["Media_nac"])
    fig_bar.add_trace(go.Bar(
        name=d["Escola"],
        x=[d["Escola"]],
        y=[d["IRD"]],
        marker_color=cor,
        text=[formatar_br(d["IRD"])],
        textposition="outside",
        hovertemplate=(
            f"<b>{d['Nome completo']}</b><br>"
            f"{d['Município']} · {d['UF']} · {d['Ano']}<br>"
            f"IRD: {formatar_br(d['IRD'])}<extra></extra>"
        )
    ))

fig_bar.add_hline(y=media_nac_ref, line_dash="dash", line_color="#333",
    annotation_text=f"Média Brasil: {formatar_br(media_nac_ref)}",
    annotation_position="top right")
fig_bar.update_layout(
    height=380, showlegend=False,
    margin=dict(l=20,r=20,t=40,b=20),
    yaxis=dict(title="Regularidade (0 a 5)", range=[0,5.5]),
    xaxis_title="", bargap=0.3
)
st.plotly_chart(fig_bar, use_container_width=True)

# ── Gráfico radar ──────────────────────────────────────────────────────────────
st.markdown("### Perfil completo dos indicadores")
st.caption("Quanto maior a área, melhor o perfil geral da escola. ATU, Esforço e Complexidade estão com escala invertida — maior = mais favorável.")

categorias = ["Regularidade (IRD)","Alunos/turma (inv.)","Formação (%)","Esforço (inv.)","Complexidade (inv.)"]
cores_escolas = ["#1a3a5c","#c0392b","#27ae60","#f39c12","#8e44ad"]

fig_radar = go.Figure()
for i, d in enumerate(dados_comp):
    ird_n = (d["IRD"]/5)*100         if pd.notna(d["IRD"]) else 0
    atu_n = max(0, 100-((d["ATU"]/40)*100)) if pd.notna(d["ATU"]) else 0
    afd_n = d["AFD"]                  if pd.notna(d["AFD"]) else 0
    ied_n = max(0, 100-d["IED"])      if pd.notna(d["IED"]) else 0
    icg_n = max(0, 100-((d["ICG"]/6)*100)) if pd.notna(d["ICG"]) else 0

    valores = [ird_n, atu_n, afd_n, ied_n, icg_n]
    valores.append(valores[0])

    fig_radar.add_trace(go.Scatterpolar(
        r=valores,
        theta=categorias + [categorias[0]],
        fill="toself",
        name=d["Escola"],
        line_color=cores_escolas[i % len(cores_escolas)],
        opacity=0.6
    ))

fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0,100])),
    height=450, margin=dict(l=40,r=40,t=40,b=40),
    legend=dict(orientation="h", y=-0.15)
)
st.plotly_chart(fig_radar, use_container_width=True)

# ── Ranking de escolas do município ───────────────────────────────────────────
st.markdown("---")
st.markdown("### Ranking de escolas do município")
st.caption("Veja onde cada escola está em relação às demais do mesmo município")

municipios_comp = list(set(d["Município"] for d in dados_comp))
anos_comp       = list(set(d["Ano"] for d in dados_comp))

col_r1, col_r2 = st.columns(2)
with col_r1:
    mun_rank = st.selectbox("Município para o ranking", municipios_comp, key="mun_rank")
with col_r2:
    ano_rank = st.selectbox("Ano", anos_comp, key="ano_rank")

co_mun_rank  = df_esc[df_esc["NO_MUNICIPIO"] == mun_rank]["CO_MUNICIPIO"].iloc[0]
df_rank_mun  = (df_esc[(df_esc["CO_MUNICIPIO"] == co_mun_rank) & (df_esc["ANO"] == ano_rank)]
                .dropna(subset=["IRD"]).sort_values("IRD", ascending=True).copy())

media_nac_rank = df_mun[df_mun["ANO"] == ano_rank]["IRD"].mean()
media_mun_rank = df_rank_mun["IRD"].mean()
escolas_dest   = [d["CO_ENTIDADE"] for d in dados_comp
                  if d["Município"] == mun_rank and d["Ano"] == ano_rank]

st.markdown(f"""
<div style="background:#f0f4f8; border-radius:8px; padding:0.8rem 1rem;
     margin-bottom:1rem; font-size:0.9rem;">
    📊 <strong>{mun_rank}</strong> em {ano_rank} —
    IRD médio do município: <strong>{formatar_br(media_mun_rank)}</strong> |
    Média nacional: <strong>{formatar_br(media_nac_rank)}</strong> |
    Total de escolas: <strong>{len(df_rank_mun)}</strong>
</div>
""", unsafe_allow_html=True)

cores_rank = []
for _, row in df_rank_mun.iterrows():
    if row["CO_ENTIDADE"] in escolas_dest:    cores_rank.append("#1a3a5c")
    elif row["IRD"] < media_nac_rank*0.85:    cores_rank.append("#c0392b")
    elif row["IRD"] < media_nac_rank:         cores_rank.append("#e67e22")
    elif row["IRD"] < media_nac_rank*1.1:     cores_rank.append("#f1c40f")
    else:                                      cores_rank.append("#27ae60")

nomes_curtos = [n[:20]+"..." if len(n)>20 else n for n in df_rank_mun["NO_ENTIDADE"]]

fig_rank = go.Figure()
fig_rank.add_trace(go.Bar(
    x=df_rank_mun["IRD"].tolist(), y=nomes_curtos,
    orientation="h", marker_color=cores_rank,
    hovertemplate="<b>%{y}</b><br>IRD: %{x:.3f}<extra></extra>"
))
fig_rank.add_vline(x=media_nac_rank, line_dash="dash", line_color="#333",
    annotation_text=f"Média Brasil: {formatar_br(media_nac_rank)}",
    annotation_position="top right")
fig_rank.add_vline(x=media_mun_rank, line_dash="dot", line_color="#e67e22",
    annotation_text=f"Média {mun_rank}: {formatar_br(media_mun_rank)}",
    annotation_position="bottom right")
fig_rank.update_layout(
    height=max(400, len(df_rank_mun)*22),
    margin=dict(l=20,r=20,t=20,b=20),
    xaxis=dict(title="Regularidade (0 a 5)", range=[0,5.5]),
    yaxis=dict(autorange="reversed")
)
st.plotly_chart(fig_rank, use_container_width=True)
st.caption("Escolas em azul escuro = escolas que você adicionou para comparação. Vermelho = Alerta | Laranja = Atenção | Amarelo = Moderado | Verde = Favorável.")

# ── Tabela comparativa ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Tabela comparativa completa")

df_tab = df_comp[["Nome completo","Município","UF","Ano","IRD","ATU","AFD","IED","ICG"]].copy()
df_tab["IRD"] = df_tab["IRD"].apply(lambda x: formatar_br(x,3))
df_tab["ATU"] = df_tab["ATU"].apply(lambda x: formatar_br(x,1))
df_tab["AFD"] = df_tab["AFD"].apply(lambda x: formatar_br(x,1))
df_tab["IED"] = df_tab["IED"].apply(lambda x: formatar_br(x,1))
df_tab["ICG"] = df_tab["ICG"].apply(lambda x: formatar_br(x,1))
df_tab = df_tab.rename(columns={
    "Nome completo":"Escola","IRD":"Regularidade",
    "ATU":"Alunos/turma","AFD":"Formação (%)","IED":"Esforço (%)","ICG":"Complexidade"
})
st.dataframe(df_tab, use_container_width=True, hide_index=True)

csv = df_tab.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="📥 Baixar comparação (CSV)",
    data=csv,
    file_name="comparacao_escolas_regdoc.csv",
    mime="text/csv"
)

# ── Nota metodológica ──────────────────────────────────────────────────────────
st.markdown("---")

with st.expander("ℹ️ Como interpretar a comparação"):
    st.markdown("""
    **Comparação lado a lado**
    Cada card mostra o IRD da escola e os indicadores associados.
    A cor do card indica a situação em relação à média nacional:
    verde = acima da média; laranja = entre 85% e 100%; vermelho = abaixo de 85%.

    **Gráfico radar**
    Os indicadores ATU, Esforço docente (IED) e Complexidade (ICG) estão
    com escala **invertida** no radar — quanto maior a área, melhor o perfil.
    Isso significa que turmas menores, jornada menos fragmentada e escola
    menos complexa aparecem como valores mais altos no gráfico.

    **Limitação importante**
    A comparação não controla pelo nível socioeconômico (INSE) das escolas.
    Escolas em contextos mais vulneráveis tendem a ter IRD menor por razões
    estruturais — use o ranking do município para contextualizar.

    **Fonte:** Censo Escolar da Educação Básica — INEP/MEC.
    """)


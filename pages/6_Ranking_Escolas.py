import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.dados import carregar_escola, carregar_municipal, formatar_br, aplicar_estilo_global

st.set_page_config(page_title="Ranking de Escolas · RegDoc", layout="wide")

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

TOOLTIP_CLASSIFICACAO = (
    "A classificação usa as mesmas referências da página Escola: "
    "Alerta = IRD abaixo da média municipal; "
    "Atenção = entre a média municipal e a média nacional; "
    "Favorável = acima da média nacional. "
    "Fonte: Censo Escolar/INEP."
)

# ── Carregar dados ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Carregando dados...")
def load_esc():
    return carregar_escola()

@st.cache_data(show_spinner="Carregando dados...")
def load_mun():
    return carregar_municipal()

df_esc = load_esc()
df_mun = load_mun()

# ── Cabeçalho ──────────────────────────────────────────────────────────────────
st.title("🏫 Quais escolas do município precisam de atenção?")
st.caption("Escolas ordenadas pela menor regularidade dos professores — diagnóstico de rede para o planejamento anual")

# ── Filtros — estrutura idêntica ao 4_Escola.py ────────────────────────────────
col1, col2 = st.columns([1, 2])

with col1:
    ufs = sorted(df_esc["SG_UF"].dropna().unique())
    uf_sel = st.selectbox("Estado", ufs, index=ufs.index("ES") if "ES" in ufs else 0)

with col2:
    municipios = (df_esc[df_esc["SG_UF"] == uf_sel][["CO_MUNICIPIO", "NO_MUNICIPIO"]]
                  .drop_duplicates().sort_values("NO_MUNICIPIO"))
    mun_sel = st.selectbox("Município", municipios["NO_MUNICIPIO"].tolist())

co_mun = municipios[municipios["NO_MUNICIPIO"] == mun_sel]["CO_MUNICIPIO"].iloc[0]

# Ano — fora das colunas, igual ao padrão do app
df_esc_mun = df_esc[df_esc["CO_MUNICIPIO"] == co_mun]
anos_disp   = sorted(df_esc_mun["ANO"].dropna().unique())

if not anos_disp:
    st.warning("Sem dados para este município.")
    st.stop()

ano_sel = st.selectbox("Ano de referência", anos_disp, index=len(anos_disp) - 1)

# Localização (defensivo)
tem_loc = "TP_LOCALIZACAO" in df_esc.columns
if tem_loc:
    loc_sel = st.radio("Localização", ["Todas", "Urbana", "Rural"], horizontal=True)
else:
    loc_sel = "Todas"

# ── Referências (mesma lógica do 4_Escola.py) ─────────────────────────────────
media_ird_nac = df_mun[df_mun["ANO"] == ano_sel]["IRD"].mean()
media_ird_mun = df_mun[
    (df_mun["ANO"] == ano_sel) & (df_mun["CO_MUNICIPIO"] == co_mun)
]["IRD"].mean()

# ── Dados do ano ───────────────────────────────────────────────────────────────
df_ano = df_esc_mun[df_esc_mun["ANO"] == ano_sel].copy()

if tem_loc and loc_sel != "Todas":
    mapa_loc = {"Urbana": 1, "Rural": 2}
    df_ano = df_ano[df_ano["TP_LOCALIZACAO"] == mapa_loc[loc_sel]]

if df_ano.empty:
    st.warning("Nenhuma escola encontrada para os filtros selecionados.")
    st.stop()

df_rank    = df_ano.dropna(subset=["IRD"]).copy()
n_sem_dado = len(df_ano) - len(df_rank)

# ── Classificação — idêntica ao 4_Escola.py ───────────────────────────────────
CORES = {"Alerta": "#c0392b", "Atenção": "#e67e22", "Favorável": "#27ae60", "Sem dados": "#aaa"}

def classificar(ird):
    if pd.isna(ird):
        return "Sem dados"
    if pd.notna(media_ird_nac) and ird >= media_ird_nac:
        return "Favorável"
    if pd.notna(media_ird_mun) and ird >= media_ird_mun:
        return "Atenção"
    return "Alerta"

ORDEM = {"Alerta": 0, "Atenção": 1, "Favorável": 2, "Sem dados": 3}

df_rank["RISCO"] = df_rank["IRD"].apply(classificar)
df_rank = df_rank.sort_values(
    ["RISCO", "IRD"],
    key=lambda col: col.map(ORDEM) if col.name == "RISCO" else col
).reset_index(drop=True)

# ── Cards de situação ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"### Diagnóstico de rede — {mun_sel} ({ano_sel})")

ordem_display = ["Alerta", "Atenção", "Favorável"]
contagem = df_rank["RISCO"].value_counts().reindex(ordem_display, fill_value=0)
total    = len(df_rank)

c_tot, c1, c2, c3 = st.columns(4)
c_tot.metric("Total de escolas", total + n_sem_dado)
for col_ui, faixa in zip([c1, c2, c3], ordem_display):
    qtd = int(contagem.get(faixa, 0))
    pct = qtd / total * 100 if total > 0 else 0
    cor = CORES[faixa]
    col_ui.markdown(f"""
    <div style="background:{cor}22; border-left:5px solid {cor};
         padding:0.8rem 1rem; border-radius:6px; text-align:center;">
        <div style="font-size:1.8rem; font-weight:bold; color:{cor};">{qtd}</div>
        <div style="font-size:0.85rem; color:#333;">{faixa}</div>
        <div style="font-size:0.8rem; color:#777;">{pct:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

# Banner
st.markdown("<br>", unsafe_allow_html=True)
n_alerta  = int(contagem.get("Alerta", 0))
n_atencao = int(contagem.get("Atenção", 0))
pct_abaixo = round((n_alerta + n_atencao) / total * 100, 1) if total > 0 else 0.0

if n_alerta > 0:
    st.error(
        f"⚠️ **{n_alerta} escola(s) em Alerta** — IRD abaixo da média de "
        f"{mun_sel} ({formatar_br(media_ird_mun, 3)}). Priorize essas unidades no plano de ação."
    )
elif pct_abaixo >= 50:
    st.warning(
        f"🔔 **{pct_abaixo}% das escolas** abaixo da média nacional "
        f"({formatar_br(media_ird_nac, 3)}). Reforce o monitoramento."
    )
else:
    st.success(
        f"✅ Rede com boa regularidade geral em {mun_sel}. "
        f"Apenas {n_alerta} escola(s) em Alerta."
    )

# Métricas de referência
st.markdown("<br>", unsafe_allow_html=True)
cm1, cm2 = st.columns(2)
cm1.metric(
    f"Média nacional — {ano_sel}",
    formatar_br(media_ird_nac, 3),
    help="IRD médio de todos os municípios brasileiros no ano selecionado."
)
cm2.metric(
    f"Média {mun_sel} — {ano_sel}",
    formatar_br(media_ird_mun, 3),
    delta=f"{media_ird_mun - media_ird_nac:+.3f}".replace(".", ",")
          if pd.notna(media_ird_mun) and pd.notna(media_ird_nac) else None,
    help=f"IRD médio das escolas de {mun_sel} no ano selecionado."
)

# ── Ranking ────────────────────────────────────────────────────────────────────
st.markdown("---")

if total <= 10:
    n_top = total
    st.caption(f"Exibindo todas as {total} escolas do município.")
else:
    n_top = st.slider("Escolas no ranking", 10, min(100, total), min(30, total))

st.markdown(f"### Top {n_top} escolas — menor regularidade dos professores")
st.markdown(
    f"🔴 Alerta = abaixo de {formatar_br(media_ird_mun, 3)} (média {mun_sel}) · "
    f"🟠 Atenção = até {formatar_br(media_ird_nac, 3)} (média nacional) · "
    f"🟢 Favorável = acima da média nacional "
    f"<span class='tooltip-wrap'><span class='info-icon'>i</span>"
    f"<span class='tip'>{TOOLTIP_CLASSIFICACAO}</span></span>",
    unsafe_allow_html=True
)

# Colunas de exibição
cols_base  = ["NO_ENTIDADE", "IRD", "RISCO"]
cols_extra = [c for c in ["ICG", "ATU", "AFD", "IED"] if c in df_rank.columns]
if tem_loc:
    df_rank["Localização"] = df_rank["TP_LOCALIZACAO"].map({1: "Urbana", 2: "Rural"}).fillna("—")
    cols_extra = ["Localização"] + cols_extra

df_tabela = df_rank.head(n_top)[cols_base + cols_extra].copy()

fmt = {"IRD": 3, "ICG": 2, "ATU": 1, "AFD": 1, "IED": 1}
for col, dec in fmt.items():
    if col in df_tabela.columns:
        df_tabela[col] = df_tabela[col].apply(
            lambda x: formatar_br(x, dec) if pd.notna(x) else "—"
        )

df_tabela = df_tabela.rename(columns={
    "NO_ENTIDADE": "Escola",
    "IRD":         "Regularidade",
    "ICG":         "Complexidade",
    "ATU":         "Alunos/turma",
    "AFD":         "Formação (%)",
    "IED":         "Esforço docente (%)",
    "RISCO":       "Situação",
})
df_tabela.index = df_tabela.index + 1
df_tabela.index.name = "Posição"

st.dataframe(df_tabela, use_container_width=True)

col_dl, _ = st.columns([1, 3])
with col_dl:
    csv = df_tabela.to_csv(index=True).encode("utf-8-sig")
    st.download_button(
        label="📥 Baixar ranking (CSV)",
        data=csv,
        file_name=f"ranking_escolas_{mun_sel}_{ano_sel}.csv",
        mime="text/csv",
    )

# ── Gráfico ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Distribuição do IRD nas escolas do município")
st.caption("Barras mais à esquerda = menor regularidade")

fig = px.histogram(
    df_rank, x="IRD", nbins=20,
    color="RISCO",
    color_discrete_map=CORES,
    category_orders={"RISCO": ["Alerta", "Atenção", "Favorável"]},
    labels={"IRD": "Regularidade (0 a 5)", "count": "Nº de escolas", "RISCO": "Situação"},
    height=340,
)
fig.add_vline(
    x=media_ird_nac, line_dash="dash", line_color="#555",
    annotation_text=f"Média nacional: {formatar_br(media_ird_nac, 3)}",
    annotation_position="top right",
)
if pd.notna(media_ird_mun):
    fig.add_vline(
        x=media_ird_mun, line_dash="dot", line_color="#e67e22",
        annotation_text=f"Média {mun_sel}: {formatar_br(media_ird_mun, 3)}",
        annotation_position="top left",
    )
fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), bargap=0.05)
st.plotly_chart(fig, use_container_width=True)

# ── Nota metodológica ──────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("ℹ️ Como interpretar este ranking"):
    st.markdown(f"""
    **O que é o IRD?**
    O Indicador de Regularidade do Docente mede a permanência dos professores
    na mesma escola ao longo de 5 anos consecutivos. Varia de 0 a 5.

    **Como as escolas são classificadas?**

    | Situação | Critério |
    |----------|---------|
    | 🔴 Alerta | IRD abaixo da média de {mun_sel} ({formatar_br(media_ird_mun, 3)}) |
    | 🟠 Atenção | IRD entre a média municipal e a média nacional ({formatar_br(media_ird_nac, 3)}) |
    | 🟢 Favorável | IRD acima da média nacional |

    **Próximo passo:** identifique as escolas em Alerta e acesse a página **Escola**
    para ver o perfil completo e as orientações específicas.

    **Fonte:** Censo Escolar da Educação Básica — INEP/MEC. Nota Técnica nº 11/2015.
    """)

if n_sem_dado > 0:
    st.caption(
        f"ℹ️ {n_sem_dado} escola(s) sem IRD disponível para {ano_sel} — "
        "não incluídas no ranking mas contabilizadas no total."
    )

st.markdown("---")
st.caption("RegDoc · Fonte: Censo Escolar / INEP · Atualização anual mediante publicação do Censo Escolar.")

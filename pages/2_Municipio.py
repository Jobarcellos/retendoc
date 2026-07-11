import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from utils.dados import (carregar_municipal, carregar_escola, formatar_br,
                         aplicar_estilo_global, classificar_tendencia,
                         render_tendencia, sombrear_pandemia, tabela_pares,
                         municipal_por_rede, REDES_DISPONIVEIS)

st.set_page_config(page_title="Município · RegDoc", layout="wide")

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
div[data-testid="stTabs"] button {
    font-size: 1rem !important;
    font-weight: 700 !important;
    padding: 0.6rem 1.6rem !important;
    color: #1a3a5c !important;
    border-bottom: 3px solid transparent !important;
    letter-spacing: 0.03em !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #1a3a5c !important;
    border-bottom: 3px solid #1a3a5c !important;
    background: #eaf0fb !important;
    border-radius: 6px 6px 0 0 !important;
}
</style>
""", unsafe_allow_html=True)

TOOLTIPS = {
    "IRD": (
        "O IRD — Indicador de Regularidade do Docente — mede se os mesmos professores "
        "continuam na escola de um ano para o outro. "
        "Calculado pelo INEP a partir do Censo Escolar, observando a presença de cada "
        "professor nos últimos 5 anos consecutivos. "
        "O valor do município é a média simples dos IRDs de todas as suas escolas. "
        "Escala de 0 a 5 — quanto maior, mais estável é o corpo docente. "
        "Classificação: abaixo de 2 = baixa regularidade; 2 a 3 = média-baixa; "
        "3 a 4 = média-alta; 4 a 5 = alta regularidade. "
        "Fonte: Nota Técnica INEP nº 11/2015."
    ),
    "ATU": (
        "ATU — Média de Alunos por Turma. "
        "Média de estudantes matriculados por turma no município. "
        "Calculado como: total de matrículas ÷ total de turmas. "
        "Turmas superlotadas aumentam a sobrecarga do professor e estão associadas "
        "a maior rotatividade docente. "
        "Parâmetros de referência: EF I = 20–25 alunos/turma; "
        "EF II = 25–30; Ensino Médio = 30–35. "
        "Fonte: Censo Escolar/INEP."
    ),
    "AFD": (
        "AFD — Adequação da Formação Docente. "
        "Percentual de professores que lecionam na área em que se formaram, "
        "conforme os requisitos da LDB. "
        "Grupo 1 e 2 = adequado (formação superior na área ou licenciatura na disciplina). "
        "Grupos 3, 4 e 5 = inadequado (área diferente, ensino médio ou fundamental). "
        "Quanto maior, mais qualificado e alinhado é o quadro docente do município. "
        "Fonte: Censo Escolar/INEP."
    ),
    "IED": (
        "IED — Indicador de Esforço Docente. "
        "Mede a complexidade da jornada de trabalho dos professores, considerando "
        "quantas escolas, turnos, disciplinas e alunos cada professor atende. "
        "Atenção: o IED NÃO indica diretamente duplo vínculo empregatício. "
        "Valores altos sugerem jornada fragmentada, o que pode reduzir "
        "o vínculo do professor com a escola. "
        "Escala de 1 (menor esforço) a 6 (maior esforço). "
        "Fonte: Censo Escolar/INEP."
    ),
    "ICG": (
        "ICG — Indicador de Complexidade de Gestão da Escola. "
        "Média da complexidade das escolas do município, combinando: "
        "porte, número de turnos, etapas de ensino e modalidades atendidas. "
        "Escala de 1 a 6: quanto maior, mais complexa é a gestão das unidades. "
        "Municípios com ICG alto têm escolas mais vulneráveis à rotatividade docente. "
        "Fonte: Censo Escolar/INEP."
    ),
}

# ── Carregar dados ─────────────────────────────────────────────────────────────
st.title("🔍 Análise por Município")
st.caption("Evolução da regularidade dos professores e comparação com médias nacionais e estaduais")

df = carregar_municipal()

@st.cache_data(show_spinner=False)
def load_escolas():
    return carregar_escola()

df_esc = load_escolas()

# ── Filtros compartilhados ─────────────────────────────────────────────────────
col1, col2, col3f = st.columns([1, 2, 1])
with col1:
    ufs = sorted(df["SG_UF"].dropna().unique())
    _uf_default = st.session_state.pop("uf_deep_link", None)
    _idx_default = ufs.index(_uf_default) if _uf_default in ufs else (ufs.index("ES") if "ES" in ufs else 0)
    uf_sel = st.selectbox("Estado", ufs, index=_idx_default)
with col3f:
    rede_sel = st.selectbox(
        "Rede",
        REDES_DISPONIVEIS,
        index=0,
        help="Escolha quais escolas entram no cálculo: todas as do município "
             "ou apenas as da rede municipal, estadual ou privada."
    )

if rede_sel != "Todas as redes":
    df = municipal_por_rede(rede_sel)
    st.info(
        f"📌 Analisando apenas a **rede {rede_sel.lower()}** deste município. "
        "Médias nacional e estadual também consideram somente essa rede."
    )

with col2:
    municipios_uf = (
        df[df["SG_UF"] == uf_sel][["CO_MUNICIPIO","NO_MUNICIPIO"]]
        .drop_duplicates().sort_values("NO_MUNICIPIO")
    )
    municipio_label = st.selectbox("Município", municipios_uf["NO_MUNICIPIO"].tolist())
co_mun = municipios_uf[municipios_uf["NO_MUNICIPIO"] == municipio_label]["CO_MUNICIPIO"].iloc[0]
df_mun = df[df["CO_MUNICIPIO"] == co_mun].sort_values("ANO").copy()

if df_mun.empty:
    st.warning("Sem dados para este município.")
    st.stop()

ano_ref = st.selectbox("Ano de referência", sorted(df_mun["ANO"].unique()),
                       index=len(df_mun["ANO"].unique()) - 1)

_sel_ano = df_mun[df_mun["ANO"] == ano_ref]
if _sel_ano.empty:
    st.warning(f"Sem dados da rede selecionada para {municipio_label} em {ano_ref}.")
    st.stop()
linha_atual   = _sel_ano.iloc[0]
media_ird_nac = df[df["ANO"] == ano_ref]["IRD"].mean()
media_ird_uf  = df[(df["ANO"] == ano_ref) & (df["SG_UF"] == uf_sel)]["IRD"].mean()
ird           = linha_atual["IRD"]

if pd.isna(ird):
    cor = "#aaa"; situacao = "Sem dados"
    texto_sit = "Não há dados de regularidade para este município no ano selecionado."
    orientacoes = []
elif ird >= media_ird_nac:
    cor = "#27ae60"; situacao = "Situação favorável"
    texto_sit = (f"A regularidade dos professores de {municipio_label} ({formatar_br(ird)}) "
                 f"está acima da média nacional ({formatar_br(media_ird_nac)}) "
                 f"e da média do {uf_sel} ({formatar_br(media_ird_uf)}).")
    orientacoes = [
        "Identifique as escolas com melhor regularidade e sistematize suas boas práticas para compartilhar com toda a rede.",
        "Use os dados do RegDoc para apresentar ao prefeito e ao conselho municipal os resultados positivos da rede.",
        "Mantenha o monitoramento anual — resultados positivos podem se deteriorar se as condições de trabalho mudarem.",
        "Planeje ações de valorização docente para sustentar os bons resultados ao longo do tempo.",
    ]
elif pd.notna(media_ird_uf) and ird >= media_ird_uf:
    cor = "#f39c12"; situacao = "Atenção"
    texto_sit = (f"A regularidade dos professores de {municipio_label} ({formatar_br(ird)}) "
                 f"está abaixo da média nacional ({formatar_br(media_ird_nac)}), "
                 f"mas acima da média do {uf_sel} ({formatar_br(media_ird_uf)}).")
    orientacoes = [
        "Verifique quais escolas do município estão em situação de alerta e priorize o acompanhamento dessas unidades.",
        "Analise a tendência dos últimos anos — se o IRD está caindo, o problema está se agravando.",
        "Promova formação continuada focada nas necessidades identificadas nas escolas com maior rotatividade.",
        "Construa um plano municipal de valorização docente com metas e prazos definidos.",
    ]
else:
    cor = "#c0392b"; situacao = "Alerta"
    texto_sit = (f"A regularidade dos professores de {municipio_label} ({formatar_br(ird)}) "
                 f"está abaixo da média nacional ({formatar_br(media_ird_nac)}) "
                 f"e abaixo da média do {uf_sel} ({formatar_br(media_ird_uf)}). "
                 "A secretaria deve priorizar intervenções neste município.")
    orientacoes = [
        "Mapeie as escolas em situação crítica usando a aba Ranking de Escolas e priorize visitas técnicas imediatas.",
        "Realize diagnóstico das condições de trabalho — turmas superlotadas, infraestrutura inadequada e falta de apoio pedagógico são causas frequentes.",
        "Elabore um plano de ação municipal com metas, responsáveis e prazos para reduzir a rotatividade docente.",
        "Apresente os dados do RegDoc ao prefeito e ao conselho municipal para justificar investimentos em valorização docente.",
        "Acione o Ministério da Educação e a Secretaria Estadual para suporte técnico e financeiro se necessário.",
    ]

hist_var = df_mun[df_mun["ANO"] <= ano_ref].sort_values("ANO")
if len(hist_var) >= 2:
    variacao  = hist_var["IRD"].iloc[-1] - hist_var["IRD"].iloc[-2]
    ano_ant   = int(hist_var["ANO"].iloc[-2])
    texto_var = (f"Em relação a {ano_ant}, houve melhora de {formatar_br(variacao)}." if variacao > 0.05
        else f"Em relação a {ano_ant}, houve queda de {formatar_br(abs(variacao))}. Merece atenção." if variacao < -0.05
        else f"Em relação a {ano_ant}, a regularidade permaneceu estável.")
else:
    variacao = None; texto_var = "Não há ano anterior disponível para comparação."

tendencia = classificar_tendencia(df_mun, ano_ref)

# ══════════════════════════════════════════════════════════════════════════════
# ABAS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
aba1, aba2 = st.tabs(["📊  ANÁLISE DO MUNICÍPIO", "🏫  RANKING DE ESCOLAS"])

# ─────────────────────────────────────────────
# ABA 1 — idêntica ao documento 6
# ─────────────────────────────────────────────
with aba1:
    st.markdown(f"### {municipio_label} · {uf_sel} · {ano_ref}")

    col_ird, col_comp = st.columns([1, 2])
    with col_ird:
        st.markdown(f"""
        <div style="background:{cor}22; border:2px solid {cor}; border-radius:12px;
             padding:1.5rem 2rem; text-align:center;">
            <p style="color:{cor}; margin:0; font-size:1rem;">
                Regularidade dos professores (0 a 5)
                <span class="tooltip-wrap">
                    <span class="info-icon" style="background:{cor};">i</span>
                    <span class="tip">{TOOLTIPS['IRD']}</span>
                </span>
            </p>
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
        st.markdown(
            f"<p style='font-size:0.9rem; color:#333; margin-top:0.5rem;'>"
            f"{texto_sit}<br><strong>Variação:</strong> {texto_var}</p>",
            unsafe_allow_html=True)

    if orientacoes:
        with st.expander(f"📋 O que fazer? — Orientações para situação de {situacao}"):
            for i, ori in enumerate(orientacoes, 1):
                st.markdown(f"**{i}.** {ori}")

    st.markdown("---")
    st.markdown("### Indicadores do município")
    st.caption("Passe o mouse sobre o ℹ para entender cada indicador")

    ci1, ci2, ci3 = st.columns(3)
    with ci1:
        st.markdown(f"""
        <div style="border:1px solid #dde4ed; border-radius:8px; padding:1rem 1.2rem; background:#f7f9fc;">
            <div style="font-size:0.9rem; font-weight:600; color:#1a3a5c; margin-bottom:4px;">
                Formação adequada (AFD)
                <span class="tooltip-wrap"><span class="info-icon">i</span>
                <span class="tip">{TOOLTIPS['AFD']}</span></span>
            </div>
            <div style="font-size:1.6rem; font-weight:bold; color:#1a3a5c;">{formatar_br(linha_atual['AFD'],1)}%</div>
        </div>""", unsafe_allow_html=True)
    with ci2:
        st.markdown(f"""
        <div style="border:1px solid #dde4ed; border-radius:8px; padding:1rem 1.2rem; background:#f7f9fc;">
            <div style="font-size:0.9rem; font-weight:600; color:#1a3a5c; margin-bottom:4px;">
                Esforço docente (IED)
                <span class="tooltip-wrap"><span class="info-icon">i</span>
                <span class="tip">{TOOLTIPS['IED']}</span></span>
            </div>
            <div style="font-size:1.6rem; font-weight:bold; color:#1a3a5c;">{formatar_br(linha_atual['IED'],1)}%</div>
        </div>""", unsafe_allow_html=True)
    with ci3:
        st.markdown(f"""
        <div style="border:1px solid #dde4ed; border-radius:8px; padding:1rem 1.2rem; background:#f7f9fc;">
            <div style="font-size:0.9rem; font-weight:600; color:#1a3a5c; margin-bottom:4px;">
                Complexidade média (ICG)
                <span class="tooltip-wrap"><span class="info-icon">i</span>
                <span class="tip">{TOOLTIPS['ICG']}</span></span>
            </div>
            <div style="font-size:1.6rem; font-weight:bold; color:#1a3a5c;">{formatar_br(linha_atual['ICG'],1)}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Como seu município está entre os parecidos com ele?")
    st.caption(
        "Comparar com a média nacional mistura realidades muito diferentes. "
        "Aqui a comparação é só entre municípios de porte e complexidade semelhantes."
    )

    df_pares_full, ano_porte = tabela_pares(ano_ref, rede_sel)
    linha_par = df_pares_full[df_pares_full["CO_MUNICIPIO"] == co_mun]

    if linha_par.empty:
        st.info("Sem dados de complexidade (ICG) para este município neste ano — comparação entre pares indisponível.")
    else:
        faixa_icg   = linha_par["FAIXA_ICG"].iloc[0]
        faixa_porte = linha_par["FAIXA_PORTE"].iloc[0]
        pares = df_pares_full[
            (df_pares_full["FAIXA_ICG"] == faixa_icg) &
            (df_pares_full["FAIXA_PORTE"] == faixa_porte)
        ].dropna(subset=["IRD"]).copy()

        n_grupo = len(pares)
        if n_grupo < 10:
            st.info("Grupo de comparação muito pequeno neste ano para uma leitura confiável.")
        else:
            pares = pares.sort_values("IRD", ascending=False).reset_index(drop=True)
            posicao = int(pares.index[pares["CO_MUNICIPIO"] == co_mun][0]) + 1
            media_grupo = pares["IRD"].mean()
            dif_grupo = ird - media_grupo if pd.notna(ird) else None

            cp1, cp2, cp3 = st.columns(3)
            cp1.metric(
                "Grupo de comparação",
                f"{n_grupo} municípios",
                help=f"Municípios com {faixa_icg} e {faixa_porte} (redes municipais). "
                     f"Porte medido em {ano_porte}."
            )
            cp2.metric(
                "Posição do seu município",
                f"{posicao}º de {n_grupo}",
                help="1º lugar = maior regularidade dos professores dentro do grupo."
            )
            cp3.metric(
                "Média do grupo",
                formatar_br(media_grupo),
                delta=(f"{dif_grupo:+.3f}".replace(".", ",") if dif_grupo is not None else None),
                help="Diferença entre o IRD do seu município e a média dos municípios parecidos."
            )

            pct_frente = (n_grupo - posicao) / (n_grupo - 1) * 100 if n_grupo > 1 else 0
            if posicao <= max(1, int(n_grupo * 0.25)):
                msg = (f"**{municipio_label} está entre os 25% melhores do seu grupo.** "
                       "Contexto parecido, resultado acima — vale documentar o que a rede faz de diferente.")
            elif dif_grupo is not None and dif_grupo < 0:
                msg = (f"**{municipio_label} está abaixo da média de municípios parecidos** "
                       f"(à frente de apenas {pct_frente:.0f}% do grupo). "
                       "Como o contexto é semelhante, a diferença dificilmente se explica por porte ou complexidade — "
                       "há espaço real de melhoria na retenção dos professores.")
            else:
                msg = (f"**{municipio_label} está próximo da média de municípios parecidos** "
                       f"(à frente de {pct_frente:.0f}% do grupo).")
            st.markdown(msg)

            fig_par = go.Figure()
            fig_par.add_trace(go.Histogram(
                x=pares["IRD"], nbinsx=30,
                marker_color="#b8cfe8", name="Municípios do grupo"
            ))
            if pd.notna(ird):
                fig_par.add_vline(x=float(ird), line_color="#c0392b", line_width=3,
                                  annotation_text=municipio_label,
                                  annotation_position="top")
            fig_par.add_vline(x=float(media_grupo), line_dash="dash", line_color="#333",
                              annotation_text="média do grupo",
                              annotation_position="bottom right")
            fig_par.update_layout(
                height=280, showlegend=False,
                margin=dict(l=20, r=20, t=30, b=20),
                xaxis_title="Regularidade dos professores (0 a 5)",
                yaxis_title="Nº de municípios"
            )
            st.plotly_chart(fig_par, use_container_width=True)

            with st.expander("🏅 Quem são os destaques do seu grupo? (para trocar experiências)"):
                top5 = pares.head(5)[["NO_MUNICIPIO", "SG_UF", "IRD", "N_ESCOLAS"]].copy()
                top5["IRD"] = top5["IRD"].round(3)
                top5 = top5.rename(columns={
                    "NO_MUNICIPIO": "Município", "SG_UF": "Estado",
                    "IRD": "Regularidade (IRD)", "N_ESCOLAS": "Escolas municipais"
                })
                st.dataframe(top5, use_container_width=True, hide_index=True)
                st.caption(
                    "Municípios com contexto parecido e melhor resultado são a melhor "
                    "fonte de práticas replicáveis — mais útil que comparar com capitais "
                    "ou redes de porte muito diferente."
                )
            if ano_porte != ano_ref:
                st.caption(
                    f"Nota: o porte da rede (nº de escolas) foi medido em {ano_porte}, "
                    f"ano mais próximo com dados de escolas disponíveis."
                )

    st.markdown("---")
    st.markdown("### Evolução da regularidade dos professores")

    ird_nac    = df.groupby("ANO")["IRD"].mean().reset_index().rename(columns={"IRD":"Média Brasil"})
    ird_uf_ano = (df[df["SG_UF"] == uf_sel].groupby("ANO")["IRD"].mean()
                  .reset_index().rename(columns={"IRD":f"Média {uf_sel}"}))
    df_evo = df_mun[["ANO","IRD"]].rename(columns={"IRD":municipio_label})
    df_evo = df_evo.merge(ird_nac, on="ANO", how="left").merge(ird_uf_ano, on="ANO", how="left")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_evo["ANO"], y=df_evo[municipio_label],
        name=municipio_label, line=dict(color=cor, width=3),
        mode="lines+markers", marker_size=8))
    fig.add_trace(go.Scatter(x=df_evo["ANO"], y=df_evo["Média Brasil"],
        name="Média Brasil", line=dict(color="#aaa", dash="dash", width=1.5)))
    fig.add_trace(go.Scatter(x=df_evo["ANO"], y=df_evo[f"Média {uf_sel}"],
        name=f"Média {uf_sel}", line=dict(color="#e67e22", dash="dot", width=1.5)))
    fig.update_layout(height=380, margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", y=-0.2),
        yaxis=dict(title="Regularidade (0 a 5)", range=[0, 5.2]),
        xaxis_title="Ano")
    sombrear_pandemia(fig)
    st.plotly_chart(fig, use_container_width=True)

    render_tendencia(tendencia)

    st.markdown("### Série histórica completa")
    df_tab = df_mun[["ANO","IRD","ATU","AFD","IED","ICG"]].copy()
    df_tab = df_tab.rename(columns={"ANO":"Ano","IRD":"Regularidade (0-5)",
        "ATU":"Alunos/turma","AFD":"Formação (%)","IED":"Sobrecarga (%)","ICG":"Complexidade"})
    for col in df_tab.columns[1:]:
        df_tab[col] = df_tab[col].apply(lambda x: formatar_br(x, 1))
    st.dataframe(df_tab.set_index("Ano"), use_container_width=True)

    st.markdown("---")

    def gerar_relatorio_municipio():
        rows = ""
        df_h = df_mun[["ANO","IRD","ATU","AFD","IED","ICG"]].copy()
        df_h["VAR"] = df_h["IRD"].diff()
        for _, r in df_h.iterrows():
            var     = formatar_br(r["VAR"]) if pd.notna(r["VAR"]) else "—"
            cor_var = "#27ae60" if pd.notna(r["VAR"]) and r["VAR"] > 0 else "#c0392b" if pd.notna(r["VAR"]) and r["VAR"] < 0 else "#333"
            rows += (f"<tr><td>{int(r['ANO'])}</td><td>{formatar_br(r['IRD'])}</td>"
                     f"<td style='color:{cor_var}'>{var}</td><td>{formatar_br(r['ATU'],1)}</td>"
                     f"<td>{formatar_br(r['AFD'],1)}%</td><td>{formatar_br(r['IED'],1)}%</td>"
                     f"<td>{formatar_br(r['ICG'],1)}</td></tr>")
        ori_html = "".join([
            f"<div style='display:flex;gap:12px;align-items:flex-start;margin-bottom:8px;'>"
            f"<div style='min-width:22px;height:22px;background:{cor};border-radius:50%;"
            f"display:flex;align-items:center;justify-content:center;color:white;"
            f"font-size:11px;font-weight:bold;'>{i}</div>"
            f"<p style='margin:0;font-size:13px;'>{o}</p></div>"
            for i, o in enumerate(orientacoes, 1)
        ])
        tend_html = ""
        if tendencia:
            tend_html = (
                f"<div style='border-left:4px solid {tendencia['cor_borda']};"
                f"background:{tendencia['cor_fundo']};padding:10px 14px;"
                f"border-radius:0 6px 6px 0;margin-bottom:1rem;'>"
                f"<strong>{tendencia['icone']} Tendência histórica</strong><br>"
                f"<span style='font-size:13px;'>{tendencia['texto']}</span>"
                + (f"<br><span style='color:#c0392b;font-size:12px;'>"
                   f"⚠️ Ruptura detectada em {tendencia['ano_ruptura']}.</span>"
                   if tendencia.get("ruptura") else "")
                + "</div>"
            )
        return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>RegDoc — {municipio_label}</title>
<style>
  body{{font-family:Arial,sans-serif;padding:2rem;color:#222;max-width:900px;margin:0 auto;}}
  .header{{background:#1a3a5c;color:white;padding:1.5rem 2rem;border-radius:10px;
           margin-bottom:1.5rem;display:flex;justify-content:space-between;align-items:flex-start;}}
  .header h1{{margin:0;font-size:1.2rem;color:white;}}
  .header p{{margin:0.3rem 0 0;font-size:0.85rem;color:#b8cfe8;}}
  .grid2{{display:grid;grid-template-columns:1fr 2fr;gap:1rem;margin-bottom:1.5rem;}}
  .ird-box{{background:{cor}22;border:2px solid {cor};border-radius:10px;padding:1.5rem;text-align:center;}}
  .ird-num{{font-size:3rem;font-weight:bold;color:{cor};margin:0;}}
  .ird-label{{font-size:0.85rem;color:{cor};margin:0;}}
  .ird-sit{{font-size:1.1rem;font-weight:bold;color:{cor};margin:0.5rem 0 0;}}
  .metrics{{display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;}}
  .metric{{background:#f5f5f5;border-radius:8px;padding:0.8rem;text-align:center;}}
  .metric .val{{font-size:1.4rem;font-weight:bold;color:#1a3a5c;margin:0;}}
  .metric .lbl{{font-size:0.75rem;color:#777;margin:0;}}
  table{{width:100%;border-collapse:collapse;font-size:13px;}}
  th{{background:#1a3a5c;color:white;padding:8px;text-align:left;}}
  td{{padding:7px 8px;border-bottom:1px solid #eee;}}
  .section{{margin-bottom:1.5rem;}}
  .section h2{{font-size:1rem;color:#1a3a5c;border-bottom:2px solid {cor};padding-bottom:0.3rem;}}
  .alert-box{{border:1px solid {cor};border-radius:8px;padding:1rem;background:{cor}11;}}
  .footer{{text-align:center;font-size:11px;color:#aaa;margin-top:2rem;border-top:1px solid #eee;padding-top:1rem;}}
</style></head><body>
<div class="header">
  <div>
    <p style="margin:0;font-size:11px;color:#b8cfe8;text-transform:uppercase;">Relatório RegDoc — Município</p>
    <h1>{municipio_label} · {uf_sel}</h1><p>Ano de referência: {ano_ref}</p>
  </div>
  <div style="font-size:0.8rem;color:#b8cfe8;text-align:right;">Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
</div>
<div class="grid2">
  <div class="ird-box">
    <p class="ird-label">Regularidade dos professores (0 a 5)</p>
    <p class="ird-num">{formatar_br(ird)}</p><p class="ird-sit">● {situacao}</p>
  </div>
  <div class="metrics">
    <div class="metric"><p class="val">{formatar_br(media_ird_nac)}</p><p class="lbl">Média nacional</p></div>
    <div class="metric"><p class="val">{formatar_br(media_ird_uf)}</p><p class="lbl">Média {uf_sel}</p></div>
    <div class="metric"><p class="val">{formatar_br(linha_atual.get('ATU'),1)}</p><p class="lbl">Alunos por turma</p></div>
    <div class="metric"><p class="val">{formatar_br(linha_atual.get('AFD'),1)}%</p><p class="lbl">Formação adequada</p></div>
  </div>
</div>
<p style="font-size:13px;margin-bottom:1rem;">{texto_sit}<br><strong>Variação:</strong> {texto_var}</p>
{tend_html}
<div class="section"><h2>Série histórica completa</h2>
  <table><thead><tr><th>Ano</th><th>Regularidade</th><th>Variação</th>
  <th>Alunos/turma</th><th>Formação (%)</th><th>Sobrecarga (%)</th><th>Complexidade</th></tr></thead>
  <tbody>{rows}</tbody></table>
</div>
<div class="section"><h2>O que fazer — situação de {situacao}</h2>
  <div class="alert-box">{ori_html}</div>
</div>
<div class="footer">RegDoc · Dados: Censo Escolar/Inep · retendoc.streamlit.app · {datetime.now().strftime('%d/%m/%Y')}</div>
</body></html>"""

    html = gerar_relatorio_municipio()
    st.download_button(
        label="📄 Baixar relatório deste município (HTML)",
        data=html.encode("utf-8"),
        file_name=f"regdoc_{co_mun}_{ano_ref}.html",
        mime="text/html"
    )
    st.caption("Abra o arquivo no navegador e use Ctrl+P para imprimir ou salvar em PDF.")

# ─────────────────────────────────────────────
# ABA 2 — Ranking de Escolas
# ─────────────────────────────────────────────
with aba2:
    st.markdown(f"### Escolas de {municipio_label} — {ano_ref}")
    st.caption(
        "Ordenadas da menor para a maior regularidade. "
        "Classificação: 🔴 Alerta = abaixo da média municipal · "
        "🟠 Atenção = abaixo da média nacional · "
        "🟢 Favorável = acima da média nacional."
    )

    tem_dep   = "NO_DEPENDENCIA" in df_esc.columns
    tem_etapa = "IN_FUND" in df_esc.columns

    # ── Busca por nome — selectbox com busca integrada ───────────────────
    filtros_ativos = []

    nomes_escolas = sorted(
        df_esc[df_esc["CO_MUNICIPIO"] == co_mun]["NO_ENTIDADE"]
        .dropna().unique().tolist()
    )
    opcoes_nome = ["Todas as escolas"] + nomes_escolas

    escola_nome_sel = st.selectbox(
        "🔎 Buscar escola pelo nome (digite para filtrar a lista)",
        options=opcoes_nome,
        index=0,
        key="busca_escola"
    )
    busca_nome = "" if escola_nome_sel == "Todas as escolas" else escola_nome_sel
    if busca_nome:
        filtros_ativos.append(f"Escola: {escola_nome_sel}")

    # ── Filtros adicionais (dependência e etapa) ───────────────────────────
    if tem_dep or tem_etapa:
        with st.expander("⚙️ Filtros adicionais — dependência e etapa de ensino", expanded=False):
            fc1, fc2 = st.columns(2)

            if tem_dep:
                deps_disp = sorted(
                    df_esc[df_esc["CO_MUNICIPIO"] == co_mun]["NO_DEPENDENCIA"]
                    .dropna().unique().tolist()
                )
                dep_sel = fc1.multiselect(
                    "Dependência administrativa",
                    options=deps_disp,
                    default=deps_disp,
                    help="Municipal, Estadual, Privada ou Federal"
                )
                if set(dep_sel) != set(deps_disp):
                    filtros_ativos.append(f"Dependência: {', '.join(dep_sel)}")
            else:
                dep_sel = None

            if tem_etapa:
                etapa_sel = fc2.multiselect(
                    "Etapa de ensino oferecida",
                    options=["Educação Infantil", "Ensino Fundamental", "Ensino Médio"],
                    default=[],
                    help="Vazio = todas as escolas."
                )
                if etapa_sel:
                    filtros_ativos.append(f"Etapa: {', '.join(etapa_sel)}")
            else:
                etapa_sel = []
    else:
        dep_sel   = None
        etapa_sel = []

    # ── Badge de filtros ativos ────────────────────────────────────────────
    if filtros_ativos:
        st.markdown(
            f"<div style='background:#eaf0fb; border-left:4px solid #1a3a5c; "
            f"padding:0.5rem 1rem; border-radius:0 6px 6px 0; margin-bottom:0.5rem; "
            f"font-size:0.85rem; color:#1a3a5c;'>"
            f"🔍 Filtros ativos: {' · '.join(filtros_ativos)}"
            f"</div>",
            unsafe_allow_html=True
        )

    # ── Carregar e filtrar dados ───────────────────────────────────────────
    df_esc_mun = df_esc[
        (df_esc["CO_MUNICIPIO"] == co_mun) & (df_esc["ANO"] == ano_ref)
    ].copy()

    total_mun = len(df_esc_mun)  # total antes de filtrar (para cobertura)

    # Filtro por nome (match exato via selectbox)
    if busca_nome:
        df_esc_mun = df_esc_mun[df_esc_mun["NO_ENTIDADE"] == busca_nome]

    # Filtro de dependência
    if tem_dep and dep_sel is not None:
        df_esc_mun = df_esc_mun[df_esc_mun["NO_DEPENDENCIA"].isin(dep_sel)]

    # Filtro de etapa
    if tem_etapa and etapa_sel:
        mapa_etapa = {
            "Educação Infantil":  "IN_INF",
            "Ensino Fundamental": "IN_FUND",
            "Ensino Médio":       "IN_MED",
        }
        mascara = pd.Series(False, index=df_esc_mun.index)
        for etapa in etapa_sel:
            col_etapa = mapa_etapa[etapa]
            if col_etapa in df_esc_mun.columns:
                mascara = mascara | (df_esc_mun[col_etapa] == 1)
        df_esc_mun = df_esc_mun[mascara]

    # ── Indicador de cobertura ─────────────────────────────────────────────
    if filtros_ativos and total_mun > 0:
        pct_cob = round(len(df_esc_mun) / total_mun * 100, 1)
        st.caption(
            f"ℹ️ Exibindo **{len(df_esc_mun)} de {total_mun} escolas** "
            f"do município ({pct_cob}% da rede) com os filtros aplicados."
        )

    if df_esc_mun.empty:
        st.info("Nenhuma escola encontrada com os filtros selecionados.")
    else:
        df_esc_rank = df_esc_mun.dropna(subset=["IRD"]).copy()
        n_sd = len(df_esc_mun) - len(df_esc_rank)

        CORES_ESC = {"Alerta":"#c0392b","Atenção":"#e67e22","Favorável":"#27ae60"}

        def classif_esc(v):
            if pd.isna(v):                                          return "Sem dados"
            if pd.notna(media_ird_nac) and v >= media_ird_nac:     return "Favorável"
            if pd.notna(ird) and v >= ird:                          return "Atenção"
            return "Alerta"

        ORDEM_ESC = {"Alerta":0,"Atenção":1,"Favorável":2,"Sem dados":3}

        df_esc_rank["RISCO"] = df_esc_rank["IRD"].apply(classif_esc)
        df_esc_rank = df_esc_rank.sort_values(
            ["RISCO","IRD"],
            key=lambda c: c.map(ORDEM_ESC) if c.name == "RISCO" else c
        ).reset_index(drop=True)

        # Cards
        contagem_esc = df_esc_rank["RISCO"].value_counts()
        total_esc    = len(df_esc_rank)
        n_alerta     = int(contagem_esc.get("Alerta", 0))
        n_atencao    = int(contagem_esc.get("Atenção", 0))
        n_favoravel  = int(contagem_esc.get("Favorável", 0))

        ce0, ce1, ce2, ce3 = st.columns(4)
        ce0.metric("Total de escolas", total_esc + n_sd)
        for col_ui, faixa, qtd in zip([ce1,ce2,ce3],
                                       ["Alerta","Atenção","Favorável"],
                                       [n_alerta, n_atencao, n_favoravel]):
            pct = qtd / total_esc * 100 if total_esc > 0 else 0
            c   = CORES_ESC[faixa]
            col_ui.markdown(f"""
            <div style="background:{c}22; border-left:5px solid {c};
                 padding:0.8rem 1rem; border-radius:6px; text-align:center;">
                <div style="font-size:1.8rem; font-weight:bold; color:{c};">{qtd}</div>
                <div style="font-size:0.85rem; color:#333;">{faixa}</div>
                <div style="font-size:0.8rem; color:#777;">{pct:.1f}%</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Banner
        if n_alerta > 0:
            st.error(
                f"⚠️ **{n_alerta} escola(s) em Alerta** — IRD abaixo da média municipal "
                f"({formatar_br(ird, 3)}). Acesse a página **Escola** para orientações específicas."
            )
        elif n_atencao > 0:
            st.warning(
                f"🔔 **{n_atencao} escola(s) em Atenção** — IRD abaixo da média nacional "
                f"({formatar_br(media_ird_nac, 3)}). Monitore a tendência dessas unidades."
            )
        else:
            st.success(
                f"✅ Todas as escolas com IRD acima da média nacional ({formatar_br(media_ird_nac, 3)})."
            )

        st.markdown("<br>", unsafe_allow_html=True)
        rm1, rm2 = st.columns(2)
        with rm1:
            st.markdown(f"""
            <div style="background:#f7f9fc; border:1px solid #dde4ed; border-radius:10px;
                 padding:1rem 1.4rem; text-align:center;">
                <p style="margin:0; font-size:0.8rem; color:#5a7a9a; font-weight:600;
                   text-transform:uppercase; letter-spacing:0.04em;">Média nacional — {ano_ref}</p>
                <p style="margin:0; font-size:2rem; font-weight:bold; color:#1a3a5c;">{formatar_br(media_ird_nac, 3)}</p>
            </div>""", unsafe_allow_html=True)
        with rm2:
            st.markdown(f"""
            <div style="background:{cor}18; border:2px solid {cor}; border-radius:10px;
                 padding:1rem 1.4rem; text-align:center;">
                <p style="margin:0; font-size:0.8rem; color:{cor}; font-weight:600;
                   text-transform:uppercase; letter-spacing:0.04em;">Média {municipio_label} — {ano_ref}</p>
                <p style="margin:0; font-size:2rem; font-weight:bold; color:{cor};">{formatar_br(ird, 3)}</p>
                <p style="margin:0; font-size:0.95rem; font-weight:bold; color:{cor};">● {situacao}</p>
            </div>""", unsafe_allow_html=True)

        # ── Tabela com cores do semáforo ───────────────────────────────────
        cols_base  = ["NO_ENTIDADE","IRD","RISCO"]
        if tem_dep:
            cols_base.append("NO_DEPENDENCIA")
        cols_extra = [c for c in ["ICG","ATU","AFD","IED"] if c in df_esc_rank.columns]

        df_tab_esc = df_esc_rank[cols_base + cols_extra].copy()
        fmt_esc = {"IRD":3,"ICG":2,"ATU":1,"AFD":1,"IED":1}
        for col, dec in fmt_esc.items():
            if col in df_tab_esc.columns:
                df_tab_esc[col] = df_tab_esc[col].apply(
                    lambda x: formatar_br(x, dec) if pd.notna(x) else "—"
                )
        df_tab_esc = df_tab_esc.rename(columns={
            "NO_ENTIDADE":    "Escola",
            "IRD":            "Regularidade",
            "RISCO":          "Situação",
            "NO_DEPENDENCIA": "Dependência",
            "ICG":            "Complexidade",
            "ATU":            "Alunos/turma",
            "AFD":            "Formação (%)",
            "IED":            "Esforço docente (%)",
        })
        df_tab_esc.index = df_tab_esc.index + 1
        df_tab_esc.index.name = "Posição"

        COR_FUNDO = {
            "Alerta":    "background-color: #fde8e8; color: #c0392b; font-weight: 600;",
            "Atenção":   "background-color: #fef3e2; color: #e67e22; font-weight: 600;",
            "Favorável": "background-color: #e8f8f0; color: #27ae60; font-weight: 600;",
            "Sem dados": "background-color: #f5f5f5; color: #aaa;",
        }
        df_styled = df_tab_esc.style.map(
            lambda v: COR_FUNDO.get(v, ""), subset=["Situação"]
        )
        st.dataframe(df_styled, use_container_width=True)

        # ── Downloads ──────────────────────────────────────────────────────
        dl1, dl2, _ = st.columns([1, 1, 2])

        with dl1:
            csv_esc = df_tab_esc.to_csv(index=True).encode("utf-8-sig")
            st.download_button(
                label="📥 Baixar ranking (CSV)",
                data=csv_esc,
                file_name=f"ranking_escolas_{municipio_label}_{ano_ref}.csv",
                mime="text/csv",
            )

        with dl2:
            # Relatório HTML do ranking
            rows_html = ""
            for pos, row in enumerate(df_tab_esc.itertuples(), start=1):
                vals = list(row)[1:]
                sit  = vals[1] if len(vals) > 1 else ""
                cor_sit = ("#fde8e8" if "Alerta" in str(sit)
                           else "#fef3e2" if "Atenção" in str(sit)
                           else "#e8f8f0" if "Favorável" in str(sit) else "#f5f5f5")
                cor_txt = ("#c0392b" if "Alerta" in str(sit)
                           else "#e67e22" if "Atenção" in str(sit)
                           else "#27ae60" if "Favorável" in str(sit) else "#555")
                cells = f"<td><b>{pos}</b></td>"
                for v in vals:
                    if v == sit:
                        cells += f"<td style='background:{cor_sit};color:{cor_txt};font-weight:600'>{v}</td>"
                    else:
                        cells += f"<td>{v}</td>"
                rows_html += f"<tr>{cells}</tr>"

            hdrs_html = "<th>Posição</th>" + "".join(f"<th>{c}</th>" for c in df_tab_esc.columns)
            filtros_txt  = " · ".join(filtros_ativos) if filtros_ativos else "Todas as escolas"
            data_hora_rank = datetime.now().strftime("%d/%m/%Y %H:%M")
            data_curta_rank = datetime.now().strftime("%d/%m/%Y")

            html_rank = f"""<!DOCTYPE html>
<html lang='pt-BR'><head><meta charset='utf-8'>
<title>Ranking — {municipio_label} {ano_ref}</title>
<style>
  body{{font-family:Arial,sans-serif;padding:2rem;color:#222;max-width:1100px;margin:0 auto;}}
  .header{{background:#1a3a5c;color:white;padding:1.5rem 2rem;border-radius:10px;
           margin-bottom:1.5rem;display:flex;justify-content:space-between;align-items:flex-start;}}
  .header h1{{margin:0;font-size:1.2rem;color:white;}}
  .header p{{margin:0.3rem 0 0;font-size:0.85rem;color:#b8cfe8;}}
  .cards{{display:flex;gap:12px;flex-wrap:wrap;margin:1rem 0;}}
  .card{{padding:10px 18px;border-radius:8px;background:#f0f3f4;text-align:center;min-width:80px;}}
  .card-num{{font-size:1.8rem;font-weight:bold;}}
  .filtros{{background:#eaf0fb;border-left:4px solid #1a3a5c;padding:8px 14px;
            border-radius:0 6px 6px 0;margin-bottom:1rem;font-size:0.85rem;color:#1a3a5c;}}
  table{{width:100%;border-collapse:collapse;font-size:12px;margin-top:1rem;}}
  th{{background:#1a3a5c;color:white;padding:8px;text-align:left;}}
  td{{padding:7px 8px;border-bottom:1px solid #eee;}}
  tr:nth-child(even){{background:#f9f9f9;}}
  .footer{{text-align:center;font-size:11px;color:#aaa;margin-top:2rem;
           border-top:1px solid #eee;padding-top:1rem;}}
  @media print{{body{{padding:1rem;}}}}
</style></head><body>
<div class='header'>
  <div>
    <p style='margin:0;font-size:11px;color:#b8cfe8;text-transform:uppercase;'>Ranking de Escolas — RegDoc</p>
    <h1>{municipio_label} · {uf_sel} · {ano_ref}</h1>
  </div>
  <div style='font-size:0.8rem;color:#b8cfe8;text-align:right;'>Gerado em {data_hora_rank}</div>
</div>
<div class='cards'>
  <div class='card'><div class='card-num'>{total_esc}</div><div>Total</div></div>
  <div class='card'><div class='card-num' style='color:#c0392b'>{n_alerta}</div><div>🔴 Alerta</div></div>
  <div class='card'><div class='card-num' style='color:#e67e22'>{n_atencao}</div><div>🟠 Atenção</div></div>
  <div class='card'><div class='card-num' style='color:#27ae60'>{n_favoravel}</div><div>🟢 Favorável</div></div>
</div>
<div class='filtros'>🔍 Filtros aplicados: {filtros_txt}</div>
<table><thead><tr>{hdrs_html}</tr></thead><tbody>{rows_html}</tbody></table>
<div class='footer'>
  RegDoc · Dados: Censo Escolar/INEP · retendoc.streamlit.app · {data_curta_rank}<br>
  Abra no navegador e use Ctrl+P para imprimir ou salvar em PDF.
</div></body></html>"""

            st.download_button(
                label="📄 Baixar relatório (HTML)",
                data=html_rank.encode("utf-8"),
                file_name=f"ranking_{municipio_label}_{ano_ref}.html",
                mime="text/html",
            )

        # ── Exportação em lote — escolas em Alerta ─────────────────────────
        if n_alerta > 0:
            st.markdown("<br>", unsafe_allow_html=True)

            def gerar_zip_alerta():
                import zipfile
                import io as _io

                df_alerta = df_esc_rank[df_esc_rank["RISCO"] == "Alerta"].copy()
                buffer = _io.BytesIO()

                with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for _, r in df_alerta.iterrows():
                        nome_esc = r["NO_ENTIDADE"]
                        ird_esc  = r["IRD"]
                        icg_esc  = r.get("ICG")
                        atu_esc  = r.get("ATU")
                        afd_esc  = r.get("AFD")
                        ied_esc  = r.get("IED")
                        dep_esc  = r.get("NO_DEPENDENCIA", "—") if tem_dep else "—"

                        html_individual = f"""<!DOCTYPE html>
<html lang='pt-BR'><head><meta charset='utf-8'>
<title>{nome_esc} — {ano_ref}</title>
<style>
  body{{font-family:Arial,sans-serif;padding:2rem;color:#222;max-width:700px;margin:0 auto;}}
  .header{{background:#1a3a5c;color:white;padding:1.2rem 1.6rem;border-radius:10px;margin-bottom:1.2rem;}}
  .header h1{{margin:0;font-size:1.1rem;}}
  .header p{{margin:0.3rem 0 0;font-size:0.8rem;color:#b8cfe8;}}
  .ird-box{{background:#fde8e8;border:2px solid #c0392b;border-radius:10px;
            padding:1.2rem;text-align:center;margin-bottom:1rem;}}
  .ird-num{{font-size:2.4rem;font-weight:bold;color:#c0392b;margin:0;}}
  table{{width:100%;border-collapse:collapse;font-size:13px;margin-top:0.8rem;}}
  th{{background:#1a3a5c;color:white;padding:7px;text-align:left;}}
  td{{padding:6px 7px;border-bottom:1px solid #eee;}}
</style></head><body>
<div class='header'>
  <h1>{nome_esc}</h1>
  <p>{municipio_label} · {uf_sel} · {ano_ref} · Dependência: {dep_esc}</p>
</div>
<div class='ird-box'>
  <p style='margin:0;font-size:0.85rem;color:#c0392b;'>Regularidade dos professores</p>
  <p class='ird-num'>{formatar_br(ird_esc, 3)}</p>
  <p style='margin:0;font-weight:bold;color:#c0392b;'>● Alerta</p>
</div>
<table>
  <tr><th>Indicador</th><th>Valor</th></tr>
  <tr><td>Complexidade (ICG)</td><td>{formatar_br(icg_esc, 2) if pd.notna(icg_esc) else "—"}</td></tr>
  <tr><td>Alunos/turma (ATU)</td><td>{formatar_br(atu_esc, 1) if pd.notna(atu_esc) else "—"}</td></tr>
  <tr><td>Formação adequada (AFD)</td><td>{formatar_br(afd_esc, 1) if pd.notna(afd_esc) else "—"}%</td></tr>
  <tr><td>Esforço docente (IED)</td><td>{formatar_br(ied_esc, 1) if pd.notna(ied_esc) else "—"}%</td></tr>
</table>
<p style='font-size:11px;color:#aaa;margin-top:1.5rem;'>
  RegDoc · Censo Escolar/INEP · retendoc.streamlit.app<br>
  Para orientações detalhadas por perfil, acesse a página Escola no RegDoc.
</p>
</body></html>"""
                        nome_arquivo = "".join(
                            c for c in nome_esc if c.isalnum() or c in " -_"
                        ).strip().replace(" ", "_")[:60]
                        zf.writestr(f"{nome_arquivo}.html", html_individual)

                buffer.seek(0)
                return buffer

            zip_buffer = gerar_zip_alerta()
            st.download_button(
                label=f"📦 Baixar relatórios das {n_alerta} escola(s) em Alerta (ZIP)",
                data=zip_buffer,
                file_name=f"escolas_alerta_{municipio_label}_{ano_ref}.zip",
                mime="application/zip",
            )
            st.caption(
                "Um arquivo HTML individual por escola em Alerta — "
                "pronto para levar em visitas técnicas ou anexar ao plano de ação."
            )

        if n_sd > 0:
            st.caption(
                f"ℹ️ {n_sd} escola(s) sem IRD disponível para {ano_ref} — "
                "não incluídas no ranking mas contabilizadas no total."
            )
        if tem_dep or tem_etapa:
            st.caption(
                "ℹ️ Dependência administrativa e etapas de ensino baseadas no Censo Escolar 2022 "
                "como referência para toda a série histórica."
            )

st.markdown("---")
st.caption("RegDoc · Fonte: Censo Escolar / INEP · Atualização anual mediante publicação do Censo Escolar.")
st.caption("© 2026 Joelma Barcellos Santanna · Doutorado Profissional em Administração, FUCAPE Business School.")

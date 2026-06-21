import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from utils.dados import carregar_municipal, carregar_escola, formatar_br, aplicar_estilo_global

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

# ── Tendência ──────────────────────────────────────────────────────────────────
def classificar_tendencia(df_mun_filtrado, ano_ref):
    hist = (df_mun_filtrado[df_mun_filtrado["ANO"] <= ano_ref]
            .sort_values("ANO").dropna(subset=["IRD"]))
    if len(hist) < 3:
        return None
    anos    = hist["ANO"].values.astype(float)
    valores = hist["IRD"].values
    slope   = np.polyfit(anos - anos.mean(), valores, 1)[0]
    variacao = valores[-1] - valores[0]
    ruptura = False; ano_ruptura = None
    for i in range(1, len(hist)):
        if valores[i] - valores[i-1] <= -0.5:
            ruptura = True; ano_ruptura = int(hist["ANO"].iloc[i]); break
    if slope <= -0.15:
        return {"icone":"📉","cor_fundo":"#fdedec","cor_borda":"#c0392b",
            "texto":f"Em queda acelerada — perdeu {abs(variacao):.2f} pontos desde "
                    f"{int(hist['ANO'].iloc[0])} ({slope:.2f} pts/ano). Requer ação imediata.",
            "ruptura":ruptura,"ano_ruptura":ano_ruptura}
    elif slope <= -0.05:
        return {"icone":"↘️","cor_fundo":"#fef9e7","cor_borda":"#f39c12",
            "texto":f"Tendência de queda desde {int(hist['ANO'].iloc[0])} "
                    f"({variacao:+.2f} pontos acumulados). "
                    "Monitorar com atenção antes que atinja nível crítico.",
            "ruptura":ruptura,"ano_ruptura":ano_ruptura}
    elif slope < 0.05:
        return {"icone":"➡️","cor_fundo":"#f0f4f8","cor_borda":"#7f8c8d",
            "texto":f"Estável desde {int(hist['ANO'].iloc[0])} (variação de {variacao:+.2f} pontos). "
                    + ("Estabilidade positiva — IRD em nível satisfatório." if valores[-1] >= 3.0
                       else "Estabilidade preocupante — IRD estagnado abaixo de 3,0."),
            "ruptura":ruptura,"ano_ruptura":ano_ruptura}
    elif slope < 0.15:
        return {"icone":"↗️","cor_fundo":"#eafaf1","cor_borda":"#27ae60",
            "texto":f"Em recuperação desde {int(hist['ANO'].iloc[0])} "
                    f"(+{variacao:.2f} pontos acumulados). "
                    "Ações de retenção docente parecem estar surtindo efeito.",
            "ruptura":False,"ano_ruptura":None}
    else:
        return {"icone":"📈","cor_fundo":"#eafaf1","cor_borda":"#27ae60",
            "texto":f"Melhora expressiva desde {int(hist['ANO'].iloc[0])} "
                    f"(+{variacao:.2f} pontos, média de +{slope:.2f} pts/ano). "
                    "Documentar as práticas que estão gerando esse resultado.",
            "ruptura":False,"ano_ruptura":None}

def render_tendencia(tendencia):
    if tendencia is None:
        return
    ruptura_html = ""
    if tendencia.get("ruptura"):
        ruptura_html = (
            f"<br><span style='color:#c0392b; font-size:0.85rem;'>"
            f"⚠️ Ruptura detectada em {tendencia['ano_ruptura']}: "
            f"queda brusca neste ano. Verificar causa.</span>"
        )
    st.markdown(
        f"<div class='tendencia-box' style='background:{tendencia['cor_fundo']}; "
        f"border-left:4px solid {tendencia['cor_borda']};'>"
        f"<span style='font-size:1.3rem;'>{tendencia['icone']}</span>"
        f"<div><strong style='color:{tendencia['cor_borda']};'>Tendência histórica</strong>"
        f"<br><span style='color:#333;'>{tendencia['texto']}</span>"
        f"{ruptura_html}</div></div>",
        unsafe_allow_html=True
    )

# ── Carregar dados ─────────────────────────────────────────────────────────────
st.title("🔍 Análise por Município")
st.caption("Evolução da regularidade dos professores e comparação com médias nacionais e estaduais")

df = carregar_municipal()

@st.cache_data(show_spinner=False)
def load_escolas():
    return carregar_escola()

df_esc = load_escolas()

# ── Filtros compartilhados (fora das abas) ────────────────────────────────────
col1, col2 = st.columns([1, 2])
with col1:
    ufs = sorted(df["SG_UF"].dropna().unique())
    uf_sel = st.selectbox("Estado", ufs, index=ufs.index("ES") if "ES" in ufs else 0)
with col2:
    municipios_uf = (
        df[df["SG_UF"] == uf_sel][["CO_MUNICIPIO","NO_MUNICIPIO"]]
        .drop_duplicates().sort_values("NO_MUNICIPIO")
    )
    municipio_label = st.selectbox("Município", municipios_uf["NO_MUNICIPIO"].tolist())

co_mun  = municipios_uf[municipios_uf["NO_MUNICIPIO"] == municipio_label]["CO_MUNICIPIO"].iloc[0]
df_mun  = df[df["CO_MUNICIPIO"] == co_mun].sort_values("ANO").copy()

if df_mun.empty:
    st.warning("Sem dados para este município.")
    st.stop()

ano_ref = st.selectbox("Ano de referência", sorted(df_mun["ANO"].unique()),
                       index=len(df_mun["ANO"].unique()) - 1)

# Variáveis compartilhadas entre as duas abas
linha_atual   = df_mun[df_mun["ANO"] == ano_ref].iloc[0]
media_ird_nac = df[df["ANO"] == ano_ref]["IRD"].mean()
media_ird_uf  = df[(df["ANO"] == ano_ref) & (df["SG_UF"] == uf_sel)]["IRD"].mean()
ird           = linha_atual["IRD"]

# Situação e orientações
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
# ABA 1 — conteúdo original intacto
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

    df_esc_mun = df_esc[
        (df_esc["CO_MUNICIPIO"] == co_mun) & (df_esc["ANO"] == ano_ref)
    ].copy()

    if df_esc_mun.empty:
        st.info("Dados por escola não disponíveis para este município e ano.")
    else:
        df_esc_rank = df_esc_mun.dropna(subset=["IRD"]).copy()
        n_sd = len(df_esc_mun) - len(df_esc_rank)

        CORES_ESC = {"Alerta":"#c0392b","Atenção":"#e67e22","Favorável":"#27ae60"}

        def classif_esc(v):
            if pd.isna(v):             return "Sem dados"
            if pd.notna(media_ird_nac) and v >= media_ird_nac: return "Favorável"
            if pd.notna(ird) and v >= ird:                      return "Atenção"
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

        # Referências
        st.markdown("<br>", unsafe_allow_html=True)
        rm1, rm2 = st.columns(2)
        rm1.metric(f"Média nacional — {ano_ref}", formatar_br(media_ird_nac, 3))
        rm2.metric(f"Média {municipio_label} — {ano_ref}", formatar_br(ird, 3))

        # Tabela
        cols_base  = ["NO_ENTIDADE","IRD","RISCO"]
        cols_extra = [c for c in ["ICG","ATU","AFD","IED"] if c in df_esc_rank.columns]

        df_tab_esc = df_esc_rank[cols_base + cols_extra].copy()
        fmt_esc = {"IRD":3,"ICG":2,"ATU":1,"AFD":1,"IED":1}
        for col, dec in fmt_esc.items():
            if col in df_tab_esc.columns:
                df_tab_esc[col] = df_tab_esc[col].apply(
                    lambda x: formatar_br(x, dec) if pd.notna(x) else "—"
                )
        df_tab_esc = df_tab_esc.rename(columns={
            "NO_ENTIDADE":"Escola","IRD":"Regularidade","ICG":"Complexidade",
            "ATU":"Alunos/turma","AFD":"Formação (%)","IED":"Esforço docente (%)","RISCO":"Situação"
        })
        df_tab_esc.index = df_tab_esc.index + 1
        df_tab_esc.index.name = "Posição"

        st.dataframe(df_tab_esc, use_container_width=True)

        col_csv, _ = st.columns([1, 3])
        with col_csv:
            csv_esc = df_tab_esc.to_csv(index=True).encode("utf-8-sig")
            st.download_button(
                label="📥 Baixar ranking (CSV)",
                data=csv_esc,
                file_name=f"ranking_escolas_{municipio_label}_{ano_ref}.csv",
                mime="text/csv",
            )

        if n_sd > 0:
            st.caption(
                f"ℹ️ {n_sd} escola(s) sem IRD disponível para {ano_ref} — "
                "não incluídas no ranking mas contabilizadas no total."
            )

st.markdown("---")
st.caption("RegDoc · Fonte: Censo Escolar / INEP · Atualização anual mediante publicação do Censo Escolar.")

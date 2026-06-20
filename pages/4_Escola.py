import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from utils.dados import carregar_escola, carregar_municipal, formatar_br, aplicar_estilo_global

st.set_page_config(page_title="Escola · RegDoc", layout="wide")

st.markdown("""
<style>
.ird-destaque { border-radius:12px; padding:1.5rem 2rem; margin-bottom:1rem; text-align:center; }
.card-ind { border:1px solid #dde4ed; border-radius:8px; padding:1rem 1.2rem; background:#f7f9fc; margin-bottom:0.5rem; }
.card-ind h5 { margin:0 0 0.3rem 0; color:#1a3a5c; font-size:1rem; display:flex; align-items:center; gap:6px; }
.card-ind .valor { font-size:1.6rem; font-weight:bold; color:#1a3a5c; }
.card-ind .interp { font-size:0.85rem; color:#555; margin-top:0.3rem; }
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
.tendencia-box { border-radius:8px; padding:0.8rem 1.2rem; margin:0.5rem 0 1rem 0;
    font-size:0.9rem; display:flex; align-items:flex-start; gap:0.8rem; }
</style>
""", unsafe_allow_html=True)

# ── Tooltips enriquecidos ──────────────────────────────────────────────────────
TOOLTIPS = {
    "IRD": (
        "O IRD — Indicador de Regularidade do Docente — mede se os mesmos professores "
        "continuam na escola de um ano para o outro. "
        "Calculado pelo INEP a partir do Censo Escolar, observando a presença de cada "
        "professor nos últimos 5 anos consecutivos. "
        "Cada docente recebe uma pontuação que considera: total de anos na escola, "
        "atuação em anos mais recentes (peso maior) e continuidade sem interrupção. "
        "O IRD da escola é a média dos IRDs individuais de todos os seus docentes. "
        "Escala de 0 a 5 — quanto maior, mais estável é o corpo docente. "
        "Classificação INEP: abaixo de 2 = baixa regularidade; 2 a 3 = média-baixa; "
        "3 a 4 = média-alta; 4 a 5 = alta regularidade. "
        "Fonte: Nota Técnica INEP nº 11/2015."
    ),
    "ATU": (
        "ATU — Média de Alunos por Turma. "
        "Mede a média de estudantes matriculados por turma no Ensino Fundamental. "
        "Calculado como: total de matrículas ÷ total de turmas, por etapa e turno. "
        "Turmas superlotadas aumentam a sobrecarga do professor e estão associadas "
        "a maior rotatividade docente — especialmente quando combinadas com alta "
        "complexidade de gestão. "
        "Parâmetros de referência: EF I = 20–25 alunos/turma; "
        "EF II = 25–30; Ensino Médio = 30–35. "
        "Valores muito baixos podem indicar turmas ociosas; muito altos, sobrecarga. "
        "Limitação: a média pode esconder grande variação entre turmas da mesma escola. "
        "Fonte: Censo Escolar/INEP."
    ),
    "AFD": (
        "AFD — Adequação da Formação Docente. "
        "Mede o percentual de professores que lecionam na área em que se formaram, "
        "conforme os requisitos da LDB. "
        "Classificação por grupo: Grupo 1 = formação superior na mesma área (adequado); "
        "Grupo 2 = licenciatura na disciplina (adequado); "
        "Grupo 3 = área diferente, sem licenciatura (parcialmente adequado); "
        "Grupos 4 e 5 = ensino médio ou fundamental (inadequado). "
        "O AFD da escola é o percentual de disciplinas nos Grupos 1 e 2. "
        "Quanto maior, mais qualificado e alinhado é o quadro docente. "
        "Limitação: baseia-se na declaração do professor no Censo — "
        "erros de preenchimento afetam o indicador. "
        "Fonte: Censo Escolar/INEP."
    ),
    "IED": (
        "IED — Indicador de Esforço Docente. "
        "Mede a complexidade da jornada de trabalho dos professores, considerando "
        "quantas escolas, turnos, disciplinas e alunos cada professor atende "
        "simultaneamente. Classifica o docente em 6 níveis (1 a 6). "
        "Atenção: o IED NÃO indica diretamente duplo vínculo empregatício — "
        "um professor pode ter IED alto atuando apenas em uma rede pública "
        "com muitas turmas. "
        "Valores altos sugerem jornada mais fragmentada, o que pode reduzir "
        "o vínculo do professor com a escola e contribuir para a rotatividade. "
        "Nível 1 = menor esforço (até 25 alunos, 1 turno, 1 escola); "
        "Nível 6 = maior esforço (mais de 400 alunos, múltiplos turnos e escolas). "
        "Fonte: Censo Escolar/INEP."
    ),
    "ICG": (
        "ICG — Indicador de Complexidade de Gestão da Escola. "
        "Mede o grau de desafio que a escola impõe ao seu gestor, combinando: "
        "porte (número de matrículas), número de turnos, etapas de ensino "
        "atendidas e modalidades (EJA, AEE, educação do campo). "
        "Escala de 1 a 6: quanto maior, mais complexa é a gestão da unidade. "
        "Nível 1 = escola pequena, uma etapa, um turno; "
        "Nível 6 = grande porte com máxima diversidade de etapas e modalidades. "
        "Escolas com ICG alto são mais vulneráveis à rotatividade docente — "
        "cada saída de professor gera impacto maior no funcionamento pedagógico. "
        "Limitação: escolas rurais multisseriadas podem ter ICG baixo apesar de "
        "elevada dificuldade pedagógica. "
        "Fonte: Censo Escolar/INEP."
    ),
}

def card_com_tooltip(titulo, sigla, valor, interp):
    tip = TOOLTIPS.get(sigla, "")
    st.markdown(f"""
    <div class="card-ind">
        <h5>
            {titulo}
            <span class="tooltip-wrap">
                <span class="info-icon">i</span>
                <span class="tip">{tip}</span>
            </span>
        </h5>
        <div class="valor">{valor}</div>
        <div class="interp">{interp}</div>
    </div>""", unsafe_allow_html=True)


# ── Sinalização de tendência ───────────────────────────────────────────────────
def classificar_tendencia(df_escola, ano_ref):
    """
    Analisa os últimos anos da série e retorna diagnóstico de tendência.
    Usa até 5 anos anteriores ao ano de referência.
    """
    hist = df_escola[df_escola["ANO"] <= ano_ref].sort_values("ANO").dropna(subset=["IRD"])

    if len(hist) < 3:
        return None

    anos   = hist["ANO"].values
    valores = hist["IRD"].values

    # Regressão linear simples
    x = anos.astype(float)
    slope = np.polyfit(x - x.mean(), valores, 1)[0]

    ultimo  = valores[-1]
    primeiro = valores[0]
    variacao = ultimo - primeiro
    n_anos   = len(anos)

    # Detectar ruptura: queda >= 0,5 em um único ano
    ruptura = False
    ano_ruptura = None
    for i in range(1, len(anos)):
        if valores[i] - valores[i-1] <= -0.5:
            ruptura = True
            ano_ruptura = int(anos[i])
            break

    if slope <= -0.15:
        return {
            "icone": "📉",
            "cor_fundo": "#fdedec",
            "cor_borda": "#c0392b",
            "texto": f"Em queda acelerada — perdeu {abs(variacao):.2f} pontos desde {int(anos[0])} "
                     f"({slope:.2f} pts/ano em média). Requer ação imediata.",
            "ruptura": ruptura,
            "ano_ruptura": ano_ruptura,
        }
    elif slope <= -0.05:
        return {
            "icone": "↘️",
            "cor_fundo": "#fef9e7",
            "cor_borda": "#f39c12",
            "texto": f"Tendência de queda desde {int(anos[0])} "
                     f"({variacao:+.2f} pontos acumulados). "
                     "Monitorar com atenção — se mantida, atingirá nível crítico.",
            "ruptura": ruptura,
            "ano_ruptura": ano_ruptura,
        }
    elif slope < 0.05:
        return {
            "icone": "➡️",
            "cor_fundo": "#f0f4f8",
            "cor_borda": "#7f8c8d",
            "texto": f"Estável desde {int(anos[0])} (variação de {variacao:+.2f} pontos). "
                     + ("Estabilidade positiva — IRD em nível satisfatório." if ultimo >= 3.0
                        else "Estabilidade preocupante — IRD estagnado abaixo de 3,0."),
            "ruptura": ruptura,
            "ano_ruptura": ano_ruptura,
        }
    elif slope < 0.15:
        return {
            "icone": "↗️",
            "cor_fundo": "#eafaf1",
            "cor_borda": "#27ae60",
            "texto": f"Em recuperação desde {int(anos[0])} "
                     f"(+{variacao:.2f} pontos acumulados). "
                     "Ações de retenção docente parecem estar surtindo efeito.",
            "ruptura": False,
            "ano_ruptura": None,
        }
    else:
        return {
            "icone": "📈",
            "cor_fundo": "#eafaf1",
            "cor_borda": "#27ae60",
            "texto": f"Melhora expressiva desde {int(anos[0])} "
                     f"(+{variacao:.2f} pontos, média de +{slope:.2f} pts/ano). "
                     "Documentar as práticas que estão gerando esse resultado.",
            "ruptura": False,
            "ano_ruptura": None,
        }


def render_tendencia(tendencia):
    if tendencia is None:
        return
    st.markdown(f"""
    <div class="tendencia-box"
         style="background:{tendencia['cor_fundo']}; border-left:4px solid {tendencia['cor_borda']};">
        <span style="font-size:1.3rem;">{tendencia['icone']}</span>
        <div>
            <strong style="color:{tendencia['cor_borda']};">Tendência histórica</strong><br>
            <span style="color:#333;">{tendencia['texto']}</span>
            {"<br><span style='color:#c0392b; font-size:0.85rem;'>⚠️ Ruptura detectada em "
             + str(tendencia['ano_ruptura'])
             + ": queda brusca neste ano. Verificar causa.</span>"
             if tendencia.get('ruptura') else ""}
        </div>
    </div>""", unsafe_allow_html=True)


# ── Início da página ───────────────────────────────────────────────────────────
aplicar_estilo_global()
st.title("🏫 Consulta por Escola")
st.caption("Regularidade dos professores e indicadores educacionais por escola")

df_esc = carregar_escola()
df_mun = carregar_municipal()

busca = st.text_input("🔎 Busque pelo nome da escola (mínimo 3 letras)", placeholder="Ex: Maria, EMEF, CMEI...")

col1, col2, col3 = st.columns([1, 2, 3])
with col1:
    ufs = sorted(df_esc["SG_UF"].dropna().unique())
    uf_sel = st.selectbox("Estado", ufs, index=ufs.index("ES") if "ES" in ufs else 0)
with col2:
    municipios = (df_esc[df_esc["SG_UF"] == uf_sel][["CO_MUNICIPIO","NO_MUNICIPIO"]]
        .drop_duplicates().sort_values("NO_MUNICIPIO"))
    mun_sel = st.selectbox("Município", municipios["NO_MUNICIPIO"].tolist())

co_mun = municipios[municipios["NO_MUNICIPIO"] == mun_sel]["CO_MUNICIPIO"].iloc[0]

with col3:
    df_escolas_mun = df_esc[df_esc["CO_MUNICIPIO"] == co_mun][["CO_ENTIDADE","NO_ENTIDADE"]].drop_duplicates()
    if busca and len(busca) >= 3:
        df_escolas_mun = df_escolas_mun[df_escolas_mun["NO_ENTIDADE"].str.upper().str.contains(busca.upper(), na=False)]
    df_escolas_mun = df_escolas_mun.sort_values("NO_ENTIDADE")
    if df_escolas_mun.empty:
        st.warning("Nenhuma escola encontrada com esse nome neste município.")
        st.stop()
    escola_sel = st.selectbox("Escola", df_escolas_mun["NO_ENTIDADE"].tolist())

co_esc = df_escolas_mun[df_escolas_mun["NO_ENTIDADE"] == escola_sel]["CO_ENTIDADE"].iloc[0]
df_escola = df_esc[df_esc["CO_ENTIDADE"] == co_esc].sort_values("ANO").copy()

if df_escola.empty:
    st.warning("Sem dados para esta escola.")
    st.stop()

anos_disp = sorted(df_escola["ANO"].unique())
ano_ref = st.selectbox("Ano de referência", anos_disp, index=len(anos_disp)-1)

linha = df_escola[df_escola["ANO"] == ano_ref].iloc[0]
media_ird_nac = df_mun[df_mun["ANO"] == ano_ref]["IRD"].mean()
media_ird_mun = df_mun[(df_mun["ANO"] == ano_ref) & (df_mun["CO_MUNICIPIO"] == co_mun)]["IRD"].mean()
media_atu_nac = df_mun[df_mun["ANO"] == ano_ref]["ATU"].mean()
ird = linha["IRD"]

# ── Situação e orientações ─────────────────────────────────────────────────────
if pd.isna(ird):
    cor_hex="#aaa"; cor_bg="#f0f0f0"; situacao="Sem dados"
    texto_sit="Não há dados de regularidade para esta escola no ano selecionado."
    orientacoes=[]
elif ird >= media_ird_nac:
    cor_hex="#27ae60"; cor_bg="#eafaf1"; situacao="Situação favorável"
    texto_sit=f"A regularidade dos professores desta escola ({formatar_br(ird)}) está acima da média nacional ({formatar_br(media_ird_nac)}) e da média de {mun_sel} ({formatar_br(media_ird_mun)}). O corpo docente apresenta boa estabilidade."
    orientacoes=[
        "Identifique o que está funcionando e sistematize as boas práticas para compartilhar com a rede.",
        "Proponha à secretaria que esta escola seja referência para visitas técnicas de outras unidades.",
        "Mantenha o monitoramento anual — resultados positivos podem se deteriorar se o ambiente de trabalho mudar.",
        "Planeje a continuidade e a integração de novos professores para preservar a estabilidade construída.",
    ]
elif pd.notna(media_ird_mun) and ird >= media_ird_mun:
    cor_hex="#f39c12"; cor_bg="#fef9e7"; situacao="Atenção"
    texto_sit=f"A regularidade dos professores desta escola ({formatar_br(ird)}) está abaixo da média nacional ({formatar_br(media_ird_nac)}), mas acima da média de {mun_sel} ({formatar_br(media_ird_mun)}). Merece acompanhamento próximo."
    orientacoes=[
        "Verifique a tendência dos últimos anos — se o IRD está caindo consecutivamente, o problema está se agravando.",
        "Converse com professores recentes para identificar rapidamente o que pode melhorar.",
        "Fortaleça o projeto pedagógico coletivo — professores comprometidos com um propósito claro tendem a permanecer mais tempo.",
        "Reconheça publicamente o esforço da equipe — o reconhecimento genuíno é um dos fatores de retenção mais poderosos.",
    ]
else:
    cor_hex="#c0392b"; cor_bg="#fdedec"; situacao="Alerta"
    texto_sit=f"A regularidade dos professores desta escola ({formatar_br(ird)}) está abaixo da média nacional ({formatar_br(media_ird_nac)}) e abaixo da média de {mun_sel} ({formatar_br(media_ird_mun)}). A gestão da rede deve priorizar o acompanhamento desta unidade."
    orientacoes=[
        "Ouça os professores antes de qualquer decisão. Realize conversas individuais para entender os motivos da saída.",
        "Avalie as condições objetivas de trabalho. Turmas superlotadas e jornadas fragmentadas afastam os professores.",
        "Construa um ambiente colaborativo. Escolas onde professores participam das decisões pedagógicas retêm mais docentes.",
        "Acione a secretaria com dados. Use os dados do RegDoc para justificar apoio em lotação e formação.",
        "Invista em formação continuada dentro da escola — professores que se desenvolvem profissionalmente tendem a permanecer.",
    ]

hist = df_escola[df_escola["ANO"] <= ano_ref].sort_values("ANO")
if len(hist) >= 2:
    variacao = hist["IRD"].iloc[-1] - hist["IRD"].iloc[-2]
    ano_ant = int(hist["ANO"].iloc[-2])
    texto_var = (f"Em relação a {ano_ant}, houve melhora de {formatar_br(variacao)}." if variacao > 0.05
        else f"Em relação a {ano_ant}, houve queda de {formatar_br(abs(variacao))}. Merece atenção da gestão." if variacao < -0.05
        else f"Em relação a {ano_ant}, a regularidade permaneceu estável.")
else:
    variacao=None; texto_var="Não há ano anterior disponível para comparação."

# ── Painel principal ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"### {escola_sel}")
st.caption(f"Código INEP: {co_esc} · {mun_sel} · {uf_sel} · {ano_ref}")

col_ird, col_comp = st.columns([1, 2])
with col_ird:
    st.markdown(f"""
    <div class="ird-destaque" style="background:{cor_bg}; border:2px solid {cor_hex};">
        <p style="color:{cor_hex}; margin:0; font-size:1rem;">
            Regularidade dos professores (0 a 5)
            <span class="tooltip-wrap">
                <span class="info-icon" style="background:{cor_hex};">i</span>
                <span class="tip">{TOOLTIPS['IRD']}</span>
            </span>
        </p>
        <p style="color:{cor_hex}; margin:0; font-size:3.5rem; font-weight:bold;">{formatar_br(ird)}</p>
        <p style="color:{cor_hex}; margin:0; font-size:1.2rem; font-weight:bold;">● {situacao}</p>
    </div>""", unsafe_allow_html=True)

with col_comp:
    c1, c2 = st.columns(2)
    c1.metric("Média nacional", formatar_br(media_ird_nac),
        delta=f"{ird-media_ird_nac:+.3f}".replace(".",",") if pd.notna(ird) else None)
    c2.metric(f"Média {mun_sel}", formatar_br(media_ird_mun),
        delta=f"{ird-media_ird_mun:+.3f}".replace(".",",") if pd.notna(ird) and pd.notna(media_ird_mun) else None)
    st.markdown(f"<p style='font-size:0.95rem;color:#333;'>{texto_sit}</p>", unsafe_allow_html=True)

st.markdown(f"**Variação em relação ao ano anterior:** {texto_var}")

if orientacoes:
    with st.expander(f"📋 O que fazer? — Orientações para situação de {situacao}"):
        for i, ori in enumerate(orientacoes, 1):
            st.markdown(f"**{i}.** {ori}")

# ── Indicadores associados ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Indicadores associados")
st.caption("Passe o mouse sobre o ℹ para entender cada indicador")

atu=linha.get("ATU"); afd=linha.get("AFD")
ied=linha.get("IED"); icg=linha.get("ICG")

col1, col2 = st.columns(2)
with col1:
    atu_i = ("Acima da média nacional. Turmas numerosas aumentam a sobrecarga dos professores." if pd.notna(atu) and atu > media_atu_nac+3
        else "Abaixo da média nacional. Turmas menores favorecem a permanência dos professores." if pd.notna(atu) and atu < media_atu_nac-3
        else f"Próximo à média nacional ({formatar_br(media_atu_nac,1)} alunos/turma)." if pd.notna(atu) else "Não disponível.")
    card_com_tooltip("Alunos por turma", "ATU", formatar_br(atu,1), atu_i)

    afd_i = ("A maioria dos professores leciona na área em que se formou." if pd.notna(afd) and afd>=70
        else "Parte dos professores atua fora da sua área de formação." if pd.notna(afd) and afd>=40
        else "Grande parte dos professores atua fora da sua área de formação." if pd.notna(afd) else "Não disponível.")
    card_com_tooltip("Formação adequada", "AFD", formatar_br(afd,1)+("%" if pd.notna(afd) else ""), afd_i)

with col2:
    ied_i = ("Jornada docente com alto nível de fragmentação — professores atuam em muitas escolas, turnos ou etapas." if pd.notna(ied) and ied>=50
        else "Nível intermediário de fragmentação da jornada docente." if pd.notna(ied) and ied>=25
        else "Jornada docente menos fragmentada — professores tendem a concentrar sua atuação nesta escola." if pd.notna(ied) else "Não disponível.")
    card_com_tooltip("Esforço docente — IED", "IED", formatar_br(ied,1)+("%" if pd.notna(ied) else ""), ied_i)

    icg_i = ("Escola de alta complexidade — oferece muitos turnos, etapas ou modalidades." if pd.notna(icg) and icg>=4
        else "Escola de complexidade intermediária." if pd.notna(icg) and icg>=2.5
        else "Escola de menor complexidade — estrutura mais simples de gerir." if pd.notna(icg) else "Não disponível.")
    card_com_tooltip("Complexidade da escola — ICG", "ICG", formatar_br(icg,1), icg_i)

# ── Gráfico + tendência ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Evolução da regularidade dos professores")

ird_nac = df_mun.groupby("ANO")["IRD"].mean().reset_index()
ird_mun_s = df_mun[df_mun["CO_MUNICIPIO"] == co_mun][["ANO","IRD"]].copy()

fig = go.Figure()
fig.add_trace(go.Scatter(x=df_escola["ANO"], y=df_escola["IRD"], name="Esta escola",
    line=dict(color=cor_hex, width=3), mode="lines+markers", marker_size=9))
fig.add_trace(go.Scatter(x=ird_nac["ANO"], y=ird_nac["IRD"], name="Média Brasil",
    line=dict(color="#aaa", dash="dash", width=1.5)))
fig.add_trace(go.Scatter(x=ird_mun_s["ANO"], y=ird_mun_s["IRD"], name=f"Média {mun_sel}",
    line=dict(color="#e67e22", dash="dot", width=1.5)))
fig.update_layout(height=380, margin=dict(l=20,r=20,t=20,b=20),
    legend=dict(orientation="h", y=-0.2),
    yaxis=dict(title="Regularidade (0 a 5)", range=[0,5.2]),
    xaxis_title="Ano")
st.plotly_chart(fig, use_container_width=True)

# Sinalização de tendência logo abaixo do gráfico
tendencia = classificar_tendencia(df_escola, ano_ref)
render_tendencia(tendencia)

# ── Histórico ──────────────────────────────────────────────────────────────────
st.markdown("### Histórico de regularidade")
df_tab = df_escola[["CO_ENTIDADE","ANO","IRD"]].copy()
df_tab["Variação"] = df_tab["IRD"].diff()
df_tab = df_tab.rename(columns={"CO_ENTIDADE":"Código INEP","ANO":"Ano","IRD":"Regularidade (0-5)"})
df_tab["Regularidade (0-5)"] = df_tab["Regularidade (0-5)"].apply(formatar_br)
df_tab["Variação"] = df_tab["Variação"].apply(lambda x: formatar_br(x) if pd.notna(x) else "—")
st.dataframe(df_tab, use_container_width=True, hide_index=True)

# ── Relatório HTML ─────────────────────────────────────────────────────────────
st.markdown("---")

def gerar_relatorio_escola():
    rows = ""
    df_h = df_escola[["CO_ENTIDADE","ANO","IRD"]].copy()
    df_h["VAR"] = df_h["IRD"].diff()
    for _, r in df_h.iterrows():
        var = formatar_br(r["VAR"]) if pd.notna(r["VAR"]) else "—"
        cor_var = "#27ae60" if pd.notna(r["VAR"]) and r["VAR"]>0 else "#c0392b" if pd.notna(r["VAR"]) and r["VAR"]<0 else "#333"
        rows += f"<tr><td>{int(r['CO_ENTIDADE'])}</td><td>{int(r['ANO'])}</td><td>{formatar_br(r['IRD'])}</td><td style='color:{cor_var}'>{var}</td></tr>"

    ori_html = "".join([
        f"<div style='display:flex;gap:12px;align-items:flex-start;margin-bottom:8px;'>"
        f"<div style='min-width:22px;height:22px;background:{cor_hex};border-radius:50%;"
        f"display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:bold;'>{i}</div>"
        f"<p style='margin:0;font-size:13px;'>{o}</p></div>"
        for i, o in enumerate(orientacoes, 1)
    ])

    tend_html = ""
    if tendencia:
        tend_html = (
            f"<div style='border-left:4px solid {tendencia['cor_borda']};"
            f"background:{tendencia['cor_fundo']};padding:10px 14px;border-radius:0 6px 6px 0;margin-bottom:1rem;'>"
            f"<strong>{tendencia['icone']} Tendência histórica</strong><br>"
            f"<span style='font-size:13px;'>{tendencia['texto']}</span>"
            + (f"<br><span style='color:#c0392b;font-size:12px;'>⚠️ Ruptura detectada em {tendencia['ano_ruptura']}.</span>"
               if tendencia.get('ruptura') else "")
            + "</div>"
        )

    ind_html = f"""
    <table style="width:100%;border-collapse:collapse;font-size:13px;margin-top:0.5rem;">
      <thead><tr>
        <th style="background:#1a3a5c;color:white;padding:8px;text-align:left;">Indicador</th>
        <th style="background:#1a3a5c;color:white;padding:8px;text-align:left;">O que mede</th>
        <th style="background:#1a3a5c;color:white;padding:8px;text-align:left;">Valor</th>
      </tr></thead>
      <tbody>
        <tr><td style="padding:7px 8px;border-bottom:1px solid #eee;">Alunos por turma (ATU)</td>
            <td style="padding:7px 8px;border-bottom:1px solid #eee;">Média de estudantes por turma</td>
            <td style="padding:7px 8px;border-bottom:1px solid #eee;">{formatar_br(atu,1)}</td></tr>
        <tr><td style="padding:7px 8px;border-bottom:1px solid #eee;">Formação adequada (AFD)</td>
            <td style="padding:7px 8px;border-bottom:1px solid #eee;">% de professores na área de formação</td>
            <td style="padding:7px 8px;border-bottom:1px solid #eee;">{formatar_br(afd,1)}%</td></tr>
        <tr><td style="padding:7px 8px;border-bottom:1px solid #eee;">Esforço docente (IED)</td>
            <td style="padding:7px 8px;border-bottom:1px solid #eee;">Complexidade da jornada docente (1–6)</td>
            <td style="padding:7px 8px;border-bottom:1px solid #eee;">{formatar_br(ied,1)}%</td></tr>
        <tr><td style="padding:7px 8px;">Complexidade da escola (ICG)</td>
            <td style="padding:7px 8px;">Porte, turnos, etapas e modalidades (1–6)</td>
            <td style="padding:7px 8px;">{formatar_br(icg,1)}</td></tr>
      </tbody>
    </table>"""

    checklist = "".join([
        f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'>"
        f"<input type='checkbox'><span style='font-size:13px;'>{item}</span></div>"
        for item in [
            "Realizei escuta com os professores",
            "Avaliei as condições de trabalho da escola",
            "Comuniquei à secretaria com os dados do RegDoc",
            "Planejei ação de formação continuada",
            "Revisei a distribuição de turmas",
        ]
    ])

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>RegDoc — {escola_sel}</title>
<style>
  body{{font-family:Arial,sans-serif;margin:0;padding:2rem;color:#222;max-width:900px;margin:0 auto;}}
  .header{{background:#1a3a5c;color:white;padding:1.5rem 2rem;border-radius:10px;margin-bottom:1.5rem;display:flex;justify-content:space-between;align-items:flex-start;}}
  .header h1{{margin:0;font-size:1.2rem;color:white;}}
  .header p{{margin:0.3rem 0 0;font-size:0.85rem;color:#b8cfe8;}}
  .grid2{{display:grid;grid-template-columns:1fr 2fr;gap:1rem;margin-bottom:1.5rem;}}
  .ird-box{{background:{cor_bg};border:2px solid {cor_hex};border-radius:10px;padding:1.5rem;text-align:center;}}
  .ird-num{{font-size:3rem;font-weight:bold;color:{cor_hex};margin:0;}}
  .ird-label{{font-size:0.85rem;color:{cor_hex};margin:0;}}
  .ird-sit{{font-size:1.1rem;font-weight:bold;color:{cor_hex};margin:0.5rem 0 0;}}
  .metrics{{display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;}}
  .metric{{background:#f5f5f5;border-radius:8px;padding:0.8rem;text-align:center;}}
  .metric .val{{font-size:1.4rem;font-weight:bold;color:#1a3a5c;margin:0;}}
  .metric .lbl{{font-size:0.75rem;color:#777;margin:0;}}
  table{{width:100%;border-collapse:collapse;font-size:13px;}}
  th{{background:#1a3a5c;color:white;padding:8px;text-align:left;}}
  td{{padding:7px 8px;border-bottom:1px solid #eee;}}
  .section{{margin-bottom:1.5rem;}}
  .section h2{{font-size:1rem;color:#1a3a5c;border-bottom:2px solid {cor_hex};padding-bottom:0.3rem;}}
  .alert-box{{border:1px solid {cor_hex};border-radius:8px;padding:1rem;background:{cor_bg};}}
  .footer{{text-align:center;font-size:11px;color:#aaa;margin-top:2rem;border-top:1px solid #eee;padding-top:1rem;}}
  @media print{{body{{padding:1rem;}}}}
</style>
</head>
<body>
<div class="header">
  <div>
    <p style="margin:0;font-size:11px;color:#b8cfe8;text-transform:uppercase;">Relatório RegDoc — Escola</p>
    <h1>{escola_sel}</h1>
    <p>Código INEP: {co_esc} · {mun_sel} · {uf_sel} · {ano_ref}</p>
  </div>
  <div style="font-size:0.8rem;color:#b8cfe8;text-align:right;">Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
</div>
<div class="grid2">
  <div class="ird-box">
    <p class="ird-label">Regularidade dos professores (0 a 5)</p>
    <p class="ird-num">{formatar_br(ird)}</p>
    <p class="ird-sit">● {situacao}</p>
  </div>
  <div class="metrics">
    <div class="metric"><p class="val">{formatar_br(media_ird_nac)}</p><p class="lbl">Média nacional</p></div>
    <div class="metric"><p class="val">{formatar_br(media_ird_mun)}</p><p class="lbl">Média {mun_sel}</p></div>
    <div class="metric"><p class="val">{formatar_br(atu,1)}</p><p class="lbl">Alunos por turma</p></div>
    <div class="metric"><p class="val">{formatar_br(afd,1)}%</p><p class="lbl">Formação adequada</p></div>
  </div>
</div>
<p style="font-size:13px;margin-bottom:1rem;">{texto_sit}<br><strong>Variação:</strong> {texto_var}</p>
{tend_html}
<div class="section">
  <h2>Histórico de regularidade</h2>
  <table><thead><tr><th>Código INEP</th><th>Ano</th><th>Regularidade (0-5)</th><th>Variação</th></tr></thead>
  <tbody>{rows}</tbody></table>
</div>
<div class="section">
  <h2>Indicadores associados</h2>{ind_html}
</div>
<div class="section">
  <h2>O que fazer — situação de {situacao}</h2>
  <div class="alert-box">{ori_html}</div>
</div>
<div class="section">
  <h2>Checklist de ação</h2>{checklist}
</div>
<div class="footer">
  RegDoc · Dados: Censo Escolar/Inep · retendoc.streamlit.app · {datetime.now().strftime('%d/%m/%Y')}
</div>
</body></html>"""

html = gerar_relatorio_escola()
st.download_button(
    label="📄 Baixar relatório desta escola (HTML)",
    data=html.encode("utf-8"),
    file_name=f"regdoc_{co_esc}_{ano_ref}.html",
    mime="text/html"
)
st.caption("Abra o arquivo no navegador e use Ctrl+P para imprimir ou salvar em PDF.")

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
.perfil-tag { display:inline-block; background:#1a3a5c; color:white;
    font-size:0.78rem; font-weight:600; padding:3px 10px; border-radius:20px;
    margin-bottom:0.6rem; letter-spacing:0.03em; }
</style>
""", unsafe_allow_html=True)

# ── Tooltips ───────────────────────────────────────────────────────────────────
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


# ── Tendência histórica ────────────────────────────────────────────────────────
def classificar_tendencia(df_escola, ano_ref):
    hist = df_escola[df_escola["ANO"] <= ano_ref].sort_values("ANO").dropna(subset=["IRD"])
    if len(hist) < 3:
        return None
    anos    = hist["ANO"].values
    valores = hist["IRD"].values
    x       = anos.astype(float)
    slope   = np.polyfit(x - x.mean(), valores, 1)[0]
    ultimo  = valores[-1]
    variacao = ultimo - valores[0]

    ruptura = False
    ano_ruptura = None
    for i in range(1, len(anos)):
        if valores[i] - valores[i-1] <= -0.5:
            ruptura = True
            ano_ruptura = int(anos[i])
            break

    if slope <= -0.15:
        return {"icone": "📉", "cor_fundo": "#fdedec", "cor_borda": "#c0392b",
                "texto": f"Em queda acelerada — perdeu {abs(variacao):.2f} pontos desde {int(anos[0])} "
                         f"({slope:.2f} pts/ano em média). Requer ação imediata.",
                "ruptura": ruptura, "ano_ruptura": ano_ruptura}
    elif slope <= -0.05:
        return {"icone": "↘️", "cor_fundo": "#fef9e7", "cor_borda": "#f39c12",
                "texto": f"Tendência de queda desde {int(anos[0])} "
                         f"({variacao:+.2f} pontos acumulados). "
                         "Monitorar com atenção — se mantida, atingirá nível crítico.",
                "ruptura": ruptura, "ano_ruptura": ano_ruptura}
    elif slope < 0.05:
        return {"icone": "➡️", "cor_fundo": "#f0f4f8", "cor_borda": "#7f8c8d",
                "texto": f"Estável desde {int(anos[0])} (variação de {variacao:+.2f} pontos). "
                         + ("Estabilidade positiva — IRD em nível satisfatório." if ultimo >= 3.0
                            else "Estabilidade preocupante — IRD estagnado abaixo de 3,0."),
                "ruptura": ruptura, "ano_ruptura": ano_ruptura}
    elif slope < 0.15:
        return {"icone": "↗️", "cor_fundo": "#eafaf1", "cor_borda": "#27ae60",
                "texto": f"Em recuperação desde {int(anos[0])} "
                         f"(+{variacao:.2f} pontos acumulados). "
                         "Ações de retenção docente parecem estar surtindo efeito.",
                "ruptura": False, "ano_ruptura": None}
    else:
        return {"icone": "📈", "cor_fundo": "#eafaf1", "cor_borda": "#27ae60",
                "texto": f"Melhora expressiva desde {int(anos[0])} "
                         f"(+{variacao:.2f} pontos, média de +{slope:.2f} pts/ano). "
                         "Documentar as práticas que estão gerando esse resultado.",
                "ruptura": False, "ano_ruptura": None}


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


# ── Prescrição por perfil (IRD × ICG × Localização) ───────────────────────────
def gerar_prescricao_por_perfil(ird_faixa, icg, localizacao):
    """
    Retorna (label_perfil, lista_orientacoes).
    ird_faixa : "alerta" | "atencao" | "favoravel"
    icg       : valor numérico (float) do indicador de complexidade
    localizacao: valor da coluna TP_LOCALIZACAO (1=urbana, 2=rural)
                 ou strings "Urbana"/"Rural"/"URBANA"/"RURAL"
    """
    icg_nivel = "alta" if pd.notna(icg) and float(icg) >= 4 else "baixa"
    loc_str   = str(localizacao).strip()
    loc       = "rural" if loc_str in ["2", "Rural", "RURAL", "rural"] else "urbana"

    perfis = {

        # ══ ALERTA ════════════════════════════════════════════════════════════
        ("alerta", "alta", "urbana"): (
            "Escola urbana · Alta complexidade · Alerta",
            [
                "Mapeie a fragmentação da jornada docente. Professores com IED alto — "
                "que atuam em muitas turmas, etapas ou turnos simultaneamente — têm vínculo "
                "menor com a unidade e tendem a sair primeiro em escolas de alta complexidade.",
                "Avalie a distribuição de responsabilidades pedagógicas. Escolas com muitas "
                "etapas e modalidades sobrecarregam coordenadores e diretores, "
                "o que contamina o clima de trabalho e afeta a permanência dos professores.",
                "Realize escuta estruturada com os professores mais antigos. Em escolas urbanas "
                "de alta complexidade, quem permanece tem razões específicas — "
                "identificá-las permite replicar o que funciona.",
                "Acione a secretaria com os dados do RegDoc e solicite apoio técnico prioritário. "
                "Escolas de alta complexidade em alerta exigem intervenção coordenada, "
                "não apenas iniciativas isoladas da gestão escolar.",
                "Revise o projeto pedagógico coletivo com a equipe. Professores comprometidos "
                "com um propósito claro permanecem mais — especialmente quando participam "
                "ativamente da construção desse projeto.",
            ]
        ),
        ("alerta", "alta", "rural"): (
            "Escola rural · Alta complexidade · Alerta",
            [
                "Investigue as condições de acesso e infraestrutura. Escolas rurais de alta "
                "complexidade combinam o isolamento territorial com a sobrecarga de gestão — "
                "esse conjunto é o principal preditor de rotatividade neste perfil.",
                "Acione a secretaria para políticas de incentivo territorial. Gratificações "
                "de localização, transporte garantido e habitação próxima são fatores "
                "diretamente associados à retenção em escolas rurais com alta complexidade.",
                "Verifique se os professores têm formação adequada para as etapas e modalidades "
                "oferecidas. Alta complexidade em escola rural frequentemente inclui classes "
                "multisseriadas ou EJA — professores sem preparo para essas modalidades "
                "tendem a pedir transferência rapidamente.",
                "Fortaleça o projeto pedagógico como âncora de pertencimento. Em contextos "
                "rurais, o vínculo do professor com a comunidade é o principal fator de "
                "permanência quando as condições materiais são limitadas.",
                "Monitore o IED dos professores. Jornada muito fragmentada entre escolas "
                "rurais distintas indica que o vínculo com cada unidade é fraco "
                "e a saída se torna mais provável.",
            ]
        ),
        ("alerta", "baixa", "urbana"): (
            "Escola urbana · Baixa complexidade · Alerta",
            [
                "Investigue causas locais específicas. Escolas urbanas de baixa complexidade "
                "em alerta são um sinal particular — o problema não é estrutural, "
                "é provavelmente de clima organizacional ou gestão interna.",
                "Compare com escolas de perfil similar no município usando o módulo "
                "Comparação do RegDoc. Se escolas vizinhas de mesmo porte e etapa têm IRD "
                "melhor, a causa está nesta unidade — não no território.",
                "Converse com os professores que saíram nos últimos dois anos, se possível. "
                "Em escolas de baixa complexidade, os motivos costumam ser mais "
                "identificáveis e endereçáveis pela gestão.",
                "Avalie o estilo de liderança da gestão escolar. A literatura sobre retenção "
                "docente mostra que o diretor é o fator mais determinante da permanência "
                "em escolas menores (Boyd et al., 2011).",
                "Construa um plano de ação com a equipe e defina uma meta de IRD para o "
                "próximo Censo Escolar. Escolas de menor porte têm maior agilidade "
                "para implementar mudanças e medir resultados.",
            ]
        ),
        ("alerta", "baixa", "rural"): (
            "Escola rural · Baixa complexidade · Alerta",
            [
                "Priorize a investigação das condições de acesso. Escolas rurais pequenas "
                "em alerta quase sempre têm rotatividade associada a dificuldades de "
                "transporte, distância ou infraestrutura — fatores que a gestão escolar "
                "não resolve sozinha.",
                "Acione a secretaria para avaliar políticas de fixação docente. Mesmo em "
                "escolas rurais menores, incentivos de localização fazem diferença "
                "significativa na decisão de permanência.",
                "Verifique se os professores que saíram foram transferidos para escolas "
                "urbanas ou saíram da rede. Se é transferência interna, o problema é de "
                "atratividade relativa — a escola precisa de diferencial para reter.",
                "Envolva a comunidade local no projeto da escola. Em escolas rurais de "
                "menor porte, o vínculo com a comunidade é o principal fator de retenção "
                "quando as condições materiais não podem ser rapidamente melhoradas.",
            ]
        ),

        # ══ ATENÇÃO ═══════════════════════════════════════════════════════════
        ("atencao", "alta", "urbana"): (
            "Escola urbana · Alta complexidade · Atenção",
            [
                "Verifique a tendência histórica antes de qualquer ação. Em escolas de alta "
                "complexidade urbanas, a situação de atenção pode ser o início de uma "
                "trajetória de queda — agir agora é mais eficiente do que esperar o alerta.",
                "Revise a carga de trabalho dos professores. Alta complexidade urbana "
                "frequentemente significa muitas turmas, etapas e demandas administrativas "
                "acumuladas — o esgotamento é silencioso e percebido tardiamente.",
                "Identifique os professores em risco de saída. Em escolas maiores, há sempre "
                "um grupo com menos vínculo institucional — chegaram recentemente, atuam em "
                "poucas horas ou têm IED alto. São os primeiros a sair.",
                "Fortaleça momentos de reconhecimento coletivo. Professores de escolas "
                "urbanas de alta complexidade relatam frequentemente invisibilidade dentro "
                "da própria instituição como razão para considerar a saída.",
            ]
        ),
        ("atencao", "alta", "rural"): (
            "Escola rural · Alta complexidade · Atenção",
            [
                "Monitore com atenção redobrada. A combinação de localização rural e alta "
                "complexidade torna este perfil vulnerável a deterioração rápida do IRD — "
                "duas ou três saídas podem mover o indicador de atenção para alerta.",
                "Antecipe conversas sobre continuidade com os professores antes do "
                "encerramento do ano letivo. Em contextos rurais, a decisão de sair ou ficar "
                "costuma ser tomada nesse período.",
                "Acione preventivamente a secretaria para garantir reposição rápida em "
                "caso de saída. Escolas rurais de alta complexidade têm maior dificuldade "
                "de reposição — o tempo de vacância tem custo pedagógico alto.",
                "Invista no sentido de pertencimento. Professores que se sentem parte de "
                "algo maior — comunidade, projeto, missão — permanecem mais em contextos "
                "rurais mesmo quando as condições materiais são desfavoráveis.",
            ]
        ),
        ("atencao", "baixa", "urbana"): (
            "Escola urbana · Baixa complexidade · Atenção",
            [
                "A situação de atenção é o melhor momento para agir — antes que se torne "
                "alerta. Em escolas urbanas de baixa complexidade, intervenções preventivas "
                "têm custo baixo e impacto direto.",
                "Verifique se há professores com menos de dois anos na escola. Alta "
                "concentração de docentes recentes é o principal preditor de queda futura "
                "do IRD em escolas menores.",
                "Fortaleça a integração de novos professores com a cultura da escola. "
                "Programas de mentoria entre professores experientes e iniciantes "
                "reduzem a saída precoce em escolas urbanas de menor porte.",
                "Use o módulo Comparação do RegDoc para verificar se escolas similares "
                "no município estão em situação melhor — se sim, há algo a aprender com elas.",
            ]
        ),
        ("atencao", "baixa", "rural"): (
            "Escola rural · Baixa complexidade · Atenção",
            [
                "Monitore a tendência histórica. Escolas rurais de baixa complexidade em "
                "atenção são frequentemente estáveis nessa faixa por vários anos — "
                "verifique se é estagnação ou declínio ativo.",
                "Converse com os professores sobre suas expectativas para os próximos dois "
                "anos. Em escolas rurais menores, a intenção de permanecer ou sair costuma "
                "ser mais previsível e endereçável pela gestão.",
                "Avalie se há professores em final de carreira ou próximos à aposentadoria "
                "cuja saída impactará o IRD. Planejar a reposição com antecedência "
                "reduz o impacto sobre o indicador.",
            ]
        ),

        # ══ FAVORÁVEL ═════════════════════════════════════════════════════════
        ("favoravel", "alta", "urbana"): (
            "Escola urbana · Alta complexidade · Situação favorável",
            [
                "Identifique e sistematize o que está funcionando. Manter IRD alto em escola "
                "urbana de alta complexidade é um resultado não trivial — as práticas que "
                "explicam isso têm valor para toda a rede.",
                "Proponha à secretaria que esta escola seja referência para visitas técnicas "
                "de escolas em situação de atenção ou alerta com perfil similar.",
                "Não reduza o esforço de gestão. Escolas bem-sucedidas frequentemente "
                "revertem ganhos após atingir bons resultados — a estabilidade "
                "exige manutenção ativa (Park, 2025).",
                "Monitore o IED dos professores. Alta complexidade urbana com IRD alto "
                "pode mudar rapidamente se a secretaria redistribuir professores experientes "
                "para outras unidades ou aumentar a carga de trabalho.",
            ]
        ),
        ("favoravel", "alta", "rural"): (
            "Escola rural · Alta complexidade · Situação favorável",
            [
                "Este é um resultado expressivo. Escolas rurais de alta complexidade "
                "raramente mantêm IRD alto sem fatores deliberados de retenção — "
                "documente-os com detalhes.",
                "Investigue o que ancora os professores nesta escola: vínculo com a "
                "comunidade, liderança da gestão, condições específicas de trabalho. "
                "Esse diagnóstico tem valor de política pública para a secretaria.",
                "Compartilhe a experiência com a secretaria. A combinação de alta "
                "complexidade e IRD favorável em contexto rural é rara o suficiente "
                "para justificar um estudo de caso interno.",
                "Mantenha o monitoramento anual. A situação favorável em escolas rurais "
                "é mais frágil do que em escolas urbanas — uma mudança de gestão ou de "
                "política de transporte pode deteriorá-la rapidamente.",
            ]
        ),
        ("favoravel", "baixa", "urbana"): (
            "Escola urbana · Baixa complexidade · Situação favorável",
            [
                "Identifique o que contribui para a estabilidade e registre formalmente. "
                "Mesmo em escolas de baixa complexidade, boas práticas de gestão "
                "fazem diferença e podem ser replicadas na rede.",
                "Monitore anualmente para garantir que a estabilidade se mantém. "
                "Mudanças de gestão ou de composição do corpo docente podem alterar "
                "o IRD mesmo em escolas menores.",
                "Use o módulo Comparação do RegDoc para verificar se escolas com perfil "
                "similar estão em situação pior — se sim, esta unidade tem algo a ensinar.",
            ]
        ),
        ("favoravel", "baixa", "rural"): (
            "Escola rural · Baixa complexidade · Situação favorável",
            [
                "Reconheça e valorize a estabilidade construída. Manter professores em "
                "escola rural exige esforço contínuo — comunique esse resultado à secretaria "
                "como indicador de gestão positiva.",
                "Investigue os fatores de permanência. Em escolas rurais pequenas, o vínculo "
                "com a comunidade local é frequentemente o principal fator — "
                "fortaleça esse elo ativamente.",
                "Planeje a sucessão de professores próximos à aposentadoria para evitar "
                "queda brusca do IRD nos próximos anos.",
            ]
        ),
    }

    chave = (ird_faixa, icg_nivel, loc)
    return perfis.get(chave, (
        f"Escola {loc} — complexidade {icg_nivel}",
        [
            "Consulte os dados do RegDoc e a equipe gestora para definir as ações "
            "mais adequadas ao contexto desta unidade."
        ]
    ))


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

atu = linha.get("ATU")
afd = linha.get("AFD")
ied = linha.get("IED")
icg = linha.get("ICG")

# Localização — tenta TP_LOCALIZACAO; fallback para NO_LOCALIZACAO ou "1" (urbana)
localizacao = linha.get("TP_LOCALIZACAO", linha.get("NO_LOCALIZACAO", "1"))

# ── Situação e prescrição por perfil ──────────────────────────────────────────
if pd.isna(ird):
    cor_hex = "#aaa"; cor_bg = "#f0f0f0"; situacao = "Sem dados"
    texto_sit = "Não há dados de regularidade para esta escola no ano selecionado."
    label_perfil = None
    orientacoes = []

elif ird >= media_ird_nac:
    cor_hex = "#27ae60"; cor_bg = "#eafaf1"; situacao = "Situação favorável"
    texto_sit = (
        f"A regularidade dos professores desta escola ({formatar_br(ird)}) está acima "
        f"da média nacional ({formatar_br(media_ird_nac)}) e da média de {mun_sel} "
        f"({formatar_br(media_ird_mun)}). O corpo docente apresenta boa estabilidade."
    )
    label_perfil, orientacoes = gerar_prescricao_por_perfil("favoravel", icg, localizacao)

elif pd.notna(media_ird_mun) and ird >= media_ird_mun:
    cor_hex = "#f39c12"; cor_bg = "#fef9e7"; situacao = "Atenção"
    texto_sit = (
        f"A regularidade dos professores desta escola ({formatar_br(ird)}) está abaixo "
        f"da média nacional ({formatar_br(media_ird_nac)}), mas acima da média de "
        f"{mun_sel} ({formatar_br(media_ird_mun)}). Merece acompanhamento próximo."
    )
    label_perfil, orientacoes = gerar_prescricao_por_perfil("atencao", icg, localizacao)

else:
    cor_hex = "#c0392b"; cor_bg = "#fdedec"; situacao = "Alerta"
    texto_sit = (
        f"A regularidade dos professores desta escola ({formatar_br(ird)}) está abaixo "
        f"da média nacional ({formatar_br(media_ird_nac)}) e abaixo da média de "
        f"{mun_sel} ({formatar_br(media_ird_mun)}). A gestão da rede deve priorizar "
        f"o acompanhamento desta unidade."
    )
    label_perfil, orientacoes = gerar_prescricao_por_perfil("alerta", icg, localizacao)

# Variação ano anterior
hist = df_escola[df_escola["ANO"] <= ano_ref].sort_values("ANO")
if len(hist) >= 2:
    variacao = hist["IRD"].iloc[-1] - hist["IRD"].iloc[-2]
    ano_ant  = int(hist["ANO"].iloc[-2])
    texto_var = (
        f"Em relação a {ano_ant}, houve melhora de {formatar_br(variacao)}." if variacao > 0.05
        else f"Em relação a {ano_ant}, houve queda de {formatar_br(abs(variacao))}. Merece atenção da gestão." if variacao < -0.05
        else f"Em relação a {ano_ant}, a regularidade permaneceu estável."
    )
else:
    variacao = None; texto_var = "Não há ano anterior disponível para comparação."

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

# ── Orientações por perfil ─────────────────────────────────────────────────────
if orientacoes:
    with st.expander(f"📋 O que fazer? — {situacao}"):
        if label_perfil:
            st.markdown(
                f"<span class='perfil-tag'>📍 {label_perfil}</span>",
                unsafe_allow_html=True
            )
        for i, ori in enumerate(orientacoes, 1):
            st.markdown(f"**{i}.** {ori}")

# ── Indicadores associados ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Indicadores associados")
st.caption("Passe o mouse sobre o ℹ para entender cada indicador")

col1, col2 = st.columns(2)
with col1:
    atu_i = (
        "Acima da média nacional. Turmas numerosas aumentam a sobrecarga dos professores."
        if pd.notna(atu) and atu > media_atu_nac + 3
        else "Abaixo da média nacional. Turmas menores favorecem a permanência dos professores."
        if pd.notna(atu) and atu < media_atu_nac - 3
        else f"Próximo à média nacional ({formatar_br(media_atu_nac,1)} alunos/turma)."
        if pd.notna(atu) else "Não disponível."
    )
    card_com_tooltip("Alunos por turma", "ATU", formatar_br(atu,1), atu_i)

    afd_i = (
        "A maioria dos professores leciona na área em que se formou."
        if pd.notna(afd) and afd >= 70
        else "Parte dos professores atua fora da sua área de formação."
        if pd.notna(afd) and afd >= 40
        else "Grande parte dos professores atua fora da sua área de formação."
        if pd.notna(afd) else "Não disponível."
    )
    card_com_tooltip("Formação adequada", "AFD", formatar_br(afd,1) + ("%" if pd.notna(afd) else ""), afd_i)

with col2:
    ied_i = (
        "Jornada docente com alto nível de fragmentação — professores atuam em muitas escolas, turnos ou etapas."
        if pd.notna(ied) and ied >= 50
        else "Nível intermediário de fragmentação da jornada docente."
        if pd.notna(ied) and ied >= 25
        else "Jornada docente menos fragmentada — professores tendem a concentrar sua atuação nesta escola."
        if pd.notna(ied) else "Não disponível."
    )
    card_com_tooltip("Esforço docente — IED", "IED", formatar_br(ied,1) + ("%" if pd.notna(ied) else ""), ied_i)

    icg_i = (
        "Escola de alta complexidade — oferece muitos turnos, etapas ou modalidades."
        if pd.notna(icg) and icg >= 4
        else "Escola de complexidade intermediária."
        if pd.notna(icg) and icg >= 2.5
        else "Escola de menor complexidade — estrutura mais simples de gerir."
        if pd.notna(icg) else "Não disponível."
    )
    card_com_tooltip("Complexidade da escola — ICG", "ICG", formatar_br(icg,1), icg_i)

# ── Gráfico + tendência ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Evolução da regularidade dos professores")

ird_nac   = df_mun.groupby("ANO")["IRD"].mean().reset_index()
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
        var     = formatar_br(r["VAR"]) if pd.notna(r["VAR"]) else "—"
        cor_var = "#27ae60" if pd.notna(r["VAR"]) and r["VAR"] > 0 else "#c0392b" if pd.notna(r["VAR"]) and r["VAR"] < 0 else "#333"
        rows += f"<tr><td>{int(r['CO_ENTIDADE'])}</td><td>{int(r['ANO'])}</td><td>{formatar_br(r['IRD'])}</td><td style='color:{cor_var}'>{var}</td></tr>"

    perfil_html = ""
    if label_perfil:
        perfil_html = (
            f"<div style='display:inline-block;background:#1a3a5c;color:white;"
            f"font-size:12px;font-weight:600;padding:3px 10px;border-radius:20px;"
            f"margin-bottom:8px;'>📍 {label_perfil}</div><br>"
        )

    ori_html = perfil_html + "".join([
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
  <h2>O que fazer — {situacao}</h2>
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

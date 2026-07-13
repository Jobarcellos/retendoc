import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils.dados import aplicar_estilo_global, VERSAO_APP, FONTE_DADOS, COBERTURA, icone_pagina

st.set_page_config(page_title="Metodologia · RegDoc", page_icon=icone_pagina(), layout="wide")
aplicar_estilo_global()

st.title("📋 Metodologia e Notas Técnicas")
st.caption("Como o RegDoc calcula, classifica e sinaliza — em linguagem de gestão, sem caixa-preta")

st.markdown(f"""
**Versão do aplicativo:** {VERSAO_APP} · **Fonte dos dados:** {FONTE_DADOS} · **Cobertura:** {COBERTURA}

Esta página documenta todas as regras do RegDoc. O objetivo é que qualquer gestor,
técnico ou pesquisador consiga auditar o que cada cor, seta e recomendação significa.
""")

st.markdown("---")
st.markdown("### 1. O indicador central: IRD")
st.markdown("""
O **Indicador de Regularidade do Docente (IRD)** é calculado e publicado pelo Inep.
Ele expressa, numa escala de **0 a 5**, o quanto os professores de uma escola
permaneceram nela ao longo dos **últimos cinco anos**: docentes com presença contínua
elevam o indicador; docentes recém-chegados ou que alternam entre escolas o reduzem.

O IRD **não mede** qualidade do ensino, desempenho do professor nem resultado dos
alunos. Mede exclusivamente **permanência**. O RegDoc não altera o cálculo do Inep —
apenas o traduz em leitura gerencial.
""")

st.markdown("### 2. Semáforo de risco: classificação relativa à média nacional")
st.markdown("""
A classificação de risco compara cada município ou escola com a **média nacional do
IRD no ano de referência**:

| Situação | Regra | Cor |
|---|---|---|
| **Alerta** | IRD abaixo de **85%** da média nacional | 🔴 vermelho |
| **Atenção** | IRD entre 85% e 100% da média nacional | 🟠 laranja |
| **Moderado** | IRD entre 100% e 110% da média nacional | 🟡 amarelo |
| **Favorável** | IRD acima de **110%** da média nacional | 🟢 verde |

**Por que relativa?** Para priorizar, a cada ciclo, quem está mais atrás do país —
independentemente de quanto a média geral suba ou desça.

**Consequência que você deve conhecer:** como o critério acompanha a média do ano,
as **contagens de alerta de anos diferentes não são diretamente comparáveis**.
Um município pode entrar em alerta sem que seu IRD caia, se a média nacional subir.
Para acompanhar a evolução da sua rede ao longo do tempo, use o **valor do IRD** e a
**tendência histórica**, não a cor do semáforo.
""")

st.markdown("### 2b. As duas classificações: faixa oficial do Inep × situação na sua rede")
st.markdown("""
O RegDoc exibe **duas classificações para o mesmo IRD**, e elas não se contradizem —
respondem a perguntas diferentes.

| | Faixa Inep | Situação (RegDoc) |
|---|---|---|
| **Critério** | Absoluto e fixo: baixa (até 2), média-baixa (2 a 3), média-alta (3 a 4), alta (acima de 4) | Relativo: compara com a média nacional e a da própria rede |
| **Responde** | Como esta escola está **no Brasil**? | Por qual escola **eu começo**? |
| **Origem** | Classificação oficial publicada pelo Inep | Critério gerencial do RegDoc |

**Por que não basta o critério oficial.** Ele funciona para a estatística nacional, mas
perde força dentro de uma rede. Em Cariacica, em 2025, **73 das 122 escolas municipais
caem numa única faixa** ("média-baixa"). O critério oficial diz que são iguais; o gestor
precisa saber qual visitar primeiro. Olhando dentro dessa mesma faixa, o critério relativo
separa 48 escolas em atenção e 25 em alerta.

**Por que não basta o critério relativo.** Porque o secretário conhece a classificação do
Inep, e uma plataforma que a contradiz sem explicação perde credibilidade. Mostrando as
duas, fica claro que não há contradição: há duas perguntas.

**Onde elas discordam está a informação útil.** Uma escola pode estar em faixa aceitável
no país e ainda assim ser a que mais perde professores na sua rede — e é ela que precisa
de ação agora.
""")

st.markdown("### 3. Tendência histórica: cinco categorias + alerta de ruptura")
st.markdown("""
Nos módulos **Município** e **Escola**, o sistema ajusta uma linha de tendência
(**regressão linear simples**) sobre os **últimos 5 anos disponíveis** da série
(mínimo de 3 anos) — janela coerente com a do próprio IRD — e classifica a
trajetória pela **inclinação média anual**:

| Categoria | Inclinação (pontos de IRD por ano) |
|---|---|
| 📉 Queda acelerada | perda ≥ 0,15 |
| ↘️ Queda | perda entre 0,05 e 0,15 |
| ➡️ Estável | variação < 0,05 em qualquer direção |
| ↗️ Recuperação | ganho entre 0,05 e 0,15 |
| 📈 Melhora expressiva | ganho ≥ 0,15 |

Além da tendência, o sistema dispara um **alerta de ruptura** sempre que o IRD cai
**0,5 ponto ou mais de um ano para o outro**, em qualquer ponto da série — sinal de
evento agudo (troca de gestão, fechamento de turnos, reorganização da rede) que
merece investigação imediata.

**Anos pandêmicos (2020–2021):** os gráficos históricos sombreiam esse período.
Os dados desses Censos refletem políticas emergenciais (suspensão de contratos,
remanejamentos), e não o comportamento típico da rede. Leia quedas e recuperações
que atravessam o período com cautela redobrada.
""")

st.markdown("### 4. Prescrição por perfil de escola")
st.markdown("""
No módulo **Escola**, as orientações de ação são diferenciadas cruzando três
dimensões:

- **Faixa de risco do IRD** (alerta, atenção ou favorável);
- **Complexidade da gestão** (ICG ≥ 4 = alta; ICG < 4 = baixa);
- **Localização** (urbana ou rural).

O cruzamento gera **12 perfis**, cada um com um conjunto próprio de recomendações,
fundamentadas na literatura de retenção docente. A lógica: causas e soluções da
rotatividade variam com o contexto — receita única não funciona.
""")

st.markdown("### 5. Dados: origem, tratamento e atualização")
st.markdown("""
- **Origem:** arquivos públicos de Indicadores Educacionais do Inep (IRD, ATU, AFD,
  IED, ICG), consolidados em formato Parquet.
- **Tratamento:** padronização de cabeçalhos e códigos identificadores (município e
  escola) e consolidação da série histórica em base única.
- **Atualização:** manual, a cada divulgação anual do Censo Escolar. A versão dos
  dados vigente está indicada no topo desta página.
- **Cobertura:** séries municipal e escolar de 2013 a 2025 (treze anos). São 209.960
  escolas distintas ao longo da série e cerca de 165 mil por ano — a diferença
  corresponde a unidades abertas, fechadas ou recodificadas no período.
  Escolas criadas recentemente ou com histórico incompleto no Censo podem
  apresentar anos ausentes — nesses casos, desconfie de "quedas" em séries curtas.
""")

st.markdown("### 6. O que o RegDoc não faz")
st.markdown("""
- Não substitui o diálogo com os professores nem captura causas subjetivas da
  rotatividade;
- Não mede qualidade do ensino ou desempenho dos alunos;
- Não cruza, na versão atual, regularidade com desempenho (Saeb/Ideb) nem com
  dados fiscais (Siope) — integrações previstas para versões futuras.
""")

st.markdown("---")
st.caption("Dúvidas ou sugestões sobre a metodologia? Utilize os canais indicados na página inicial.")

from utils.dados import rodape_institucional
rodape_institucional()

import pandas as pd
import streamlit as st

NOMES_INDICADORES = {
    "IRD": "Regularidade dos professores",
    "ATU": "Alunos por turma",
    "AFD": "Formação adequada (%)",
    "IED": "Sobrecarga dos professores (%)",
    "ICG": "Complexidade da escola",
}

EXPLICACOES = {
    "IRD": """
**O que é:** Indica se os mesmos professores continuam na escola de um ano para o outro.
Uma escola com alta regularidade é aquela onde os professores permanecem, constroem vínculos
com os alunos e mantêm a continuidade do trabalho pedagógico.

**Como é medido:** O Inep observa a presença de cada professor na escola nos últimos 5 anos.
Professores que estão há mais tempo e de forma contínua recebem pontuação maior.
O resultado é uma escala de **0 a 5**:

| Valor | Situação |
|---|---|
| 0 a 2 | Corpo docente muito instável — alta rotatividade |
| 2 a 3 | Rotatividade moderada — atenção necessária |
| 3 a 4 | Regularidade satisfatória |
| 4 a 5 | Corpo docente muito estável |

**Por que importa:** A instabilidade do corpo docente prejudica a aprendizagem,
sobrecarrega a gestão e fragiliza os projetos pedagógicos.
""",
    "ATU": """
**O que é:** Média de estudantes em cada turma da escola ou município.

**Como é medido:** Total de alunos matriculados dividido pelo número de turmas,
considerando o Ensino Fundamental.

**Por que importa:** Turmas muito cheias aumentam a sobrecarga do professor,
dificultam o acompanhamento individual dos alunos e estão associadas
a maior rotatividade docente. É o indicador com maior impacto na regularidade
dos professores segundo a pesquisa.
""",
    "AFD": """
**O que é:** Percentual de professores que lecionam na área em que se formaram.

**Como é medido:** O Inep verifica se a formação do professor é compatível
com a disciplina e a etapa em que atua. O resultado é expresso em percentual (0 a 100%).

**Por que importa:** Quanto maior esse percentual, mais qualificado é o quadro docente
e maior tende a ser a identificação profissional do professor com seu trabalho.
""",
    "IED": """
**O que é:** Indica se os professores trabalham em várias escolas, turnos ou etapas ao mesmo tempo.

**Como é medido:** Considera o número de escolas, turnos e etapas em que cada professor atua.
Valores altos indicam que muitos professores têm jornada fragmentada entre diferentes unidades.

**Por que importa:** Professores com jornada muito fragmentada tendem a ter menor
vínculo com cada escola individualmente, o que pode afetar a continuidade pedagógica.
""",
    "ICG": """
**O que é:** Mede o grau de dificuldade de administração de uma escola.

**Como é medido:** Considera o porte da escola, o número de turnos, etapas
e modalidades de ensino oferecidas. A escala vai de **1 a 6**,
onde 1 é a escola mais simples e 6 a mais complexa.

**Por que importa:** Escolas mais complexas demandam maior esforço de gestão
e coordenação pedagógica, o que pode influenciar as condições de trabalho dos professores.
""",
}

FAIXAS_RISCO = {
    "Risco elevado": "#c0392b",
    "Atenção": "#e67e22",
    "Moderado": "#f1c40f",
    "Favorável": "#27ae60",
}


@st.cache_data
def carregar_municipal():
    df = pd.read_parquet("municipal_consolidado.parquet")
    df["CO_MUNICIPIO"] = df["CO_MUNICIPIO"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["ANO"] = df["ANO"].astype(int)
    df["NO_MUNICIPIO"] = df["NO_MUNICIPIO"].fillna("Não identificado")
    df["SG_UF"] = df["SG_UF"].fillna("??")
    return df


@st.cache_data
def carregar_escola():
    df = pd.read_parquet("escola_consolidado.parquet")
    df["CO_MUNICIPIO"] = df["CO_MUNICIPIO"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["CO_ENTIDADE"] = df["CO_ENTIDADE"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["ANO"] = df["ANO"].astype(int)
    df["NO_MUNICIPIO"] = df["NO_MUNICIPIO"].fillna("Não identificado")
    df["SG_UF"] = df["SG_UF"].fillna("??")
    df["NO_ENTIDADE"] = df["NO_ENTIDADE"].fillna("Escola não identificada")
    return df


def classificar_risco(atu, media_nacional):
    if pd.isna(atu) or pd.isna(media_nacional):
        return "Sem dados", "#aaa"
    desvio = atu - media_nacional
    if desvio >= 5:
        return "Risco elevado", "#c0392b"
    elif desvio >= 2:
        return "Atenção", "#e67e22"
    elif desvio >= 0:
        return "Moderado", "#f1c40f"
    else:
        return "Favorável", "#27ae60"


def formatar_br(valor, casas=3):
    if pd.isna(valor):
        return "—"
    return f"{float(valor):.{casas}f}".replace(".", ",")

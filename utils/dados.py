import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

FUSO_BR = ZoneInfo("America/Sao_Paulo")


def agora_br():
    """Data/hora atual no fuso de Brasília — usar em vez de datetime.now() em
    qualquer 'Gerado em' de relatório. O servidor do Streamlit Cloud roda em
    UTC; sem fuso explícito, o carimbo do relatório aparece três horas à
    frente do horário real do Brasil."""
    return datetime.now(FUSO_BR)


# Identidade e versionamento do artefato (exibidos na página Metodologia)
VERSAO_APP = "1.2"
FONTE_DADOS = "Indicadores Educacionais do Censo Escolar — Inep/MEC"
COBERTURA = "5.570 municípios (2013–2025) e 209 mil+ escolas (2019–2025)"


def aplicar_estilo_global():
    st.markdown("""
    <style>
        /* ══════════════ TIPOGRAFIA E BASE PROFISSIONAL ══════════════ */
        html, body, [class*="css"] {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont,
                         'Helvetica Neue', Arial, sans-serif !important;
            -webkit-font-smoothing: antialiased;
        }
        h1 { letter-spacing: -0.02em !important; font-weight: 700 !important; }
        h2, h3 { letter-spacing: -0.01em !important; font-weight: 650 !important;
                 color: #1a3a5c !important; }
        p, li { line-height: 1.65 !important; }

        /* Métricas com visual refinado */
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e6ecf3;
            border-radius: 10px;
            padding: 0.9rem 1.1rem;
            box-shadow: 0 1px 3px rgba(26,58,92,0.06);
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
            color: #5a7a9a !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        [data-testid="stMetricValue"] {
            color: #1a3a5c !important;
            font-weight: 700 !important;
        }


        /* ══════════════ RESPONSIVIDADE (celular e tablet) ══════════════ */
        /* Tablets e telas médias (até 1024px) */
        @media (max-width: 1024px) {
            .block-container {
                padding-left: 1.2rem !important;
                padding-right: 1.2rem !important;
            }
            [data-testid="stMetric"] { padding: 0.6rem 0.7rem !important; }
            [data-testid="stMetricValue"] { font-size: 1.35rem !important; }
            [data-testid="stMetricLabel"] { font-size: 0.68rem !important; }
            h1 { font-size: 1.5rem !important; }
            h2, h3 { font-size: 1.15rem !important; }
            .num-card p:first-child { font-size: 1.4rem !important; }
        }
        /* Celulares (até 640px) */
        @media (max-width: 640px) {
            .block-container {
                padding-left: 0.8rem !important;
                padding-right: 0.8rem !important;
            }
            [data-testid="stMetricValue"] { font-size: 1.15rem !important; }
            h1 { font-size: 1.25rem !important; }
            .num-card { border-right: none !important; }
            /* tabelas: rolagem horizontal em vez de corte */
            [data-testid="stDataFrame"] { overflow-x: auto !important; }
        }
        /* Cards numéricos da home: flexíveis em qualquer largura */
        .num-card { text-align: center; padding: 1rem; min-width: 0; }
        .num-card p { margin: 0; overflow-wrap: break-word; }


        /* Rodapé institucional */
        .rodape-regdoc { text-align: center; padding: 0.4rem 0 1rem; }
        .rodape-regdoc p { font-size: 0.78rem !important; color: #8aa0b5 !important;
                           margin: 0.15rem 0 !important; line-height: 1.5 !important; }
        @media (max-width: 640px) {
            .rodape-regdoc p { font-size: 0.7rem !important; }
        }

        /* Botões */
        .stButton > button, .stDownloadButton > button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            border: 1.5px solid #1a3a5c !important;
            color: #1a3a5c !important;
            transition: all 0.15s ease !important;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            background: #1a3a5c !important;
            color: white !important;
            box-shadow: 0 2px 8px rgba(26,58,92,0.25) !important;
        }

        /* Selectbox / inputs mais suaves */
        [data-baseweb="select"] > div,
        .stTextInput > div > div {
            border-radius: 8px !important;
        }

        /* Expanders com destaque sutil */
        [data-testid="stExpander"] {
            border: 1px solid #e6ecf3 !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 3px rgba(26,58,92,0.05);
        }

        /* Tabelas */
        [data-testid="stDataFrame"] {
            border: 1px solid #e6ecf3;
            border-radius: 10px;
            overflow: hidden;
        }

        /* ══════════════ SIDEBAR ══════════════ */
        [data-testid="stSidebar"] {
            background-color: #1a3a5c !important;
        }
        [data-testid="stSidebar"] * {
            color: #e8f0f7 !important;
        }
        [data-testid="stSidebarNav"]::before {
            content: "📊 RegDoc";
            display: block;
            font-size: 1.05rem;
            font-weight: 600;
            color: white !important;
            padding: 1.2rem 1rem 0.8rem 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.15);
            margin-bottom: 0.5rem;
        }
        [data-testid="stSidebarNav"] a {
            color: #b8cfe8 !important;
            font-size: 0.95rem !important;
            padding: 0.45rem 1rem !important;
            border-radius: 6px !important;
            margin: 2px 0.5rem !important;
            display: block !important;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background-color: rgba(255,255,255,0.15) !important;
            color: white !important;
            font-weight: 500 !important;
        }
        [data-testid="stSidebarNav"] a:hover {
            background-color: rgba(255,255,255,0.1) !important;
            color: white !important;
        }
        [data-testid="stSidebarCollapseButton"] svg {
            color: white !important;
            fill: white !important;
        }
        section[data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,0.15) !important;
        }

        /* ══════════════ MOBILE (≤ 768px) ══════════════ */
        @media (max-width: 768px) {

            /* Reduz padding geral do conteúdo */
            .block-container {
                padding-left: 0.8rem !important;
                padding-right: 0.8rem !important;
                padding-top: 1.5rem !important;
            }

            /* Títulos proporcionais à tela */
            h1 { font-size: 1.5rem !important; }
            h2 { font-size: 1.25rem !important; }
            h3 { font-size: 1.1rem !important; }

            /* Colunas empilham verticalmente */
            [data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
            }
            [data-testid="stHorizontalBlock"] > div {
                width: 100% !important;
                min-width: 100% !important;
                margin-bottom: 0.5rem;
            }

            /* Métricas compactas */
            [data-testid="stMetric"] {
                padding: 0.6rem 0.8rem;
            }
            [data-testid="stMetricValue"] {
                font-size: 1.4rem !important;
            }

            /* Tabelas com scroll horizontal */
            [data-testid="stDataFrame"] {
                overflow-x: auto !important;
            }

            /* Abas com fonte menor para caber */
            div[data-testid="stTabs"] button {
                font-size: 0.8rem !important;
                padding: 0.5rem 0.8rem !important;
                letter-spacing: 0 !important;
            }

            /* Gráficos plotly ocupam largura total */
            .js-plotly-plot {
                width: 100% !important;
            }

            /* Botões de download em largura total */
            .stDownloadButton > button,
            .stButton > button {
                width: 100% !important;
            }
        }

        /* ══════════════ TELAS MUITO PEQUENAS (≤ 480px) ══════════════ */
        @media (max-width: 480px) {
            h1 { font-size: 1.3rem !important; }
            [data-testid="stMetricValue"] {
                font-size: 1.2rem !important;
            }
            .block-container {
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data
def carregar_municipal():
    df = pd.read_parquet("municipal_consolidado.parquet")
    df["CO_MUNICIPIO"] = df["CO_MUNICIPIO"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["ANO"] = df["ANO"].astype(int)
    df["NO_MUNICIPIO"] = df["NO_MUNICIPIO"].fillna("Não identificado")
    df["SG_UF"] = df["SG_UF"].fillna("??")
    return df


@st.cache_resource(show_spinner=False)
def carregar_escola():
    # ATENÇÃO — cache_resource, e não cache_data, por causa do tamanho da base
    # (~74 MB). cache_data serializaria uma CÓPIA por sessão e estoura o limite de
    # memória do Streamlit Cloud; cache_resource devolve SEMPRE O MESMO OBJETO,
    # compartilhado entre todos os usuários.
    # Consequência: NUNCA escreva colunas no DataFrame devolvido por esta função.
    # Sempre filtre e faça .copy() antes de criar coluna — caso contrário a mutação
    # vaza para todas as sessões e só desaparece com reboot do app.
    df = pd.read_parquet("escola_consolidado.parquet")
    df["CO_MUNICIPIO"] = df["CO_MUNICIPIO"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["CO_ENTIDADE"] = df["CO_ENTIDADE"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["ANO"] = df["ANO"].astype(int)
    df["SG_UF"] = df["SG_UF"].fillna("??")
    df["NO_ENTIDADE"] = df["NO_ENTIDADE"].fillna("Escola não identificada")

    # Nome do município: o Censo grava em CAIXA ALTA e sem acento até 2015, e em caixa
    # mista com acento a partir de 2016 — por isso o mesmo município aparecia duas vezes
    # nas listas de seleção. Adota-se o nome da base municipal (grafia oficial do IBGE,
    # acentuada, em caixa mista) como versão canônica única em todo o app.
    _canon = (carregar_municipal()[["CO_MUNICIPIO", "NO_MUNICIPIO"]]
              .drop_duplicates("CO_MUNICIPIO")
              .rename(columns={"NO_MUNICIPIO": "_NO_CANON"}))
    df = df.merge(_canon, on="CO_MUNICIPIO", how="left")
    # Fallback: municípios ausentes da base municipal (ex.: instalados recentemente)
    # recebem o nome do Censo normalizado para caixa mista, com preposições em minúscula.
    _fallback = (df["NO_MUNICIPIO"].astype(str).str.title()
                 .str.replace(r"\b(Do|Da|Dos|Das|De|D)\b",
                              lambda m: m.group(0).lower(), regex=True))
    df["NO_MUNICIPIO"] = (df["_NO_CANON"].fillna(_fallback)
                          .replace({"Nan": None, "None": None})
                          .fillna("Não identificado"))
    df = df.drop(columns=["_NO_CANON"])

    # Nome canônico da escola: o Censo altera o nome quando a escola muda de rede
    # (ex.: EEEFM → EMEF após municipalização) ou é renomeada — por isso a mesma
    # escola aparecia duas vezes nas listas de seleção e a busca pelo nome antigo
    # devolvia vazio no ano de referência. Adota-se o nome mais recente da série
    # como versão única em todo o app; o nome original de cada ano fica preservado
    # em NO_ENTIDADE_CENSO para rastreabilidade.
    df["NO_ENTIDADE_CENSO"] = df["NO_ENTIDADE"]
    _nome_atual = (df.sort_values("ANO")
                     .drop_duplicates("CO_ENTIDADE", keep="last")
                     [["CO_ENTIDADE", "NO_ENTIDADE"]]
                     .rename(columns={"NO_ENTIDADE": "_NOME_ATUAL"}))
    df = df.merge(_nome_atual, on="CO_ENTIDADE", how="left")
    df["NO_ENTIDADE"] = df["_NOME_ATUAL"].fillna(df["NO_ENTIDADE"])
    df = df.drop(columns=["_NOME_ATUAL"])
    return df


@st.cache_data
def carregar_saeb():
    df = pd.read_parquet("saeb_escola_consolidado.parquet")
    df["CO_ENTIDADE"] = df["CO_ENTIDADE"].astype(str).str.replace(r"\.0$", "", regex=True)
    return df


def classificar_risco(ird, media_nacional):
    if pd.isna(ird) or pd.isna(media_nacional):
        return "Sem dados", "#aaa"
    if ird < media_nacional * 0.85:
        return "Alerta", "#c0392b"
    elif ird < media_nacional:
        return "Atenção", "#e67e22"
    elif ird < media_nacional * 1.1:
        return "Moderado", "#f1c40f"
    else:
        return "Favorável", "#27ae60"


# ── Cronicidade do alerta (compartilhada por Home, Ranking e Município) ────────
@st.cache_data(show_spinner=False)
def calcular_anos_em_alerta(ano_ref):
    """Para cada município, conta há quantos ANOS CONSECUTIVOS (terminando em
    ano_ref) o IRD está abaixo de 85% da média nacional daquele ano — o mesmo
    critério de "Alerta" usado em todo o app.

    Um ano sem dados interrompe a contagem (critério conservador).
    Retorna um DataFrame com CO_MUNICIPIO e ANOS_EM_ALERTA (>= 1 apenas para
    municípios em alerta no próprio ano de referência).
    """
    df = carregar_municipal().dropna(subset=["IRD"]).copy()
    df = df[df["ANO"] <= int(ano_ref)]

    # Média nacional de cada ano e flag de alerta ano a ano
    df["MEDIA_ANO"] = df.groupby("ANO")["IRD"].transform("mean")
    df["ALERTA"] = df["IRD"] < df["MEDIA_ANO"] * 0.85

    # Ordena do ano de referência para trás e exige sequência sem buracos
    df = df.sort_values(["CO_MUNICIPIO", "ANO"], ascending=[True, False])
    df["POS"] = df.groupby("CO_MUNICIPIO").cumcount()
    df["ANO_ESPERADO"] = int(ano_ref) - df["POS"]
    df["SEGUE"] = df["ALERTA"] & (df["ANO"] == df["ANO_ESPERADO"])

    # A sequência quebra no primeiro ano que não atende ao critério
    df["QUEBROU"] = (~df["SEGUE"]).groupby(df["CO_MUNICIPIO"]).cummax()
    streak = (df[~df["QUEBROU"]]
              .groupby("CO_MUNICIPIO").size()
              .rename("ANOS_EM_ALERTA").reset_index())
    return streak


def rotulo_cronicidade(anos):
    """Traduz a contagem em linguagem de gestão."""
    if pd.isna(anos) or anos <= 0:
        return "—"
    anos = int(anos)
    if anos == 1:
        return "1º ano em alerta"
    if anos <= 3:
        return f"{anos} anos seguidos"
    return f"{anos} anos seguidos ⚠️ crônico"


# ── Grupo de pares (municípios comparáveis) ────────────────────────────────────
@st.cache_data(show_spinner=False)
def tabela_pares(ano_ref, rede="Todas as redes"):
    """Classifica todos os municípios do ano em grupos de comparação:
    quartil nacional de complexidade (ICG) × faixa de porte da rede
    (nº de escolas da rede selecionada). Retorna (DataFrame, ano_usado_para_porte).

    O porte vem da base de escolas (disponível a partir de 2019); para anos
    anteriores usa-se o ano mais próximo disponível como proxy estrutural.
    """
    ano_ref = int(ano_ref)
    df = municipal_por_rede(rede)
    df_ano = df[df["ANO"] == ano_ref].dropna(subset=["IRD", "ICG"]).copy()
    if df_ano.empty:
        return df_ano, ano_ref

    # Porte: nº de escolas municipais por município
    esc = carregar_escola()
    anos_esc = sorted(esc["ANO"].unique())
    ano_porte = ano_ref if ano_ref in anos_esc else min(anos_esc, key=lambda a: abs(a - ano_ref))
    esc_ano = esc[esc["ANO"] == ano_porte]
    if rede != "Todas as redes":
        esc_ano = esc_ano[esc_ano["NO_DEPENDENCIA"].astype(str) == rede]
    porte = (esc_ano.groupby("CO_MUNICIPIO")["CO_ENTIDADE"]
             .nunique().rename("N_ESCOLAS").reset_index())
    df_ano = df_ano.merge(porte, on="CO_MUNICIPIO", how="left")
    df_ano["N_ESCOLAS"] = df_ano["N_ESCOLAS"].fillna(0).astype(int)

    # Faixas de complexidade (quartis nacionais; rank evita erro de limites repetidos)
    rotulos_icg = ["complexidade baixa", "complexidade média-baixa",
                   "complexidade média-alta", "complexidade alta"]
    df_ano["FAIXA_ICG"] = pd.qcut(df_ano["ICG"].rank(method="first"), 4, labels=rotulos_icg)

    # Faixas de porte
    df_ano["FAIXA_PORTE"] = pd.cut(
        df_ano["N_ESCOLAS"], bins=[-1, 5, 15, 40, 10**6],
        labels=["até 5 escolas", "6 a 15 escolas", "16 a 40 escolas", "mais de 40 escolas"]
    )
    return df_ano, ano_porte


# ── Visão municipal por rede (dependência administrativa) ─────────────────────
REDES_DISPONIVEIS = ["Todas as redes", "Municipal", "Estadual", "Privada"]

@st.cache_data(show_spinner=False)
def municipal_por_rede(rede):
    """Retorna o consolidado municipal (mesmas colunas de carregar_municipal),
    calculado apenas com as escolas da rede escolhida.

    Para "Todas as redes", devolve o consolidado original — garantindo que os
    números padrão do app não mudam.
    """
    if rede == "Todas as redes":
        return carregar_municipal()
    esc = carregar_escola()
    esc = esc[esc["NO_DEPENDENCIA"].astype(str) == rede]
    agg = (esc.groupby(["CO_MUNICIPIO", "ANO"])
              .agg(IRD=("IRD", "mean"), ICG=("ICG", "mean"),
                   AFD=("AFD", "mean"), ATU=("ATU", "mean"),
                   IED=("IED", "mean"),
                   NO_MUNICIPIO=("NO_MUNICIPIO", "first"),
                   SG_UF=("SG_UF", "first"))
              .reset_index())
    return agg


# ── Rodapé institucional (usado por todas as páginas) ──────────────────────────
def rodape_institucional():
    st.markdown("---")
    st.markdown("""
    <div class="rodape-regdoc">
        <p><strong>RegDoc — Regularidade Docente</strong> · Fonte: Censo Escolar / Inep · Dados públicos, uso gratuito.</p>
        <p>© 2026 <strong>Joelma Barcellos Santanna</strong> · Desenvolvido no Doutorado Profissional em
        Administração e Contabilidade — linha Gestão Escolar — FUCAPE Business School.</p>
    </div>
    """, unsafe_allow_html=True)


def formatar_br(valor, casas=3):
    if pd.isna(valor):
        return "—"
    return f"{float(valor):.{casas}f}".replace(".", ",")


# ── Tendência histórica (compartilhada por Município e Escola) ────────────────
def classificar_tendencia(df, ano_ref, janela=5):
    """Classifica a trajetória do IRD até ano_ref.

    A tendência é estimada por regressão linear sobre os últimos `janela`
    anos disponíveis (mínimo de 3), janela coerente com a do próprio IRD.
    A ruptura (queda >= 0,5 ponto de um ano para o outro) é verificada
    sobre toda a série disponível.
    """
    hist = (df[df["ANO"] <= ano_ref]
            .sort_values("ANO").dropna(subset=["IRD"]))
    if len(hist) < 3:
        return None

    # Ruptura: série completa
    vals_full = hist["IRD"].values
    anos_full = hist["ANO"].values
    ruptura, ano_ruptura = False, None
    for i in range(1, len(anos_full)):
        if vals_full[i] - vals_full[i - 1] <= -0.5:
            ruptura, ano_ruptura = True, int(anos_full[i])
            break

    # Tendência: janela móvel dos últimos N anos
    jan = hist.tail(janela) if len(hist) >= janela else hist
    if len(jan) < 3:
        jan = hist
    anos    = jan["ANO"].values.astype(float)
    valores = jan["IRD"].values
    slope   = np.polyfit(anos - anos.mean(), valores, 1)[0]
    variacao = valores[-1] - valores[0]
    ano_ini  = int(jan["ANO"].iloc[0])

    if slope <= -0.15:
        return {"icone": "📉", "cor_fundo": "#fdedec", "cor_borda": "#c0392b",
                "texto": f"Em queda acelerada — perdeu {abs(variacao):.2f} pontos desde {ano_ini} "
                         f"({slope:.2f} pts/ano em média). Requer ação imediata.",
                "ruptura": ruptura, "ano_ruptura": ano_ruptura}
    elif slope <= -0.05:
        return {"icone": "↘️", "cor_fundo": "#fef9e7", "cor_borda": "#f39c12",
                "texto": f"Tendência de queda desde {ano_ini} "
                         f"({variacao:+.2f} pontos acumulados). "
                         "Monitorar com atenção — se mantida, atingirá nível crítico.",
                "ruptura": ruptura, "ano_ruptura": ano_ruptura}
    elif slope < 0.05:
        return {"icone": "➡️", "cor_fundo": "#f0f4f8", "cor_borda": "#7f8c8d",
                "texto": f"Estável desde {ano_ini} (variação de {variacao:+.2f} pontos). "
                         + ("Estabilidade positiva — IRD em nível satisfatório." if valores[-1] >= 3.0
                            else "Estabilidade preocupante — IRD estagnado abaixo de 3,0."),
                "ruptura": ruptura, "ano_ruptura": ano_ruptura}
    elif slope < 0.15:
        return {"icone": "↗️", "cor_fundo": "#eafaf1", "cor_borda": "#27ae60",
                "texto": f"Em recuperação desde {ano_ini} "
                         f"(+{variacao:.2f} pontos acumulados). "
                         "Ações de retenção docente parecem estar surtindo efeito.",
                "ruptura": False, "ano_ruptura": None}
    else:
        return {"icone": "📈", "cor_fundo": "#eafaf1", "cor_borda": "#27ae60",
                "texto": f"Melhora expressiva desde {ano_ini} "
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


def sombrear_pandemia(fig):
    """Sombreia 2020–2021 nos gráficos históricos: o Censo desses anos reflete
    políticas emergenciais da pandemia, não o comportamento típico da rede."""
    fig.add_vrect(x0=2019.5, x1=2021.5, fillcolor="#95a5a6",
                  opacity=0.12, line_width=0)
    fig.add_annotation(x=2020.5, y=1.0, yref="paper", yanchor="bottom",
                       text="pandemia", showarrow=False,
                       font=dict(size=10, color="#7f8c8d"))
    return fig


# ── Leitura em texto do ranking de escolas ────────────────────────────────────
# Os cards e a tabela dizem QUANTO. Este bloco diz O QUE ISSO SIGNIFICA naquela
# rede, em linguagem de gestão — sem jargão estatístico. É gerado a partir dos
# próprios dados do município, e não de um texto fixo: as frases mudam conforme
# o retrato da rede. Degrada com elegância quando há poucas escolas no filtro.

def leitura_ranking(df_rank, ird_mun, media_nac, municipio, ano):
    """Devolve um bloco HTML com a leitura gerencial do ranking de escolas.

    Usado tanto na tela (st.markdown) quanto no relatório exportado, para que
    o gestor leve para a reunião o mesmo texto que leu no app.
    """
    if df_rank is None or df_rank.empty:
        return ""

    d = df_rank.copy()
    total = len(d)
    n_alerta = int((d["RISCO"] == "Alerta").sum())
    n_atencao = int((d["RISCO"] == "Atenção").sum())
    n_favoravel = int((d["RISCO"] == "Favorável").sum())
    pct_alerta = (n_alerta / total * 100) if total else 0

    def _media(col):
        return d[col].mean() if col in d.columns and d[col].notna().any() else float("nan")

    icg_m, atu_m = _media("ICG"), _media("ATU")
    afd_m, ied_m = _media("AFD"), _media("IED")

    acima = pd.notna(ird_mun) and pd.notna(media_nac) and ird_mun >= media_nac
    comp_nac = "acima" if acima else "abaixo"

    # ── Parágrafo 1: o que é regularidade e onde a rede está ──────────────────
    p1 = (
        f"<b>Regularidade (IRD)</b> mede o quanto o corpo docente permaneceu na escola "
        f"ao longo dos últimos cinco anos, numa escala de 0 a 5. Não é a rotatividade de "
        f"um ano: é a marca acumulada da permanência. Quanto mais alto, mais estável a equipe. "
        f"Em {municipio}, a média das escolas é <b>{formatar_br(ird_mun, 3)}</b>, "
        f"<b>{comp_nac}</b> da média nacional de {formatar_br(media_nac, 3)} em {ano}."
    )

    # ── Parágrafo 2: as faixas são relativas, não notas ───────────────────────
    p2 = (
        f"<b>Situação</b> não é uma nota fixa — é uma posição relativa, e por isso muda "
        f"conforme a rede. <b>Favorável</b>: a escola tem regularidade igual ou acima da média "
        f"nacional ({formatar_br(media_nac, 3)}). <b>Atenção</b>: está acima da média do próprio "
        f"município ({formatar_br(ird_mun, 3)}), mas ainda abaixo da nacional. <b>Alerta</b>: "
        f"está abaixo da média da sua própria rede — ou seja, perde professores mais rápido "
        f"que a média das escolas vizinhas, sob a mesma gestão e as mesmas regras."
    )

    if total >= 2:
        p2 += (
            f" Neste recorte, <b>{n_alerta} de {total} escolas</b> "
            f"({formatar_br(pct_alerta, 1)}%) estão em alerta, {n_atencao} em atenção e "
            f"{n_favoravel} em situação favorável."
        )

    # ── Parágrafo 3: o que cada coluna de contexto acrescenta ─────────────────
    p3 = (
        "<b>As demais colunas explicam o contexto</b> em que essa permanência acontece. "
        "<b>Complexidade (ICG)</b> vai de 1 a 6 e resume o tamanho e a variedade da escola "
        "(porte, turnos, etapas ofertadas): uma escola complexa com regularidade baixa é um "
        "problema diferente de uma escola simples com regularidade baixa — a primeira pede "
        "apoio estrutural, a segunda costuma responder a ajustes de gestão. "
        "<b>Alunos por turma</b> indica a carga de sala. "
        "<b>Formação (%)</b> é a proporção de professores com formação adequada à disciplina "
        "que lecionam. <b>Esforço docente (%)</b> mede o desgaste: quantos turnos, turmas, "
        "escolas e alunos cada professor acumula — quanto mais alto, mais espalhado está o "
        "professor, e maior a chance de ele sair."
    )

    ctx = []
    if pd.notna(icg_m):
        ctx.append(f"complexidade média de {formatar_br(icg_m, 2)}")
    if pd.notna(atu_m):
        ctx.append(f"{formatar_br(atu_m, 1)} alunos por turma")
    if pd.notna(afd_m):
        ctx.append(f"{formatar_br(afd_m, 1)}% de formação adequada")
    if pd.notna(ied_m):
        ctx.append(f"{formatar_br(ied_m, 1)}% de esforço docente")
    if ctx and total >= 2:
        p3 += f" Na média deste recorte: {', '.join(ctx)}."

    # ── Parágrafo 4: o contraste que aponta onde investigar ───────────────────
    # Só faz sentido com escolas nos dois extremos; com 1 ou 2 escolas, calar.
    p4 = ""
    if n_alerta >= 3 and n_favoravel >= 3:
        al = d[d["RISCO"] == "Alerta"]
        fv = d[d["RISCO"] == "Favorável"]
        pistas = []
        for col, rotulo, casas, sufixo in [
            ("IED", "esforço docente", 1, "%"),
            ("ICG", "complexidade", 2, ""),
            ("ATU", "alunos por turma", 1, ""),
            ("AFD", "formação adequada", 1, "%"),
        ]:
            if col in d.columns and al[col].notna().any() and fv[col].notna().any():
                m_al, m_fv = al[col].mean(), fv[col].mean()
                if pd.notna(m_al) and pd.notna(m_fv) and abs(m_al - m_fv) > 0.01:
                    direcao = "maior" if m_al > m_fv else "menor"
                    pistas.append(
                        f"{rotulo} <b>{direcao}</b> ({formatar_br(m_al, casas)}{sufixo} "
                        f"contra {formatar_br(m_fv, casas)}{sufixo})"
                    )
        if pistas:
            p4 = (
                f"<b>Onde investigar primeiro.</b> Comparadas às escolas em situação favorável, "
                f"as {n_alerta} escolas em alerta desta rede têm, em média, "
                + "; ".join(pistas[:3]) + ". "
                "São <b>pistas, não causas</b>: apontam a hipótese que vale testar com a "
                "direção da escola, não o motivo comprovado da saída dos professores."
            )

    # ── Ressalva final: a fronteira do instrumento ────────────────────────────
    p5 = (
        "<b>O que esta tabela não responde.</b> Ela mostra <i>onde</i> a permanência é frágil "
        "e <i>em que condições</i> — nunca <i>por quê</i>. A causa se confirma na escola: "
        "escuta dos professores, análise do vínculo, da remuneração e do clima. "
        "A leitura é sempre da escola ou da rede, nunca do desempenho de um professor "
        "ou de um diretor."
    )

    paragrafos = "".join(
        f"<p style='margin:0 0 0.7rem;'>{p}</p>" for p in [p1, p2, p3, p4, p5] if p
    )

    return f"""
<div style="background:#f7f9fc; border:1px solid #dde4ed; border-left:5px solid #1a3a5c;
     border-radius:0 10px 10px 0; padding:1.1rem 1.4rem; margin:1rem 0;
     font-size:0.92rem; line-height:1.6; color:#2c3e50;">
  <p style="margin:0 0 0.8rem; font-weight:700; color:#1a3a5c; font-size:1rem;">
    📖 Como ler esta tabela — {municipio}, {ano}
  </p>
  {paragrafos}
</div>"""

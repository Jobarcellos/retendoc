"""IED — Indicador de Esforço Docente, como o Inep publica.

O Inep classifica cada docente em seis níveis de esforço (1 = rotina mais leve,
6 = rotina mais pesada) e publica, por escola, município, UF e Brasil, o
percentual de docentes em cada nível, separado por etapa. O indicador que o Inep
destaca é o percentual de docentes com esforço elevado:
    anos iniciais  -> níveis 5 e 6
    anos finais    -> nível 6
    ensino médio   -> nível 6
(Nota Técnica Inep nº 039/2014.)

Os arquivos ficam fora das bases principais e são lidos sob demanda, só para as
escolas e municípios em tela, para não aumentar o uso de memória do app.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ARQ_ESCOLA = "ied_niveis_escola.parquet"
ARQ_MUNICIPIO = "ied_niveis_municipio.parquet"
ARQ_BRASIL_UF = "ied_niveis_brasil_uf.parquet"

ETAPAS = {"AI": "Anos iniciais", "AF": "Anos finais", "EM": "Ensino médio"}
NIVEIS_ELEVADOS = {"AI": (5, 6), "AF": (6,), "EM": (6,)}
COLS_NIVEIS = [f"IED_{e}_N{n}" for e in ETAPAS for n in range(1, 7)]
COLS_ELEVADO = {
    "ELEV_AI": "Esforço elevado: anos iniciais (%)",
    "ELEV_AF": "Esforço elevado: anos finais (%)",
    "ELEV_EM": "Esforço elevado: ensino médio (%)",
}
# Rede do app -> rótulo da rede nas planilhas do Inep
REDE_INEP = {"Todas as redes": "Total", "Municipal": "Municipal",
             "Estadual": "Estadual", "Privada": "Privada"}

# Rampa sequencial (um só tom, do claro ao escuro) na cor do RegDoc
CORES_NIVEIS = ["#dce8f4", "#b5cee6", "#86aed4", "#5688bb", "#2e6199", "#1a3a5c"]
TINTA_NIVEIS = ["#1a3a5c", "#1a3a5c", "#1a3a5c", "#ffffff", "#ffffff", "#ffffff"]

TOOLTIP_IED = (
    "IED — Indicador de Esforço Docente (Inep). Mede o peso da rotina de trabalho do "
    "professor. O Inep classifica cada docente em seis níveis, de 1 (rotina mais leve) "
    "a 6 (rotina mais pesada), conforme o número de alunos, escolas, turnos e etapas em "
    "que atua, e publica o percentual de docentes em cada nível. O destaque é o "
    "percentual com esforço elevado: níveis 5 e 6 nos anos iniciais; nível 6 nos anos "
    "finais e no ensino médio. Quanto MAIOR, mais professores com rotina pesada. "
    "Não indica duplo vínculo. Fonte: Censo Escolar/Inep, Nota Técnica nº 039/2014."
)


def _ler(arquivo, filtros=None, colunas=None):
    try:
        return pd.read_parquet(arquivo, filters=filtros, columns=colunas)
    except (FileNotFoundError, OSError):
        return pd.DataFrame()


def com_elevado(df):
    """Acrescenta ELEV_AI, ELEV_AF e ELEV_EM (percentual com esforço elevado)."""
    if df is None or df.empty:
        return df
    df = df.copy()
    for e, niveis in NIVEIS_ELEVADOS.items():
        cols = [f"IED_{e}_N{n}" for n in niveis]
        if all(c in df.columns for c in cols):
            df[f"ELEV_{e}"] = df[cols].astype("float64").sum(axis=1, min_count=len(cols)).round(1)
    return df


@st.cache_data(show_spinner=False, max_entries=512)
def ied_escolas(codigos, anos=None):
    """Níveis do IED das escolas indicadas (tupla de CO_ENTIDADE em texto)."""
    codigos = [str(c) for c in codigos]
    if not codigos:
        return pd.DataFrame()
    filtros = [("CO_ENTIDADE", "in", codigos)]
    if anos:
        filtros.append(("ANO", "in", [int(a) for a in anos]))
    df = _ler(ARQ_ESCOLA, filtros)
    if not df.empty:
        df["ANO"] = df["ANO"].astype(int)
    return com_elevado(df)


@st.cache_data(show_spinner=False, max_entries=256)
def ied_escolas_municipio(co_municipio, ano=None):
    """Níveis do IED de todas as escolas de um município."""
    filtros = [("CO_MUNICIPIO", "==", str(co_municipio))]
    if ano is not None:
        filtros.append(("ANO", "==", int(ano)))
    df = _ler(ARQ_ESCOLA, filtros)
    if not df.empty:
        df["ANO"] = df["ANO"].astype(int)
    return com_elevado(df)


@st.cache_data(show_spinner=False, max_entries=256)
def ied_municipios(codigos=None, rede="Todas as redes", anos=None):
    """Níveis do IED publicados pelo Inep para o município, na rede escolhida."""
    filtros = [("REDE", "==", REDE_INEP.get(rede, "Total"))]
    if codigos:
        filtros.append(("CO_MUNICIPIO", "in", [int(c) for c in codigos]))
    if anos:
        filtros.append(("ANO", "in", [int(a) for a in anos]))
    df = _ler(ARQ_MUNICIPIO, filtros, ["CO_MUNICIPIO", "ANO", "REDE"] + COLS_NIVEIS)
    if not df.empty:
        df["CO_MUNICIPIO"] = df["CO_MUNICIPIO"].astype(str)
        df["ANO"] = df["ANO"].astype(int)
    return com_elevado(df)


@st.cache_data(show_spinner=False, max_entries=256)
def ied_brasil_uf(unidade="BR", rede="Todas as redes", anos=None):
    """Níveis do IED publicados pelo Inep para o Brasil ('BR') ou para uma UF (sigla)."""
    filtros = [("UNIDADE", "==", unidade), ("REDE", "==", REDE_INEP.get(rede, "Total"))]
    if anos:
        filtros.append(("ANO", "in", [int(a) for a in anos]))
    df = _ler(ARQ_BRASIL_UF, filtros, ["UNIDADE", "ANO", "REDE"] + COLS_NIVEIS)
    if not df.empty:
        df["ANO"] = df["ANO"].astype(int)
    return com_elevado(df)


def linha_ou_vazia(df):
    """Primeira linha do recorte, ou uma série vazia."""
    if df is None or df.empty:
        return pd.Series(dtype="float64")
    return df.iloc[0]


def fmt_pct(v, casas=1):
    if v is None or pd.isna(v):
        return "—"
    return f"{v:.{casas}f}".replace(".", ",") + "%"


def etapas_com_dado(linha):
    return [e for e in ETAPAS if pd.notna(linha.get(f"ELEV_{e}"))]


def resumo_html(linha, cor="#1a3a5c"):
    """Esforço elevado por etapa, em linhas curtas (para cards)."""
    partes = []
    for e, nome in ETAPAS.items():
        v = linha.get(f"ELEV_{e}") if linha is not None else None
        if v is not None and pd.notna(v):
            partes.append(
                f"<div style='display:flex;justify-content:space-between;gap:8px;'>"
                f"<span>{nome}</span><strong style='color:{cor};'>{fmt_pct(v)}</strong></div>")
    return "".join(partes) or "<div>—</div>"


def resumo_texto(linha):
    partes = [f"{nome.lower()} {fmt_pct(linha.get(f'ELEV_{e}'))}"
              for e, nome in ETAPAS.items() if pd.notna(linha.get(f"ELEV_{e}"))]
    return "; ".join(partes) if partes else "—"


def colunas_elevado_formatadas(df, casas=1):
    """Copia as colunas ELEV_* com os rótulos de tabela e o número em formato brasileiro."""
    out = pd.DataFrame(index=df.index)
    for c, rot in COLS_ELEVADO.items():
        if c in df.columns:
            out[rot] = df[c].apply(lambda v: fmt_pct(v, casas).replace("%", "") if pd.notna(v) else "—")
    return out


def grafico_niveis(linha, titulo=None, altura=None):
    """Barras 100% empilhadas: uma por etapa, seis segmentos (níveis 1 a 6)."""
    etapas = [e for e in ETAPAS
              if all(pd.notna(linha.get(f"IED_{e}_N{n}")) for n in range(1, 7))]
    if not etapas:
        return None
    nomes = [ETAPAS[e] for e in etapas][::-1]
    fig = go.Figure()
    for n in range(1, 7):
        vals = [float(linha.get(f"IED_{e}_N{n}")) for e in etapas][::-1]
        fig.add_trace(go.Bar(
            y=nomes, x=vals, orientation="h", name=f"Nível {n}",
            marker=dict(color=CORES_NIVEIS[n - 1], line=dict(color="#ffffff", width=2)),
            text=[fmt_pct(v, 0) if v >= 7 else "" for v in vals],
            textposition="inside", insidetextanchor="middle",
            textfont=dict(color=TINTA_NIVEIS[n - 1], size=12),
            hovertemplate="<b>%{y}</b><br>Nível " + str(n) + ": %{x:.1f}%<extra></extra>",
        ))
    elev = [linha.get(f"ELEV_{e}") for e in etapas][::-1]
    for y, v, e in zip(nomes, elev, etapas[::-1]):
        rot = "níveis 5 e 6" if e == "AI" else "nível 6"
        fig.add_annotation(x=1.01, xref="paper", y=y, xanchor="left", showarrow=False,
                           text=f"<b>{fmt_pct(v)}</b> com esforço elevado ({rot})",
                           font=dict(size=12, color="#333"))
    fig.update_layout(
        barmode="stack", height=altura or (90 + 52 * len(etapas)),
        margin=dict(l=10, r=250, t=40 if titulo else 10, b=10),
        title=dict(text=titulo, font=dict(size=14, color="#1a3a5c")) if titulo else None,
        xaxis=dict(range=[0, 100], ticksuffix="%", showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, automargin=True, ticksuffix="  "), plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        legend=dict(orientation="h", y=-0.25, x=0, traceorder="normal",
                    title=dict(text="Rotina mais leve → mais pesada: ")),
        bargap=0.35,
    )
    return fig

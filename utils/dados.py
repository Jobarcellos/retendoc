import pandas as pd
import numpy as np
import streamlit as st

# Identidade e versionamento do artefato (exibidos na página Metodologia)
VERSAO_APP = "1.1"
FONTE_DADOS = "Indicadores Educacionais do Censo Escolar — Inep/MEC"
COBERTURA = "5.570 municípios (2013–2025) e 209 mil+ escolas (2019–2025)"


def aplicar_estilo_global():
    st.markdown("""
    <style>
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
    fig.add_annotation(x=2020.5, y=5.05, text="pandemia", showarrow=False,
                       font=dict(size=10, color="#7f8c8d"))
    return fig

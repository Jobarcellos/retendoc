import streamlit as st

st.set_page_config(
    page_title="RegDoc — Regularidade Docente",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Menu lateral — fundo azul escuro */
    [data-testid="stSidebar"] {
        background-color: #1a3a5c !important;
    }
    [data-testid="stSidebar"] * {
        color: #e8f0f7 !important;
    }

    /* Logo/título no topo do menu */
    [data-testid="stSidebarNav"]::before {
        content: "📊 RegDoc";
        display: block;
        font-size: 1.1rem;
        font-weight: 600;
        color: white !important;
        padding: 1.2rem 1rem 0.5rem 1rem;
        border-bottom: 1px solid rgba(255,255,255,0.15);
        margin-bottom: 0.5rem;
    }

    /* Itens do menu */
    [data-testid="stSidebarNav"] a {
        color: #b8cfe8 !important;
        font-size: 0.95rem !important;
        padding: 0.5rem 1rem !important;
        border-radius: 6px !important;
        margin: 2px 0.5rem !important;
        display: block !important;
        transition: background 0.2s !important;
    }

    /* Item ativo */
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background-color: rgba(255,255,255,0.15) !important;
        color: white !important;
        font-weight: 500 !important;
    }

    /* Hover nos itens */
    [data-testid="stSidebarNav"] a:hover {
        background-color: rgba(255,255,255,0.1) !important;
        color: white !important;
    }

    /* Linha divisória no menu */
    [data-testid="stSidebarNav"] {
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }

    /* Botão de fechar/abrir menu */
    [data-testid="stSidebarCollapseButton"] {
        color: white !important;
    }

    /* Página principal */
    .bloco-topo {
        background: linear-gradient(135deg, #1a3a5c 0%, #2e6da4 100%);
        color: white;
        padding: 2.5rem 3rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    .bloco-topo h1 { color: white; margin: 0; font-size: 2.2rem; }
    .bloco-topo p  { color: #b8cfe8; margin: 0.5rem 0 0 0; font-size: 1.05rem; }
    .card-nav {
        border: 1px solid #dde4ed;
        border-radius: 10px;
        padding: 1.4rem 1.6rem;
        background: #f7f9fc;
        height: 100%;
    }
    .card-nav:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    .card-nav h4 { margin: 0 0 0.5rem 0; color: #1a3a5c; font-size: 1.05rem; }
    .card-nav p  { margin: 0; color: #555; font-size: 0.9rem; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="bloco-topo">
    <h1>📊 RegDoc — Regularidade Docente</h1>
    <p>Monitoramento da permanência dos professores nas redes municipais brasileiras · 2013–2025</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("""
    <div style="text-align:center; padding:1rem; border-right:1px solid #eee;">
        <p style="font-size:2rem; font-weight:bold; color:#1a3a5c; margin:0;">5.570</p>
        <p style="font-size:0.85rem; color:#777; margin:0;">municípios monitorados</p>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div style="text-align:center; padding:1rem; border-right:1px solid #eee;">
        <p style="font-size:2rem; font-weight:bold; color:#1a3a5c; margin:0;">209 mil</p>
        <p style="font-size:0.85rem; color:#777; margin:0;">escolas acompanhadas</p>
    </div>""", unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div style="text-align:center; padding:1rem; border-right:1px solid #eee;">
        <p style="font-size:2rem; font-weight:bold; color:#1a3a5c; margin:0;">13 anos</p>
        <p style="font-size:0.85rem; color:#777; margin:0;">de série histórica</p>
    </div>""", unsafe_allow_html=True)
with col4:
    st.markdown("""
    <div style="text-align:center; padding:1rem;">
        <p style="font-size:2rem; font-weight:bold; color:#c0392b; margin:0;">622</p>
        <p style="font-size:0.85rem; color:#777; margin:0;">municípios em alerta (2024)</p>
    </div>""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("### Selecione o que você quer analisar")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("""
    <div class="card-nav">
        <h4>🗺️ Painel da Rede</h4>
        <p>Veja como está a regularidade dos professores em todo o Brasil ou no seu estado. Compare estados e acompanhe a evolução ao longo dos anos.</p>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/1_Painel_da_Rede.py", label="Acessar →")

with col2:
    st.markdown("""
    <div class="card-nav">
        <h4>🔍 Município</h4>
        <p>Acompanhe a evolução de um município específico e compare com as médias nacionais e estaduais.</p>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/2_Municipio.py", label="Acessar →")

with col3:
    st.markdown("""
    <div class="card-nav">
        <h4>⚠️ Ranking</h4>
        <p>Identifique quais municípios precisam de atenção prioritária. Filtre por estado e baixe a lista completa.</p>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/3_Ranking.py", label="Acessar →")

with col4:
    st.markdown("""
    <div class="card-nav">
        <h4>🏫 Escola</h4>
        <p>Consulte a situação de uma escola específica com histórico completo, comparações e classificação de risco.</p>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/4_Escola.py", label="Acessar →")

st.markdown("---")
st.markdown("""
**Sobre o RegDoc**

O RegDoc transforma dados oficiais do Censo Escolar (Inep) em informação de apoio à gestão educacional.
Os dados cobrem 5.570 municípios brasileiros de 2013 a 2025.
A regularidade dos professores é medida pelo Indicador de Regularidade do Docente (IRD),
numa escala de 0 a 5 — quanto maior, mais estável é o corpo docente da escola ou município.
""")

st.set_page_config(
    page_title="RegDoc — Regularidade Docente",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

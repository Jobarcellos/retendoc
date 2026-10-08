import streamlit as st

st.set_page_config(
    page_title="RegDoc — Regularidade Docente",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    [data-testid="stSidebarNav"] { font-size: 0.95rem; }
    .bloco-topo {
        background: #1a3a5c;
        color: white;
        padding: 2rem 2.5rem 1.5rem 2.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    .bloco-topo h1 { color: white; margin: 0; font-size: 2rem; }
    .bloco-topo p  { color: #b8cfe8; margin: 0.4rem 0 0 0; font-size: 1rem; }
    .card-nav {
        border: 1px solid #dde4ed;
        border-radius: 8px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.8rem;
        background: #f7f9fc;
    }
    .card-nav h4 { margin: 0 0 0.3rem 0; color: #1a3a5c; }
    .card-nav p  { margin: 0; color: #555; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="bloco-topo">
    <h1>📊 RegDoc — Regularidade Docente</h1>
    <p>Instrumento de monitoramento da permanência docente nas redes municipais brasileiras · 2013–2025</p>
</div>
""", unsafe_allow_html=True)

st.markdown("### Selecione uma análise no menu lateral ou explore as opções abaixo:")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="card-nav">
        <h4>🗺️ Painel da Rede</h4>
        <p>Visão nacional do IRD por UF e município. Identifique padrões e desigualdades territoriais.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card-nav">
        <h4>🔍 Análise por Município</h4>
        <p>Evolução temporal dos indicadores de um município. Compare com a média nacional e estadual.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="card-nav">
        <h4>⚠️ Ranking de Atenção</h4>
        <p>Municípios priorizados por risco à regularidade docente, com base nos determinantes do modelo estimado.</p>
    </div>
    """, unsafe_allow_html=True)



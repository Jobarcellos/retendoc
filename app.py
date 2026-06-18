import streamlit as st

st.set_page_config(
    page_title="RegDoc — Regularidade Docente",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
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
    <p>Monitoramento da permanência dos professores nas redes municipais brasileiras · 2013–2025</p>
</div>
""", unsafe_allow_html=True)

st.markdown("### O que você quer analisar?")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="card-nav">
        <h4>🗺️ Painel da Rede</h4>
        <p>Veja como está a regularidade dos professores em todo o Brasil ou no seu estado.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card-nav">
        <h4>🔍 Município</h4>
        <p>Acompanhe a evolução de um município específico e compare com as médias nacionais.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="card-nav">
        <h4>⚠️ Ranking</h4>
        <p>Identifique quais municípios precisam de atenção prioritária da gestão.</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="card-nav">
        <h4>🏫 Escola</h4>
        <p>Consulte a situação de uma escola específica com histórico e comparações.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
**Sobre o RegDoc**

O RegDoc transforma dados oficiais do Censo Escolar (Inep) em informação de apoio
à gestão educacional. Os indicadores cobrem 5.570 municípios brasileiros de 2013 a 2025.

Use o menu lateral para navegar entre as análises.
""")

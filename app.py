import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Roteador do app. O primeiro item do menu precisa ter o nome "Início" (no modo
# antigo de páginas, o nome vinha do arquivo de entrada: "app"). O conteúdo da
# página inicial está em inicio.py; as demais páginas continuam em pages/.
paginas = [
    st.Page("inicio.py", title="Início", default=True),
    st.Page("pages/1_Painel_da_Rede.py", title="Painel da Rede"),
    st.Page("pages/2_Município.py", title="Município"),
    st.Page("pages/3_Ranking.py", title="Ranking"),
    st.Page("pages/4_Escola.py", title="Escola"),
    st.Page("pages/5_Comparação.py", title="Comparação"),
    st.Page("pages/6_Metodologia.py", title="Metodologia"),
]
st.navigation(paginas).run()

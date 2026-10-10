# Ponto de entrada alternativo do RegDoc (endereço regdoc-brasil.streamlit.app).
# Executa exatamente o mesmo roteador de app.py; não duplique código aqui.
import os
import runpy

runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py"), run_name="__main__")

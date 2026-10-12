"""
RegDoc — IED (esforço docente): os seis níveis publicados pelo Inep, por etapa.

Roda no Google Colab, lendo os zips originais do Inep que estão no seu Google Drive
(IED_<ano>_ESCOLAS.zip e IED_<ano>_MUNICIPIOS.zip).

Gera dois arquivos na mesma pasta dos zips:
  - ied_niveis_municipio.parquet   -> municípios, 2013–2025, por rede (localização Total)
  - ied_niveis_escola_2013_2014.parquet -> escolas, 2013 e 2014

Colunas de valor (percentual de docentes em cada nível, como o Inep publica):
  IED_<ETAPA>_N1 ... IED_<ETAPA>_N6, com ETAPA em FUN (Ensino Fundamental total),
  AI (anos iniciais), AF (anos finais) e EM (ensino médio).

Como usar no Colab:
  1. Arquivo > Novo notebook. Cole este código numa célula e rode (Shift+Enter).
  2. Autorize o acesso ao Google Drive quando pedir.
  3. Ao final, o script mostra onde salvou os dois arquivos.
"""
import glob
import os
import re
import zipfile

import numpy as np
import pandas as pd

try:
    from google.colab import drive
    drive.mount("/content/drive")
    RAIZ = "/content/drive/MyDrive"
except ImportError:  # fora do Colab: informe a pasta com os zips
    RAIZ = os.environ.get("PASTA_IED", ".")

ANOS = range(2013, 2026)
ETAPAS = ["FUN", "AI", "AF", "EM"]          # ordem em que o Inep publica os blocos
COLS_NIVEIS = [f"IED_{e}_N{n}" for e in ETAPAS for n in range(1, 7)]
LOCALIZACOES = {"Total", "Urbana", "Rural"}
REDES = {"Total", "Federal", "Estadual", "Municipal", "Privada", "Pública", "Publica"}


def achar_pasta():
    achados = glob.glob(os.path.join(RAIZ, "**", "IED_2025_MUNICIPIOS.zip"), recursive=True)
    if not achados:
        raise FileNotFoundError("Não achei IED_2025_MUNICIPIOS.zip no seu Drive.")
    return os.path.dirname(achados[0])


def ler_planilha(caminho_zip):
    """Lê a planilha de dentro do zip, sem cabeçalho (o Inep usa várias linhas de título)."""
    with zipfile.ZipFile(caminho_zip) as z:
        nomes = [n for n in z.namelist() if n.lower().endswith((".xlsx", ".xls", ".ods"))]
        nomes.sort(key=lambda n: (not n.lower().endswith(".xlsx"), not n.lower().endswith(".ods")))
        nome = nomes[0]
        with z.open(nome) as f:
            dados = f.read()
    destino = "/tmp/" + os.path.basename(nome)
    with open(destino, "wb") as f:
        f.write(dados)
    motor = "odf" if destino.lower().endswith(".ods") else None
    return pd.read_excel(destino, header=None, engine=motor, dtype=object)


def coluna_inicial_niveis(df):
    """Coluna onde começa 'Nível 1' do primeiro bloco (Ensino Fundamental, total)."""
    for i in range(min(20, len(df))):
        linha = [str(x).strip() for x in df.iloc[i].tolist()]
        if "Nível 1" in linha:
            return linha.index("Nível 1")
    raise ValueError("Não achei a linha 'Nível 1' no cabeçalho.")


def coluna_por_valores(df, teste, ate):
    """Primeira coluna (entre 0 e 'ate') cujos valores passam no teste em quase todas as linhas."""
    for c in range(ate):
        v = df.iloc[:, c].dropna()
        if len(v) and teste(v).mean() > 0.95:
            return c
    return None


def eh_codigo(n_digitos):
    lo, hi = 10 ** (n_digitos - 1), 10 ** n_digitos - 1
    def teste(v):
        x = pd.to_numeric(v, errors="coerce")
        return (x >= lo) & (x <= hi)
    return teste


def extrair(df, nivel, ano):
    c0 = coluna_inicial_niveis(df)
    n_dig = 8 if nivel == "escola" else 7
    # só linhas de dados: as que têm um código numérico com o número certo de dígitos
    corpo = df.copy()
    c_cod = coluna_por_valores(corpo.iloc[:, :c0], eh_codigo(n_dig), c0)
    if c_cod is None:
        raise ValueError(f"{ano} {nivel}: não achei a coluna de código.")
    cod = pd.to_numeric(corpo.iloc[:, c_cod], errors="coerce")
    corpo = corpo[(cod >= 10 ** (n_dig - 1)) & (cod < 10 ** n_dig)]
    out = pd.DataFrame({
        "CO_ENTIDADE" if nivel == "escola" else "CO_MUNICIPIO":
            pd.to_numeric(corpo.iloc[:, c_cod]).astype("int64").values,
        "ANO": ano,
    })
    if nivel == "municipio":
        c_loc = coluna_por_valores(corpo.iloc[:, :c0], lambda v: v.astype(str).str.strip().isin(LOCALIZACOES), c0)
        c_dep = coluna_por_valores(corpo.iloc[:, :c0], lambda v: v.astype(str).str.strip().isin(REDES), c0)
        if c_loc is None or c_dep is None or c_loc == c_dep:
            raise ValueError(f"{ano}: não achei as colunas de localização e de rede.")
        out["LOCALIZACAO"] = corpo.iloc[:, c_loc].astype(str).str.strip().values
        out["REDE"] = corpo.iloc[:, c_dep].astype(str).str.strip().replace({"Publica": "Pública"}).values
    for j, nome in enumerate(COLS_NIVEIS):
        v = corpo.iloc[:, c0 + j].replace({"--": np.nan, "-": np.nan, "": np.nan})
        out[nome] = pd.to_numeric(v, errors="coerce").astype("float32").values
    # conferência: cada bloco de seis níveis soma cerca de 100%
    for e in ETAPAS:
        s = out[[f"IED_{e}_N{n}" for n in range(1, 7)]].sum(axis=1, min_count=6).dropna()
        if len(s) and not s.between(99, 101).mean() > 0.99:
            raise ValueError(f"{ano} {nivel}: os níveis de {e} não somam 100%. Verifique a planilha.")
    return out


pasta = achar_pasta()
print("Pasta dos zips:", pasta)

municipios = []
for ano in ANOS:
    z = os.path.join(pasta, f"IED_{ano}_MUNICIPIOS.zip")
    if not os.path.exists(z):
        print(f"  {ano}: zip de municípios não encontrado — pulando")
        continue
    m = extrair(ler_planilha(z), "municipio", ano)
    m = m[m["LOCALIZACAO"] == "Total"].drop(columns="LOCALIZACAO")
    municipios.append(m)
    print(f"  {ano}: {m['CO_MUNICIPIO'].nunique()} municípios, redes: {sorted(m['REDE'].unique())}")
mun = pd.concat(municipios, ignore_index=True)
saida_mun = os.path.join(pasta, "ied_niveis_municipio.parquet")
mun.to_parquet(saida_mun, index=False, compression="zstd")

escolas = []
for ano in (2013, 2014):
    z = os.path.join(pasta, f"IED_{ano}_ESCOLAS.zip")
    e = extrair(ler_planilha(z), "escola", ano)
    escolas.append(e)
    print(f"  {ano}: {len(e)} escolas")
esc = pd.concat(escolas, ignore_index=True)
saida_esc = os.path.join(pasta, "ied_niveis_escola_2013_2014.parquet")
esc.to_parquet(saida_esc, index=False, compression="zstd")

print()
print("Pronto. Arquivos salvos:")
for s in (saida_mun, saida_esc):
    print(f"  {s}  ({os.path.getsize(s) / 1e6:.1f} MB)")

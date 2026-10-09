#!/usr/bin/env python3
"""
10_conferencia_indicadores_inep.py
Conferência de ICG, AFD, IED e ATU dos Parquet do RegDoc com as planilhas originais do Inep (2013-2025).
Complementa o 09_conferencia_inep.py, que confere o IRD.

O que confere
  Escolas (escola_consolidado.parquet), por código de escola e ano:
    - presença da escola e valor de cada indicador (ICG, AFD, IED, ATU);
    - valores do RegDoc sem origem no Inep; valores do Inep ausentes no RegDoc; diferenças de valor.
  Municípios (municipal_consolidado.parquet), por município e ano:
    - ICG municipal = nível médio ponderado pela distribuição de escolas por nível (planilha MUNICIPIOS, Total/Total);
    - AFD, IED e ATU municipais = valor municipal publicado pelo Inep (planilha MUNICIPIOS, Total/Total, Ensino Fundamental).

Colunas do Inep usadas (conferidas por posição e por comparação de valores, em todos os anos):
    ICG: nível de complexidade de gestão ("Nível N" -> N);  AFD: Grupo 1, Ensino Fundamental total;
    IED: Nível 1, Ensino Fundamental total;                 ATU: Ensino Fundamental total.
O cabeçalho técnico das planilhas muda entre anos (ordem das colunas, rótulos e, em alguns anos, até a
ordem das colunas de código); por isso a coluna do código da escola e a do município são localizadas
pelo conteúdo (8 e 7 dígitos), e as colunas de valor, por posição.

Uso
  python 10_conferencia_indicadores_inep.py --inep PASTA_COM_ICG_AFD_IED_ATU --repo PASTA_DO_REPOSITORIO \
         [--cache PASTA_CACHE] [--saida PASTA_SAIDA] [--inds ICG AFD IED ATU]
  PASTA_COM_ICG_AFD_IED_ATU: contém as subpastas ICG, AFD, IED e ATU com os zips <IND>_<ano>_ESCOLAS.zip e <IND>_<ano>_MUNICIPIOS.zip.
  A primeira execução converte as planilhas para Parquet em --cache (leva alguns minutos); as seguintes reaproveitam.
Dependências: pandas, pyarrow, python-calamine.
"""
import argparse, os, shutil, sys, tempfile, zipfile
import numpy as np
import pandas as pd
from python_calamine import CalamineWorkbook

ANOS = range(2013, 2026)
IDX_VALOR = {"AFD": 14, "IED": 9, "ATU": 12}          # posição da coluna de valor nas planilhas de ESCOLAS (Ensino Fundamental, total)
IDX_MUN = {"AFD": 12, "IED": 7, "ATU": 10}            # posição da coluna de valor nas planilhas de MUNICÍPIOS (Ensino Fundamental, total)
TOL_ARRED = 0.051                                       # municipal arredondado em 1 casa decimal


def _ano_ok(v):
    try:
        return 2000 < int(float(str(v).strip())) < 2035
    except Exception:
        return False


def _dig(v, n):
    s = str(v).strip()
    s = s[:-2] if s.endswith(".0") else s
    return s.isdigit() and len(s) == n


def _num(s):
    t = s.astype("string").str.strip().str.extract(r"(\d+(?:[.,]\d+)?)$")[0].str.replace(",", ".")
    return pd.to_numeric(t, errors="coerce").astype("float64").to_numpy()


def _ler(zip_path, so_total=False):
    tmp = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(zip_path) as z:
            x = [n for n in z.namelist() if n.lower().endswith(".xlsx")][0]
            z.extract(x, tmp)
        rows = CalamineWorkbook.from_path(os.path.join(tmp, x)).get_sheet_by_index(0).to_python(skip_empty_area=False)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    hi = next((k for k, r in enumerate(rows[:60]) if str(r[0]).strip().upper() == "NU_ANO_CENSO"), None)
    if hi is None:
        hi = next(k for k, r in enumerate(rows[:60]) if str(r[0]).strip() == "Ano")
    nomes, vistos = [], {}
    for i, c in enumerate(rows[hi]):
        h = str(c).strip() if c not in ("", None) else f"x{i}"
        vistos[h] = vistos.get(h, 0) + 1
        nomes.append(h if vistos[h] == 1 else f"{h}__{vistos[h]}")
    n = len(nomes)
    amostra = [r for r in rows[hi + 1:hi + 400] if len(r) > 9 and _ano_ok(r[0])][:200]
    # escolas: código da escola (8 dígitos); municípios: não há código de escola
    ie = None
    if not so_total:
        for j in range(1, 10):
            if amostra and all(_dig(r[j], 8) for r in amostra):
                ie = j
                break
        assert ie is not None, zip_path
    im = None
    for j in range(1, 10):
        if amostra and all(_dig(r[j], 7) for r in amostra):
            im = j
            break
    assert im is not None, zip_path
    if so_total:
        dados = [r for r in rows[hi + 1:] if len(r) > 6 and _ano_ok(r[0]) and _dig(r[im], 7)
                 and str(r[5]).strip().lower() == "total" and str(r[6]).strip().lower() == "total"]
    else:
        dados = [r for r in rows[hi + 1:] if len(r) > ie and _ano_ok(r[0]) and _dig(r[ie], 8)]
    df = pd.DataFrame([[None if c in ("", None) else str(c).strip() for c in (list(r)[:n] + [None] * (n - len(r)))]
                       for r in dados], columns=nomes)
    df.insert(0, "KM", [str(int(float(r[im]))) for r in dados])
    if not so_total:
        df.insert(0, "K", [str(int(float(r[ie]))) for r in dados])
    return df


def cache(inep, ind, ano, tipo, pasta):
    os.makedirs(pasta, exist_ok=True)
    p = os.path.join(pasta, f"{tipo}_{ind}_{ano}.parquet")
    if not os.path.exists(p):
        z = os.path.join(inep, ind, f"{ind}_{ano}_{'ESCOLAS' if tipo == 'esc' else 'MUNICIPIOS'}.zip")
        _ler(z, so_total=(tipo == "mun")).to_parquet(p, index=False)
        print("convertido", os.path.basename(p), flush=True)
    return pd.read_parquet(p)


def valor_escola(ind, d):
    if ind == "ICG":
        col = next(c for c in d.columns if c.startswith("COMPLEX") or c.startswith("Nível de complexidade"))
    else:
        col = d.columns[IDX_VALOR[ind] + 2]            # +2: colunas K e KM inseridas no início
    return col, _num(d[col])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inep", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--cache", default="cache_inep")
    ap.add_argument("--saida", default=".")
    ap.add_argument("--inds", nargs="*", default=["ICG", "AFD", "IED", "ATU"])
    ap.add_argument("--so-municipios", action="store_true", help="confere apenas a base municipal")
    a = ap.parse_args()

    esc = None
    if not a.so_municipios:
        esc = pd.read_parquet(os.path.join(a.repo, "escola_consolidado.parquet"),
                              columns=["CO_ENTIDADE", "CO_MUNICIPIO", "ANO", "ICG", "AFD", "IED", "ATU"])
        esc["K"] = esc.CO_ENTIDADE.astype(float).astype("int64").astype(str)
        esc["ANO"] = esc.ANO.astype(int)
    mun = pd.read_parquet(os.path.join(a.repo, "municipal_consolidado.parquet"))
    mun["KM"] = mun.CO_MUNICIPIO.astype(float).astype("int64").astype(str)
    mun["ANO"] = mun.ANO.astype(int)

    res_e, res_m, amostras = [], [], []
    for ind in a.inds:
        for ano in ANOS:
            if not a.so_municipios:
                d = cache(a.inep, ind, ano, "esc", a.cache)
                col, v = valor_escola(ind, d)
                d = d.assign(v=v)
                r = esc[esc.ANO == ano][["K", ind]].rename(columns={ind: "r"})
                m = r.merge(d[["K", "v"]].drop_duplicates("K"), on="K", how="outer", indicator=True)
                amb, sr, si = m[m._merge == "both"], m[m._merge == "left_only"], m[m._merge == "right_only"]
                rv, iv = amb.r.to_numpy(float), amb.v.to_numpy(float)
                ambos = ~np.isnan(rv) & ~np.isnan(iv)
                dif = ambos & (np.abs(rv - iv) > 1e-6)
                res_e.append(dict(indicador=ind, ano=ano, coluna_inep=col[:40], escolas_regdoc=len(r), linhas_inep=len(d),
                                  duplicadas_inep=int(d.K.duplicated().sum()), em_ambos=len(amb),
                                  so_regdoc=len(sr), so_regdoc_com_valor=int(sr.r.notna().sum()),
                                  so_inep=len(si), so_inep_com_valor=int(si.v.notna().sum()),
                                  valores_comparados=int(ambos.sum()), valores_diferentes=int(dif.sum()),
                                  regdoc_vazio_inep_com_valor=int((np.isnan(rv) & ~np.isnan(iv)).sum()),
                                  regdoc_com_valor_inep_vazio=int((~np.isnan(rv) & np.isnan(iv)).sum()),
                                  dif_max=float(np.abs(rv - iv)[ambos].max()) if ambos.any() else 0.0))
                if dif.any():
                    amostras.append(amb[dif].assign(indicador=ind, ano=ano).head(50))
            # município
            q = mun[mun.ANO == ano][["KM", ind]].rename(columns={ind: "r"})
            if ind == "ICG":
                dm = cache(a.inep, ind, ano, "mun", a.cache)
                P = np.column_stack([_num(dm[dm.columns[j + 1]]) for j in range(7, 13)])
                with np.errstate(invalid="ignore", divide="ignore"):
                    e = (P * np.arange(1, 7)).sum(1) / P.sum(1)
                g = pd.DataFrame({"KM": dm.KM, "e": e}).drop_duplicates("KM")
            else:
                dm = cache(a.inep, ind, ano, "mun", a.cache)
                g = pd.DataFrame({"KM": dm.KM, "e": _num(dm[dm.columns[IDX_MUN[ind] + 1]])}).drop_duplicates("KM")
            mm = q.merge(g, on="KM", how="outer", indicator=True)
            rr, ee = mm.r.to_numpy(float), mm.e.to_numpy(float)
            ambos = ~np.isnan(rr) & ~np.isnan(ee)
            res_m.append(dict(indicador=ind, ano=ano, municipios_regdoc=len(q), com_valor_regdoc=int(q.r.notna().sum()),
                              comparados=int(ambos.sum()), diferem_acima_de_0_05=int((np.abs(rr - ee)[ambos] > TOL_ARRED).sum()),
                              regdoc_vazio_inep_com_valor=int((np.isnan(rr) & ~np.isnan(ee)).sum()),
                              regdoc_com_valor_inep_vazio=int((~np.isnan(rr) & np.isnan(ee)).sum()),
                              dif_max=float(np.abs(rr - ee)[ambos].max()) if ambos.any() else 0.0))
            if a.so_municipios:
                print(ind, ano, "municípios: comparados", res_m[-1]["comparados"], "dif", res_m[-1]["diferem_acima_de_0_05"],
                      "| RegDoc vazio/Inep valor", res_m[-1]["regdoc_vazio_inep_com_valor"], flush=True)
            else:
                print(res_e[-1]["indicador"], ano, "escolas: dif", res_e[-1]["valores_diferentes"],
                      "| RegDoc vazio/Inep valor", res_e[-1]["regdoc_vazio_inep_com_valor"],
                      "| municípios: dif", res_m[-1]["diferem_acima_de_0_05"], flush=True)

    os.makedirs(a.saida, exist_ok=True)
    if res_e:
        pd.DataFrame(res_e).to_csv(os.path.join(a.saida, "resultado_escolas_4_indicadores.csv"), index=False)
    pd.DataFrame(res_m).to_csv(os.path.join(a.saida, "resultado_municipios_4_indicadores.csv"), index=False)
    if amostras:
        pd.concat(amostras).to_csv(os.path.join(a.saida, "divergencias_amostra.csv"), index=False)
    print("Gravado em", a.saida)


if __name__ == "__main__":
    sys.exit(main())

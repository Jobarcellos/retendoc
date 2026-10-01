# -*- coding: utf-8 -*-
"""
Verificação e análise de sensibilidade das regras do RegDoc (v1.2).
Reproduz, a partir dos Parquet publicados no repositório, os números citados
no manuscrito e mede quanto as classificações mudam quando os parâmetros variam.
Uso:  python 08_analise_sensibilidade.py <pasta_com_os_parquet>
"""
import sys, json
import numpy as np, pandas as pd

pasta = sys.argv[1] if len(sys.argv) > 1 else "."
m = pd.read_parquet(f"{pasta}/municipal_consolidado.parquet")
e = pd.read_parquet(f"{pasta}/escola_consolidado.parquet")
m["CO_MUNICIPIO"] = m["CO_MUNICIPIO"].astype(str).str.replace(r"\.0$", "", regex=True)
e["CO_MUNICIPIO"] = e["CO_MUNICIPIO"].astype(str).str.replace(r"\.0$", "", regex=True)
e["CO_ENTIDADE"] = e["CO_ENTIDADE"].astype(str).str.replace(r"\.0$", "", regex=True)
R = {}
ANO = 2025

# ---------- A. Conferência dos números do manuscrito ----------
m25 = m[m.ANO == ANO].copy()
R["linhas_municipais_2025"] = int(len(m25))
R["municipios_distintos_2025"] = int(m25.CO_MUNICIPIO.nunique())
R["municipios_2025_com_IRD"] = int(m25.IRD.notna().sum())
media_nac = m25.IRD.mean()
R["media_nacional_IRD_simples_entre_municipios"] = round(float(media_nac), 4)
R["mediana_municipal_2025"] = round(float(m25.IRD.median()), 4)
e25 = e[e.ANO == ANO]
R["media_simples_escolas_2025"] = round(float(e25.IRD.mean()), 4)

alerta = m25[m25.IRD < 0.85 * media_nac]
R["alerta_2025_n"] = int(len(alerta))
R["alerta_2025_pct_dos_5570"] = round(len(alerta) / 5570 * 100, 2)
R["alerta_2025_pct_dos_com_IRD"] = round(len(alerta) / m25.IRD.notna().sum() * 100, 2)
es = m25[m25.SG_UF == "ES"]
R["ES_municipios"] = int(es.CO_MUNICIPIO.nunique())
R["ES_alerta_n"] = int((es.IRD < 0.85 * media_nac).sum())
R["ES_alerta_pct"] = round((es.IRD < 0.85 * media_nac).sum() / es.CO_MUNICIPIO.nunique() * 100, 1)
R["ES_menores_IRD"] = es.sort_values("IRD")[["NO_MUNICIPIO", "IRD"]].head(3).round(3).values.tolist()

# Cariacica (ES)
cari = m25[(m25.SG_UF == "ES") & (m25.NO_MUNICIPIO.str.contains("Cariacica"))]
co_car = cari.CO_MUNICIPIO.iloc[0]
R["cariacica_IRD_municipal_todas_redes"] = round(float(cari.IRD.iloc[0]), 4)
ec = e25[(e25.CO_MUNICIPIO == co_car) & (e25.NO_DEPENDENCIA.astype(str) == "Municipal")].dropna(subset=["IRD"]).copy()
R["cariacica_escolas_municipais_com_IRD"] = int(len(ec))
def faixa_inep(v):
    for lim, r in [(2.0, "baixa"), (3.0, "media-baixa"), (4.0, "media-alta"), (5.1, "alta")]:
        if v <= lim: return r
fi = ec.IRD.apply(faixa_inep).value_counts()
R["cariacica_faixas_inep"] = {k: int(v) for k, v in fi.items()}
# média municipal: (a) linha municipal 'todas as redes'; (b) média das escolas municipais
for rotulo, ref in [("ref_municipal_todas_redes", float(cari.IRD.iloc[0])),
                    ("ref_media_das_escolas_municipais", float(ec.IRD.mean()))]:
    def cl(v, ref=ref):
        if v >= media_nac: return "Favoravel"
        if v >= ref: return "Atencao"
        return "Alerta"
    c = ec.IRD.apply(cl).value_counts()
    R[f"cariacica_classes_{rotulo}"] = {k: int(v) for k, v in c.items()}
    R[f"cariacica_ref_valor_{rotulo}"] = round(ref, 4)
    ec["R_" + rotulo] = ec.IRD.apply(cl)
    dentro = ec[ec.IRD.apply(faixa_inep) == "media-baixa"]["R_" + rotulo].value_counts()
    R[f"cariacica_dentro_media_baixa_{rotulo}"] = {k: int(v) for k, v in dentro.items()}
    g = ec.groupby("R_" + rotulo)["IED"].mean()
    R[f"cariacica_IED_medio_{rotulo}"] = {k: round(float(v), 2) for k, v in g.items()}

# escolas que mudaram de rede
dep = e.groupby("CO_ENTIDADE")["NO_DEPENDENCIA"].nunique()
R["escolas_que_mudaram_de_dependencia"] = int((dep > 1).sum())
R["escolas_distintas_serie"] = int(e.CO_ENTIDADE.nunique())

# ---------- B. Regra de escola quando média municipal > nacional ----------
ref_mun = m25.set_index("CO_MUNICIPIO")["IRD"]
e25c = e25.dropna(subset=["IRD"]).copy()
e25c["REF_MUN"] = e25c.CO_MUNICIPIO.map(ref_mun)
e25c = e25c.dropna(subset=["REF_MUN"])
e25c["MUN_ACIMA_NAC"] = e25c.REF_MUN > media_nac
def cl_esc(r):
    if r.IRD >= media_nac: return "Favoravel"
    if r.IRD >= r.REF_MUN: return "Atencao"
    return "Alerta"
e25c["CLASSE"] = [("Favoravel" if v >= media_nac else ("Atencao" if v >= rm else "Alerta"))
                  for v, rm in zip(e25c.IRD, e25c.REF_MUN)]
R["municipios_com_media_acima_da_nacional_pct"] = round(float((m25.IRD > media_nac).mean() * 100), 1)
tab = pd.crosstab(e25c.MUN_ACIMA_NAC, e25c.CLASSE)
R["escolas_por_classe_e_posicao_do_municipio"] = {str(k): {c: int(v) for c, v in r.items()} for k, r in tab.iterrows()}

# ---------- C. Sensibilidade: alerta municipal (limiar % da média) ----------
def n_alerta(pct, ref=media_nac):
    return int((m25.IRD < pct * ref).sum())
base = set(m25[m25.IRD < 0.85 * media_nac].CO_MUNICIPIO)
sens = {}
for pct in (0.80, 0.85, 0.90):
    s = set(m25[m25.IRD < pct * media_nac].CO_MUNICIPIO)
    sens[f"alerta_{int(pct*100)}pct"] = {"n": len(s), "pct_de_5570": round(len(s) / 5570 * 100, 1),
                                         "entram_vs_85": len(s - base), "saem_vs_85": len(base - s)}
# referência pela mediana, em vez da média
s = set(m25[m25.IRD < 0.85 * m25.IRD.median()].CO_MUNICIPIO)
sens["alerta_85pct_da_MEDIANA"] = {"n": len(s), "entram_vs_base": len(s - base), "saem_vs_base": len(base - s)}
# Favorável
for pct in (1.05, 1.10, 1.15):
    sens[f"favoravel_{int(round(pct*100))}pct"] = int((m25.IRD >= pct * media_nac).sum())
R["sensibilidade_alerta_municipal"] = sens

# ---------- D. Sensibilidade: ruptura (queda de um ano para o outro) ----------
pv = e.pivot_table(index="CO_ENTIDADE", columns="ANO", values="IRD", aggfunc="first")
anos = sorted(pv.columns)
d = pv[anos].diff(axis=1)
ativos25 = pv[ANO].notna()
nobs = pv.notna().sum(axis=1)
mask = ativos25 & (nobs >= 3)
rup = {}
for lim in (0.4, 0.5, 0.6):
    hit = (d[mask] <= -lim)
    algum = hit.any(axis=1)
    # ano da 1ª ruptura (regra do app: primeira da série)
    primeiro = hit.idxmax(axis=1).where(algum)
    ultimos5 = hit[[a for a in anos if a >= ANO - 4]].any(axis=1)
    rup[f"limiar_{lim}"] = {
        "escolas_analisadas": int(mask.sum()),
        "com_alguma_ruptura_na_serie": int(algum.sum()),
        "pct": round(float(algum.mean() * 100), 1),
        "com_ruptura_nos_ultimos_5_anos": int(ultimos5.sum()),
        "primeira_ruptura_em_2020_ou_2021_pct": round(float(primeiro.isin([2020, 2021]).sum() / max(algum.sum(), 1) * 100), 1),
        "primeira_ruptura_antes_de_2020_pct": round(float((primeiro < 2020).sum() / max(algum.sum(), 1) * 100), 1),
    }
# ruptura que o app mostra (primeira da série) vs. mais recente, quando há duas ou mais
hit05 = (d[mask] <= -0.5)
n_rup = hit05.sum(axis=1)
mult = hit05[n_rup >= 2]
prim = mult.idxmax(axis=1)
ult = mult.iloc[:, ::-1].idxmax(axis=1)
rup["escolas_com_2_ou_mais_rupturas_0.5"] = int((n_rup >= 2).sum())
rup["dessas_o_app_exibe_apenas_a_primeira"] = True
rup["dessas_primeira_diferente_da_mais_recente"] = int((prim != ult).sum())
R["sensibilidade_ruptura_escolas"] = rup

# ---------- E. Sensibilidade: tendência (municípios, últimos 5 anos) ----------
pm = m.pivot_table(index="CO_MUNICIPIO", columns="ANO", values="IRD", aggfunc="first")
jan = pm[[a for a in sorted(pm.columns) if a >= ANO - 4]].dropna()
x = np.arange(5) - 2.0
slope = (jan.values * x).sum(axis=1) / (x ** 2).sum()
def cats(sl, a, b):  # a: limiar de "acelerada", b: limiar de "estável"
    return pd.cut(sl, [-np.inf, -a, -b, b, a, np.inf],
                  labels=["queda_acelerada", "tendencia_de_queda", "estavel", "recuperacao", "melhora_expressiva"],
                  right=True)
def dist(a, b):
    return {k: int(v) for k, v in pd.Series(cats(slope, a, b)).value_counts().items()}
base_c = pd.Series(cats(slope, 0.15, 0.05))
R["tendencia_municipios_n"] = int(len(slope))
tend = {}
for a, b in [(0.15, 0.05), (0.10, 0.03), (0.20, 0.07), (0.15, 0.03), (0.15, 0.07)]:
    c = pd.Series(cats(slope, a, b))
    tend[f"acelerada={a}_estavel={b}"] = {"distribuicao": dist(a, b),
                                          "pct_que_muda_de_categoria_vs_regra_atual": round(float((c != base_c).mean() * 100), 1)}
R["sensibilidade_tendencia_municipal"] = tend

# ---------- F. Sensibilidade: cronicidade do alerta (municípios) ----------
mm = m.dropna(subset=["IRD"]).copy()
mm["MEDIA"] = mm.groupby("ANO")["IRD"].transform("mean")
mm["AL"] = mm["IRD"] < 0.85 * mm["MEDIA"]
pa = mm.pivot_table(index="CO_MUNICIPIO", columns="ANO", values="AL", aggfunc="first")
seq = []
for co, row in pa.iterrows():
    n = 0
    for a in range(ANO, 2012, -1):
        v = row.get(a)
        if v is True or v == 1: n += 1
        else: break
    seq.append(n)
seq = pd.Series(seq, index=pa.index)
em_alerta = seq[seq >= 1]
R["cronicidade"] = {"em_alerta_2025": int(len(em_alerta)),
                    **{f"cronico_se_>={k}_anos": int((em_alerta >= k).sum()) for k in (3, 4, 5)}}
R["alerta_2025_pela_serie_anual"] = int(len(em_alerta))

# ---------- G. Sensibilidade: 'vitórias rápidas' e corte de ICG ----------
qw = {}
al = e25c[e25c.CLASSE == "Alerta"].copy()
for tol in (0.03, 0.05, 0.10):
    q = al[al.IRD >= (1 - tol) * al.REF_MUN]
    qw[f"tolerancia_{int(tol*100)}pct"] = {"escolas": int(len(q)), "pct_das_escolas_em_alerta": round(len(q) / len(al) * 100, 1)}
R["escolas_em_alerta_2025_pais"] = int(len(al))
R["sensibilidade_vitorias_rapidas"] = qw
icg = e25.dropna(subset=["ICG"])
R["sensibilidade_icg_alta_complexidade"] = {f"ICG>={c}": round(float((icg.ICG >= c).mean() * 100), 1) for c in (3, 4, 5)}
R["icg_escolas_2025_com_ICG"] = int(len(icg))

# ---------- H. Oscilação anual do IRD (ruído): variação absoluta ano a ano das escolas em quase-lá ----------
dd = d[[a for a in anos if a >= 2021]].abs()
R["variacao_anual_absoluta_mediana_escolas_2021_2025"] = round(float(np.nanmedian(dd.values)), 3)

print(json.dumps(R, ensure_ascii=False, indent=1, default=str))
json.dump(R, open("resultados_sensibilidade.json", "w"), ensure_ascii=False, indent=1, default=str)

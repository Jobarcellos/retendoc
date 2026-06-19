import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils.dados import carregar_municipal, formatar_br

st.set_page_config(page_title="Município · RegDoc", layout="wide")

st.title("🔍 Análise por Município")
st.caption("Evolução da regularidade dos professores e comparação com médias nacionais e estaduais")

df = carregar_municipal()

col1, col2 = st.columns([1, 2])
with col1:
    ufs = sorted(df["SG_UF"].dropna().unique())
    uf_sel = st.selectbox("Estado", ufs, index=ufs.index("ES") if "ES" in ufs else 0)
with col2:
    municipios_uf = (
        df[df["SG_UF"] == uf_sel][["CO_MUNICIPIO","NO_MUNICIPIO"]]
        .drop_duplicates().sort_values("NO_MUNICIPIO")
    )
    municipio_label = st.selectbox("Município", municipios_uf["NO_MUNICIPIO"].tolist())

co_mun = municipios_uf[municipios_uf["NO_MUNICIPIO"] == municipio_label]["CO_MUNICIPIO"].iloc[0]
df_mun = df[df["CO_MUNICIPIO"] == co_mun].sort_values("ANO").copy()

if df_mun.empty:
    st.warning("Sem dados para este município.")
    st.stop()

ano_ref = st.selectbox("Ano de referência", sorted(df_mun["ANO"].unique()), index=len(df_mun["ANO"].unique()) - 2)
linha_atual = df_mun[df_mun["ANO"] == ano_ref].iloc[0]
media_ird_nac = df[df["ANO"] == ano_ref]["IRD"].mean()
media_ird_uf = df[(df["ANO"] == ano_ref) & (df["SG_UF"] == uf_sel)]["IRD"].mean()
media_atu_nac = df[df["ANO"] == ano_ref]["ATU"].mean()

ird = linha_atual["IRD"]
if pd.isna(ird):
    cor = "#aaa"; situacao = "Sem dados"
    texto_sit = "Não há dados de regularidade para este município no ano selecionado."
    orientacoes = []
elif ird >= media_ird_nac:
    cor = "#27ae60"; situacao = "Situação favorável"
    texto_sit = f"A regularidade dos professores de {municipio_label} ({formatar_br(ird)}) está acima da média nacional ({formatar_br(media_ird_nac)}) e da média do {uf_sel} ({formatar_br(media_ird_uf)})."
    orientacoes = [
        "Identifique as escolas com melhor regularidade e sistematize suas boas práticas para compartilhar com toda a rede.",
        "Use os dados do RegDoc para apresentar ao prefeito e ao conselho municipal os resultados positivos da rede.",
        "Mantenha o monitoramento anual — resultados positivos podem se deteriorar se as condições de trabalho mudarem.",
        "Planeje ações de valorização docente para sustentar os bons resultados ao longo do tempo."
    ]
elif pd.notna(media_ird_uf) and ird >= media_ird_uf:
    cor = "#f39c12"; situacao = "Atenção"
    texto_sit = f"A regularidade dos professores de {municipio_label} ({formatar_br(ird)}) está abaixo da média nacional ({formatar_br(media_ird_nac)}), mas acima da média do {uf_sel} ({formatar_br(media_ird_uf)})."
    orientacoes = [
        "Verifique quais escolas do município estão em situação de alerta e priorize o acompanhamento dessas unidades.",
        "Analise a tendência dos últimos dois anos — se o IRD está caindo, o problema está se agravando.",
        "Promova formação continuada focada nas necessidades identificadas nas escolas com maior rotatividade.",
        "Construa um plano municipal de valorização docente com metas e prazos definidos."
    ]
else:
    cor = "#c0392b"; situacao = "Alerta"
    texto_sit = f"A regularidade dos professores de {municipio_label} ({formatar_br(ird)}) está abaixo da média nacional ({formatar_br(media_ird_nac)}) e abaixo da média do {uf_sel} ({formatar_br(media_ird_uf)}). A secretaria deve priorizar intervenções neste município."
    orientacoes = [
        "Mapeie as escolas em situação crítica usando a página Escola do RegDoc e priorize visitas técnicas imediatas.",
        "Realize diagnóstico das condições de trabalho — turmas superlotadas, infraestrutura inadequada e falta de apoio pedagógico são causas frequentes.",
        "Elabore um plano de ação municipal com metas, responsáveis e prazos para reduzir a rotatividade docente.",
        "Apresente os dados do RegDoc ao prefeito e ao conselho municipal para justificar investimentos em valorização docente.",
        "Acione o Ministério da Educação e a Secretaria Estadual para suporte técnico e financeiro se necessário."
    ]

hist = df_mun[df_mun["ANO"] <= ano_ref].sort_values("ANO")
if len(hist) >= 2:
    variacao = hist["IRD"].iloc[-1] - hist["IRD"].iloc[-2]
    ano_ant = int(hist["ANO"].iloc[-2])
    texto_var = (f"Em relação a {ano_ant}, houve melhora de {formatar_br(variacao)}." if variacao > 0.05
        else f"Em relação a {ano_ant}, houve queda de {formatar_br(abs(variacao))}. Merece atenção." if variacao < -0.05
        else f"Em relação a {ano_ant}, a regularidade permaneceu estável.")
else:
    variacao = None; texto_var = "Não há ano anterior disponível para comparação."

# ── Resultado ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"### {municipio_label} · {uf_sel} · {ano_ref}")

col_ird, col_comp = st.columns([1, 2])
with col_ird:
    st.markdown(f"""
    <div style="background:{cor}22; border:2px solid {cor}; border-radius:12px;
         padding:1.5rem 2rem; text-align:center;">
        <p style="color:{cor}; margin:0; font-size:1rem;">Regularidade dos professores (0 a 5)</p>
        <p style="color:{cor}; margin:0; font-size:3.5rem; font-weight:bold;">{formatar_br(ird)}</p>
        <p style="color:{cor}; margin:0; font-size:1.2rem; font-weight:bold;">● {situacao}</p>
    </div>
    """, unsafe_allow_html=True)

with col_comp:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Média Brasil", formatar_br(media_ird_nac))
    c2.metric(f"Média {uf_sel}", formatar_br(media_ird_uf))
    c3.metric("Alunos por turma", formatar_br(linha_atual["ATU"], 1))
    c4.metric("Formação adequada (%)", formatar_br(linha_atual["AFD"], 1))
    st.markdown(f"<p style='font-size:0.9rem; color:#333; margin-top:0.5rem;'>{texto_sit}<br><strong>Variação:</strong> {texto_var}</p>", unsafe_allow_html=True)

# ── O que fazer ───────────────────────────────────────────────────────────────
if orientacoes:
    with st.expander(f"📋 O que fazer? — Orientações para situação de {situacao}"):
        for i, ori in enumerate(orientacoes, 1):
            st.markdown(f"**{i}.** {ori}")

# ── Gráfico ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Evolução da regularidade dos professores")

ird_nac = df.groupby("ANO")["IRD"].mean().reset_index().rename(columns={"IRD":"Média Brasil"})
ird_uf_ano = df[df["SG_UF"] == uf_sel].groupby("ANO")["IRD"].mean().reset_index().rename(columns={"IRD":f"Média {uf_sel}"})
df_evo = df_mun[["ANO","IRD"]].rename(columns={"IRD":municipio_label})
df_evo = df_evo.merge(ird_nac, on="ANO", how="left").merge(ird_uf_ano, on="ANO", how="left")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df_evo["ANO"], y=df_evo[municipio_label],
    name=municipio_label, line=dict(color=cor, width=3), mode="lines+markers", marker_size=8))
fig.add_trace(go.Scatter(x=df_evo["ANO"], y=df_evo["Média Brasil"],
    name="Média Brasil", line=dict(color="#aaa", dash="dash", width=1.5)))
fig.add_trace(go.Scatter(x=df_evo["ANO"], y=df_evo[f"Média {uf_sel}"],
    name=f"Média {uf_sel}", line=dict(color="#e67e22", dash="dot", width=1.5)))
fig.update_layout(height=380, margin=dict(l=20, r=20, t=20, b=20),
    legend=dict(orientation="h", y=-0.2),
    yaxis=dict(title="Regularidade (0 a 5)", range=[0, 5.2]),
    xaxis_title="Ano")
st.plotly_chart(fig, use_container_width=True)

# ── Tabela histórica ──────────────────────────────────────────────────────────
st.markdown("### Série histórica completa")
df_tab = df_mun[["ANO","IRD","ATU","AFD","IED","ICG"]].copy()
df_tab = df_tab.rename(columns={"ANO":"Ano","IRD":"Regularidade (0-5)",
    "ATU":"Alunos/turma","AFD":"Formação (%)","IED":"Sobrecarga (%)","ICG":"Complexidade"})
for col in df_tab.columns[1:]:
    df_tab[col] = df_tab[col].apply(lambda x: formatar_br(x, 1))
st.dataframe(df_tab.set_index("Ano"), use_container_width=True)

# ── Relatório HTML ────────────────────────────────────────────────────────────
st.markdown("---")

def gerar_relatorio_municipio():
    rows = ""
    df_h = df_mun[["ANO","IRD","ATU","AFD","IED","ICG"]].copy()
    df_h["VAR"] = df_h["IRD"].diff()
    for _, r in df_h.iterrows():
        var = formatar_br(r["VAR"]) if pd.notna(r["VAR"]) else "—"
        cor_var = "#27ae60" if pd.notna(r["VAR"]) and r["VAR"] > 0 else "#c0392b" if pd.notna(r["VAR"]) and r["VAR"] < 0 else "#333"
        rows += f"""<tr>
            <td>{int(r['ANO'])}</td>
            <td>{formatar_br(r['IRD'])}</td>
            <td style="color:{cor_var}">{var}</td>
            <td>{formatar_br(r['ATU'], 1)}</td>
            <td>{formatar_br(r['AFD'], 1)}%</td>
            <td>{formatar_br(r['IED'], 1)}%</td>
            <td>{formatar_br(r['ICG'], 1)}</td>
        </tr>"""

    ori_html = "".join([f"<div style='display:flex;gap:12px;align-items:flex-start;margin-bottom:8px;'><div style='min-width:22px;height:22px;background:{cor};border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:bold;'>{i}</div><p style='margin:0;font-size:13px;'>{o}</p></div>" for i, o in enumerate(orientacoes, 1)])

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>RegDoc — {municipio_label}</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 0; padding: 2rem; color: #222; max-width: 900px; margin: 0 auto; }}
  .header {{ background: #1a3a5c; color: white; padding: 1.5rem 2rem; border-radius: 10px; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: flex-start; }}
  .header h1 {{ margin: 0; font-size: 1.2rem; color: white; }}
  .header p {{ margin: 0.3rem 0 0; font-size: 0.85rem; color: #b8cfe8; }}
  .grid2 {{ display: grid; grid-template-columns: 1fr 2fr; gap: 1rem; margin-bottom: 1.5rem; }}
  .ird-box {{ background: {cor}22; border: 2px solid {cor}; border-radius: 10px; padding: 1.5rem; text-align: center; }}
  .ird-num {{ font-size: 3rem; font-weight: bold; color: {cor}; margin: 0; }}
  .ird-label {{ font-size: 0.85rem; color: {cor}; margin: 0; }}
  .ird-sit {{ font-size: 1.1rem; font-weight: bold; color: {cor}; margin: 0.5rem 0 0; }}
  .metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }}
  .metric {{ background: #f5f5f5; border-radius: 8px; padding: 0.8rem; text-align: center; }}
  .metric .val {{ font-size: 1.4rem; font-weight: bold; color: #1a3a5c; margin: 0; }}
  .metric .lbl {{ font-size: 0.75rem; color: #777; margin: 0; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ background: #1a3a5c; color: white; padding: 8px; text-align: left; }}
  td {{ padding: 7px 8px; border-bottom: 1px solid #eee; }}
  .section {{ margin-bottom: 1.5rem; }}
  .section h2 {{ font-size: 1rem; color: #1a3a5c; border-bottom: 2px solid {cor}; padding-bottom: 0.3rem; }}
  .alert-box {{ border: 1px solid {cor}; border-radius: 8px; padding: 1rem; background: {cor}11; }}
  .footer {{ text-align: center; font-size: 11px; color: #aaa; margin-top: 2rem; border-top: 1px solid #eee; padding-top: 1rem; }}
  @media print {{ body {{ padding: 1rem; }} }}
</style>
</head>
<body>
<div class="header">
  <div>
    <p style="margin:0;font-size:11px;color:#b8cfe8;text-transform:uppercase;">Relatório RegDoc — Município</p>
    <h1>{municipio_label} · {uf_sel}</h1>
    <p>Ano de referência: {ano_ref}</p>
  </div>
  <div style="font-size:0.8rem;color:#b8cfe8;text-align:right;">Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
</div>

<div class="grid2">
  <div class="ird-box">
    <p class="ird-label">Regularidade dos professores (0 a 5)</p>
    <p class="ird-num">{formatar_br(ird)}</p>
    <p class="ird-sit">● {situacao}</p>
  </div>
  <div class="metrics">
    <div class="metric"><p class="val">{formatar_br(media_ird_nac)}</p><p class="lbl">Média nacional</p></div>
    <div class="metric"><p class="val">{formatar_br(media_ird_uf)}</p><p class="lbl">Média {uf_sel}</p></div>
    <div class="metric"><p class="val">{formatar_br(linha_atual.get('ATU'), 1)}</p><p class="lbl">Alunos por turma</p></div>
    <div class="metric"><p class="val">{formatar_br(linha_atual.get('AFD'), 1)}%</p><p class="lbl">Formação adequada</p></div>
  </div>
</div>

<p style="font-size:13px; margin-bottom:1.5rem;">{texto_sit}<br><strong>Variação:</strong> {texto_var}</p>

<div class="section">
  <h2>Série histórica completa</h2>
  <table>
    <thead><tr><th>Ano</th><th>Regularidade</th><th>Variação</th><th>Alunos/turma</th><th>Formação (%)</th><th>Sobrecarga (%)</th><th>Complexidade</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>

<div class="section">
  <h2>O que fazer — situação de {situacao}</h2>
  <div class="alert-box">{ori_html}</div>
</div>

<div class="footer">
  RegDoc · Dados: Censo Escolar/Inep · retendoc.streamlit.app · {datetime.now().strftime('%d/%m/%Y')}
</div>
</body>
</html>"""

html = gerar_relatorio_municipio()
st.download_button(
    label="📄 Baixar relatório deste município (HTML)",
    data=html.encode("utf-8"),
    file_name=f"regdoc_{co_mun}_{ano_ref}.html",
    mime="text/html"
)
st.caption("Abra o arquivo no navegador e use Ctrl+P para imprimir ou salvar em PDF.")

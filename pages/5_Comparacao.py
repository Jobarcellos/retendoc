import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from utils.dados import carregar_escola, carregar_municipal, formatar_br, aplicar_estilo_global, sombrear_pandemia

st.set_page_config(page_title="Comparação · RegDoc", layout="wide")
aplicar_estilo_global()

st.markdown("""
<style>
.tooltip-wrap { position:relative; display:inline-block; cursor:pointer; }
.tooltip-wrap .tip {
    visibility:hidden; opacity:0; width:320px; background:#1a3a5c; color:white;
    font-size:12px; font-weight:normal; line-height:1.6;
    border-radius:8px; padding:12px 16px;
    position:absolute; z-index:999; bottom:130%; left:50%; transform:translateX(-50%);
    transition:opacity 0.2s; pointer-events:none;
}
.tooltip-wrap:hover .tip { visibility:visible; opacity:1; }
.info-icon { display:inline-flex; align-items:center; justify-content:center;
    width:16px; height:16px; border-radius:50%; background:#1a3a5c;
    color:white; font-size:10px; font-weight:bold; cursor:help; }
.tab-header { font-size:1.1rem; font-weight:600; color:#1a3a5c; margin-bottom:0.5rem; }
</style>
""", unsafe_allow_html=True)

TOOLTIPS = {
    "IRD": "O IRD mede se os mesmos professores continuam na escola de um ano para o outro. Escala de 0 a 5 — quanto maior, mais estável é o corpo docente. Fonte: Nota Técnica INEP nº 11/2015.",
    "ATU": "ATU — Média de Alunos por Turma. Turmas maiores aumentam a sobrecarga docente e estão associadas a maior rotatividade. Fonte: Censo Escolar/INEP.",
    "AFD": "AFD — Adequação da Formação Docente. Percentual de professores que lecionam na área em que se formaram. Quanto maior, melhor. Fonte: Censo Escolar/INEP.",
    "IED": "IED — Indicador de Esforço Docente. Mede a complexidade da jornada — escolas, turnos e disciplinas simultâneas. Valores altos = jornada mais fragmentada. Fonte: Censo Escolar/INEP.",
    "ICG": "ICG — Complexidade de Gestão da Escola. Combina porte, turnos, etapas e modalidades. Escala de 1 a 6. Fonte: Censo Escolar/INEP.",
}

def tooltip_html(sigla):
    tip = TOOLTIPS.get(sigla, "")
    return (f"<span class='tooltip-wrap'><span class='info-icon'>i</span>"
            f"<span class='tip'>{tip}</span></span>")

def cor_ird(ird, media):
    if pd.isna(ird) or pd.isna(media): return "#aaa", "#f5f5f5"
    if ird >= media:        return "#27ae60", "#eafaf1"
    elif ird >= media*0.85: return "#f39c12", "#fef9e7"
    else:                   return "#c0392b", "#fdedec"

st.title("📊 Comparação")
st.caption("Compare escolas ou municípios lado a lado")

df_esc = carregar_escola()
df_mun = carregar_municipal()

# ── Abas principais ────────────────────────────────────────────────────────────
aba_esc, aba_mun = st.tabs(["🏫 Comparação de Escolas", "🏙️ Comparação de Municípios"])

# ══════════════════════════════════════════════════════════════════════════════
# ABA 1 — COMPARAÇÃO DE ESCOLAS
# ══════════════════════════════════════════════════════════════════════════════
with aba_esc:
    st.markdown("### Selecione as escolas para comparar")
    st.caption("Adicione até 20 escolas de qualquer estado e município")

    if "escolas_selecionadas" not in st.session_state:
        st.session_state.escolas_selecionadas = []

    col1, col2, col3, col4 = st.columns([1, 2, 3, 1])
    with col1:
        ufs = sorted(df_esc["SG_UF"].dropna().unique())
        uf_add = st.selectbox("Estado", ufs, key="uf_add",
            index=ufs.index("ES") if "ES" in ufs else 0)
    with col2:
        municipios = (df_esc[df_esc["SG_UF"] == uf_add][["CO_MUNICIPIO","NO_MUNICIPIO"]]
            .drop_duplicates().sort_values("NO_MUNICIPIO"))
        mun_add = st.selectbox("Município", municipios["NO_MUNICIPIO"].tolist(), key="mun_add")
    co_mun_add = municipios[municipios["NO_MUNICIPIO"] == mun_add]["CO_MUNICIPIO"].iloc[0]
    with col3:
        busca_add = st.text_input("Buscar escola", placeholder="Digite parte do nome...", key="busca_add")
        escolas_mun = df_esc[df_esc["CO_MUNICIPIO"] == co_mun_add][["CO_ENTIDADE","NO_ENTIDADE"]].drop_duplicates()
        if busca_add and len(busca_add) >= 3:
            escolas_mun = escolas_mun[escolas_mun["NO_ENTIDADE"].str.upper().str.contains(busca_add.upper(), na=False)]
        escolas_mun = escolas_mun.sort_values("NO_ENTIDADE")
        if not escolas_mun.empty:
            escola_add = st.selectbox("Escola", escolas_mun["NO_ENTIDADE"].tolist(), key="escola_add")
        else:
            st.warning("Nenhuma escola encontrada.")
            escola_add = None
    with col4:
        anos_disp = sorted(df_esc["ANO"].unique())
        ano_comp = st.selectbox("Ano", anos_disp, index=len(anos_disp)-1, key="ano_comp")
        st.markdown("<br>", unsafe_allow_html=True)
        if escola_add and st.button("➕ Adicionar", use_container_width=True):
            co_esc_add = escolas_mun[escolas_mun["NO_ENTIDADE"] == escola_add]["CO_ENTIDADE"].iloc[0]
            entrada = {"CO_ENTIDADE":co_esc_add,"NO_ENTIDADE":escola_add,
                       "NO_MUNICIPIO":mun_add,"SG_UF":uf_add,"ANO":ano_comp}
            if len(st.session_state.escolas_selecionadas) >= 20:
                st.warning("Máximo de 20 escolas atingido.")
            elif any(e["CO_ENTIDADE"]==co_esc_add and e["ANO"]==ano_comp
                     for e in st.session_state.escolas_selecionadas):
                st.warning("Esta escola já foi adicionada para este ano.")
            else:
                st.session_state.escolas_selecionadas.append(entrada)
                st.rerun()

    if st.session_state.escolas_selecionadas:
        n = len(st.session_state.escolas_selecionadas)
        cols_lista = st.columns(min(n, 5))
        for i, esc in enumerate(st.session_state.escolas_selecionadas):
            with cols_lista[i % 5]:
                st.markdown(f"""
                <div style="background:#f0f4f8;border-radius:8px;padding:0.5rem 0.8rem;
                     border-left:4px solid #1a3a5c;font-size:0.82rem;margin-bottom:4px;">
                    <strong>{esc['NO_ENTIDADE'][:28]}...</strong><br>
                    {esc['NO_MUNICIPIO'][:20]} · {esc['SG_UF']} · {esc['ANO']}
                </div>""", unsafe_allow_html=True)
                if st.button("✕", key=f"rem_{i}"):
                    st.session_state.escolas_selecionadas.pop(i)
                    st.rerun()

    if st.button("🗑️ Limpar todas", key="limpar_esc"):
        st.session_state.escolas_selecionadas = []
        st.rerun()

    if len(st.session_state.escolas_selecionadas) < 2:
        st.info("Adicione pelo menos 2 escolas para comparar.")
    else:
        # Montar dados
        dados_comp = []
        for esc in st.session_state.escolas_selecionadas:
            linha = df_esc[(df_esc["CO_ENTIDADE"]==esc["CO_ENTIDADE"]) & (df_esc["ANO"]==esc["ANO"])]
            if not linha.empty:
                r = linha.iloc[0]
                media_nac = df_mun[df_mun["ANO"]==esc["ANO"]]["IRD"].mean()
                dados_comp.append({
                    "Escola": esc["NO_ENTIDADE"][:25]+"..." if len(esc["NO_ENTIDADE"])>25 else esc["NO_ENTIDADE"],
                    "Nome completo": esc["NO_ENTIDADE"],
                    "Município": esc["NO_MUNICIPIO"],
                    "UF": esc["SG_UF"],
                    "Ano": esc["ANO"],
                    "CO_ENTIDADE": esc["CO_ENTIDADE"],
                    "IRD": r["IRD"], "ATU": r.get("ATU"),
                    "AFD": r.get("AFD"), "IED": r.get("IED"),
                    "ICG": r.get("ICG"), "Media_nac": media_nac
                })

        if not dados_comp:
            st.warning("Sem dados para as escolas selecionadas.")
        else:
            df_comp = pd.DataFrame(dados_comp)
            n_escolas = len(df_comp)

            st.markdown("---")

            if n_escolas <= 5:
                # ── Cards lado a lado (até 5) ──────────────────────────────────
                st.markdown("### Comparação lado a lado")
                cols_cards = st.columns(n_escolas)
                for i, d in enumerate(dados_comp):
                    cor, bg = cor_ird(d["IRD"], d["Media_nac"])
                    with cols_cards[i]:
                        st.markdown(f"""
                        <div style="background:{bg};border:2px solid {cor};border-radius:10px;
                             padding:1rem;text-align:center;margin-bottom:0.5rem;">
                            <p style="font-size:0.75rem;color:{cor};margin:0;font-weight:bold;">{d['Escola']}</p>
                            <p style="font-size:0.7rem;color:#777;margin:0.2rem 0;">{d['Município']} · {d['UF']} · {d['Ano']}</p>
                            <p style="font-size:2rem;font-weight:bold;color:{cor};margin:0.3rem 0;">{formatar_br(d['IRD'])}</p>
                        </div>
                        <div style="background:#f7f9fc;border-radius:8px;padding:0.8rem;font-size:0.8rem;">
                            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                                <span>Alunos/turma {tooltip_html('ATU')}</span>
                                <strong>{formatar_br(d['ATU'],1)}</strong>
                            </div>
                            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                                <span>Formação (%) {tooltip_html('AFD')}</span>
                                <strong>{formatar_br(d['AFD'],1)}{'%' if pd.notna(d['AFD']) else ''}</strong>
                            </div>
                            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                                <span>Esforço {tooltip_html('IED')}</span>
                                <strong>{formatar_br(d['IED'],1)}{'%' if pd.notna(d['IED']) else ''}</strong>
                            </div>
                            <div style="display:flex;justify-content:space-between;">
                                <span>Complexidade {tooltip_html('ICG')}</span>
                                <strong>{formatar_br(d['ICG'],1)}</strong>
                            </div>
                        </div>""", unsafe_allow_html=True)

                # Radar
                st.markdown("---")
                st.markdown("### Perfil completo dos indicadores")
                st.caption("Quanto maior a área, melhor o perfil. ATU, Esforço e Complexidade estão com escala invertida.")
                categorias = ["Regularidade (IRD)","Alunos/turma (inv.)","Formação (%)","Esforço (inv.)","Complexidade (inv.)"]
                cores_esc  = ["#1a3a5c","#c0392b","#27ae60","#f39c12","#8e44ad"]
                fig_radar  = go.Figure()
                for i, d in enumerate(dados_comp):
                    valores = [
                        (d["IRD"]/5)*100        if pd.notna(d["IRD"]) else 0,
                        max(0,100-((d["ATU"]/40)*100)) if pd.notna(d["ATU"]) else 0,
                        d["AFD"]                if pd.notna(d["AFD"]) else 0,
                        max(0,100-d["IED"])     if pd.notna(d["IED"]) else 0,
                        max(0,100-((d["ICG"]/6)*100)) if pd.notna(d["ICG"]) else 0,
                    ]
                    valores.append(valores[0])
                    fig_radar.add_trace(go.Scatterpolar(
                        r=valores, theta=categorias+[categorias[0]],
                        fill="toself", name=d["Escola"],
                        line_color=cores_esc[i%len(cores_esc)], opacity=0.6
                    ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True,range=[0,100])),
                    height=450, margin=dict(l=40,r=40,t=40,b=40),
                    legend=dict(orientation="h",y=-0.15)
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            else:
                # ── Tabela interativa (6 a 20 escolas) ────────────────────────
                st.markdown(f"### Tabela comparativa — {n_escolas} escolas")
                st.caption("Com mais de 5 escolas, a tabela interativa substitui os cards e o radar para melhor visualização.")

                df_tab_int = df_comp[["Nome completo","Município","UF","Ano","IRD","ATU","AFD","IED","ICG","Media_nac"]].copy()
                df_tab_int["Situação"] = df_tab_int.apply(
                    lambda r: "🟢 Favorável" if pd.notna(r["IRD"]) and r["IRD"] >= r["Media_nac"]
                    else "🟡 Atenção" if pd.notna(r["IRD"]) and r["IRD"] >= r["Media_nac"]*0.85
                    else "🔴 Alerta" if pd.notna(r["IRD"]) else "⚪ Sem dados", axis=1
                )
                df_exib = df_tab_int[["Nome completo","Município","UF","Ano","IRD","ATU","AFD","IED","ICG","Situação"]].copy()
                df_exib["IRD"] = df_exib["IRD"].apply(lambda x: formatar_br(x,2))
                df_exib["ATU"] = df_exib["ATU"].apply(lambda x: formatar_br(x,1))
                df_exib["AFD"] = df_exib["AFD"].apply(lambda x: formatar_br(x,1))
                df_exib["IED"] = df_exib["IED"].apply(lambda x: formatar_br(x,1))
                df_exib["ICG"] = df_exib["ICG"].apply(lambda x: formatar_br(x,1))
                df_exib = df_exib.rename(columns={
                    "Nome completo":"Escola","IRD":"Regularidade",
                    "ATU":"Alunos/turma","AFD":"Formação (%)","IED":"Esforço (%)","ICG":"Complexidade"
                })
                st.dataframe(df_exib, use_container_width=True, hide_index=True)

                # Gráfico de barras IRD
                st.markdown("### Regularidade por escola")
                anos_unicos   = list(set(d["Ano"] for d in dados_comp))
                media_nac_ref = df_mun[df_mun["ANO"]==anos_unicos[0]]["IRD"].mean() if len(anos_unicos)==1 else df_mun["IRD"].mean()
                fig_bar = go.Figure()
                for d in dados_comp:
                    cor, _ = cor_ird(d["IRD"], d["Media_nac"])
                    fig_bar.add_trace(go.Bar(
                        name=d["Escola"], x=[d["Escola"]], y=[d["IRD"]],
                        marker_color=cor, text=[formatar_br(d["IRD"])], textposition="outside",
                        hovertemplate=f"<b>{d['Nome completo']}</b><br>{d['Município']} · {d['UF']} · {d['Ano']}<br>IRD: {formatar_br(d['IRD'])}<extra></extra>"
                    ))
                fig_bar.add_hline(y=media_nac_ref, line_dash="dash", line_color="#333",
                    annotation_text=f"Média Brasil: {formatar_br(media_nac_ref)}",
                    annotation_position="top right")
                fig_bar.update_layout(height=420, showlegend=False,
                    margin=dict(l=20,r=20,t=40,b=80),
                    yaxis=dict(title="Regularidade (0 a 5)",range=[0,5.5]),
                    xaxis=dict(tickangle=-45), bargap=0.3)
                st.plotly_chart(fig_bar, use_container_width=True)

            # ── Ranking do município (comum para qualquer quantidade) ──────────
            st.markdown("---")
            st.markdown("### Ranking de escolas do município")
            municipios_comp = list(set(d["Município"] for d in dados_comp))
            anos_comp_list  = list(set(d["Ano"] for d in dados_comp))
            col_r1, col_r2  = st.columns(2)
            with col_r1:
                mun_rank = st.selectbox("Município", municipios_comp, key="mun_rank")
            with col_r2:
                ano_rank = st.selectbox("Ano", anos_comp_list, key="ano_rank")

            co_mun_rank  = df_esc[df_esc["NO_MUNICIPIO"]==mun_rank]["CO_MUNICIPIO"].iloc[0]
            df_rank_mun  = (df_esc[(df_esc["CO_MUNICIPIO"]==co_mun_rank) & (df_esc["ANO"]==ano_rank)]
                            .dropna(subset=["IRD"]).sort_values("IRD",ascending=True).copy())
            media_nac_rank = df_mun[df_mun["ANO"]==ano_rank]["IRD"].mean()
            media_mun_rank = df_rank_mun["IRD"].mean()
            escolas_dest   = [d["CO_ENTIDADE"] for d in dados_comp if d["Município"]==mun_rank and d["Ano"]==ano_rank]

            st.markdown(f"""
            <div style="background:#f0f4f8;border-radius:8px;padding:0.8rem 1rem;margin-bottom:1rem;font-size:0.9rem;">
                📊 <strong>{mun_rank}</strong> em {ano_rank} —
                IRD médio: <strong>{formatar_br(media_mun_rank)}</strong> |
                Média nacional: <strong>{formatar_br(media_nac_rank)}</strong> |
                Total de escolas: <strong>{len(df_rank_mun)}</strong>
            </div>""", unsafe_allow_html=True)

            cores_rank = []
            for _, row in df_rank_mun.iterrows():
                if row["CO_ENTIDADE"] in escolas_dest: cores_rank.append("#1a3a5c")
                elif row["IRD"] < media_nac_rank*0.85: cores_rank.append("#c0392b")
                elif row["IRD"] < media_nac_rank:      cores_rank.append("#e67e22")
                elif row["IRD"] < media_nac_rank*1.1:  cores_rank.append("#f1c40f")
                else:                                   cores_rank.append("#27ae60")

            nomes_curtos = [n[:22]+"..." if len(n)>22 else n for n in df_rank_mun["NO_ENTIDADE"]]
            fig_rank = go.Figure()
            fig_rank.add_trace(go.Bar(x=df_rank_mun["IRD"].tolist(), y=nomes_curtos,
                orientation="h", marker_color=cores_rank,
                hovertemplate="<b>%{y}</b><br>IRD: %{x:.3f}<extra></extra>"))
            fig_rank.add_vline(x=media_nac_rank, line_dash="dash", line_color="#333",
                annotation_text=f"Média Brasil: {formatar_br(media_nac_rank)}", annotation_position="top right")
            fig_rank.add_vline(x=media_mun_rank, line_dash="dot", line_color="#e67e22",
                annotation_text=f"Média {mun_rank}: {formatar_br(media_mun_rank)}", annotation_position="bottom right")
            fig_rank.update_layout(height=max(400,len(df_rank_mun)*22),
                margin=dict(l=20,r=20,t=20,b=20),
                xaxis=dict(title="Regularidade (0 a 5)",range=[0,5.5]),
                yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_rank, use_container_width=True)
            st.caption("Azul escuro = escolas selecionadas. Vermelho = Alerta | Laranja = Atenção | Amarelo = Moderado | Verde = Favorável.")

            # ── Tabela e download ──────────────────────────────────────────────
            st.markdown("---")
            st.markdown("### Tabela comparativa completa")
            df_dl = df_comp[["Nome completo","Município","UF","Ano","IRD","ATU","AFD","IED","ICG"]].copy()
            for col in ["IRD","ATU","AFD","IED","ICG"]:
                df_dl[col] = df_dl[col].apply(lambda x: formatar_br(x,2))
            df_dl = df_dl.rename(columns={"Nome completo":"Escola","IRD":"Regularidade",
                "ATU":"Alunos/turma","AFD":"Formação (%)","IED":"Esforço (%)","ICG":"Complexidade"})
            st.dataframe(df_dl, use_container_width=True, hide_index=True)
            csv = df_dl.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 Baixar comparação (CSV)", data=csv,
                file_name="comparacao_escolas_regdoc.csv", mime="text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# ABA 2 — COMPARAÇÃO DE MUNICÍPIOS
# ══════════════════════════════════════════════════════════════════════════════
with aba_mun:
    st.markdown("### Selecione os municípios para comparar")
    st.caption("Adicione até 10 municípios de qualquer estado")

    if "municipios_selecionados" not in st.session_state:
        st.session_state.municipios_selecionados = []

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        ufs_m = sorted(df_mun["SG_UF"].dropna().unique())
        uf_mun = st.selectbox("Estado", ufs_m, key="uf_mun",
            index=ufs_m.index("ES") if "ES" in ufs_m else 0)
    with col2:
        muns_uf = (df_mun[df_mun["SG_UF"]==uf_mun][["CO_MUNICIPIO","NO_MUNICIPIO"]]
            .drop_duplicates().sort_values("NO_MUNICIPIO"))
        mun_sel_add = st.selectbox("Município", muns_uf["NO_MUNICIPIO"].tolist(), key="mun_sel_add")
    with col3:
        anos_mun = sorted(df_mun["ANO"].unique())
        ano_mun = st.selectbox("Ano", anos_mun, index=len(anos_mun)-1, key="ano_mun")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Adicionar", use_container_width=True, key="btn_add_mun"):
            co_mun_sel = muns_uf[muns_uf["NO_MUNICIPIO"]==mun_sel_add]["CO_MUNICIPIO"].iloc[0]
            entrada_mun = {"CO_MUNICIPIO":co_mun_sel,"NO_MUNICIPIO":mun_sel_add,
                           "SG_UF":uf_mun,"ANO":ano_mun}
            if len(st.session_state.municipios_selecionados) >= 10:
                st.warning("Máximo de 10 municípios atingido.")
            elif any(m["CO_MUNICIPIO"]==co_mun_sel and m["ANO"]==ano_mun
                     for m in st.session_state.municipios_selecionados):
                st.warning("Este município já foi adicionado para este ano.")
            else:
                st.session_state.municipios_selecionados.append(entrada_mun)
                st.rerun()

    if st.session_state.municipios_selecionados:
        cols_mun = st.columns(min(len(st.session_state.municipios_selecionados), 5))
        for i, m in enumerate(st.session_state.municipios_selecionados):
            with cols_mun[i % 5]:
                st.markdown(f"""
                <div style="background:#f0f4f8;border-radius:8px;padding:0.5rem 0.8rem;
                     border-left:4px solid #2e6da4;font-size:0.82rem;margin-bottom:4px;">
                    <strong>{m['NO_MUNICIPIO'][:28]}</strong><br>
                    {m['SG_UF']} · {m['ANO']}
                </div>""", unsafe_allow_html=True)
                if st.button("✕", key=f"rem_mun_{i}"):
                    st.session_state.municipios_selecionados.pop(i)
                    st.rerun()

    if st.button("🗑️ Limpar todos", key="limpar_mun"):
        st.session_state.municipios_selecionados = []
        st.rerun()

    if len(st.session_state.municipios_selecionados) < 2:
        st.info("Adicione pelo menos 2 municípios para comparar.")
    else:
        dados_mun_comp = []
        for m in st.session_state.municipios_selecionados:
            linha = df_mun[(df_mun["CO_MUNICIPIO"]==m["CO_MUNICIPIO"]) & (df_mun["ANO"]==m["ANO"])]
            if not linha.empty:
                r = linha.iloc[0]
                media_nac = df_mun[df_mun["ANO"]==m["ANO"]]["IRD"].mean()
                dados_mun_comp.append({
                    "Município": m["NO_MUNICIPIO"],
                    "UF": m["SG_UF"],
                    "Ano": m["ANO"],
                    "IRD": r["IRD"], "ATU": r.get("ATU"),
                    "AFD": r.get("AFD"), "IED": r.get("IED"),
                    "ICG": r.get("ICG"), "Media_nac": media_nac
                })

        if not dados_mun_comp:
            st.warning("Sem dados para os municípios selecionados.")
        else:
            df_mun_comp = pd.DataFrame(dados_mun_comp)
            anos_unicos_m = list(set(d["Ano"] for d in dados_mun_comp))
            media_ref     = df_mun[df_mun["ANO"]==anos_unicos_m[0]]["IRD"].mean() if len(anos_unicos_m)==1 else df_mun["IRD"].mean()

            st.markdown("---")

            # Cards IRD
            st.markdown("### Regularidade dos professores por município")
            cols_mc = st.columns(len(dados_mun_comp))
            for i, d in enumerate(dados_mun_comp):
                cor, bg = cor_ird(d["IRD"], d["Media_nac"])
                with cols_mc[i]:
                    st.markdown(f"""
                    <div style="background:{bg};border:2px solid {cor};border-radius:10px;
                         padding:1rem;text-align:center;">
                        <p style="font-size:0.8rem;color:{cor};margin:0;font-weight:bold;">{d['Município']}</p>
                        <p style="font-size:0.7rem;color:#777;margin:0.2rem 0;">{d['UF']} · {d['Ano']}</p>
                        <p style="font-size:2rem;font-weight:bold;color:{cor};margin:0.3rem 0;">{formatar_br(d['IRD'])}</p>
                        <p style="font-size:0.75rem;color:{cor};margin:0;">vs. Média Brasil: {formatar_br(d['Media_nac'])}</p>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Gráfico barras IRD
            st.markdown("### Comparação visual — IRD")
            fig_mun_bar = go.Figure()
            cores_mun = ["#1a3a5c","#c0392b","#27ae60","#f39c12","#8e44ad",
                         "#16a085","#d35400","#2980b9","#8e44ad","#27ae60"]
            for i, d in enumerate(dados_mun_comp):
                cor, _ = cor_ird(d["IRD"], d["Media_nac"])
                fig_mun_bar.add_trace(go.Bar(
                    name=f"{d['Município']} ({d['Ano']})",
                    x=[f"{d['Município']} · {d['Ano']}"], y=[d["IRD"]],
                    marker_color=cor, text=[formatar_br(d["IRD"])], textposition="outside",
                    hovertemplate=f"<b>{d['Município']}</b><br>{d['UF']} · {d['Ano']}<br>IRD: {formatar_br(d['IRD'])}<extra></extra>"
                ))
            fig_mun_bar.add_hline(y=media_ref, line_dash="dash", line_color="#333",
                annotation_text=f"Média Brasil: {formatar_br(media_ref)}",
                annotation_position="top right")
            fig_mun_bar.update_layout(height=400, showlegend=False,
                margin=dict(l=20,r=20,t=40,b=80),
                yaxis=dict(title="Regularidade (0 a 5)",range=[0,5.5]),
                xaxis=dict(tickangle=-30), bargap=0.3)
            st.plotly_chart(fig_mun_bar, use_container_width=True)

            # Tabela comparativa de todos os indicadores
            st.markdown("---")
            st.markdown("### Tabela comparativa de indicadores")
            df_mun_tab = df_mun_comp[["Município","UF","Ano","IRD","ATU","AFD","IED","ICG"]].copy()
            df_mun_tab["IRD"] = df_mun_tab["IRD"].apply(lambda x: formatar_br(x,2))
            df_mun_tab["ATU"] = df_mun_tab["ATU"].apply(lambda x: formatar_br(x,1))
            df_mun_tab["AFD"] = df_mun_tab["AFD"].apply(lambda x: formatar_br(x,1))
            df_mun_tab["IED"] = df_mun_tab["IED"].apply(lambda x: formatar_br(x,1))
            df_mun_tab["ICG"] = df_mun_tab["ICG"].apply(lambda x: formatar_br(x,1))
            df_mun_tab = df_mun_tab.rename(columns={
                "IRD":"Regularidade","ATU":"Alunos/turma",
                "AFD":"Formação (%)","IED":"Esforço (%)","ICG":"Complexidade"
            })
            st.dataframe(df_mun_tab, use_container_width=True, hide_index=True)

            csv_mun = df_mun_tab.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 Baixar comparação de municípios (CSV)",
                data=csv_mun, file_name="comparacao_municipios_regdoc.csv", mime="text/csv")

            # Evolução histórica comparada
            st.markdown("---")
            st.markdown("### Evolução histórica comparada")
            st.caption("Série histórica do IRD de cada município selecionado")

            fig_evo_mun = go.Figure()
            cores_evo = ["#1a3a5c","#c0392b","#27ae60","#f39c12","#8e44ad",
                         "#16a085","#d35400","#2980b9","#8e44ad","#27ae60"]
            muns_unicos = list(set(d["Município"] for d in dados_mun_comp))
            for i, mun in enumerate(muns_unicos):
                co = df_mun[df_mun["NO_MUNICIPIO"]==mun]["CO_MUNICIPIO"].iloc[0]
                uf = next(d["UF"] for d in dados_mun_comp if d["Município"]==mun)
                serie = df_mun[df_mun["CO_MUNICIPIO"]==co][["ANO","IRD"]].sort_values("ANO")
                fig_evo_mun.add_trace(go.Scatter(
                    x=serie["ANO"], y=serie["IRD"],
                    name=f"{mun} · {uf}",
                    line=dict(color=cores_evo[i%len(cores_evo)],width=2.5),
                    mode="lines+markers", marker_size=7
                ))

            ird_nac_serie = df_mun.groupby("ANO")["IRD"].mean().reset_index()
            fig_evo_mun.add_trace(go.Scatter(
                x=ird_nac_serie["ANO"], y=ird_nac_serie["IRD"],
                name="Média Brasil", line=dict(color="#aaa",dash="dash",width=1.5)
            ))
            fig_evo_mun.update_layout(height=400,
                margin=dict(l=20,r=20,t=20,b=20),
                legend=dict(orientation="h",y=-0.2),
                yaxis=dict(title="Regularidade (0 a 5)",range=[0,5.2]),
                xaxis_title="Ano")
            sombrear_pandemia(fig_evo_mun)
            st.plotly_chart(fig_evo_mun, use_container_width=True)

# ── Nota metodológica ──────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("ℹ️ Como interpretar as comparações"):
    st.markdown("""
    **Comparação de Escolas**
    Cada escola é comparada com a média nacional do ano selecionado.
    Verde = acima da média; Laranja = entre 85% e 100%; Vermelho = abaixo de 85%.
    Com até 5 escolas, aparece o gráfico radar. Com 6 a 20 escolas, aparece a tabela interativa.

    **Comparação de Municípios**
    Permite comparar o IRD médio, ATU, AFD, IED e ICG de até 10 municípios lado a lado,
    incluindo a evolução histórica de cada um desde 2013.

    **Limitação importante**
    As comparações não controlam pelo nível socioeconômico (INSE) — municípios e escolas
    em contextos mais vulneráveis tendem a ter IRD menor por razões estruturais.
    Use como ponto de partida para investigação, não como diagnóstico definitivo.

    **Fonte:** Censo Escolar da Educação Básica — INEP/MEC. Dados públicos, uso gratuito e irrestrito.
    """)

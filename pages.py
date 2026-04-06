
import streamlit as st
import pandas as pd
import plotly.express as px

# Importar funções auxiliares do app.py se necessário, ou passá-las como argumento
# Por enquanto, assumimos que carregar_metas e obter_coluna_nome_turma serão passadas ou importadas

def render_visao_360(dados, mes_analise, col_nome, df_turmas_f, df_ocupacao_f, carregar_metas_func):
    st.title(f"🌐 Visão Institucional - {mes_analise[5:] if mes_analise else ''}") 
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Turmas Abertas", len(df_turmas_f))
    col2.metric("Alunos", df_turmas_f["VAGAS_OCUPADAS"].sum() if not df_turmas_f.empty else 0)
    col3.metric("Salas Físicas", len(dados["amb"][dados["amb"]["VIRTUAL"] == "NÃO"]))
    col4.metric("Instrutores", len(dados["inst"])) 
    col5.metric("Faltas Registadas", len(dados["faltas"])) 
    
    st.divider()
    st.markdown("### 🎯 Execução de Hora-Aluno (HA) - Visão Macro")
    
    df_disc = dados["disc"].copy()
    df_disc["STATUS_NORM"] = df_disc["STATUS"].astype(str).str.strip().str.upper()
    
    df_turmas_resumo = df_turmas_f[["ID_TURMA", "VAGAS_OCUPADAS"]].copy()
    if col_nome != "ID_TURMA":
        df_turmas_resumo[col_nome] = df_turmas_f[col_nome]
        df_turmas_resumo["TURMA_EXIBICAO"] = df_turmas_resumo["ID_TURMA"].astype(str) + " - " + df_turmas_resumo[col_nome].astype(str)
    else:
        df_turmas_resumo["TURMA_EXIBICAO"] = "Turma " + df_turmas_resumo["ID_TURMA"].astype(str)
        
    df_ha = pd.merge(df_disc, df_turmas_resumo, on="ID_TURMA", how="inner")
    df_ha["HA_TOTAL"] = df_ha["CARGA_HORARIA"] * df_ha["VAGAS_OCUPADAS"]
    
    ha_meta_planilha = df_ha["HA_TOTAL"].sum()
    metas_config = carregar_metas_func()
    meta_manual = metas_config.get(mes_analise, 0)
    
    if meta_manual > 0:
        ha_meta = meta_manual
        tipo_meta = "Manual (Admin)"
    else:
        ha_meta = ha_meta_planilha
        tipo_meta = "Automática (Planilha)"
        
    ha_cumprida = df_ha[df_ha["STATUS_NORM"].isin(["CONCLUÍDO", "CONCLUIDO", "FINALIZADO"])]["HA_TOTAL"].sum()
    perc_ha = (ha_cumprida / ha_meta) * 100 if ha_meta > 0 else 0
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric(f"📚 Meta HA - {tipo_meta}", f"{ha_meta:,.0f} HA".replace(",", "."))
    col_m2.metric("✅ Realizado (Hora-Aluno)", f"{ha_cumprida:,.0f} HA".replace(",", "."))
    col_m3.metric("🚀 Progresso da Meta", f"{perc_ha:.1f}%")
    st.progress(min(int(perc_ha), 100))
    
    st.divider()
    st.markdown("### 🏁 Progresso de Conclusão por Turma")
    st.caption("Acompanhamento individual de cada turma com base nas disciplinas concluídas.")
    
    # Vetorização: Criar coluna booleana para status concluído
    df_ha["CONCLUIDO"] = df_ha["STATUS_NORM"].isin(["CONCLUÍDO", "CONCLUIDO", "FINALIZADO"])
    
    # Agregação vetorizada (mais rápida que .apply)
    df_ha_turma = df_ha.groupby("TURMA_EXIBICAO").agg(
        HA_META=("HA_TOTAL", "sum"),
        HA_REALIZADO=("HA_TOTAL", lambda x: x[df_ha.loc[x.index, "CONCLUIDO"]].sum())
    ).reset_index()
    
    df_ha_turma["PROGRESSO_%"] = (df_ha_turma["HA_REALIZADO"] / df_ha_turma["HA_META"]) * 100
    df_ha_turma["PROGRESSO_%"] = df_ha_turma["PROGRESSO_%"].fillna(0).round(1)
    
    if not df_ha_turma.empty:
        fig_turmas = px.bar(
            df_ha_turma.sort_values("PROGRESSO_%", ascending=True), 
            x="PROGRESSO_%", 
            y="TURMA_EXIBICAO", 
            orientation="h",
            title="Ranking de Progresso por Turma (%)",
            text="PROGRESSO_%",
            color="PROGRESSO_%",
            color_continuous_scale="Greens"
        )
        fig_turmas.update_layout(xaxis=dict(range=[0, 100]), yaxis_title="Turma / Curso", xaxis_title="Conclusão (%)")
        st.plotly_chart(fig_turmas, use_container_width=True)
        
        with st.expander("🔍 Ver detalhamento de disciplinas por turma"):
            turma_selecionada = st.selectbox("Selecione uma turma para analisar:", df_ha_turma["TURMA_EXIBICAO"].unique())
            df_detalhe_turma = df_ha[df_ha["TURMA_EXIBICAO"] == turma_selecionada][["NOME_DISCIPLINA", "CARGA_HORARIA", "STATUS", "HA_TOTAL"]]
            
            def pintar_status(val):
                cor = "#d4edda" if str(val).strip().upper() in ["CONCLUÍDO", "CONCLUIDO", "FINALIZADO"] else "#f8d7da"
                return f"background-color: {cor}; color: black"
            
            try:
                st.dataframe(df_detalhe_turma.style.map(pintar_status, subset=["STATUS"]), use_container_width=True, hide_index=True)
            except AttributeError:
                st.dataframe(df_detalhe_turma.style.applymap(pintar_status, subset=["STATUS"]), use_container_width=True, hide_index=True)
    else:
        st.info("Não há dados suficientes para cruzar turmas e disciplinas neste mês.")

    st.divider()
    st.markdown("#### Status de Execução das Disciplinas (Geral)")
    status_disc = df_disc["STATUS"].value_counts().reset_index()
    status_disc.columns = ["Status", "Quantidade"]
    st.plotly_chart(px.pie(status_disc, names="Status", values="Quantidade", hole=0.4, color_discrete_sequence=px.colors.sequential.Teal), use_container_width=True)


def render_analise_docentes(dados, mes_analise):
    st.title(f"👥 Docentes e Não Regência - {mes_analise[5:]}")
    df_nr_det = pd.merge(dados["nr"], dados["inst"][["ID", "NOME_COMPLETO"]], left_on="ID_INSTRUTOR", right_on="ID", how="left")
    if not df_nr_det.empty:
        df_horas_inst = df_nr_det.groupby("NOME_COMPLETO")["HORAS_NAO_REGENCIA"].sum().reset_index().sort_values("HORAS_NAO_REGENCIA")
        st.plotly_chart(px.bar(df_horas_inst, x="HORAS_NAO_REGENCIA", y="NOME_COMPLETO", orientation="h", title="Ranking de Horas Não Regência", color="HORAS_NAO_REGENCIA", color_continuous_scale="Oranges"), use_container_width=True)
        
        # --- Suporte às colunas de Data ---
        if "DATA_INICIO" in df_nr_det.columns:
            df_nr_det["DATA_INICIO"] = pd.to_datetime(df_nr_det["DATA_INICIO"], errors="coerce").dt.strftime("%d/%m/%Y")
        if "DATA_FIM" in df_nr_det.columns:
            df_nr_det["DATA_FIM"] = pd.to_datetime(df_nr_det["DATA_FIM"], errors="coerce").dt.strftime("%d/%m/%Y")
            
        colunas_exibir = ["NOME_COMPLETO", "TIPO_ATIVIDADE", "HORAS_NAO_REGENCIA"]
        if "DATA_INICIO" in df_nr_det.columns and "DATA_FIM" in df_nr_det.columns:
            colunas_exibir = ["DATA_INICIO", "DATA_FIM"] + colunas_exibir
        elif "DATA" in df_nr_det.columns:
            colunas_exibir = ["DATA"] + colunas_exibir
            
        st.dataframe(df_nr_det[colunas_exibir], use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados de Não Regência para este mês.")

def render_ocupacao_ambientes(dados, mes_analise, df_ocupacao_f):
    st.title(f"🏢 Uso de Laboratórios e Salas - {mes_analise[5:] if mes_analise else ''}")
    
    if not df_ocupacao_f.empty:
        if 'DATA' in df_ocupacao_f.columns:
            df_ocupacao_f['DATA'] = pd.to_datetime(df_ocupacao_f['DATA'], errors='coerce')
        
        tipo_grafico = st.selectbox(
            "📊 Selecione a visão de análise de ocupação:",
            [
                "Visão Geral (Média por Ambiente)", 
                "Evolução Diária (Linha do Tempo)", 
                "Mapa de Calor (Ambiente vs. Dia)"
            ]
        )
        
        st.divider()
        
        if tipo_grafico == "Visão Geral (Média por Ambiente)":
            st.subheader("Ocupação Média Acumulada")
            df_amb_uso = df_ocupacao_f.groupby('AMBIENTE')['PERCENTUAL_OCUPACAO'].mean().reset_index()
            df_amb_uso['PERCENTUAL_OCUPACAO'] *= 100
            
            fig = px.bar(
                df_amb_uso.sort_values('PERCENTUAL_OCUPACAO'), 
                x='PERCENTUAL_OCUPACAO', 
                y='AMBIENTE', 
                orientation='h', 
                color='PERCENTUAL_OCUPACAO', 
                color_continuous_scale='Blues',
                text_auto='.1f'
            )
            fig.update_layout(xaxis_title="Ocupação Média (%)", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
            
        elif tipo_grafico == "Evolução Diária (Linha do Tempo)":
            st.subheader("Evolução da Ocupação ao Longo do Mês")
            if 'DATA' in df_ocupacao_f.columns:
                df_diario = df_ocupacao_f.groupby('DATA')['PERCENTUAL_OCUPACAO'].mean().reset_index()
                df_diario['PERCENTUAL_OCUPACAO'] *= 100
                df_diario = df_diario.dropna(subset=['DATA']).sort_values('DATA')
                
                fig = px.line(
                    df_diario, 
                    x='DATA', 
                    y='PERCENTUAL_OCUPACAO', 
                    markers=True,
                    line_shape="spline"
                )
                fig.update_traces(line_color='#1f77b4', line_width=3, marker=dict(size=8))
                fig.update_yaxes(range=[0, 100], title="Ocupação Média (%)")
                fig.update_xaxes(title="Data")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ A coluna 'DATA' não foi encontrada na planilha de Ocupação.")
                
        elif tipo_grafico == "Mapa de Calor (Ambiente vs. Dia)":
            st.subheader("🔥 Mapa de Calor Diário por Ambiente")
            st.caption("Cores mais escuras indicam maior nível de lotação.")
            
            if 'DATA' in df_ocupacao_f.columns:
                df_heat = df_ocupacao_f.copy()
                df_heat['DIA_FORMATADO'] = df_heat['DATA'].dt.strftime('%d/%m')
                
                pivot_heat = df_heat.pivot_table(
                    index='AMBIENTE', 
                    columns='DIA_FORMATADO', 
                    values='PERCENTUAL_OCUPACAO', 
                    aggfunc='mean'
                )
                
                pivot_heat = pivot_heat * 100
                
                fig = px.imshow(
                    pivot_heat, 
                    text_auto=".0f", 
                    aspect="auto",
                    color_continuous_scale='YlOrRd', 
                    labels=dict(x="Dia", y="Ambiente", color="Ocupação (%)")
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ A coluna 'DATA' não foi encontrada na planilha de Ocupação.")
                
    else:
        st.info("Sem dados de Ocupação para este mês.")

import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Dashboard Digitech 2026", layout="wide", page_icon="📊")

# ==========================================
# 2. CARREGAMENTO DOS DADOS
# ==========================================
@st.cache_data
def load_data():
    arquivo_excel = "Consolidado - Status 2026.xlsx"
    xls = pd.ExcelFile(arquivo_excel)
    
    # Lendo as abas com os devidos tratamentos de cabeçalho
    df_turmas = pd.read_excel(xls, sheet_name="TURMAS")
    df_ocupacao = pd.read_excel(xls, sheet_name="OCUPAÇÃO")
    df_nr = pd.read_excel(xls, sheet_name="NÃO_REGÊNCIA")
    df_inst = pd.read_excel(xls, sheet_name="INSTRUTORES")
    df_disc = pd.read_excel(xls, sheet_name="DISCIPLINAS", skiprows=1)
    df_amb = pd.read_excel(xls, sheet_name="AMBIENTES")
    df_faltas = pd.read_excel(xls, sheet_name="FALTAS")
    df_param = pd.read_excel(xls, sheet_name="PARÂMETROS", skiprows=9)
    
    return df_turmas, df_ocupacao, df_nr, df_inst, df_disc, df_amb, df_faltas, df_param

try:
    df_turmas, df_ocupacao, df_nr, df_inst, df_disc, df_amb, df_faltas, df_param = load_data()
except Exception as e:
    st.error(f"Erro ao carregar o ficheiro Excel. Verifique se o nome está correto e na mesma pasta. Detalhe: {e}")
    st.stop()

# ==========================================
# 3. MENU LATERAL (SIDEBAR) E FILTROS
# ==========================================
st.sidebar.title("🧭 Navegação")
pagina_selecionada = st.sidebar.radio(
    "Escolha o Painel:",
    ["🌐 Visão 360º", "👥 Análise de Docentes (RH)", "🏢 Ocupação e Ambientes"]
)

st.sidebar.divider()

st.sidebar.markdown("### 🔍 Filtros Globais")
# Criar lista de turnos únicos e adicionar a opção "Todos"
lista_turnos = ["Todos"] + list(df_turmas['TURNO'].dropna().unique())
turno_selecionado = st.sidebar.selectbox("Filtrar por Turno:", lista_turnos)

# Aplicar o filtro nos DataFrames que possuem a coluna TURNO
if turno_selecionado != "Todos":
    df_turmas_filtrado = df_turmas[df_turmas['TURNO'] == turno_selecionado]
    if 'TURNO' in df_ocupacao.columns:
        df_ocupacao_filtrado = df_ocupacao[df_ocupacao['TURNO'] == turno_selecionado]
    else:
        df_ocupacao_filtrado = df_ocupacao.copy()
else:
    df_turmas_filtrado = df_turmas.copy()
    df_ocupacao_filtrado = df_ocupacao.copy()

st.sidebar.info("💡 **Dica:** O filtro de Turno afeta as métricas de Turmas e Ocupação de Ambientes.")

# Função auxiliar para encurtar nomes nos gráficos
def encurtar_nome(nome):
    partes = str(nome).split()
    if len(partes) > 1:
        return f"{partes[0]} {partes[-1]}"
    return nome

# ==========================================
# 4. ROTEAMENTO DAS PÁGINAS
# ==========================================

# ------------------------------------------
# PÁGINA 1: VISÃO 360º
# ------------------------------------------
if pagina_selecionada == "🌐 Visão 360º":
    st.title("🌐 Visão Institucional Completa")
    st.markdown("Visão geral de todas as métricas da unidade (Os dados de turmas respeitam o filtro lateral).")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    total_alunos = df_turmas_filtrado['VAGAS_OCUPADAS'].sum() if not df_turmas_filtrado.empty else 0
    total_salas_fisicas = len(df_amb[df_amb['VIRTUAL'] == 'NÃO'])
    
    col1.metric("Turmas Abertas", len(df_turmas_filtrado))
    col2.metric("Alunos Matriculados", total_alunos)
    col3.metric("Salas Físicas", total_salas_fisicas)
    col4.metric("Corpo Docente", len(df_inst))
    col5.metric("Total de Disciplinas", len(df_disc))
    col6.metric("Faltas Registadas", len(df_faltas))
    
    st.divider()
    
    st.markdown("#### Status de Execução das Disciplinas")
    status_disc = df_disc['STATUS'].value_counts().reset_index()
    status_disc.columns = ['Status', 'Quantidade']
    fig_disc = px.pie(status_disc, names='Status', values='Quantidade', hole=0.4, 
                      color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_disc.update_layout(height=350)
    st.plotly_chart(fig_disc, use_container_width=True)


# ------------------------------------------
# PÁGINA 2: ANÁLISE DE DOCENTES (RH)
# ------------------------------------------
elif pagina_selecionada == "👥 Análise de Docentes (RH)":
    st.title("👥 Desempenho e Alocação de Instrutores")
    
    aba1, aba2 = st.tabs(["📌 Afastamentos e Status", "⏳ Detalhamento de Não Regência"])
    
    with aba1:
        st.markdown("#### Profissionais com Observações (Férias/Afastamentos)")
        df_inst_afastados = df_inst.dropna(subset=['OBSERVAÇÃO']).copy()
        
        if not df_inst_afastados.empty:
            df_inst_afastados['Nome Curto'] = df_inst_afastados['NOME_COMPLETO'].apply(encurtar_nome)
            fig_inst = px.bar(
                df_inst_afastados, 
                x="OBSERVAÇÃO", 
                y="Nome Curto", 
                color="OBSERVAÇÃO",
                orientation='h',
                labels={'Nome Curto': 'Instrutor', 'OBSERVAÇÃO': 'Motivo'}
            )
            fig_inst.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_inst, use_container_width=True)
            
            with st.expander("Ver lista detalhada de docentes afastados"):
                st.dataframe(df_inst_afastados[['NOME_COMPLETO', 'EMAIL', 'OBSERVAÇÃO']], use_container_width=True)
        else:
            st.success("Todos os instrutores estão ativos e sem observações de afastamento neste momento.")

    with aba2:
        st.markdown("#### Análise de Atividades Extra-Classe (Não Regência)")
        if not df_nr.empty:
            
            # 1. Cruzando os dados da aba Não Regência (ID) com a aba Instrutores (Nomes)
            df_nr_detalhado = pd.merge(df_nr, df_inst[['ID', 'NOME_COMPLETO']], left_on='ID_INSTRUTOR', right_on='ID', how='left')
            df_nr_detalhado['Nome Curto'] = df_nr_detalhado['NOME_COMPLETO'].apply(encurtar_nome)
            
            # Criando duas colunas para os gráficos
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                # Gráfico de Pizza: Tipos de Atividade
                df_tipo = df_nr_detalhado.groupby('TIPO_ATIVIDADE')['HORAS_NAO_REGENCIA'].sum().reset_index()
                fig_tipo = px.pie(df_tipo, values='HORAS_NAO_REGENCIA', names='TIPO_ATIVIDADE', hole=0.4, 
                                  title="Horas por Tipo de Atividade")
                fig_tipo.update_layout(height=400)
                st.plotly_chart(fig_tipo, use_container_width=True)
                
            with col_g2:
                # Gráfico de Barras: Horas por Instrutor
                df_horas_inst = df_nr_detalhado.groupby('Nome Curto')['HORAS_NAO_REGENCIA'].sum().reset_index()
                df_horas_inst = df_horas_inst.sort_values('HORAS_NAO_REGENCIA', ascending=True)
                fig_inst_nr = px.bar(df_horas_inst, x='HORAS_NAO_REGENCIA', y='Nome Curto', orientation='h',
                                     title="Ranking de Horas por Instrutor",
                                     labels={'HORAS_NAO_REGENCIA': 'Total de Horas', 'Nome Curto': ''},
                                     color='HORAS_NAO_REGENCIA', color_continuous_scale='Oranges')
                fig_inst_nr.update_layout(height=400)
                st.plotly_chart(fig_inst_nr, use_container_width=True)
            
            st.divider()
            
            # 2. Tabela Interativa de Detalhamento
            st.markdown("#### 📋 Histórico Detalhado (Registro a Registro)")
            st.caption("Explore a tabela abaixo para ver o motivo exato de cada alocação. Você pode clicar nos cabeçalhos para ordenar.")
            
            # Preparando a tabela para exibição (selecionando e renomeando colunas)
            df_tabela = df_nr_detalhado[['DATA', 'NOME_COMPLETO', 'TIPO_ATIVIDADE', 'HORAS_NAO_REGENCIA', 'DESCRICAO', 'COMPROVANTE']].copy()
            df_tabela.columns = ['Data', 'Instrutor', 'Atividade', 'Horas', 'Descrição Detalhada', 'Status Comprovante']
            
            # Formatando a data para o padrão brasileiro
            df_tabela['Data'] = pd.to_datetime(df_tabela['Data']).dt.strftime('%d/%m/%Y')
            
            # Exibindo a tabela usando a funcionalidade nativa e interativa do Streamlit
            st.dataframe(df_tabela, use_container_width=True, hide_index=True)
            
        else:
            st.info("Não há dados de Não Regência registados na planilha.")


# ------------------------------------------
# PÁGINA 3: OCUPAÇÃO E AMBIENTES
# ------------------------------------------
elif pagina_selecionada == "🏢 Ocupação e Ambientes":
    st.title("🏢 Análise de Uso de Laboratórios e Salas")
    if turno_selecionado != "Todos":
        st.caption(f"Visualizando dados apenas para o turno: **{turno_selecionado}**")
    
    aba_vagas, aba_salas = st.tabs(["🎓 Ocupação de Vagas (Turmas)", "🏫 Uso de Salas Físicas"])
    
    with aba_vagas:
        st.markdown("#### Preenchimento de Vagas por Turma")
        if not df_turmas_filtrado.empty:
            df_turmas_filtrado['Turma Curta'] = df_turmas_filtrado['NOME_TURMA'].apply(lambda x: str(x)[:30] + "..." if len(str(x)) > 30 else x)
            df_t_melt = df_turmas_filtrado.melt(id_vars=['Turma Curta'], value_vars=['VAGAS_TOTAL', 'VAGAS_OCUPADAS'], 
                                                var_name='Tipo', value_name='Quantidade')
            
            fig_vagas = px.bar(df_t_melt, x='Turma Curta', y='Quantidade', color='Tipo', barmode='group',
                               color_discrete_sequence=['#1f77b4', '#ff7f0e'],
                               labels={'Turma Curta': 'Turma', 'Quantidade': 'Nº de Vagas'})
            
            fig_vagas.update_layout(height=500)
            st.plotly_chart(fig_vagas, use_container_width=True)
        else:
            st.warning(f"Não há turmas registadas para o turno {turno_selecionado}.")

    with aba_salas:
        st.markdown("#### Ranking de Ocupação Média por Ambiente")
        if not df_ocupacao_filtrado.empty:
            df_amb_uso = df_ocupacao_filtrado.groupby('AMBIENTE')['PERCENTUAL_OCUPACAO'].mean().reset_index()
            df_amb_uso['PERCENTUAL_OCUPACAO'] *= 100
            df_amb_uso = df_amb_uso.sort_values('PERCENTUAL_OCUPACAO', ascending=True)
            
            fig_amb = px.bar(df_amb_uso, x='PERCENTUAL_OCUPACAO', y='AMBIENTE', orientation='h', 
                             color='PERCENTUAL_OCUPACAO', color_continuous_scale='Blues',
                             labels={'PERCENTUAL_OCUPACAO': 'Ocupação Média (%)', 'AMBIENTE': 'Sala / Laboratório'})
                             
            try:
                meta_ideal = df_param[df_param['PARÂMETRO'] == 'Meta Ocupação Ideal']['VALOR'].values[0] * 100
                fig_amb.add_vline(x=meta_ideal, line_dash="dot", line_color="red", annotation_text="Meta Ideal")
            except:
                pass
            
            fig_amb.update_layout(height=600)
            st.plotly_chart(fig_amb, use_container_width=True)
        else:
            st.warning(f"Não há dados de ocupação de salas registados para o turno {turno_selecionado}.")
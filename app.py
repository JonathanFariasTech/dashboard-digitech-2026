import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==========================================
# 1. CONFIGURAÇÃO E CRIAÇÃO DO COFRE DE DADOS
# ==========================================
st.set_page_config(page_title="Dashboard Digitech", layout="wide", page_icon="📊")

PASTA_HISTORICO = "historico_dados"
os.makedirs(PASTA_HISTORICO, exist_ok=True) # Cria a pasta automaticamente se não existir

# ==========================================
# 2. MENU LATERAL: GESTÃO DE UPLOADS
# ==========================================
st.sidebar.title("📥 Gestão de Dados")

with st.sidebar.expander("➕ Adicionar Novo Mês", expanded=False):
    st.markdown("Faça o upload da planilha mensal para guardá-la no histórico.")
    arquivo_carregado = st.file_uploader("Planilha (.xlsx)", type=["xlsx"])
    nome_mes = st.text_input("Nome do Mês/Ano (Ex: 01 - Jan 2026)")
    
    if st.button("💾 Salvar no Histórico"):
        if arquivo_carregado and nome_mes:
            caminho_arquivo = os.path.join(PASTA_HISTORICO, f"{nome_mes}.xlsx")
            # Salva o arquivo fisicamente na pasta
            with open(caminho_arquivo, "wb") as f:
                f.write(arquivo_carregado.getbuffer())
            st.success(f"Dados de {nome_mes} salvos com sucesso!")
            st.rerun() # Recarrega a página para atualizar a lista
        else:
            st.warning("Insira o ficheiro e digite o nome do mês.")

# ==========================================
# 3. VERIFICAÇÃO DE HISTÓRICO EXISTENTE
# ==========================================
arquivos_salvos = sorted([f for f in os.listdir(PASTA_HISTORICO) if f.endswith('.xlsx')])

if not arquivos_salvos:
    st.title("📊 Painel de Desempenho 360º - Digitech")
    st.info("👈 **Cofre vazio!** Utilize o menu lateral esquerdo em 'Adicionar Novo Mês' para subir sua primeira planilha consolidada.")
    st.stop()

# ==========================================
# 4. CARREGAMENTO DOS DADOS (CACHE)
# ==========================================
@st.cache_data
def load_data(file_path):
    xls = pd.ExcelFile(file_path)
    return {
        'turmas': pd.read_excel(xls, sheet_name="TURMAS"),
        'ocupacao': pd.read_excel(xls, sheet_name="OCUPAÇÃO"),
        'nr': pd.read_excel(xls, sheet_name="NÃO_REGÊNCIA"),
        'inst': pd.read_excel(xls, sheet_name="INSTRUTORES"),
        'disc': pd.read_excel(xls, sheet_name="DISCIPLINAS", skiprows=1),
        'amb': pd.read_excel(xls, sheet_name="AMBIENTES"),
        'faltas': pd.read_excel(xls, sheet_name="FALTAS"),
        'param': pd.read_excel(xls, sheet_name="PARÂMETROS", skiprows=9)
    }

@st.cache_data
def compilar_historico(arquivos):
    """Lê um resumo de todos os arquivos salvos para criar a linha do tempo"""
    dados_linha_tempo = []
    for arq in arquivos:
        mes = arq.replace(".xlsx", "")
        caminho = os.path.join(PASTA_HISTORICO, arq)
        try:
            # Lendo apenas as abas essenciais para ser rápido
            df_nr = pd.read_excel(caminho, sheet_name="NÃO_REGÊNCIA")
            df_oc = pd.read_excel(caminho, sheet_name="OCUPAÇÃO")
            
            total_nr = df_nr['HORAS_NAO_REGENCIA'].sum() if not df_nr.empty else 0
            ocupacao_media = df_oc['PERCENTUAL_OCUPACAO'].mean() * 100 if not df_oc.empty else 0
            
            dados_linha_tempo.append({
                "Mês": mes,
                "Horas Não Regência": total_nr,
                "Ocupação Média (%)": ocupacao_media
            })
        except:
            pass
    return pd.DataFrame(dados_linha_tempo)

# ==========================================
# 5. MENU LATERAL: NAVEGAÇÃO
# ==========================================
st.sidebar.divider()
st.sidebar.title("🧭 Navegação")

# Nova seleção de qual mês o usuário quer detalhar
mes_analise = st.sidebar.selectbox("📅 Selecionar Mês para Detalhamento:", [f.replace(".xlsx", "") for f in arquivos_salvos])
caminho_selecionado = os.path.join(PASTA_HISTORICO, f"{mes_analise}.xlsx")
dados = load_data(caminho_selecionado)

pagina_selecionada = st.sidebar.radio(
    "Escolha o Painel:",
    ["🌐 Visão 360º (Mês Atual)", "👥 Análise de Docentes (RH)", "🏢 Ocupação e Ambientes", "📈 Evolução Histórica"]
)

st.sidebar.divider()
lista_turnos = ["Todos"] + list(dados['turmas']['TURNO'].dropna().unique())
turno_selecionado = st.sidebar.selectbox("Filtro de Turno (Páginas de Detalhe):", lista_turnos)

# ==========================================
# 6. ROTEAMENTO DAS PÁGINAS
# ==========================================

# ------------------------------------------
# NOVA PÁGINA 4: EVOLUÇÃO HISTÓRICA
# ------------------------------------------
if pagina_selecionada == "📈 Evolução Histórica":
    st.title("📈 Evolução e Tendências (Comparativo Mensal)")
    st.markdown("Esta página consolida os dados de todos os meses arquivados no sistema para análise de tendências.")
    
    df_historico = compilar_historico(arquivos_salvos)
    
    if len(df_historico) > 1:
        col1, col2 = st.columns(2)
        
        with col1:
            fig_hist_oc = px.line(df_historico, x="Mês", y="Ocupação Média (%)", markers=True, 
                                  title="Evolução da Ocupação Média dos Ambientes",
                                  line_shape="spline", color_discrete_sequence=['#1f77b4'])
            fig_hist_oc.update_yaxes(range=[0, 100])
            st.plotly_chart(fig_hist_oc, use_container_width=True)
            
        with col2:
            fig_hist_nr = px.bar(df_historico, x="Mês", y="Horas Não Regência", text_auto=True,
                                 title="Volume de Horas de Não Regência por Mês",
                                 color="Horas Não Regência", color_continuous_scale="Reds")
            st.plotly_chart(fig_hist_nr, use_container_width=True)
            
        st.dataframe(df_historico, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Você precisa de pelo menos 2 meses arquivados no sistema para gerar gráficos de evolução.")

# ------------------------------------------
# PÁGINAS 1 a 3 (Adaptadas para ler o dicionário 'dados')
# ------------------------------------------
else:
    # Aplicando o filtro de turno
    if turno_selecionado != "Todos":
        df_turmas_f = dados['turmas'][dados['turmas']['TURNO'] == turno_selecionado]
        df_ocupacao_f = dados['ocupacao'][dados['ocupacao']['TURNO'] == turno_selecionado] if 'TURNO' in dados['ocupacao'].columns else dados['ocupacao']
    else:
        df_turmas_f = dados['turmas'].copy()
        df_ocupacao_f = dados['ocupacao'].copy()

    if pagina_selecionada == "🌐 Visão 360º (Mês Atual)":
        st.title(f"🌐 Visão Institucional - {mes_analise}")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        col1.metric("Turmas Abertas", len(df_turmas_f))
        col2.metric("Alunos", df_turmas_f['VAGAS_OCUPADAS'].sum() if not df_turmas_f.empty else 0)
        col3.metric("Salas Físicas", len(dados['amb'][dados['amb']['VIRTUAL'] == 'NÃO']))
        col4.metric("Instrutores", len(dados['inst']))
        col5.metric("Faltas Registadas", len(dados['faltas']))
        
        st.divider()
        st.markdown("#### Status de Execução das Disciplinas")
        status_disc = dados['disc']['STATUS'].value_counts().reset_index()
        status_disc.columns = ['Status', 'Quantidade']
        st.plotly_chart(px.pie(status_disc, names='Status', values='Quantidade', hole=0.4), use_container_width=True)

    elif pagina_selecionada == "👥 Análise de Docentes (RH)":
        st.title(f"👥 Docentes e Não Regência - {mes_analise}")
        df_nr_det = pd.merge(dados['nr'], dados['inst'][['ID', 'NOME_COMPLETO']], left_on='ID_INSTRUTOR', right_on='ID', how='left')
        
        if not df_nr_det.empty:
            df_horas_inst = df_nr_det.groupby('NOME_COMPLETO')['HORAS_NAO_REGENCIA'].sum().reset_index().sort_values('HORAS_NAO_REGENCIA')
            st.plotly_chart(px.bar(df_horas_inst, x='HORAS_NAO_REGENCIA', y='NOME_COMPLETO', orientation='h', title="Ranking de Horas Não Regência"), use_container_width=True)
            st.dataframe(df_nr_det[['DATA', 'NOME_COMPLETO', 'TIPO_ATIVIDADE', 'HORAS_NAO_REGENCIA']], use_container_width=True, hide_index=True)
        else:
            st.info("Sem dados de Não Regência para este mês.")

    elif pagina_selecionada == "🏢 Ocupação e Ambientes":
        st.title(f"🏢 Uso de Laboratórios e Salas - {mes_analise}")
        if not df_ocupacao_f.empty:
            df_amb_uso = df_ocupacao_f.groupby('AMBIENTE')['PERCENTUAL_OCUPACAO'].mean().reset_index()
            df_amb_uso['PERCENTUAL_OCUPACAO'] *= 100
            st.plotly_chart(px.bar(df_amb_uso.sort_values('PERCENTUAL_OCUPACAO'), x='PERCENTUAL_OCUPACAO', y='AMBIENTE', orientation='h', title="Ocupação Média (%)"), use_container_width=True)
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuração da Página
st.set_page_config(
    page_title="Dashboard DIGITECH 2026",
    page_icon="📊",
    layout="wide"
)

# Título
st.title("📊 Dashboard de Gestão - DIGITECH 2026")
st.markdown("---")

# Carregar Dados (URL do Google Sheets ou arquivo no repo)
@st.cache_data
def carregar_dados():
    # Para produção, upload dos Excel no GitHub ou use Google Sheets
    try:
        # Exemplo com URLs públicas (substitua pelos seus links)
        df_instrutores = pd.read_excel("https://raw.githubusercontent.com/JonathanFariasTech/dashboard-digitech-2026/main/dados/INSTRUTORES.xlsx")
        df_turmas = pd.read_excel("https://raw.githubusercontent.com/JonathanFariasTech/dashboard-digitech-2026/main/dados/TURMAS.xlsx")
        df_ocupacao = pd.read_excel("https://raw.githubusercontent.com/JonathanFariasTech/dashboard-digitech-2026/main/dados/OCUPACAO.xlsx")
        df_nao_regencia = pd.read_excel("https://raw.githubusercontent.com/JonathanFariasTech/dashboard-digitech-2026/main/dados/NAO_REGENCIA.xlsx")
        df_calendario = pd.read_excel("https://raw.githubusercontent.com/JonathanFariasTech/dashboard-digitech-2026/main/dados/CALENDARIO.xlsx")
        return df_instrutores, df_turmas, df_ocupacao, df_nao_regencia, df_calendario
    except:
        # Dados de exemplo para demonstração
        return None, None, None, None, None

# Sidebar - Filtros
st.sidebar.header("🔍 Filtros")
filtro_turno = st.sidebar.multiselect("Turno:", ["MANHÃ", "TARDE", "NOITE"], default=["MANHÃ", "TARDE", "NOITE"])
filtro_modalidade = st.sidebar.multiselect("Modalidade:", ["PRESENCIAL", "EAD"], default=["PRESENCIAL", "EAD"])

# Carregar dados
df_instrutores, df_turmas, df_ocupacao, df_nao_regencia, df_calendario = carregar_dados()

# KPIs Principais
st.subheader("📈 Indicadores Principais")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Instrutores", "13" if df_instrutores is None else len(df_instrutores))
with col2:
    st.metric("Turmas Ativas", "3" if df_turmas is None else len(df_turmas[df_turmas['STATUS'] == 'Em andamento']))
with col3:
    st.metric("Ocupação Média", "78%" if df_ocupacao is None else f"{df_ocupacao['PERCENTUAL_OCUPACAO'].mean():.1f}%")
with col4:
    st.metric("Horas Não Regência", "210" if df_nao_regencia is None else df_nao_regencia['HORAS_NAO_REGENCIA'].sum())

st.markdown("---")

# Gráfico 1: Ocupação por Ambiente
st.subheader("🏢 Ocupação por Ambiente")
if df_ocupacao is not None:
    df_ocupacao_limpo = df_ocupacao.dropna(subset=['PERCENTUAL_OCUPACAO'])
    fig_ocupacao = px.bar(
        df_ocupacao_limpo.groupby('AMBIENTE')['PERCENTUAL_OCUPACAO'].mean().reset_index(),
        x='AMBIENTE',
        y='PERCENTUAL_OCUPACAO',
        color='PERCENTUAL_OCUPACAO',
        color_continuous_scale='RdYlGn',
        title='Percentual de Ocupação por Ambiente'
    )
    fig_ocupacao.add_hline(y=70, line_dash="dash", line_color="orange", annotation_text="Meta Mínima (70%)")
    fig_ocupacao.add_hline(y=85, line_dash="dash", line_color="green", annotation_text="Meta Ideal (85%)")
    st.plotly_chart(fig_ocupacao, use_container_width=True)
else:
    st.info("📁 Upload dos dados necessário para visualizar gráficos")

# Gráfico 2: Instrutores por Status
st.subheader("👥 Distribuição de Instrutores")
if df_instrutores is not None:
    fig_instrutores = px.pie(
        df_instrutores,
        names='STATUS',
        title='Status dos Instrutores',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    st.plotly_chart(fig_instrutores, use_container_width=True)
else:
    # Dados de exemplo
    dados_exemplo = pd.DataFrame({'STATUS': ['ATIVO', 'ATIVO', 'ATIVO'], 'Count': [11, 2, 0]})
    fig_instrutores = px.pie(dados_exemplo, values='Count', names='STATUS', title='Status dos Instrutores (Exemplo)')
    st.plotly_chart(fig_instrutores, use_container_width=True)

# Gráfico 3: Horas de Não Regência por Tipo
st.subheader("⏱️ Horas de Não Regência por Atividade")
if df_nao_regencia is not None:
    fig_nao_regencia = px.bar(
        df_nao_regencia.groupby('TIPO_ATIVIDADE')['HORAS_NAO_REGENCIA'].sum().reset_index(),
        x='TIPO_ATIVIDADE',
        y='HORAS_NAO_REGENCIA',
        color='HORAS_NAO_REGENCIA',
        title='Distribuição de Horas por Tipo de Atividade'
    )
    st.plotly_chart(fig_nao_regencia, use_container_width=True)
else:
    st.info("📁 Dados de não regência não carregados")

# Gráfico 4: Ocupação por Turno
st.subheader("📅 Ocupação por Turno vs Metas")
if df_ocupacao is not None:
    ocupacao_turno = df_ocupacao.dropna(subset=['PERCENTUAL_OCUPACAO']).groupby('TURNO')['PERCENTUAL_OCUPACAO'].mean().reset_index()
    fig_turno = go.Figure()
    fig_turno.add_trace(go.Bar(x=ocupacao_turno['TURNO'], y=ocupacao_turno['PERCENTUAL_OCUPACAO'], name='Ocupação Real'))
    fig_turno.add_hline(y=70, line_dash="dash", line_color="orange", annotation_text="Meta Mínima (70%)")
    fig_turno.add_hline(y=85, line_dash="dash", line_color="green", annotation_text="Meta Ideal (85%)")
    fig_turno.update_layout(height=400, title='Ocupação por Turno')
    st.plotly_chart(fig_turno, use_container_width=True)
else:
    st.info("📁 Dados de ocupação não carregados")

# Tabela de Turmas
st.subheader("🎓 Turmas Ativas")
if df_turmas is not None:
    st.dataframe(
        df_turmas[['CODIGO_TURMA', 'NOME_TURMA', 'TURNO', 'MODALIDADE', 'VAGAS_OCUPADAS', 'VAGAS_TOTAL', 'STATUS']],
        use_container_width=True
    )
else:
    st.info("📁 Dados de turmas não carregados")

# Rodapé
st.markdown("---")
st.caption(f"Dashboard gerado automaticamente | Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
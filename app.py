import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# Configuração da Página
st.set_page_config(
    page_title="Dashboard DIGITECH 2026",
    page_icon="📊",
    layout="wide"
)

# Título
st.title("📊 Dashboard de Gestão - DIGITECH 2026")
st.markdown("---")

# 🔍 SIDEBAR COM FILTROS
st.sidebar.header("🔍 Filtros")
filtro_turno = st.sidebar.multiselect(
    "Turno:", 
    ["MANHÃ", "TARDE", "NOITE"], 
    default=["MANHÃ", "TARDE", "NOITE"]
)
filtro_modalidade = st.sidebar.multiselect(
    "Modalidade:", 
    ["PRESENCIAL", "EAD"], 
    default=["PRESENCIAL", "EAD"]
)

# 📈 KPIs PRINCIPAIS (Dados da planilha)
st.subheader("📈 Indicadores Principais")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Instrutores", "13")
with col2:
    st.metric("Turmas Ativas", "3")
with col3:
    st.metric("Ocupação Média", "78%")
with col4:
    st.metric("Horas Não Regência", "210")

st.markdown("---")

# 📊 GRÁFICO 1: Ocupação por Ambiente
st.subheader("🏢 Ocupação por Ambiente")

# Dados de exemplo baseados na sua planilha
dados_ocupacao = pd.DataFrame({
    'AMBIENTE': ['LABORATÓRIO DE SOFTWARE 04', 'LABORATÓRIO DE SOFTWARE 08', 'CYBER ARENA', 'ESPAÇO IA'],
    'PERCENTUAL_OCUPACAO': [91.67, 62.50, 75.00, 45.00],
    'STATUS': ['ALTA', 'MÉDIO', 'MÉDIO', 'BAIXA']
})

fig_ocupacao = px.bar(
    dados_ocupacao,
    x='AMBIENTE',
    y='PERCENTUAL_OCUPACAO',
    color='PERCENTUAL_OCUPACAO',
    color_continuous_scale='RdYlGn',
    title='Percentual de Ocupação por Ambiente'
)
fig_ocupacao.add_hline(y=70, line_dash="dash", line_color="orange", annotation_text="Meta Mínima (70%)")
fig_ocupacao.add_hline(y=85, line_dash="dash", line_color="green", annotation_text="Meta Ideal (85%)")
fig_ocupacao.update_layout(height=400, xaxis_tickangle=-45)
st.plotly_chart(fig_ocupacao, use_container_width=True)

# 📊 GRÁFICO 2: Instrutores por Status
st.subheader("👥 Distribuição de Instrutores")

dados_instrutores = pd.DataFrame({
    'STATUS': ['ATIVO', 'EM FÉRIAS', 'CEDIDO'],
    'QUANTIDADE': [11, 2, 1]
})

fig_instrutores = px.pie(
    dados_instrutores,
    values='QUANTIDADE',
    names='STATUS',
    title='Status dos Instrutores',
    color_discrete_sequence=px.colors.qualitative.Set2
)
st.plotly_chart(fig_instrutores, use_container_width=True)

# 📊 GRÁFICO 3: Horas de Não Regência por Tipo
st.subheader("⏱️ Horas de Não Regência por Atividade")

dados_nao_regencia = pd.DataFrame({
    'TIPO_ATIVIDADE': ['Reunião Pedagógica', 'Capacitação', 'Planejamento', 'Correção', 'Outros'],
    'HORAS': [45, 60, 35, 40, 30]
})

fig_nao_regencia = px.bar(
    dados_nao_regencia,
    x='TIPO_ATIVIDADE',
    y='HORAS',
    color='HORAS',
    title='Distribuição de Horas por Tipo de Atividade'
)
st.plotly_chart(fig_nao_regencia, use_container_width=True)

# 📊 GRÁFICO 4: Ocupação por Turno
st.subheader("📅 Ocupação por Turno vs Metas")

dados_turno = pd.DataFrame({
    'TURNO': ['MANHÃ', 'TARDE', 'NOITE'],
    'OCUPACAO': [78.27, 0, 0]  # Baseado no seu RESUMO
})

fig_turno = go.Figure()
fig_turno.add_trace(go.Bar(
    x=dados_turno['TURNO'],
    y=dados_turno['OCUPACAO'],
    name='Ocupação Real',
    marker_color='steelblue'
))
fig_turno.add_hline(y=70, line_dash="dash", line_color="orange", annotation_text="Meta Mínima (70%)")
fig_turno.add_hline(y=85, line_dash="dash", line_color="green", annotation_text="Meta Ideal (85%)")
fig_turno.update_layout(height=400, title='Ocupação por Turno', yaxis_range=[0, 100])
st.plotly_chart(fig_turno, use_container_width=True)

# 📋 TABELA DE TURMAS
st.subheader("🎓 Turmas Ativas")

dados_turmas = pd.DataFrame({
    'CÓDIGO': ['QUA20502026U001', 'QUA04382026U003', 'APR01302026U006'],
    'NOME': ['Qualificação Básica em IA', 'Programador Full Stack', 'Desenvolvedor de Soluções TI'],
    'TURNO': ['EAD', 'MANHÃ', 'MANHÃ'],
    'MODALIDADE': ['EAD', 'PRESENCIAL', 'PRESENCIAL'],
    'VAGAS': ['364/500', '22/22', '15/15'],
    'STATUS': ['Em andamento', 'Em andamento', 'Em andamento']
})

st.dataframe(dados_turmas, use_container_width=True)

# 💾 EXPORTAÇÃO DE DADOS
st.sidebar.subheader("💾 Exportar Dados")
if st.sidebar.button("📥 Baixar Relatório em CSV"):
    csv = dados_ocupacao.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="Download CSV",
        data=csv,
        file_name='relatorio_ocupacao.csv',
        mime='text/csv'
    )

# Rodapé
st.markdown("---")
st.caption(f"Dashboard gerado automaticamente | Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
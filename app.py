import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração da Página
st.set_page_config(page_title="Dashboard de Desempenho Institucional", layout="wide")
st.title("📊 Painel de Desempenho - Digitech 2026")

# 2. Carregamento e Tratamento dos Dados
# Dica: O st.cache_data ajuda a não recarregar os dados toda vez que a tela for atualizada
@st.cache_data
def load_data():
    # Observação: Ajuste o caminho dos arquivos conforme a sua pasta no Streamlit Cloud
    # Alguns arquivos tinham cabeçalhos deslocados, usamos skiprows onde necessário
    df_turmas = pd.read_csv("Consolidado - Status 2026.xlsx - TURMAS.csv")
    df_ocupacao = pd.read_csv("Consolidado - Status 2026.xlsx - OCUPAÇÃO.csv")
    df_nao_regencia = pd.read_csv("Consolidado - Status 2026.xlsx - NÃO_REGÊNCIA.csv")
    df_instrutores = pd.read_csv("Consolidado - Status 2026.xlsx - INSTRUTORES.csv")
    df_parametros = pd.read_csv("Consolidado - Status 2026.xlsx - PARÂMETROS.csv", skiprows=9)
    
    return df_turmas, df_ocupacao, df_nao_regencia, df_instrutores, df_parametros

try:
    df_turmas, df_ocupacao, df_nao_regencia, df_instrutores, df_parametros = load_data()
except FileNotFoundError:
    st.error("Arquivos CSV não encontrados. Verifique se os nomes e o diretório estão corretos.")
    st.stop()

# 3. Cálculo de Métricas (KPIs)
turmas_ativas = df_turmas[df_turmas['STATUS'] == 'Em andamento'].shape[0]
vagas_totais = df_turmas['VAGAS_TOTAL'].sum()
vagas_ocupadas = df_turmas['VAGAS_OCUPADAS'].sum()
taxa_preenchimento = (vagas_ocupadas / vagas_totais) * 100 if vagas_totais > 0 else 0

ocupacao_media = df_ocupacao['PERCENTUAL_OCUPACAO'].mean() * 100
meta_ocupacao_ideal = df_parametros[df_parametros['PARÂMETRO'] == 'Meta Ocupação Ideal']['VALOR'].values[0] * 100

total_instrutores_ativos = df_instrutores[df_instrutores['STATUS'] == 'ATIVO'].shape[0]

# 4. Exibição dos KPIs Superiores
st.markdown("### 🎯 Indicadores Chave de Desempenho (KPIs)")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Turmas em Andamento", turmas_ativas)
with col2:
    st.metric("Taxa de Preenchimento (Vagas)", f"{taxa_preenchimento:.1f}%", f"{vagas_ocupadas} alunos")
with col3:
    # Mostra a ocupação e compara com a meta (verde se positivo, vermelho se negativo)
    st.metric("Ocupação Média Física", f"{ocupacao_media:.1f}%", f"Meta: {meta_ocupacao_ideal}%")
with col4:
    st.metric("Instrutores Ativos", total_instrutores_ativos)

st.divider()

# 5. Gráficos de Desempenho
colA, colB = st.columns(2)

with colA:
    st.markdown("#### Ocupação de Vagas por Turma")
    # Gráfico de barras comparando vagas totais e ocupadas
    df_turmas_melt = df_turmas.melt(id_vars=['NOME_TURMA'], value_vars=['VAGAS_TOTAL', 'VAGAS_OCUPADAS'], 
                                    var_name='Tipo', value_name='Quantidade')
    fig_vagas = px.bar(df_turmas_melt, x='NOME_TURMA', y='Quantidade', color='Tipo', barmode='group',
                       labels={'NOME_TURMA': 'Turma', 'Quantidade': 'Nº de Vagas'},
                       color_discrete_sequence=['#1f77b4', '#ff7f0e'])
    fig_vagas.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_vagas, use_container_width=True)

with colB:
    st.markdown("#### Ocupação Média por Ambiente")
    # Agrupando por ambiente para ver quais salas são mais usadas
    df_amb_ocup = df_ocupacao.groupby('AMBIENTE')['PERCENTUAL_OCUPACAO'].mean().reset_index()
    df_amb_ocup['PERCENTUAL_OCUPACAO'] *= 100
    fig_ambientes = px.bar(df_amb_ocup, x='AMBIENTE', y='PERCENTUAL_OCUPACAO', 
                           labels={'AMBIENTE': 'Ambiente', 'PERCENTUAL_OCUPACAO': 'Ocupação Média (%)'},
                           color='PERCENTUAL_OCUPACAO', color_continuous_scale='Blues')
    # Linha de meta
    fig_ambientes.add_hline(y=meta_ocupacao_ideal, line_dash="dot", line_color="red", annotation_text="Meta Ideal")
    st.plotly_chart(fig_ambientes, use_container_width=True)

st.divider()

# 6. Desempenho e Alocação de Instrutores
colC, colD = st.columns(2)

with colC:
    st.markdown("#### Distribuição de Atividades: Não Regência")
    # Gráfico de pizza mostrando onde os professores gastam tempo fora de sala
    df_nr_agrupado = df_nao_regencia.groupby('TIPO_ATIVIDADE')['HORAS_NAO_REGENCIA'].sum().reset_index()
    fig_nr = px.pie(df_nr_agrupado, values='HORAS_NAO_REGENCIA', names='TIPO_ATIVIDADE', hole=0.4)
    st.plotly_chart(fig_nr, use_container_width=True)

with colD:
    st.markdown("#### Status dos Instrutores")
    # Entender gargalos de RH (Ativos vs Férias/World Skills)
    status_counts = df_instrutores['OBSERVAÇÃO'].fillna('SEM OBSERVAÇÃO').value_counts().reset_index()
    status_counts.columns = ['Status/Observação', 'Quantidade']
    fig_status = px.bar(status_counts, y='Status/Observação', x='Quantidade', orientation='h',
                        color='Status/Observação')
    st.plotly_chart(fig_status, use_container_width=True)
import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração da Página
st.set_page_config(page_title="Dashboard 360º - Digitech 2026", layout="wide")
st.title("📊 Painel de Desempenho 360º - Digitech 2026")

# 2. Carregamento de TODAS as abas
@st.cache_data
def load_data():
    arquivo_excel = "Consolidado - Status 2026.xlsx"
    xls = pd.ExcelFile(arquivo_excel)
    
    # Lendo todas as abas estratégicas
    df_turmas = pd.read_excel(xls, sheet_name="TURMAS")
    df_ocupacao = pd.read_excel(xls, sheet_name="OCUPAÇÃO")
    df_nao_regencia = pd.read_excel(xls, sheet_name="NÃO_REGÊNCIA")
    df_instrutores = pd.read_excel(xls, sheet_name="INSTRUTORES")
    df_disciplinas = pd.read_excel(xls, sheet_name="DISCIPLINAS", skiprows=1) # Tratando cabeçalho
    df_ambientes = pd.read_excel(xls, sheet_name="AMBIENTES")
    df_faltas = pd.read_excel(xls, sheet_name="FALTAS")
    df_param = pd.read_excel(xls, sheet_name="PARÂMETROS", skiprows=9)
    
    return df_turmas, df_ocupacao, df_nao_regencia, df_instrutores, df_disciplinas, df_ambientes, df_faltas, df_param

try:
    df_turmas, df_ocupacao, df_nr, df_inst, df_disc, df_amb, df_faltas, df_param = load_data()
except Exception as e:
    st.error(f"Erro ao carregar o arquivo: {e}")
    st.stop()

# ==========================================
# SEÇÃO 1: MÉTRICAS GERAIS (LENDO TUDO)
# ==========================================
st.markdown("### 🌐 Visão Institucional Completa")

# Cálculos de todas as abas
total_turmas = len(df_turmas)
total_alunos_ativos = df_turmas['VAGAS_OCUPADAS'].sum()
total_amb_fisicos = len(df_amb[df_amb['VIRTUAL'] == 'NÃO'])
total_instrutores = len(df_inst)
total_disciplinas = len(df_disc)
horas_nao_regencia_total = df_nr['HORAS_NAO_REGENCIA'].sum()
registros_faltas = len(df_faltas)

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Turmas Abertas", total_turmas)
col2.metric("Alunos Ocupando Vagas", total_alunos_ativos)
col3.metric("Salas Físicas (Ambientes)", total_amb_fisicos)
col4.metric("Corpo Docente", total_instrutores)
col5.metric("Total de Disciplinas", total_disciplinas)
col6.metric("Faltas Registradas", registros_faltas)

st.divider()

# ==========================================
# SEÇÃO 2: RH DOCENTE E OCUPAÇÃO
# ==========================================
colA, colB = st.columns(2)

with colA:
    st.markdown("#### 👤 Instrutores Fora de Regência (Afastamentos)")
    
    # Filtra apenas os professores que TEM observação (Remove os vazios)
    df_inst_afastados = df_inst.dropna(subset=['OBSERVAÇÃO']).copy()
    
    # Função para encurtar o nome e não quebrar o gráfico (Ex: "Raphael Barreto de Oliveira" -> "Raphael Oliveira")
    def encurtar_nome(nome):
        partes = str(nome).split()
        if len(partes) > 1:
            return f"{partes[0]} {partes[-1]}"
        return nome
        
    df_inst_afastados['Nome Curto'] = df_inst_afastados['NOME_COMPLETO'].apply(encurtar_nome)
    
    if not df_inst_afastados.empty:
        # Gráfico focado nas observações
        fig_inst = px.bar(
            df_inst_afastados, 
            x="OBSERVAÇÃO", 
            y="Nome Curto", 
            color="OBSERVAÇÃO",
            orientation='h',
            labels={'Nome Curto': 'Instrutor', 'OBSERVAÇÃO': 'Motivo'}
        )
        # Ajustando altura para caber todo mundo sem esmagar
        fig_inst.update_layout(height=450, showlegend=False)
        st.plotly_chart(fig_inst, use_container_width=True)
    else:
        st.success("Excelente! Todos os instrutores estão sem observações de afastamento no momento.")

with colB:
    st.markdown("#### 📊 Ocupação de Vagas nas Turmas")
    # Encurtando o nome da turma para o gráfico ficar legível
    df_turmas['Turma Curta'] = df_turmas['NOME_TURMA'].apply(lambda x: x[:25] + "..." if len(str(x)) > 25 else x)
    
    df_t_melt = df_turmas.melt(id_vars=['Turma Curta'], value_vars=['VAGAS_TOTAL', 'VAGAS_OCUPADAS'], 
                               var_name='Tipo', value_name='Quantidade')
    
    fig_vagas = px.bar(df_t_melt, x='Turma Curta', y='Quantidade', color='Tipo', barmode='group',
                       color_discrete_sequence=['#1f77b4', '#ff7f0e'])
    
    fig_vagas.update_layout(height=450, xaxis_title="", yaxis_title="Vagas")
    st.plotly_chart(fig_vagas, use_container_width=True)

st.divider()

# ==========================================
# SEÇÃO 3: PRODUTIVIDADE E AMBIENTES
# ==========================================
colC, colD = st.columns(2)

with colC:
    st.markdown("#### 📚 Status Geral das Disciplinas")
    status_disc = df_disc['STATUS'].value_counts().reset_index()
    status_disc.columns = ['Status', 'Quantidade']
    
    fig_disc = px.pie(status_disc, names='Status', values='Quantidade', hole=0.4, 
                      color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_disc.update_layout(height=400)
    st.plotly_chart(fig_disc, use_container_width=True)

with colD:
    st.markdown("#### 🏢 Eficiência no Uso de Salas")
    df_amb_uso = df_ocupacao.groupby('AMBIENTE')['PERCENTUAL_OCUPACAO'].mean().reset_index()
    df_amb_uso['PERCENTUAL_OCUPACAO'] *= 100
    df_amb_uso = df_amb_uso.sort_values('PERCENTUAL_OCUPACAO', ascending=True) # Ordena do menor pro maior uso
    
    fig_amb = px.bar(df_amb_uso, x='PERCENTUAL_OCUPACAO', y='AMBIENTE', orientation='h', 
                     color='PERCENTUAL_OCUPACAO', color_continuous_scale='Blues',
                     labels={'PERCENTUAL_OCUPACAO': 'Ocupação Média (%)', 'AMBIENTE': ''})
                     
    # Pegando a meta da aba de parâmetros
    meta_ideal = df_param[df_param['PARÂMETRO'] == 'Meta Ocupação Ideal']['VALOR'].values[0] * 100
    fig_amb.add_vline(x=meta_ideal, line_dash="dot", line_color="red", annotation_text="Meta Ideal")
    
    fig_amb.update_layout(height=400)
    st.plotly_chart(fig_amb, use_container_width=True)
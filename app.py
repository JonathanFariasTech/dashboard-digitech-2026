import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==========================================
# 1. CONFIGURAÇÃO E INICIALIZAÇÃO
# ==========================================
st.set_page_config(page_title="Dashboard Digitech", layout="wide", page_icon="📊")

PASTA_HISTORICO = "historico_dados"
os.makedirs(PASTA_HISTORICO, exist_ok=True)

MESES_PT = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 
            7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}

ABAS_OBRIGATORIAS = [
    "TURMAS", "OCUPAÇÃO", "NÃO_REGÊNCIA", "INSTRUTORES", 
    "DISCIPLINAS", "AMBIENTES", "FALTAS", "PARÂMETROS"
]

# Inicializa o controlo de sessão para o Login
if 'admin_logado' not in st.session_state:
    st.session_state['admin_logado'] = False

# ==========================================
# 2. FUNÇÕES DE VALIDAÇÃO
# ==========================================
def validar_planilha(file):
    try:
        xls = pd.ExcelFile(file)
        abas_arquivo = xls.sheet_names
        abas_faltantes = [aba for aba in ABAS_OBRIGATORIAS if aba not in abas_arquivo]
        if abas_faltantes:
            return False, f"Planilha fora do padrão! Faltam as seguintes abas: {', '.join(abas_faltantes)}"
        return True, "Planilha validada com sucesso."
    except Exception as e:
        return False, f"Erro ao ler o ficheiro. Certifique-se de que é um Excel válido. Detalhe: {e}"

def extrair_mes_automatico(file):
    try:
        df_temp = pd.read_excel(file, sheet_name="OCUPAÇÃO", usecols=["DATA"])
        datas = pd.to_datetime(df_temp["DATA"], errors="coerce").dropna()
        if not datas.empty:
            data_predominante = datas.mode()[0]
            mes_num = data_predominante.month
            ano = data_predominante.year
            return f"{mes_num:02d} - {MESES_PT[mes_num]} {ano}"
    except Exception:
        return None
    return None

# ==========================================
# 3. BARRA LATERAL: LOGIN COM FORMULÁRIO
# ==========================================
st.sidebar.title("🔐 Acesso Administrativo")

# Lógica de Login com st.form (Permite submeter com a tecla ENTER)
if not st.session_state['admin_logado']:
    with st.sidebar.form("form_login"):
        st.markdown("🔒 **Faça login para gerir os dados**")
        senha = st.text_input("Palavra-passe:", type="password")
        
        # O botão de submissão do formulário
        btn_entrar = st.form_submit_button("Entrar 🚀", use_container_width=True)
        
        if btn_entrar:
            if senha == "admin123": # <-- COLOQUE A SUA SENHA AQUI
                st.session_state['admin_logado'] = True
                st.rerun() # Recarrega a página instantaneamente
            else:
                st.error("❌ Palavra-passe incorreta!")
else:
    st.sidebar.success("✅ Logado como Administrador")
    if st.sidebar.button("Sair (Logout)", use_container_width=True):
        st.session_state['admin_logado'] = False
        st.rerun()

st.sidebar.divider()

# Listagem dos ficheiros já existentes
arquivos_salvos = sorted([f for f in os.listdir(PASTA_HISTORICO) if f.endswith('.xlsx')])

# ==========================================
# 3.1. FERRAMENTAS DO ADMIN (SÓ SE ESTIVER LOGADO)
# ==========================================
if st.session_state['admin_logado']:
    st.sidebar.title("🛠️ Ferramentas Admin")
    
    with st.sidebar.expander("➕ Adicionar / Atualizar Mês", expanded=False):
        arquivo_carregado = st.file_uploader("Upload de Planilha (.xlsx)", type=["xlsx"])
        
        if arquivo_carregado:
            valida, mensagem = validar_planilha(arquivo_carregado)
            if not valida:
                st.error("❌ " + mensagem)
            else:
                nome_mes_auto = extrair_mes_automatico(arquivo_carregado)
                if nome_mes_auto:
                    caminho_arquivo = os.path.join(PASTA_HISTORICO, f"{nome_mes_auto}.xlsx")
                    if os.path.exists(caminho_arquivo):
                        st.warning(f"⚠️ Atualizar dados de **{nome_mes_auto}**?")
                        texto_botao = "🔄 Sobrescrever Histórico"
                    else:
                        st.success(f"✅ Salvar novo mês: **{nome_mes_auto}**?")
                        texto_botao = "💾 Salvar Novo Mês"
                        
                    if st.button(texto_botao, use_container_width=True):
                        arquivo_carregado.seek(0)
                        with open(caminho_arquivo, "wb") as f:
                            f.write(arquivo_carregado.getbuffer())
                        st.cache_data.clear()
                        st.toast(f"Mês {nome_mes_auto} guardado!", icon="✅")
                        st.rerun()
                else:
                    st.error("Não foi possível detetar o mês automaticamente.")
                    
    if arquivos_salvos:
        with st.sidebar.expander("🗑️ Remover Mês do Sistema", expanded=False):
            st.warning("Atenção: Esta ação não pode ser desfeita.")
            mes_remover = st.selectbox("Selecione o mês para excluir:", [f.replace(".xlsx", "") for f in arquivos_salvos])
            if st.button("🚨 Confirmar Exclusão", use_container_width=True):
                caminho_remover = os.path.join(PASTA_HISTORICO, f"{mes_remover}.xlsx")
                if os.path.exists(caminho_remover):
                    os.remove(caminho_remover)
                    st.cache_data.clear()
                    st.toast("Mês removido com sucesso!", icon="🗑️")
                    st.rerun()

    st.sidebar.divider()

# ==========================================
# 4. VERIFICAÇÃO DE HISTÓRICO EXISTENTE
# ==========================================
if not arquivos_salvos:
    st.title("📊 Painel de Desempenho 360º - Digitech")
    if st.session_state['admin_logado']:
        st.info("👈 **O sistema está vazio!** Utilize o painel lateral 'Adicionar Mês' para carregar a primeira planilha.")
    else:
        st.warning("Nenhum dado disponível. Aguarde o Administrador fazer o upload da planilha atual.")
    st.stop()

# ==========================================
# 5. CARREGAMENTO DOS DADOS (CACHE)
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
    dados_linha_tempo = []
    for arq in arquivos:
        mes = arq.replace(".xlsx", "")
        caminho = os.path.join(PASTA_HISTORICO, arq)
        try:
            df_nr = pd.read_excel(caminho, sheet_name="NÃO_REGÊNCIA")
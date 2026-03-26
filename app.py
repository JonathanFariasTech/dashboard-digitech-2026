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

# Inicializa o controle de sessão para o Login
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
        return False, f"Erro ao ler o arquivo. Certifique-se de que é um Excel válido. Detalhe: {e}"

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
# 3. BARRA LATERAL: LOGIN E ÁREA DO ADMIN
# ==========================================
st.sidebar.title("🔐 Acesso Administrativo")

# Lógica de Login/Logout
if not st.session_state['admin_logado']:
    senha = st.sidebar.text_input("Senha de Administrador:", type="password")
    if st.sidebar.button("Entrar"):
        if senha == "admin123": # <-- COLOQUE SUA SENHA AQUI
            st.session_state['admin_logado'] = True
            st.toast("Login realizado com sucesso!", icon="🔓")
            st.rerun()
        else:
            st.sidebar.error("Senha incorreta!")
else:
    st.sidebar.success("✅ Logado como Administrador")
    if st.sidebar.button("Sair (Logout)"):
        st.session_state['admin_logado'] = False
        st.rerun()

st.sidebar.divider()

# Listagem dos arquivos já existentes (Precisamos disso para o painel de exclusão e leitura)
arquivos_salvos = sorted([f for f in os.listdir(PASTA_HISTORICO) if f.endswith('.xlsx')])

# Renderiza as ferramentas de edição APENAS se estiver logado
if st.session_state['admin_logado']:
    st.sidebar.title("🛠️ Ferramentas Admin")
    
    # Ferramenta 1: Upload / Atualização
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
                        
                    if st.button(texto_botao):
                        arquivo_carregado.seek(0)
                        with open(caminho_arquivo, "wb") as f:
                            f.write(arquivo_carregado.getbuffer())
                        st.cache_data.clear()
                        st.rerun()
                else:
                    st.error("Não foi possível detectar o mês automaticamente.")
                    
    # Ferramenta 2: Exclusão de Meses (Nova)
    if arquivos_salvos:
        with st.sidebar.expander("🗑️ Remover Mês do Sistema", expanded=False):
            st.warning("Atenção: Esta ação não pode ser desfeita.")
            mes_remover = st.selectbox("Selecione o mês para excluir:", [f.replace(".xlsx", "") for f in arquivos_salvos])
            if st.button("🚨 Confirmar Exclusão"):
                caminho_remover = os.path.join(PASTA_HISTORICO, f"{mes_remover}.xlsx")
                if os.path.exists(caminho_remover):
                    os.remove(caminho_remover)
                    st.cache_data.clear()
                    st.rerun()

    st.sidebar.divider()

# ==========================================
# 4. VERIFICAÇÃO DE HISTÓRICO EXISTENTE
# ==========================================
# Se o cofre estiver vazio, avisa o usuário e trava a renderização do resto
if not arquivos_salvos:
    st.title("📊 Painel de Desempenho 360º - Digitech")
    if st.session_state['admin_logado']:
        st.info("👈 **O sistema está vazio!** Utilize o painel lateral 'Adicionar Mês' para carregar a primeira planilha.")
    else:
        st.warning("Nenhum dado disponível. Aguarde o Administrador
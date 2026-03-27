import streamlit as st
import pandas as pd
import plotly.express as px
import os
from github import Github # <-- NOVA BIBLIOTECA AQUI

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

if 'admin_logado' not in st.session_state:
    st.session_state['admin_logado'] = False

# ==========================================
# 2. FUNÇÕES DE VALIDAÇÃO E GITHUB
# ==========================================
def validar_planilha(file):
    try:
        xls = pd.ExcelFile(file)
        abas_arquivo = xls.sheet_names
        abas_faltantes = [aba for aba in ABAS_OBRIGATORIAS if aba not in abas_arquivo]
        if abas_faltantes:
            return False, f"Faltam as abas: {', '.join(abas_faltantes)}"
        return True, "Planilha validada com sucesso."
    except Exception as e:
        return False, f"Erro ao ler o ficheiro: {e}"

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

# --- NOVA FUNÇÃO PARA PERSISTIR DADOS NO GITHUB ---
def salvar_no_github(caminho_arquivo_local, nome_arquivo_github, file_buffer):
    try:
        if "GITHUB_TOKEN" in st.secrets and "GITHUB_REPO" in st.secrets:
            g = Github(st.secrets["GITHUB_TOKEN"])
            repo = g.get_repo(st.secrets["GITHUB_REPO"])
            caminho_no_repo = f"{PASTA_HISTORICO}/{nome_arquivo_github}"
            mensagem_commit = f"Upload automático via Dashboard: {nome_arquivo_github}"
            
            # Tenta verificar se o ficheiro já existe para o atualizar
            try:
                contents = repo.get_contents(caminho_no_repo)
                repo.update_file(contents.path, mensagem_commit, file_buffer.getvalue(), contents.sha)
            except Exception:
                # Se não existir, cria um novo
                repo.create_file(caminho_no_repo, mensagem_commit, file_buffer.getvalue())
            return True, "Sincronizado com a Nuvem!"
        else:
            return False, "Faltam os Secrets do GitHub no Streamlit."
    except Exception as e:
        return False, f"Erro na sincronização: {e}"

# ==========================================
# 3. BARRA LATERAL: LOGIN COM FORMULÁRIO
# ==========================================
st.sidebar.title("🔐 Acesso Administrativo")

if not st.session_state['admin_logado']:
    with st.sidebar.form("form_login"):
        st.markdown("🔒 **Faça login para gerir os dados**")
        senha = st.text_input("Palavra-passe:", type="password")
        btn_entrar = st.form_submit_button("Entrar 🚀", use_container_width=True)
        
        if btn_entrar:
            if senha == "admin123": 
                st.session_state['admin_logado'] = True
                st.rerun() 
            else:
                st.error("❌ Palavra-passe incorreta!")
else:
    st.sidebar.success("✅ Logado como Administrador")
    if st.sidebar.button("Sair (Logout)", use_container_width=True):
        st.session_state['admin_logado'] = False
        st.rerun()

st.sidebar.divider()

arquivos_salvos = sorted([f for f in os.listdir(PASTA_HISTORICO) if f.endswith('.xlsx')])

# ==========================================
# 3.1. FERRAMENTAS DO ADMIN (COM INTEGRAÇÃO GITHUB)
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
                    nome_arquivo_completo = f"{nome_mes_auto}.xlsx"
                    caminho_arquivo = os.path.join(PASTA_HISTORICO, nome_arquivo_completo)
                    
                    if os.path.exists(caminho_arquivo):
                        st.warning(f"⚠️ Atualizar dados de **{nome_mes_auto}**?")
                        texto_botao = "🔄 Sobrescrever Histórico"
                    else:
                        st.success(f"✅ Salvar novo mês: **{nome_mes_auto}**?")
                        texto_botao = "💾 Salvar Novo Mês"
                        
                    if st.button(texto_botao, use_container_width=True):
                        with st.spinner("Salvando e Sincronizando com a Nuvem... ☁️"):
                            # 1. Salva localmente (para o dashboard ler na hora)
                            arquivo_carregado.seek(0)
                            with open(caminho_arquivo, "wb") as f:
                                f.write(arquivo_carregado.getbuffer())
                            
                            # 2. Envia para o GitHub (Para persistir para sempre)
                            sucesso_gh, msg_gh = salvar_no_github(caminho_arquivo, nome_arquivo_completo, arquivo_carregado)
                            
                            st.cache_data.clear()
                            
                            if sucesso_gh:
                                st.toast(f"Mês {nome_mes_auto} guardado e protegido! ✅", icon="✅")
                            else:
                                st.error(f"Salvo localmente, mas erro na nuvem: {msg_gh}")
                        st.rerun()
                else:
                    st.error("Não foi possível detetar o mês automaticamente.")
                    
    if arquivos_salvos:
        with st.sidebar.expander("🗑️ Remover Mês (Apenas Local)", expanded=False):
            st.warning("Remove apenas a visualização temporária atual.")
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
# O RESTO DO CÓDIGO PERMANECE EXATAMENTE IGUAL
# (Secções 4, 5, 6 e 7 de visualização de dados)
# ==========================================

if not arquivos_salvos:
    st.title("📊 Painel de Desempenho 360º - Digitech")
    if st.session_state['admin_logado']:
        st.info("👈 **O sistema está vazio!** Utilize o painel lateral 'Adicionar Mês' para carregar a primeira planilha.")
    else:
        st.warning("Nenhum dado disponível. Aguarde o Administrador fazer o upload da planilha atual.")
    st.stop()

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
            df_oc = pd.read_excel(caminho, sheet_name="OCUPAÇÃO")
            
            total_nr = df_nr['HORAS_NAO_REGENCIA'].sum() if not df_nr.empty else 0
            ocupacao_media = df_oc['PERCENTUAL_OCUPACAO'].mean() * 100 if not df_oc.empty else 0
            
            dados_linha_tempo.append({"Mês": mes, "Horas Não Regência": total_nr, "Ocupação Média (%)": ocupacao_media})
        except Exception:
            pass 
    return pd.DataFrame(dados_linha_tempo)

st.sidebar.title("🧭 Navegação Visual")
mes_analise = st.sidebar.selectbox("📅 Mês de Análise:", [f.replace(".xlsx", "") for f in arquivos_salvos], index=len(arquivos_salvos)-1)
caminho_selecionado = os.path.join(PASTA_HISTORICO, f"{mes_analise}.xlsx")
dados = load_data(caminho_selecionado)

pagina_selecionada = st.sidebar.radio("Escolha o Painel:", ["🌐 Visão 360º", "👥 Análise de Docentes (RH)", "🏢 Ocupação e Ambientes", "📈 Evolução Histórica"])
st.sidebar.divider()
lista_turnos = ["Todos"] + list(dados['turmas']['TURNO'].dropna().unique())
turno_selecionado = st.sidebar.selectbox("Filtro de Turno:", lista_turnos)

if pagina_selecionada == "📈 Evolução Histórica":
    st.title("📈 Evolução e Tendências (Comparativo Mensal)")
    df_historico = compilar_historico(arquivos_salvos)
    
    if len(df_historico) > 1:
        col1, col2 = st.columns(2)
        with col1:
            fig_hist_oc = px.line(df_historico, x="Mês", y="Ocupação Média (%)", markers=True, title="Evolução da Ocupação Média dos Ambientes", line_shape="spline")
            fig_hist_oc.update_yaxes(range=[0, 100])
            st.plotly_chart(fig_hist_oc, use_container_width=True)
        with col2:
            fig_hist_nr = px.bar(df_historico, x="Mês", y="Horas Não Regência", text_auto=True, title="Volume de Horas de Não Regência por Mês", color="Horas Não Regência", color_continuous_scale="Reds")
            st.plotly_chart(fig_hist_nr, use_container_width=True)
        st.dataframe(df_historico, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ É necessário pelo menos 2 meses arquivados para visualizar tendências.")
else:
    if turno_selecionado != "Todos":
        df_turmas_f = dados['turmas'][dados['turmas']['TURNO'] == turno_selecionado]
        df_ocupacao_f = dados['ocupacao'][dados['ocupacao']['TURNO'] == turno_selecionado] if 'TURNO' in dados['ocupacao'].columns else dados['ocupacao']
    else:
        df_turmas_f = dados['turmas'].copy()
        df_ocupacao_f = dados['ocupacao'].copy()

    if pagina_selecionada == "🌐 Visão 360º":
        st.title(f"🌐 Visão Institucional - {mes_analise[5:]}") 
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Turmas Abertas", len(df_turmas_f))
        col2.metric("Alunos", df_turmas_f['VAGAS_OCUPADAS'].sum() if not df_turmas_f.empty else 0)
        col3.metric("Salas Físicas", len(dados['amb'][dados['amb']['VIRTUAL'] == 'NÃO']))
        col4.metric("Instrutores", len(dados['inst']))
        col5.metric("Faltas Registadas", len(dados['faltas']))
        
        st.divider()
        st.markdown("### 🎯 Execução de Hora-Aluno (HA) - Macro")
        st.caption("Cálculo: Carga Horária da Disciplina × Número de Alunos Matriculados na Turma.")
        
        df_disc = dados['disc'].copy()
        df_disc['STATUS_NORM'] = df_disc['STATUS'].astype(str).str.strip().str.upper()
        df_turmas_resumo = df_turmas_f[['ID_TURMA', 'VAGAS_OCUPADAS']].copy()
        df_ha = pd.merge(df_disc, df_turmas_resumo, on='ID_TURMA', how='inner')
        df_ha['HA_TOTAL'] = df_ha['CARGA_HORARIA'] * df_ha['VAGAS_OCUPADAS']
        
        ha_meta = df_ha['HA_TOTAL'].sum()
        ha_cumprida = df_ha[df_ha['STATUS_NORM'].isin(['CONCLUÍDO', 'CONCLUIDO', 'FINALIZADO'])]['HA_TOTAL'].sum()
        perc_ha = (ha_cumprida / ha_meta) * 100 if ha_meta > 0 else 0
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("📚 Meta (Hora-Aluno Total)", f"{ha_meta:,.0f} HA".replace(',', '.'))
        col_m2.metric("✅ Realizado (Hora-Aluno)", f"{ha_cumprida:,.0f} HA".replace(',', '.'))
        col_m3.metric("🚀 Progresso da Meta", f"{perc_ha:.1f}%")
        st.progress(min(int(perc_ha), 100))
        
        st.divider()
        st.markdown("#### Status de Execução das Disciplinas")
        status_disc = df_disc['STATUS'].value_counts().reset_index()
        status_disc.columns = ['Status', 'Quantidade']
        st.plotly_chart(px.pie(status_disc, names='Status', values='Quantidade', hole=0.4, color_discrete_sequence=px.colors.sequential.Teal), use_container_width=True)

    elif pagina_selecionada == "👥 Análise de Docentes (RH)":
        st.title(f"👥 Docentes e Não Regência - {mes_analise[5:]}")
        df_nr_det = pd.merge(dados['nr'], dados['inst'][['ID', 'NOME_COMPLETO']], left_on='ID_INSTRUTOR', right_on='ID', how='left')
        if not df_nr_det.empty:
            df_horas_inst = df_nr_det.groupby('NOME_COMPLETO')['HORAS_NAO_REGENCIA'].sum().reset_index().sort_values('HORAS_NAO_REGENCIA')
            st.plotly_chart(px.bar(df_horas_inst, x='HORAS_NAO_REGENCIA', y='NOME_COMPLETO', orientation='h', title="Ranking de Horas Não Regência", color='HORAS_NAO_REGENCIA', color_continuous_scale='Oranges'), use_container_width=True)
            st.dataframe(df_nr_det[['DATA', 'NOME_COMPLETO', 'TIPO_ATIVIDADE', 'HORAS_NAO_REGENCIA']], use_container_width=True, hide_index=True)
        else:
            st.info("Sem dados de Não Regência para este mês.")

    elif pagina_selecionada == "🏢 Ocupação e Ambientes":
        st.title(f"🏢 Uso de Laboratórios e Salas - {mes_analise[5:]}")
        if not df_ocupacao_f.empty:
            df_amb_uso = df_ocupacao_f.groupby('AMBIENTE')['PERCENTUAL_OCUPACAO'].mean().reset_index()
            df_amb_uso['PERCENTUAL_OCUPACAO'] *= 100
            st.plotly_chart(px.bar(df_amb_uso.sort_values('PERCENTUAL_OCUPACAO'), x='PERCENTUAL_OCUPACAO', y='AMBIENTE', orientation='h', title="Ocupação Média (%)", color='PERCENTUAL_OCUPACAO', color_continuous_scale='Blues'), use_container_width=True)
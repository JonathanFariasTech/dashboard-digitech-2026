import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json 
from github import Github 

# ==========================================
# 1. CONFIGURAÇÃO E INICIALIZAÇÃO
# ==========================================
st.set_page_config(page_title="Dashboard Digitech", layout="wide", page_icon="📊")

PASTA_HISTORICO = "historico_dados"
os.makedirs(PASTA_HISTORICO, exist_ok=True)
ARQUIVO_META = os.path.join(PASTA_HISTORICO, "metas_ha.json") 

MESES_PT = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 
            7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}

ABAS_OBRIGATORIAS = {
    "TURMAS": ["ID_TURMA", "TURNO", "VAGAS_OCUPADAS", "STATUS"],
    "OCUPAÇÃO": ["DATA", "AMBIENTE", "PERCENTUAL_OCUPACAO", "TURNO"],
    "NÃO_REGÊNCIA": ["ID_INSTRUTOR", "HORAS_NAO_REGENCIA"],
    "INSTRUTORES": ["ID", "NOME_COMPLETO"],
    "DISCIPLINAS": ["ID_TURMA", "NOME_DISCIPLINA", "CARGA_HORARIA", "STATUS"],
    "AMBIENTES": ["ID_AMBIENTE", "NOME_AMBIENTE", "CAPACIDADE", "VIRTUAL"],
    "FALTAS": ["ID_ALUNO", "DATA_FALTA", "TIPO_FALTA"],
    "PARÂMETROS": ["META_HA_AUTOMATICA"]
}

if 'admin_logado' not in st.session_state:
    st.session_state['admin_logado'] = False

# ==========================================
# 2. FUNÇÕES DE VALIDAÇÃO, GITHUB E METAS
# ==========================================
def validar_planilha(file):
    try:
        xls = pd.ExcelFile(file)
        abas_arquivo = xls.sheet_names
        abas_faltantes = [aba for aba in ABAS_OBRIGATORIAS if aba not in abas_arquivo]
        if abas_faltantes:
            return False, f"Faltam as abas: {', '.join(abas_faltantes)}"
        
        for aba, colunas_obrigatorias in ABAS_OBRIGATORIAS.items():
            if aba in abas_arquivo:
                df_temp = pd.read_excel(file, sheet_name=aba, nrows=1) # Ler apenas a primeira linha para obter os nomes das colunas
                colunas_faltantes = [col for col in colunas_obrigatorias if col not in df_temp.columns]
                if colunas_faltantes:
                    return False, f"Na aba '{aba}', faltam as colunas: {', '.join(colunas_faltantes)}"
        
        return True, "Planilha validada com sucesso."
    except Exception as e:
        return False, f"Erro ao ler o ficheiro ou validar colunas: {e}"

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

def salvar_no_github(caminho_arquivo_local, nome_arquivo_github, file_buffer):
    try:
        if "GITHUB_TOKEN" in st.secrets and "GITHUB_REPO" in st.secrets:
            g = Github(st.secrets["GITHUB_TOKEN"])
            repo = g.get_repo(st.secrets["GITHUB_REPO"])
            caminho_no_repo = f"{PASTA_HISTORICO}/{nome_arquivo_github}"
            mensagem_commit = f"Upload automático via Dashboard: {nome_arquivo_github}"
            
            try:
                contents = repo.get_contents(caminho_no_repo)
                repo.update_file(contents.path, mensagem_commit, file_buffer.getvalue(), contents.sha)
            except Exception:
                repo.create_file(caminho_no_repo, mensagem_commit, file_buffer.getvalue())
            return True, "Sincronizado com a Nuvem!"
        else:
            return False, "Faltam os Secrets do GitHub no Streamlit."
    except KeyError:
        return False, "Faltam os Secrets do GitHub no Streamlit (GITHUB_TOKEN ou GITHUB_REPO)."
    except Exception as e:
        return False, f"Erro na sincronização com o GitHub: {e}"

def carregar_metas():
    if os.path.exists(ARQUIVO_META):
        try:
            with open(ARQUIVO_META, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def salvar_metas_github(metas_dict):
    with open(ARQUIVO_META, "w") as f:
        json.dump(metas_dict, f, indent=4)
        
    try:
        if "GITHUB_TOKEN" in st.secrets and "GITHUB_REPO" in st.secrets:
            g = Github(st.secrets["GITHUB_TOKEN"])
            repo = g.get_repo(st.secrets["GITHUB_REPO"])
            caminho_no_repo = f"{PASTA_HISTORICO}/metas_ha.json"
            mensagem_commit = "Atualização manual da Meta de Hora-Aluno"
            conteudo = json.dumps(metas_dict, indent=4)
            
            try:
                contents = repo.get_contents(caminho_no_repo)
                repo.update_file(contents.path, mensagem_commit, conteudo, contents.s            except Exception as e_update:
                # Se o arquivo não existe, cria. Se der outro erro, registra.
                try:
                    repo.create_file(caminho_no_repo, mensagem_commit, conteudo)
                except Exception as e_create:
                    st.error(f"Erro ao criar/atualizar metas no GitHub: {e_create}")
                    return False
            return True
    except KeyError:
        st.error("Faltam os Secrets do GitHub no Streamlit (GITHUB_TOKEN ou GITHUB_REPO).")
        return False
    except Exception as e:
        st.error(f"Erro geral ao salvar metas no GitHub: {e}")
        return False========================================
# 3. BARRA LATERAL: LOGIN COM FORMULÁRIO
# ==========================================
st.sidebar.title("🔐 Acesso Administrativo")

if not st.session_state['admin_logado']:
    with st.sidebar.form("form_login"):
        st.markdown("🔒 **Faça login para gerir os dados**")
        senha = st.text_input("Palavra-passe:", type="password")
        btn_entrar = st.form_submit_button("Entrar 🚀", use_container_width=True)
        
        if btn_entrar:
            if senha == st.secrets["ADMIN_PASSWORD"]: 
                st.session_state['admin_logado'] = True
                st.rerun() # Força a re-renderização para atualizar a UI após o login
            elif "ADMIN_PASSWORD" not in st.secrets:
                st.error("❌ Senha de administrador não configurada nos secrets do Streamlit.")
            
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
# 3.1. FERRAMENTAS DO ADMIN E NAVEGAÇÃO
# ==========================================
st.sidebar.title("🧭 Navegação Visual")
mes_analise = st.sidebar.selectbox("📅 Mês de Análise:", [f.replace(".xlsx", "") for f in arquivos_salvos], index=max(0, len(arquivos_salvos)-1)) if arquivos_salvos else None

if st.session_state['admin_logado']:
    st.sidebar.title("🛠️ Ferramentas Admin")
    
    with st.sidebar.expander("🎯 Ajustar Meta Hora-Aluno", expanded=False):
        st.markdown(f"**A editar a meta de:** {mes_analise if mes_analise else 'Nenhum mês'}")
        metas_salvas = carregar_metas()
        meta_atual = metas_salvas.get(mes_analise, 0) if mes_analise else 0
        
        nova_meta = st.number_input(
            "Definir Meta Manual (0 = Automático):", 
            min_value=0, value=int(meta_atual), step=500,
            help="Se deixar 0, o sistema multiplicará os alunos pelas horas das disciplinas."
        )
        
        if st.button("💾 Guardar Meta", use_container_width=True):
            if mes_analise:
                metas_salvas[mes_analise] = nova_meta
                with st.spinner("Sincronizando meta... ☁️"):
                    salvar_metas_github(metas_salvas)
                st.toast("Meta atualizada com sucesso!", icon="🎯")
                st.rerun()
            else:
                st.error("Adicione uma planilha primeiro!")
    
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
                            arquivo_carregado.seek(0)
                            with open(caminho_arquivo, "wb") as f:
                                f.write(arquivo_carregado.getbuffer())
                            
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
# 5. CARREGAMENTO DOS DADOS E ROTEAMENTO
# ==========================================
@st.cache_data
def load_data(file_path):
    """Carrega todas as abas necessárias de uma planilha Excel com otimização de colunas."""
    xls = pd.ExcelFile(file_path)
    
    # Mapeamento de abas para colunas necessárias (otimização de memória)
    config_abas = {
        'turmas': ("TURMAS", None, 0),
        'ocupacao': ("OCUPAÇÃO", None, 0),
        'nr': ("NÃO_REGÊNCIA", None, 0),
        'inst': ("INSTRUTORES", None, 0),
        'disc': ("DISCIPLINAS", None, 1),
        'amb': ("AMBIENTES", None, 0),
        'faltas': ("FALTAS", None, 0),
        'param': ("PARÂMETROS", None, 9)
    }
    
    dados_carregados = {}
    for chave, (nome_aba, colunas, pular_linhas) in config_abas.items():
        try:
            dados_carregados[chave] = pd.read_excel(
                xls, 
                sheet_name=nome_aba, 
                usecols=colunas, 
                skiprows=pular_linhas
            )
        except Exception as e:
            st.error(f"Erro ao carregar aba '{nome_aba}': {e}")
            dados_carregados[chave] = pd.DataFrame()
            
    return dados_carregados

@st.cache_data
def compilar_historico(arquivos):
    """Compila dados de múltiplos meses para análise de tendências, otimizando a leitura."""
    dados_linha_tempo = []
    for arq in arquivos:
        mes = arq.replace(".xlsx", "")
        caminho = os.path.join(PASTA_HISTORICO, arq)
        try:
            # Lê apenas as colunas necessárias para o histórico
            df_nr = pd.read_excel(caminho, sheet_name="NÃO_REGÊNCIA", usecols=["HORAS_NAO_REGENCIA"])
            df_oc = pd.read_excel(caminho, sheet_name="OCUPAÇÃO", usecols=["PERCENTUAL_OCUPACAO"])
            
            total_nr = df_nr['HORAS_NAO_REGENCIA'].sum()
            ocupacao_media = df_oc['PERCENTUAL_OCUPACAO'].mean() * 100
            
            dados_linha_tempo.append({
                "Mês": mes, 
                "Horas Não Regência": total_nr, 
                "Ocupação Média (%)": ocupacao_media
            })
        except Exception as e:
            # Silencioso para não quebrar a UI, mas poderia ser logado
            continue 
            
    df_hist = pd.DataFrame(dados_linha_tempo)
    if not df_hist.empty:
        df_hist = df_hist.sort_values("Mês") # Garante ordem cronológica se os nomes permitirem
    return df_hist

caminho_selecionado = os.path.join(PASTA_HISTORICO, f"{mes_analise}.xlsx")
dados = load_data(caminho_selecionado)

pagina_selecionada = st.sidebar.radio("Escolha o Painel:", [
    "🌐 Visão 360º", 
    "👥 Análise de Docentes (RH)", 
    "🏢 Ocupação e Ambientes", 
    "📈 Evolução Histórica",
    "📑 Relatórios Detalhados"
])

st.sidebar.divider()
lista_turnos = ["Todos"] + list(dados['turmas']['TURNO'].dropna().unique())
turno_selecionado = st.sidebar.selectbox("Filtro de Turno:", lista_turnos)

# ==========================================
# FUNÇÃO AUXILIAR PARA CRIAR O NOME DA TURMA
# ==========================================
def obter_coluna_nome_turma(df_turmas):
    if 'NOME_TURMA' in df_turmas.columns: return 'NOME_TURMA'
    if 'CURSO' in df_turmas.columns: return 'CURSO'
    if 'NOME' in df_turmas.columns: return 'NOME'
    return 'ID_TURMA'

col_nome = obter_coluna_nome_turma(dados['turmas'])

# ==========================================
# 6. RENDERIZAÇÃO DOS PAINÉIS
# ==========================================

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

elif pagina_selecionada == "📑 Relatórios Detalhados":
    st.title(f"📑 Relatório Gerencial Pormenorizado - {mes_analise[5:] if mes_analise else ''}")
    st.markdown("Auditoria de dados cruzados e exportação de listagens para o Excel.")
    
    tab1, tab2 = st.tabs(["📚 Raio-X das Disciplinas", "⚠️ Análise de Faltas"])
    
    with tab1:
        st.subheader("Situação Detalhada das Disciplinas e Turmas")
        df_turmas_resumo = dados['turmas'][['ID_TURMA', 'TURNO', 'VAGAS_OCUPADAS']].copy()
        if col_nome != 'ID_TURMA':
            df_turmas_resumo[col_nome] = dados['turmas'][col_nome]
            df_turmas_resumo['TURMA_EXIBICAO'] = df_turmas_resumo['ID_TURMA'].astype(str) + " - " + df_turmas_resumo[col_nome].astype(str)
        else:
            df_turmas_resumo['TURMA_EXIBICAO'] = "Turma " + df_turmas_resumo['ID_TURMA'].astype(str)
            
        df_relatorio_disc = pd.merge(dados['disc'], df_turmas_resumo, on='ID_TURMA', how='inner')
        df_relatorio_disc['HORA_ALUNO_TOTAL'] = df_relatorio_disc['CARGA_HORARIA'] * df_relatorio_disc['VAGAS_OCUPADAS']
        
        cols = ['TURMA_EXIBICAO'] + [c for c in df_relatorio_disc.columns if c != 'TURMA_EXIBICAO']
        df_relatorio_disc = df_relatorio_disc[cols]
        
        lista_status = df_relatorio_disc['STATUS'].dropna().unique()
        filtro_status = st.multiselect("Filtrar por Status da Disciplina:", lista_status, default=lista_status)
        
        df_final = df_relatorio_disc[df_relatorio_disc['STATUS'].isin(filtro_status)]
        
        st.dataframe(df_final, use_container_width=True, hide_index=True)
        
        csv_disc = df_final.to_csv(index=False, sep=";").encode('utf-8-sig')
        st.download_button(
            label="📥 Exportar Dados Visíveis para Excel (CSV)", 
            data=csv_disc, 
            file_name=f"relatorio_disciplinas_{mes_analise.replace(' ', '_')}.csv", 
            mime="text/csv",
            use_container_width=True
        )

    with tab2:
        st.subheader("Relatório e Tendência de Ocorrências (Faltas)")
        df_faltas = dados['faltas'].copy()
        
        if not df_faltas.empty:
            coluna_data = 'DATA_FALTA' if 'DATA_FALTA' in df_faltas.columns else ('DATA' if 'DATA' in df_faltas.columns else None)
            
            if coluna_data:
                # Prepara os dados para o gráfico de linha
                df_tendencia = df_faltas.copy()
                df_tendencia['DATA_DATETIME'] = pd.to_datetime(df_tendencia[coluna_data], errors='coerce')
                df_tendencia = df_tendencia.dropna(subset=['DATA_DATETIME'])
                
                df_tendencia_grupo = df_tendencia.groupby('DATA_DATETIME').size().reset_index(name='QTD_FALTAS')
                df_tendencia_grupo = df_tendencia_grupo.sort_values('DATA_DATETIME')
                
                if not df_tendencia_grupo.empty:
                    fig_faltas = px.line(
                        df_tendencia_grupo, 
                        x='DATA_DATETIME', 
                        y='QTD_FALTAS', 
                        markers=True, 
                        title="📉 Tendência Diária de Ausências",
                        labels={'DATA_DATETIME': 'Data da Ocorrência', 'QTD_FALTAS': 'Número de Faltas'},
                        line_shape="spline" 
                    )
                    fig_faltas.update_traces(line_color='#e63946', marker=dict(size=8))
                    st.plotly_chart(fig_faltas, use_container_width=True)
                    st.divider()

            # --- TABELA DE FALTAS ---
            st.markdown("**Listagem Detalhada:**")
            if coluna_data:
                df_faltas[coluna_data] = pd.to_datetime(df_faltas[coluna_data], errors='coerce').dt.strftime('%d/%m/%Y')
            st.dataframe(df_faltas, use_container_width=True, hide_index=True)
            
            csv_faltas = df_faltas.to_csv(index=False, sep=";").encode('utf-8-sig')
            st.download_button(
                label="📥 Exportar Registo de Faltas (CSV)", 
                data=csv_faltas, 
                file_name=f"relatorio_faltas_{mes_analise.replace(' ', '_')}.csv", 
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.success("🎉 Nenhuma falta registada neste período!")

else:
    # Filtro Global de Turno para as páginas abaixo
    if turno_selecionado != "Todos":
        df_turmas_f = dados['turmas'][dados['turmas']['TURNO'] == turno_selecionado]
        df_ocupacao_f = dados['ocupacao'][dados['ocupacao']['TURNO'] == turno_selecionado] if 'TURNO' in dados['ocupacao'].columns else dados['ocupacao']
    else:
        df_turmas_f = dados['turmas'].copy()
        df_ocupacao_f = dados['ocupacao'].copy()

        from pages import render_visao_360
        render_visao_360(dados, mes_analise, col_nome, df_turmas_f, df_ocupacao_f, carregar_metas)

    elif pagina_selecionada == "👥 Análise de Docentes (RH)":
        from pages import render_analise_docentes
        render_analise_docentes(dados, mes_analise)

    elif pagina_selecionada == "🏢 Ocupação e Ambientes":
        from pages import render_ocupacao_ambientes
        render_ocupacao_ambientes(dados, mes_analise, df_ocupacao_f)
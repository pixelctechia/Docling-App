import streamlit as st
import os
import sys
import subprocess
from pathlib import Path

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.core.processor import processar_url, ProcessorError
from src.database.db_manager import add_task, get_recent_tasks

st.set_page_config(
    page_title="Docling App - Extrator Web",
    page_icon="🔓",
    layout="wide"
)

# Estilo Customizado
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        font-weight: bold;
    }
    .status-box {
        padding: 10px;
        border-radius: 5px;
        background-color: #f0f2f6;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

def abrir_pasta_local(caminho):
    """Abre a pasta no explorador de arquivos do Linux (Ubuntu)."""
    try:
        if sys.platform.startswith('linux'):
            subprocess.Popen(['xdg-open', str(caminho)])
        elif sys.platform == 'win32':
            os.startfile(caminho)
    except Exception as e:
        st.error(f"Não foi possível abrir a pasta: {e}")

# --- SIDEBAR (Configurações) ---
with st.sidebar:
    st.header("⚙️ Configurações do Robô")
    
    st.write("---")
    st.subheader("1. Modo de Extração")
    modo_extracao = st.radio(
        "Como você quer capturar?",
        options=["Página Única (Apenas o Link)", "Site Completo (Crawler)"],
        index=0,
        help="Página Única: Baixa apenas o link informado.\nSite Completo: Segue os links internos."
    )
    
    st.subheader("2. Limites")
    max_pages = st.number_input(
        "Limite Máximo de Páginas", 
        min_value=1, 
        max_value=500, 
        value=50,
        disabled=(modo_extracao == "Página Única (Apenas o Link)"),
        help="Se escolher 'Página Única', este valor será ignorado (será 1)."
    )
    
    st.subheader("3. Formato de Saída")
    output_format = st.radio(
        "Salvar arquivos como:",
        options=["Markdown", "JSON", "Ambos"],
        index=2
    )
    
    st.write("---")
    st.info("ℹ️ O sistema usa Auto-Scroll para garantir captura total de sites dinâmicos (React/Vue).")
    
    st.write("---")
    st.markdown("""
        <div style='text-align: center'>
            <p>🚀 Desenvolvido por <b><a href='https://www.pixelctech.com.br' target='_blank'>Pixelc Tech</a></b></p>
            <p style='font-size: 0.8em; color: gray;'>Sistema Open Source livre para todos.</p>
            <p><a href='https://github.com/pixelctechia/Docling-App' target='_blank'>⭐ Ver no GitHub</a></p>
        </div>
    """, unsafe_allow_html=True)

# --- ÁREA PRINCIPAL ---
st.title("🔓 Docling App - Pixelc Tech")
st.markdown("### Extrator de Dados Web Sem Restrições (Open Source)")
st.write("Desenvolvido por [Pixelc Tech](https://www.pixelctech.com.br) | Repositório: [GitHub](https://github.com/pixelctechia/Docling-App)")

url_input = st.text_input("🔗 Cole a URL do Website aqui:", placeholder="https://exemplo.com.br")

col1, col2 = st.columns([1, 2])

with col1:
    btn_iniciar = st.button("🚀 INICIAR EXTRAÇÃO", type="primary")

if btn_iniciar and url_input:
    # Lógica de decisão do limite
    limite_real = 1 if modo_extracao == "Página Única (Apenas o Link)" else max_pages
    
    status_container = st.empty()
    logs_container = st.expander("Ver Logs de Processamento", expanded=True)
    
    try:
        with st.spinner(f"Iniciando motor Playwright... (Modo: {modo_extracao})"):
            # Redirecionando print para a interface (opcional, aqui simplificado)
            arquivos = processar_url(url_input, output_format, limite_real)
            
            # Salvar no histórico
            caminho_primeiro_arquivo = arquivos[0] if arquivos else ""
            pasta_destino = Path(caminho_primeiro_arquivo).parent if caminho_primeiro_arquivo else ""
            
            add_task(url_input, output_format, "Sucesso", str(pasta_destino))
            
            st.success(f"✅ Processamento Concluído! {len(arquivos)} páginas capturadas.")
            
            if pasta_destino:
                st.markdown(f"**📂 Arquivos salvos em:** `{pasta_destino}`")
                if st.button("📂 Abrir Pasta dos Arquivos"):
                    abrir_pasta_local(pasta_destino)

    except ProcessorError as e:
        st.error(f"❌ Erro no Processamento: {str(e)}")
        add_task(url_input, output_format, "Falha", str(e))
    except Exception as e:
        st.error(f"❌ Erro Inesperado: {str(e)}")

st.write("---")
st.subheader("📜 Histórico Recente")
try:
    df = get_recent_tasks()
    st.dataframe(df, use_container_width=True)
except Exception:
    st.write("Nenhum histórico ainda.")
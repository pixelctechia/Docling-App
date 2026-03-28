import streamlit as st
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

# Garante imports absolutos quando a UI for executada diretamente por
# `streamlit run src/ui/app.py`, além do entrypoint raiz `streamlit_app.py`.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.artifacts import criar_zip_em_memoria
from src.core.processor import processar_url, ProcessorError, validar_url
from src.config.settings import (
    OUTPUTS_DIR,
    RAG_DEFAULT_CHUNK_OVERLAP,
    RAG_DEFAULT_CHUNK_SIZE,
    RAG_DEFAULT_ENABLED,
    UI_DEFAULT_MAX_DEPTH,
    UI_DEFAULT_MAX_PAGES,
    UI_MAX_PAGES_LIMIT,
)
from src.config.presets import DEFAULT_PRESET_KEY, get_usage_preset, list_usage_presets
from src.database import db_manager

add_task = db_manager.add_task
get_recent_tasks = db_manager.get_recent_tasks
clear_tasks = getattr(db_manager, "clear_tasks", lambda: False)

def abrir_pasta_local(caminho):
    """Abre a pasta no explorador de arquivos do Linux (Ubuntu)."""
    try:
        if sys.platform.startswith('linux'):
            subprocess.Popen(['xdg-open', str(caminho)])
        elif sys.platform == 'win32':
            os.startfile(caminho)
    except Exception as e:
        st.error(f"Não foi possível abrir a pasta: {e}")

def outputs_tem_conteudo() -> bool:
    """Verifica se a pasta de saídas possui arquivos ou diretórios."""
    if not OUTPUTS_DIR.exists() or not OUTPUTS_DIR.is_dir():
        return False
    return any(OUTPUTS_DIR.iterdir())

def obter_resumo_outputs() -> tuple[int, int]:
    """Conta diretórios e arquivos existentes dentro de `outputs`."""
    if not OUTPUTS_DIR.exists() or not OUTPUTS_DIR.is_dir():
        return 0, 0

    total_diretorios = 0
    total_arquivos = 0
    for item in OUTPUTS_DIR.rglob("*"):
        if item.is_dir():
            total_diretorios += 1
        elif item.is_file():
            total_arquivos += 1
    return total_diretorios, total_arquivos

def limpar_arquivos_extraidos() -> tuple[bool, int]:
    """Remove todo o conteúdo da pasta de saídas, preservando a raiz `outputs`."""
    if not OUTPUTS_DIR.exists():
        return True, 0

    removidos = 0
    try:
        for item in OUTPUTS_DIR.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
                removidos += 1
            else:
                item.unlink()
                removidos += 1
        return True, removidos
    except Exception:
        return False, removidos

def criar_monitor_de_progresso(limite_real: int):
    """Monta callbacks para atualizar a interface durante o processamento."""
    estado = {
        "status": "Aguardando início...",
        "url_atual": "",
        "processadas": 0,
        "fila": 0,
        "arquivos": 0,
        "erros": 0,
        "progresso": 0,
        "rag_chunks": 0,
        "pasta_saida": "",
        "logs": []
    }

    status_placeholder = st.empty()
    progresso_placeholder = st.empty()
    metricas_placeholder = st.empty()
    logs_expander = st.expander("Ver Logs de Processamento", expanded=True)
    with logs_expander:
        logs_placeholder = st.empty()

    def renderizar():
        status_placeholder.markdown(
            f"**Status:** {estado['status']}\n\n"
            f"**URL atual:** `{estado['url_atual'] or '-'}`"
        )

        percentual = int((estado["progresso"] / max(limite_real, 1)) * 100)
        percentual = max(0, min(percentual, 100))
        progresso_placeholder.progress(percentual, text=f"{percentual}% concluído")

        with metricas_placeholder.container():
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Páginas", f"{estado['processadas']}/{limite_real}")
            col2.metric("Arquivos", estado["arquivos"])
            col3.metric("Fila", estado["fila"])
            col4.metric("Erros", estado["erros"])
            col5.metric("Chunks RAG", estado["rag_chunks"])

        logs = "\n".join(estado["logs"][-20:]) if estado["logs"] else "Aguardando logs..."
        logs_placeholder.code(logs, language="text")

    def on_log(mensagem: str):
        estado["logs"].append(mensagem)
        renderizar()

    def on_progress(payload: dict):
        evento = payload.get("event")

        if evento == "startup":
            estado["status"] = f"Iniciando extração em {payload.get('target', 'site alvo')}..."
            estado["pasta_saida"] = payload.get("output_dir", "")
        elif evento == "page_start":
            pagina_atual = payload.get("current_page", 0)
            limite = payload.get("max_pages", limite_real)
            estado["status"] = f"Processando página {pagina_atual} de {limite}"
            estado["url_atual"] = payload.get("current_url", "")
            estado["fila"] = payload.get("queue_size", 0)
            estado["arquivos"] = payload.get("generated_files", estado["arquivos"])
            estado["progresso"] = max(pagina_atual - 1, 0)
        elif evento == "links_discovered":
            estado["fila"] = payload.get("queue_size", estado["fila"])
        elif evento == "page_done":
            pagina_atual = payload.get("current_page", estado["processadas"])
            estado["status"] = f"Página {pagina_atual} concluída"
            estado["url_atual"] = payload.get("current_url", estado["url_atual"])
            estado["processadas"] = pagina_atual
            estado["fila"] = payload.get("queue_size", estado["fila"])
            estado["arquivos"] = payload.get("generated_files", estado["arquivos"])
            estado["progresso"] = pagina_atual
        elif evento == "page_error":
            pagina_atual = payload.get("current_page", estado["processadas"])
            estado["status"] = f"Falha na página {pagina_atual}, seguindo para a próxima"
            estado["url_atual"] = payload.get("current_url", estado["url_atual"])
            estado["processadas"] = pagina_atual
            estado["fila"] = payload.get("queue_size", estado["fila"])
            estado["arquivos"] = payload.get("generated_files", estado["arquivos"])
            estado["erros"] += 1
            estado["progresso"] = pagina_atual
        elif evento == "completed":
            estado["status"] = "Processamento concluído com sucesso"
            estado["processadas"] = payload.get("total_pages", estado["processadas"])
            estado["arquivos"] = payload.get("generated_files", estado["arquivos"])
            estado["rag_chunks"] = payload.get("rag_chunks", estado["rag_chunks"])
            estado["pasta_saida"] = payload.get("output_dir", estado["pasta_saida"])
            estado["fila"] = 0
            estado["progresso"] = limite_real

        renderizar()

    renderizar()
    return on_progress, on_log, lambda: estado.copy()

def parse_textarea_paths(texto: str) -> list[str]:
    """Transforma caminhos informados na sidebar em lista limpa."""
    if not texto.strip():
        return []

    itens = []
    for linha in texto.splitlines():
        for parte in linha.split(","):
            caminho = parte.strip()
            if caminho:
                itens.append(caminho)
    return itens

def format_paths_for_textarea(caminhos: list[str]) -> str:
    """Transforma uma lista de caminhos em texto para a UI."""
    return "\n".join(caminhos)

def aplicar_preset_na_sessao(preset) -> None:
    """Aplica os valores de um preset no estado da interface."""
    preset_ui = preset.to_ui_state()
    st.session_state["preset_key"] = preset.key
    st.session_state["modo_extracao"] = preset_ui["modo_extracao"]
    st.session_state["output_format"] = preset_ui["output_format"]
    st.session_state["max_pages"] = preset_ui["max_pages"]
    st.session_state["max_depth"] = preset_ui["max_depth"]
    st.session_state["include_paths_text"] = format_paths_for_textarea(preset_ui["include_paths"])
    st.session_state["exclude_paths_text"] = format_paths_for_textarea(preset_ui["exclude_paths"])
    st.session_state["ignorar_arquivos_binarios"] = preset_ui["ignorar_arquivos_binarios"]
    st.session_state["gerar_rag_artifacts"] = preset_ui["gerar_rag_artifacts"]
    st.session_state["rag_chunk_size"] = preset_ui["rag_chunk_size"]
    st.session_state["rag_chunk_overlap"] = preset_ui["rag_chunk_overlap"]
    st.session_state["_preset_aplicado_key"] = preset.key
    st.session_state["_preset_personalizado_manual"] = False

def estado_sidebar_diferente_do_preset(preset, estado_atual: dict) -> bool:
    """Verifica se o usuario alterou manualmente a configuracao em relacao ao preset."""
    preset_ui = preset.to_ui_state()
    return any(
        [
            estado_atual["modo_extracao"] != preset_ui["modo_extracao"],
            estado_atual["output_format"] != preset_ui["output_format"],
            estado_atual["max_pages"] != preset_ui["max_pages"],
            estado_atual["max_depth"] != preset_ui["max_depth"],
            parse_textarea_paths(estado_atual["include_paths_text"]) != preset_ui["include_paths"],
            parse_textarea_paths(estado_atual["exclude_paths_text"]) != preset_ui["exclude_paths"],
            estado_atual["ignorar_arquivos_binarios"] != preset_ui["ignorar_arquivos_binarios"],
            estado_atual["gerar_rag_artifacts"] != preset_ui["gerar_rag_artifacts"],
            estado_atual["rag_chunk_size"] != preset_ui["rag_chunk_size"],
            estado_atual["rag_chunk_overlap"] != preset_ui["rag_chunk_overlap"],
        ]
    )

def renderizar_sidebar_configuracoes():
    """Renderiza o menu de configuracoes e devolve os valores da UI."""
    st.write("---")
    presets = list_usage_presets()
    preset_labels = [preset.label for preset in presets]
    preset_keys_by_label = {preset.label: preset.key for preset in presets}

    st.subheader("1. Preset de Uso")
    preset_label_selecionado = st.selectbox(
        "Escolha um objetivo pronto",
        options=preset_labels,
        index=next(
            (
                indice
                for indice, preset in enumerate(presets)
                if preset.key == st.session_state.get("preset_key", DEFAULT_PRESET_KEY)
            ),
            0,
        ),
        help="Os presets preenchem automaticamente a configuracao para cenarios comuns e ajudam a acelerar o uso da ferramenta."
    )
    preset_ativo = get_usage_preset(preset_keys_by_label[preset_label_selecionado])
    preservar_personalizado_manual = (
        preset_ativo.key == DEFAULT_PRESET_KEY
        and st.session_state.get("_preset_personalizado_manual", False)
    )
    if st.session_state.get("_preset_aplicado_key") != preset_ativo.key and not preservar_personalizado_manual:
        aplicar_preset_na_sessao(preset_ativo)

    st.session_state["preset_key"] = preset_ativo.key
    st.caption(f"Preset ativo: **{preset_ativo.label}**")
    if preset_ativo.key == DEFAULT_PRESET_KEY and st.session_state.get("_preset_personalizado_manual", False):
        st.warning("Modo Personalizado ativo: voce alterou manualmente uma ou mais configuracoes do preset.")
    elif preset_ativo.key == DEFAULT_PRESET_KEY:
        st.info("Modo Personalizado: voce tem liberdade total para ajustar todos os campos manualmente.")
    else:
        st.success(f"Preset aplicado: {preset_ativo.description}")
        st.caption("Se voce editar os campos manualmente, a interface muda automaticamente para o modo Personalizado.")

    st.subheader("2. Modo de Extração")
    modo_extracao = st.radio(
        "Como você quer capturar?",
        options=["Página Única (Apenas o Link)", "Site Completo (Crawler)"],
        index=["Página Única (Apenas o Link)", "Site Completo (Crawler)"].index(
            st.session_state.get("modo_extracao", "Página Única (Apenas o Link)")
        ),
        key="modo_extracao",
        help="Página Única: Baixa apenas o link informado.\nSite Completo: Segue os links internos."
    )

    st.subheader("3. Limites")
    max_pages = st.number_input(
        "Limite Máximo de Páginas",
        min_value=1,
        max_value=UI_MAX_PAGES_LIMIT,
        value=st.session_state.get("max_pages", UI_DEFAULT_MAX_PAGES),
        key="max_pages",
        disabled=(modo_extracao == "Página Única (Apenas o Link)"),
        help="Se escolher 'Página Única', este valor será ignorado (será 1)."
    )

    max_depth = st.number_input(
        "Profundidade Máxima do Crawler",
        min_value=0,
        max_value=10,
        value=st.session_state.get("max_depth", UI_DEFAULT_MAX_DEPTH),
        key="max_depth",
        disabled=(modo_extracao == "Página Única (Apenas o Link)"),
        help="0 captura apenas a URL inicial. 1 segue os links encontrados nela, e assim por diante."
    )

    st.subheader("4. Formato de Saída")
    output_format = st.radio(
        "Salvar arquivos como:",
        options=["Markdown", "JSON", "Ambos"],
        index=["Markdown", "JSON", "Ambos"].index(st.session_state.get("output_format", "Ambos")),
        key="output_format",
    )

    st.subheader("5. Filtros do Crawler")
    include_paths_text = st.text_area(
        "Incluir apenas caminhos",
        value=st.session_state.get("include_paths_text", ""),
        key="include_paths_text",
        disabled=(modo_extracao == "Página Única (Apenas o Link)"),
        help="Opcional. Um caminho por linha ou separados por vírgula. Ex.: /blog ou /docs"
    )
    exclude_paths_text = st.text_area(
        "Ignorar caminhos",
        value=st.session_state.get("exclude_paths_text", ""),
        key="exclude_paths_text",
        disabled=(modo_extracao == "Página Única (Apenas o Link)"),
        help="Opcional. Um caminho por linha ou separados por vírgula. Ex.: /admin ou /login"
    )
    ignorar_arquivos_binarios = st.checkbox(
        "Ignorar arquivos não HTML comuns",
        value=st.session_state.get("ignorar_arquivos_binarios", True),
        key="ignorar_arquivos_binarios",
        help="Evita seguir links para imagens, PDFs, arquivos compactados, mídia, fontes e assets."
    )

    st.subheader("6. Saída para RAG")
    gerar_rag_artifacts = st.checkbox(
        "Gerar arquivo pronto para RAG (.jsonl)",
        value=st.session_state.get("gerar_rag_artifacts", RAG_DEFAULT_ENABLED),
        key="gerar_rag_artifacts",
        help="Cria um arquivo consolidado `rag_chunks.jsonl` com chunks e metadados por página."
    )
    rag_chunk_size = st.number_input(
        "Tamanho do chunk RAG",
        min_value=200,
        max_value=5000,
        value=st.session_state.get("rag_chunk_size", RAG_DEFAULT_CHUNK_SIZE),
        step=100,
        key="rag_chunk_size",
        disabled=not gerar_rag_artifacts
    )
    rag_chunk_overlap = st.number_input(
        "Sobreposição do chunk RAG",
        min_value=0,
        max_value=2000,
        value=st.session_state.get("rag_chunk_overlap", RAG_DEFAULT_CHUNK_OVERLAP),
        step=50,
        key="rag_chunk_overlap",
        disabled=not gerar_rag_artifacts
    )

    estado_atual = {
        "modo_extracao": modo_extracao,
        "output_format": output_format,
        "max_pages": max_pages,
        "max_depth": max_depth,
        "include_paths_text": include_paths_text,
        "exclude_paths_text": exclude_paths_text,
        "ignorar_arquivos_binarios": ignorar_arquivos_binarios,
        "gerar_rag_artifacts": gerar_rag_artifacts,
        "rag_chunk_size": rag_chunk_size,
        "rag_chunk_overlap": rag_chunk_overlap,
    }
    if (
        preset_ativo.key != DEFAULT_PRESET_KEY
        and estado_sidebar_diferente_do_preset(preset_ativo, estado_atual)
    ):
        st.session_state["preset_key"] = DEFAULT_PRESET_KEY
        st.session_state["_preset_personalizado_manual"] = True
        st.rerun()

    return {
        "preset_key": preset_ativo.key,
        "preset_label": preset_ativo.label,
        "preset_description": preset_ativo.description,
        "modo_extracao": modo_extracao,
        "max_pages": max_pages,
        "max_depth": max_depth,
        "output_format": output_format,
        "include_paths_text": include_paths_text,
        "exclude_paths_text": exclude_paths_text,
        "ignorar_arquivos_binarios": ignorar_arquivos_binarios,
        "gerar_rag_artifacts": gerar_rag_artifacts,
        "rag_chunk_size": rag_chunk_size,
        "rag_chunk_overlap": rag_chunk_overlap,
    }

def renderizar_tutorial():
    """Exibe um tutorial simples e amigavel para qualquer tipo de usuario."""
    st.markdown(
        """
        <style>
        .tutorial-hero {
            padding: 1.5rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #102542 0%, #1f4e79 55%, #4ea5d9 100%);
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 12px 30px rgba(16, 37, 66, 0.18);
        }
        .tutorial-hero h1 {
            margin: 0 0 0.5rem 0;
            font-size: 2rem;
        }
        .tutorial-hero p {
            margin: 0;
            font-size: 1rem;
            line-height: 1.6;
        }
        .tutorial-card {
            background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
            border: 1px solid #d9e7f5;
            border-radius: 16px;
            padding: 1rem 1.1rem;
            box-shadow: 0 6px 18px rgba(26, 71, 112, 0.08);
            height: 100%;
        }
        .tutorial-card h3 {
            margin-top: 0;
            margin-bottom: 0.4rem;
            color: #12395b;
            font-size: 1.05rem;
        }
        .tutorial-card p {
            margin-bottom: 0;
            color: #284760;
            line-height: 1.55;
            font-size: 0.95rem;
        }
        .tutorial-step {
            border-left: 4px solid #1f4e79;
            background: #f7fbff;
            padding: 0.85rem 1rem;
            border-radius: 0 12px 12px 0;
            margin-bottom: 0.75rem;
        }
        .tutorial-step strong {
            color: #12395b;
        }
        .tutorial-highlight {
            background: #eef7ff;
            border: 1px solid #cfe4f7;
            border-radius: 14px;
            padding: 1rem;
            margin: 0.75rem 0 1rem 0;
        }
        @media (max-width: 768px) {
            .tutorial-hero {
                padding: 1.15rem;
                border-radius: 16px;
            }
            .tutorial-hero h1 {
                font-size: 1.55rem;
            }
            .tutorial-hero p {
                font-size: 0.94rem;
            }
            .tutorial-card {
                padding: 0.9rem 0.95rem;
                border-radius: 14px;
            }
            .tutorial-card h3 {
                font-size: 0.98rem;
            }
            .tutorial-card p,
            .tutorial-step,
            .tutorial-highlight {
                font-size: 0.92rem;
            }
        }
        </style>
        <div class="tutorial-hero">
            <h1>📘 Tutorial do Sistema</h1>
            <p>
                Aqui você entende o sistema de forma simples: o que ele faz, como funciona por dentro
                e como usar cada configuração sem precisar ter conhecimento técnico.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="tutorial-highlight">
            <strong>Resumo rápido:</strong> você informa uma URL, o robô abre o site, entende o conteúdo visível,
            organiza os dados e salva tudo em arquivos prontos para consulta, documentação ou uso em IA.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div class="tutorial-card">
                <h3>🌐 O que ele captura</h3>
                <p>Páginas únicas ou várias páginas internas do mesmo site, inclusive conteúdos dinâmicos.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="tutorial-card">
                <h3>📦 O que ele entrega</h3>
                <p>Arquivos em Markdown, JSON, manifesto da extração, chunks RAG e pacote ZIP para download.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="tutorial-card">
                <h3>🤝 Para quem serve</h3>
                <p>Usuários iniciantes, equipes de conteúdo, documentação, automação e projetos com IA.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Navegação do Tutorial")
    aba_visao, aba_config, aba_resultados, aba_boas_praticas = st.tabs(
        ["Visão Geral", "Configurações", "Resultados", "Boas Práticas"]
    )

    with aba_visao:
        st.subheader("O que este sistema faz")
        st.write(
            """
            O sistema transforma o conteúdo de sites em arquivos organizados. Ele pode trabalhar em dois modos:
            capturar apenas uma página específica ou navegar por várias páginas do mesmo site.
            """
        )

        st.subheader("Como o processo acontece")
        passos = [
            ("1. Você informa a URL", "O sistema recebe o endereço da página ou do site que você quer extrair."),
            ("2. A URL é validada", "O robô confirma se o link está em um formato aceitável antes de começar."),
            ("3. O navegador automatizado abre o site", "Ele simula um acesso real para conseguir ler páginas modernas."),
            ("4. O sistema faz a rolagem automática", "Isso ajuda a carregar conteúdos dinâmicos que aparecem só depois do scroll."),
            ("5. O conteúdo é convertido", "A página vira texto estruturado em formatos como Markdown e JSON."),
            ("6. O crawler pode seguir novos links", "Se você ativar o site completo, ele descobre e visita páginas internas."),
            ("7. Os arquivos são organizados", "Tudo vai para uma pasta de saída, pronto para consulta e download."),
            ("8. O histórico é salvo", "A execução fica registrada para você acompanhar o que já foi processado."),
        ]
        for titulo, descricao in passos:
            st.markdown(
                f"""
                <div class="tutorial-step">
                    <strong>{titulo}</strong><br>
                    {descricao}
                </div>
                """,
                unsafe_allow_html=True,
            )

    with aba_config:
        st.subheader("O que significa cada configuração")
        cards_config = [
            ("🧭 Modo de Extração", "Escolhe se o sistema vai capturar uma única página ou fazer um rastreamento por várias páginas internas."),
            ("📄 Limite Máximo de Páginas", "Define até quantas páginas o robô pode visitar no modo crawler."),
            ("🪜 Profundidade Máxima", "Controla o quanto o robô pode se afastar da URL inicial ao seguir links."),
            ("🗂️ Formato de Saída", "Permite salvar os resultados em Markdown, JSON ou nos dois formatos."),
            ("🎯 Incluir apenas caminhos", "Restringe a coleta a partes específicas do site, como `/blog` ou `/docs`."),
            ("🚫 Ignorar caminhos", "Impede a visita a áreas que você não quer extrair, como `/admin` e `/login`."),
            ("🧱 Ignorar arquivos não HTML", "Evita que o crawler tente abrir imagens, PDFs, vídeos e outros arquivos que não são páginas."),
            ("🤖 Saída para RAG", "Gera um arquivo com blocos de texto prontos para chatbots, IA e busca semântica."),
        ]
        for indice in range(0, len(cards_config), 2):
            col_a, col_b = st.columns(2)
            titulo_a, texto_a = cards_config[indice]
            with col_a:
                st.markdown(
                    f"""
                    <div class="tutorial-card">
                        <h3>{titulo_a}</h3>
                        <p>{texto_a}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            if indice + 1 < len(cards_config):
                titulo_b, texto_b = cards_config[indice + 1]
                with col_b:
                    st.markdown(
                        f"""
                        <div class="tutorial-card">
                            <h3>{titulo_b}</h3>
                            <p>{texto_b}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    with aba_resultados:
        st.subheader("O que você acompanha durante a extração")
        st.write(
            """
            Enquanto o robô trabalha, a interface mostra status, URL atual, barra de progresso, contagem de páginas,
            quantidade de arquivos, erros encontrados e logs em tempo real.
            """
        )

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(
                """
                <div class="tutorial-card">
                    <h3>📡 Monitoramento ao vivo</h3>
                    <p>Você vê o que o robô está fazendo sem precisar abrir terminal ou acompanhar logs técnicos.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown(
                """
                <div class="tutorial-card">
                    <h3>🧾 Histórico salvo</h3>
                    <p>Cada execução fica registrada para consulta, comparação e controle do trabalho já realizado.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.subheader("Arquivos gerados no final")
        arquivos_saida = [
            ("Markdown (.md)", "Ideal para leitura humana, documentação e bases de conhecimento."),
            ("JSON (.json)", "Ideal para integrações, automações e uso por outros sistemas."),
            ("manifest.json", "Resumo geral da execução com informações importantes da extração."),
            ("rag_chunks.jsonl", "Arquivo opcional com blocos de texto preparados para uso em IA e RAG."),
            ("ZIP dos resultados", "Pacote pronto para baixar tudo de uma vez pela interface."),
        ]
        for nome, descricao in arquivos_saida:
            st.markdown(
                f"""
                <div class="tutorial-step">
                    <strong>{nome}</strong><br>
                    {descricao}
                </div>
                """,
                unsafe_allow_html=True,
            )

    with aba_boas_praticas:
        st.subheader("Como usar no dia a dia")
        st.write(
            """
            Para a maioria dos casos, o melhor caminho é começar pequeno, validar o resultado e só depois ampliar
            o número de páginas ou a profundidade do crawler.
            """
        )

        dicas_col1, dicas_col2 = st.columns(2)
        with dicas_col1:
            st.markdown(
                """
                <div class="tutorial-card">
                    <h3>✅ Boas práticas</h3>
                    <p>
                        Comece com poucas páginas, use filtros quando o site for grande e ative o RAG
                        quando o objetivo for IA, chatbot ou busca semântica.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with dicas_col2:
            st.markdown(
                """
                <div class="tutorial-card">
                    <h3>⚠️ O que considerar</h3>
                    <p>
                        Quanto maior o site, maior será o tempo de processamento. Áreas privadas ou protegidas
                        só podem ser capturadas se estiverem realmente acessíveis.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.subheader("Fluxo recomendado")
        fluxo_recomendado = [
            "Cole a URL do site.",
            "Escolha entre página única ou site completo.",
            "Defina formato de saída e, se necessário, filtros.",
            "Clique em `INICIAR EXTRAÇÃO`.",
            "Acompanhe o progresso e os logs.",
            "Baixe o ZIP ou abra a pasta com os resultados.",
        ]
        for item in fluxo_recomendado:
            st.markdown(
                f"""
                <div class="tutorial-step">
                    {item}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.success("Quando quiser operar o sistema, volte ao menu `Configurações` na lateral.")

def renderizar_pagina_principal():
    """Renderiza a apresentacao visual da tela principal."""
    st.markdown(
        """
        <style>
        :root {
            --pixelc-navy: #0f2740;
            --pixelc-blue: #1e5b8f;
            --pixelc-sky: #57aee6;
            --pixelc-ice: #eef7ff;
            --pixelc-line: #d7e7f6;
            --pixelc-text: #26455f;
        }
        .home-hero {
            position: relative;
            overflow: hidden;
            padding: 1.8rem;
            border-radius: 22px;
            background: linear-gradient(135deg, var(--pixelc-navy) 0%, var(--pixelc-blue) 58%, var(--pixelc-sky) 100%);
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 18px 38px rgba(18, 57, 91, 0.2);
        }
        .home-hero::before {
            content: "";
            position: absolute;
            width: 220px;
            height: 220px;
            right: -60px;
            top: -90px;
            background: radial-gradient(circle, rgba(255,255,255,0.28) 0%, rgba(255,255,255,0) 70%);
            border-radius: 50%;
        }
        .home-hero::after {
            content: "";
            position: absolute;
            width: 180px;
            height: 180px;
            left: -40px;
            bottom: -70px;
            background: radial-gradient(circle, rgba(255,255,255,0.16) 0%, rgba(255,255,255,0) 72%);
            border-radius: 50%;
        }
        .home-badge {
            display: inline-block;
            padding: 0.35rem 0.8rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.16);
            border: 1px solid rgba(255, 255, 255, 0.24);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            margin-bottom: 0.85rem;
        }
        .home-hero h1 {
            margin: 0;
            font-size: 2.15rem;
        }
        .home-hero p {
            margin: 0.6rem 0 0 0;
            line-height: 1.6;
            font-size: 1.02rem;
            max-width: 760px;
        }
        .home-brand-row {
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }
        .home-brand-pill {
            padding: 0.5rem 0.85rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.18);
            font-size: 0.88rem;
        }
        .home-card {
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            border: 1px solid var(--pixelc-line);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            box-shadow: 0 10px 24px rgba(18, 57, 91, 0.08);
            height: 100%;
        }
        .home-card h3 {
            margin: 0 0 0.4rem 0;
            color: var(--pixelc-navy);
            font-size: 1.02rem;
        }
        .home-card p {
            margin: 0;
            color: var(--pixelc-text);
            line-height: 1.55;
            font-size: 0.95rem;
        }
        .home-section {
            background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
            border: 1px solid #deebf7;
            border-radius: 20px;
            padding: 1.1rem 1.2rem;
            box-shadow: 0 10px 22px rgba(18, 57, 91, 0.06);
            margin: 1rem 0;
        }
        .home-section h2 {
            margin-top: 0;
            color: var(--pixelc-navy);
            font-size: 1.2rem;
        }
        .home-highlight {
            background: var(--pixelc-ice);
            border: 1px solid #cfe4f7;
            border-radius: 14px;
            padding: 0.95rem 1rem;
            margin-top: 0.8rem;
            color: #21425b;
        }
        .home-metrics {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.8rem;
            margin: 1rem 0 0 0;
        }
        .home-metric {
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 16px;
            padding: 0.9rem 1rem;
        }
        .home-metric strong {
            display: block;
            font-size: 1.25rem;
            margin-bottom: 0.2rem;
        }
        .home-metric span {
            font-size: 0.85rem;
            opacity: 0.92;
        }
        .pixelc-signature {
            margin-top: 1rem;
            padding: 0.95rem 1rem;
            border-radius: 16px;
            background: linear-gradient(180deg, #f8fbff 0%, #f0f7ff 100%);
            border: 1px solid var(--pixelc-line);
            color: var(--pixelc-text);
        }
        .ux-panel {
            background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
            border: 1px solid #deebf7;
            border-radius: 20px;
            padding: 1.15rem 1.2rem;
            box-shadow: 0 10px 22px rgba(18, 57, 91, 0.06);
            margin: 1rem 0;
        }
        .ux-panel h2 {
            margin: 0 0 0.35rem 0;
            color: var(--pixelc-navy);
            font-size: 1.18rem;
        }
        .ux-panel p {
            margin: 0;
            color: var(--pixelc-text);
            line-height: 1.55;
        }
        .ux-tip {
            margin-top: 0.9rem;
            background: #f4f9ff;
            border: 1px solid #d7e7f6;
            border-radius: 14px;
            padding: 0.9rem 1rem;
            color: var(--pixelc-text);
        }
        .ux-empty {
            text-align: center;
            padding: 1.4rem 1rem;
            border-radius: 18px;
            background: linear-gradient(180deg, #fbfdff 0%, #f4f9ff 100%);
            border: 1px dashed #cfe2f5;
            color: var(--pixelc-text);
        }
        .ux-empty strong {
            display: block;
            margin-bottom: 0.35rem;
            color: var(--pixelc-navy);
        }
        .ux-chip-row {
            display: flex;
            gap: 0.65rem;
            flex-wrap: wrap;
            margin-top: 0.9rem;
        }
        .ux-chip {
            padding: 0.48rem 0.82rem;
            border-radius: 999px;
            background: #eef7ff;
            border: 1px solid #d5e6f6;
            color: var(--pixelc-navy);
            font-size: 0.88rem;
            font-weight: 600;
        }
        .ux-mini-metrics {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin: 0.95rem 0 1rem 0;
        }
        .ux-mini-card {
            background: linear-gradient(180deg, #ffffff 0%, #f6fbff 100%);
            border: 1px solid #d8e7f6;
            border-radius: 18px;
            padding: 0.95rem 1rem;
            box-shadow: 0 10px 22px rgba(18, 57, 91, 0.06);
        }
        .ux-mini-card strong {
            display: block;
            font-size: 1.4rem;
            color: var(--pixelc-navy);
            margin-bottom: 0.2rem;
        }
        .ux-mini-card span {
            color: var(--pixelc-text);
            font-size: 0.9rem;
        }
        .ux-history-panel {
            background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
            border: 1px solid #deebf7;
            border-radius: 22px;
            padding: 1.15rem 1.2rem 1.25rem 1.2rem;
            box-shadow: 0 12px 26px rgba(18, 57, 91, 0.06);
            margin-top: 0.75rem;
        }
        .ux-history-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
            margin-bottom: 0.4rem;
        }
        .ux-history-header h3 {
            margin: 0;
            color: var(--pixelc-navy);
            font-size: 1.18rem;
        }
        .ux-history-header p {
            margin: 0.3rem 0 0 0;
            color: var(--pixelc-text);
            line-height: 1.5;
            font-size: 0.95rem;
        }
        .ux-history-badge {
            padding: 0.46rem 0.82rem;
            border-radius: 999px;
            background: #eef7ff;
            border: 1px solid #d4e5f6;
            color: var(--pixelc-navy);
            font-size: 0.82rem;
            font-weight: 700;
            white-space: nowrap;
        }
        .ux-history-actions {
            margin-top: 0.4rem;
            margin-bottom: 0.35rem;
        }
        .ux-confirm {
            margin: 0.9rem 0 1rem 0;
            padding: 1rem 1.05rem;
            border-radius: 18px;
            background: linear-gradient(180deg, #fff8f4 0%, #fff2ea 100%);
            border: 1px solid #ffd6c2;
            box-shadow: 0 10px 22px rgba(168, 85, 27, 0.08);
            color: #6b3f21;
        }
        .ux-confirm strong {
            display: block;
            margin-bottom: 0.3rem;
            color: #8f3f10;
            font-size: 1rem;
        }
        @media (max-width: 900px) {
            .home-metrics {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        @media (max-width: 768px) {
            .home-hero {
                padding: 1.2rem;
                border-radius: 18px;
            }
            .home-hero h1 {
                font-size: 1.55rem;
            }
            .home-hero p {
                font-size: 0.94rem;
            }
            .home-section,
            .ux-panel,
            .home-card,
            .pixelc-signature {
                border-radius: 16px;
                padding-left: 0.95rem;
                padding-right: 0.95rem;
            }
            .home-metrics {
                grid-template-columns: 1fr;
            }
            .home-brand-pill,
            .ux-chip {
                font-size: 0.82rem;
            }
            .ux-mini-metrics {
                grid-template-columns: 1fr;
            }
            .ux-history-panel {
                border-radius: 18px;
                padding-left: 0.95rem;
                padding-right: 0.95rem;
            }
            .ux-history-header {
                flex-direction: column;
            }
            .ux-history-badge {
                white-space: normal;
            }
        }
        </style>
        <div class="home-hero">
            <div class="home-badge">PIXELC TECH • WEB EXTRACTION PLATFORM</div>
            <h1>🔓 Docling App - Pixelc Tech</h1>
            <p>
                Extraia conteúdo de sites de forma visual, organizada e pronta para documentação,
                automações e projetos com IA. Você escolhe a URL, o robô faz o trabalho pesado
                e o sistema entrega tudo estruturado.
            </p>
            <div class="home-brand-row">
                <div class="home-brand-pill">Markdown + JSON</div>
                <div class="home-brand-pill">Crawler Inteligente</div>
                <div class="home-brand-pill">Pronto para RAG</div>
                <div class="home-brand-pill">Histórico Local</div>
            </div>
            <div class="home-metrics">
                <div class="home-metric">
                    <strong>1 clique</strong>
                    <span>para iniciar a captura</span>
                </div>
                <div class="home-metric">
                    <strong>2 modos</strong>
                    <span>página única ou site completo</span>
                </div>
                <div class="home-metric">
                    <strong>4 saídas</strong>
                    <span>MD, JSON, manifesto e RAG</span>
                </div>
                <div class="home-metric">
                    <strong>100%</strong>
                    <span>foco em clareza operacional</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="home-section">
            <h2>Comece por aqui</h2>
            <p>
                Informe a URL do site, ajuste as configurações na lateral e clique em
                <strong>INICIAR EXTRAÇÃO</strong>. O sistema vai validar o link, abrir a página,
                capturar o conteúdo e organizar os resultados automaticamente.
            </p>
            <div class="home-highlight">
                <strong>Dica:</strong> se for sua primeira vez, comece com uma página única ou com poucas páginas
                no crawler para validar o resultado com mais rapidez.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div class="home-card">
                <h3>🌐 Captura inteligente</h3>
                <p>Funciona bem com sites modernos, incluindo páginas dinâmicas que precisam de rolagem para carregar.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="home-card">
                <h3>📦 Saída organizada</h3>
                <p>Os resultados podem ser salvos em Markdown, JSON, manifesto da extração e arquivos prontos para RAG.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="home-card">
                <h3>📊 Acompanhamento claro</h3>
                <p>Você acompanha progresso, logs, arquivos gerados, erros e histórico recente sem sair da interface.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="pixelc-signature">
            <strong>Assinatura Pixelc Tech:</strong> a interface foi pensada para unir clareza,
            velocidade operacional e preparação real para fluxos com IA, documentação e automações.
        </div>
        """,
        unsafe_allow_html=True,
    )

def renderizar_resumo_configuracao(
    modo_extracao: str,
    output_format: str,
    max_pages: int,
    max_depth: int,
    gerar_rag_artifacts: bool,
    include_paths: list[str],
    exclude_paths: list[str],
):
    """Exibe um resumo rápido das configurações ativas."""
    limite_real = 1 if modo_extracao == "Página Única (Apenas o Link)" else max_pages
    profundidade_real = 0 if modo_extracao == "Página Única (Apenas o Link)" else max_depth
    rag_label = "RAG ativado" if gerar_rag_artifacts else "RAG desativado"

    st.markdown(
        """
        <div class="ux-panel">
            <h2>Resumo das Configurações Atuais</h2>
            <p>Veja rapidamente como o robô está preparado para esta execução antes de iniciar o processo.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="ux-chip-row">
            <div class="ux-chip">{modo_extracao}</div>
            <div class="ux-chip">Formato: {output_format}</div>
            <div class="ux-chip">Páginas: {limite_real}</div>
            <div class="ux-chip">Profundidade: {profundidade_real}</div>
            <div class="ux-chip">{rag_label}</div>
            <div class="ux-chip">Inclusões: {len(include_paths)}</div>
            <div class="ux-chip">Exclusões: {len(exclude_paths)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def renderizar_confirmacao_acao(
    state_key: str,
    titulo: str,
    mensagem: str,
    confirm_label: str = "✅ Confirmar",
    cancel_label: str = "Cancelar",
):
    """Renderiza um painel de confirmação reutilizável para ações sensíveis."""
    if not st.session_state.get(state_key, False):
        return None

    st.markdown(
        f"""
        <div class="ux-confirm">
            <strong>{titulo}</strong>
            {mensagem}
        </div>
        """,
        unsafe_allow_html=True,
    )

    confirmar_col1, confirmar_col2 = st.columns(2)
    with confirmar_col1:
        if st.button(confirm_label, key=f"{state_key}_confirmar"):
            st.session_state[state_key] = False
            return "confirmado"
    with confirmar_col2:
        if st.button(cancel_label, key=f"{state_key}_cancelar"):
            st.session_state[state_key] = False
            return "cancelado"

    return None

def main():
    st.set_page_config(
        page_title="Docling App - Extrator Web",
        page_icon="🔓",
        layout="wide"
    )

    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f7fbff 0%, #eef6ff 100%);
            border-right: 1px solid #d7e7f6;
        }
        [data-testid="stSidebar"] > div:first-child {
            background: linear-gradient(180deg, #f7fbff 0%, #eef6ff 100%);
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #12395b;
        }
        [data-testid="stSidebar"] .stRadio > label,
        [data-testid="stSidebar"] .stCheckbox > label,
        [data-testid="stSidebar"] .stNumberInput label,
        [data-testid="stSidebar"] .stTextArea label {
            color: #284760;
            font-weight: 600;
        }
        [data-testid="stSidebar"] .stAlert {
            border-radius: 14px;
            border: 1px solid #cfe4f7;
            background: #f5faff;
        }
        [data-testid="stSidebar"] [data-baseweb="radio"] > div {
            background: rgba(255, 255, 255, 0.65);
            border: 1px solid #d8e6f5;
            border-radius: 14px;
            padding: 0.35rem;
        }
        [data-testid="stSidebar"] [data-baseweb="radio"] label {
            border-radius: 10px;
            padding: 0.2rem 0.3rem;
        }
        [data-testid="stSidebar"] .stTextArea textarea,
        [data-testid="stSidebar"] .stNumberInput input {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid #d3e3f3;
            box-shadow: inset 0 1px 2px rgba(18, 57, 91, 0.04);
        }
        [data-testid="stSidebar"] hr {
            border-color: #dbe9f7;
        }
        .sidebar-brand {
            padding: 1rem 1rem 0.95rem 1rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #0f2740 0%, #1e5b8f 60%, #57aee6 100%);
            color: white;
            box-shadow: 0 14px 28px rgba(15, 39, 64, 0.18);
            margin-bottom: 1rem;
        }
        .sidebar-brand strong {
            display: block;
            font-size: 1rem;
            margin-bottom: 0.25rem;
        }
        .sidebar-brand span {
            font-size: 0.86rem;
            line-height: 1.5;
            opacity: 0.95;
        }
        .sidebar-menu-caption {
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            color: #4a7398;
            text-transform: uppercase;
            margin: 0.25rem 0 0.45rem 0;
        }
        .stButton>button,
        .stDownloadButton>button {
            width: 100%;
            background-color: #FF4B4B;
            color: white;
            font-weight: bold;
            border-radius: 12px;
            border: none;
            padding: 0.8rem 1rem;
            box-shadow: 0 10px 22px rgba(255, 75, 75, 0.18);
        }
        .status-box {
            padding: 10px;
            border-radius: 5px;
            background-color: #f0f2f6;
            margin-bottom: 10px;
        }
        .stTextInput > div > div,
        .stTextArea textarea,
        .stNumberInput input {
            border-radius: 12px;
        }
        @media (max-width: 768px) {
            .block-container {
                padding-top: 1rem;
                padding-left: 0.8rem;
                padding-right: 0.8rem;
            }
            [data-testid="stHorizontalBlock"] {
                flex-direction: column;
                gap: 0.75rem;
            }
            [data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
            }
            [data-testid="stSidebar"] {
                border-right: none;
            }
            .sidebar-brand {
                padding: 0.9rem;
                border-radius: 16px;
            }
            .sidebar-brand strong {
                font-size: 0.95rem;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <strong>Pixelc Tech</strong>
                <span>
                    Plataforma de extração web com foco em clareza operacional,
                    documentação estruturada e preparação para IA.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.header("⚙️ Configurações do Robô")
        st.markdown("<div class='sidebar-menu-caption'>Navegação</div>", unsafe_allow_html=True)
        menu_sidebar = st.radio(
            "Menu",
            options=["Configurações", "Tutorial"],
            index=0,
            label_visibility="collapsed"
        )

        configuracoes = None
        if menu_sidebar == "Configurações":
            configuracoes = renderizar_sidebar_configuracoes()
        else:
            st.write("---")
            st.subheader("Tutorial")
            st.write(
                "Abra o tutorial na área principal para entender cada parte do sistema de forma simples."
            )
            st.caption(
                "Você pode voltar para `Configurações` a qualquer momento para iniciar uma nova extração."
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

    if menu_sidebar == "Tutorial":
        renderizar_tutorial()
        return

    renderizar_pagina_principal()
    st.caption(
        "Desenvolvido por [Pixelc Tech](https://www.pixelctech.com.br) | "
        "Repositório: [GitHub](https://github.com/pixelctechia/Docling-App)"
    )

    modo_extracao = configuracoes["modo_extracao"]
    max_pages = configuracoes["max_pages"]
    max_depth = configuracoes["max_depth"]
    output_format = configuracoes["output_format"]
    include_paths_text = configuracoes["include_paths_text"]
    exclude_paths_text = configuracoes["exclude_paths_text"]
    ignorar_arquivos_binarios = configuracoes["ignorar_arquivos_binarios"]
    gerar_rag_artifacts = configuracoes["gerar_rag_artifacts"]
    rag_chunk_size = configuracoes["rag_chunk_size"]
    rag_chunk_overlap = configuracoes["rag_chunk_overlap"]

    st.markdown("## 🚀 Nova Extração")
    st.write("Preencha a URL abaixo e inicie o processamento com as configurações escolhidas na lateral.")

    url_input = st.text_input("🔗 Cole a URL do Website aqui:", placeholder="https://exemplo.com.br")
    include_paths = parse_textarea_paths(include_paths_text)
    exclude_paths = parse_textarea_paths(exclude_paths_text)
    renderizar_resumo_configuracao(
        modo_extracao=modo_extracao,
        output_format=output_format,
        max_pages=max_pages,
        max_depth=max_depth,
        gerar_rag_artifacts=gerar_rag_artifacts,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
    )

    st.markdown(
        """
        <div class="ux-panel">
            <h2>Área de Execução</h2>
            <p>
                Cole a URL, revise o resumo das configurações e clique no botão para iniciar.
                O sistema vai mostrar o andamento da extração e entregar os arquivos logo abaixo.
            </p>
            <div class="ux-tip">
                <strong>Dica rápida:</strong> se esta for sua primeira vez, use o menu <strong>Tutorial</strong>
                na lateral para entender cada parte do sistema de forma simples.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        btn_iniciar = st.button("🚀 INICIAR EXTRAÇÃO", type="primary")
    with col2:
        st.caption("A extração vai respeitar exatamente as opções definidas na lateral.")

    if not url_input:
        st.markdown(
            """
            <div class="ux-empty">
                <strong>Aguardando uma URL para começar</strong>
                Cole um endereço de site no campo acima para liberar o fluxo de extração.
            </div>
            """,
            unsafe_allow_html=True,
        )

    if btn_iniciar and url_input:
        url_ok, url_processada, erro_url = validar_url(url_input)
        if not url_ok:
            st.error(f"❌ {erro_url}")
            st.stop()

        limite_real = 1 if modo_extracao == "Página Única (Apenas o Link)" else max_pages
        profundidade_real = 0 if modo_extracao == "Página Única (Apenas o Link)" else max_depth
        ignored_extensions = None if ignorar_arquivos_binarios else set()

        on_progress, on_log, obter_estado_execucao = criar_monitor_de_progresso(limite_real)
        inicio_execucao = datetime.now()
        inicio_monotonic = time.perf_counter()

        try:
            arquivos = processar_url(
                url_processada,
                output_format,
                limite_real,
                max_depth=profundidade_real,
                include_paths=include_paths,
                exclude_paths=exclude_paths,
                ignored_extensions=ignored_extensions,
                generate_rag_artifacts=gerar_rag_artifacts,
                rag_chunk_size=rag_chunk_size,
                rag_chunk_overlap=rag_chunk_overlap,
                on_progress=on_progress,
                on_log=on_log
            )

            estado_execucao = obter_estado_execucao()
            fim_execucao = datetime.now()
            duracao_execucao = round(time.perf_counter() - inicio_monotonic, 2)
            caminho_primeiro_arquivo = arquivos[0] if arquivos else ""
            pasta_destino = (
                Path(caminho_primeiro_arquivo).parent
                if caminho_primeiro_arquivo
                else Path(estado_execucao["pasta_saida"]) if estado_execucao["pasta_saida"] else ""
            )

            add_task(
                url=url_processada,
                output_format=output_format,
                status="Sucesso",
                result_path=str(pasta_destino),
                extraction_mode=modo_extracao,
                pages_processed=estado_execucao["processadas"],
                files_generated=estado_execucao["arquivos"],
                errors_count=estado_execucao["erros"],
                started_at=inicio_execucao,
                finished_at=fim_execucao,
                duration_seconds=duracao_execucao
            )

            st.success(
                "✅ Processamento Concluído! "
                f"{estado_execucao['processadas']} páginas processadas e "
                f"{estado_execucao['arquivos']} arquivos gerados."
            )
            st.caption(
                f"URL validada: `{url_processada}` | Profundidade: `{profundidade_real}` | "
                f"Filtros de inclusão: `{len(include_paths)}` | Filtros de exclusão: `{len(exclude_paths)}` | "
                f"Chunks RAG: `{estado_execucao['rag_chunks']}`"
            )

            if pasta_destino:
                st.markdown(f"**📂 Arquivos salvos em:** `{pasta_destino}`")
                zip_bytes = criar_zip_em_memoria(Path(pasta_destino))
                acao_col1, acao_col2 = st.columns(2)
                with acao_col1:
                    st.download_button(
                        "⬇️ Baixar ZIP dos Resultados",
                        data=zip_bytes,
                        file_name=f"{Path(pasta_destino).name}.zip",
                        mime="application/zip"
                    )
                with acao_col2:
                    if st.button("📂 Abrir Pasta dos Arquivos"):
                        abrir_pasta_local(pasta_destino)

        except ProcessorError as e:
            st.error(f"❌ Erro no Processamento: {str(e)}")
            estado_execucao = obter_estado_execucao()
            fim_execucao = datetime.now()
            duracao_execucao = round(time.perf_counter() - inicio_monotonic, 2)
            add_task(
                url=url_processada,
                output_format=output_format,
                status="Falha",
                result_path=estado_execucao["pasta_saida"],
                extraction_mode=modo_extracao,
                pages_processed=estado_execucao["processadas"],
                files_generated=estado_execucao["arquivos"],
                errors_count=estado_execucao["erros"],
                error_message=str(e),
                started_at=inicio_execucao,
                finished_at=fim_execucao,
                duration_seconds=duracao_execucao
            )
        except Exception as e:
            st.error(f"❌ Erro Inesperado: {str(e)}")
            estado_execucao = obter_estado_execucao()
            fim_execucao = datetime.now()
            duracao_execucao = round(time.perf_counter() - inicio_monotonic, 2)
            add_task(
                url=url_processada,
                output_format=output_format,
                status="Falha",
                result_path=estado_execucao["pasta_saida"],
                extraction_mode=modo_extracao,
                pages_processed=estado_execucao["processadas"],
                files_generated=estado_execucao["arquivos"],
                errors_count=estado_execucao["erros"],
                error_message=str(e),
                started_at=inicio_execucao,
                finished_at=fim_execucao,
                duration_seconds=duracao_execucao
            )

    st.write("---")
    st.markdown("## 📜 Histórico Recente")
    st.markdown(
        """
        <div class="ux-history-panel">
            <div class="ux-history-header">
                <div>
                    <h3>Central de Histórico</h3>
                    <p>Consulte os registros recentes, exporte o histórico e gerencie os dados locais da aplicação.</p>
                </div>
                <div class="ux-history-badge">Painel operacional</div>
            </div>
        """,
        unsafe_allow_html=True,
    )
    try:
        df = get_recent_tasks()
        historico_vazio = df.empty
        outputs_com_arquivos = outputs_tem_conteudo()
        total_historico = len(df.index)
        total_diretorios_outputs, total_arquivos_outputs = obter_resumo_outputs()

        st.markdown(
            f"""
            <div class="ux-mini-metrics">
                <div class="ux-mini-card">
                    <strong>{total_historico}</strong>
                    <span>registro(s) no histórico</span>
                </div>
                <div class="ux-mini-card">
                    <strong>{total_diretorios_outputs}</strong>
                    <span>pasta(s) dentro de outputs</span>
                </div>
                <div class="ux-mini-card">
                    <strong>{total_arquivos_outputs}</strong>
                    <span>arquivo(s) dentro de outputs</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="ux-history-actions">', unsafe_allow_html=True)
        historico_col1, historico_col2, historico_col3, historico_col4 = st.columns(4)
        with historico_col1:
            st.download_button(
                "⬇️ Baixar Histórico CSV",
                data=df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"historico_docling_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                disabled=historico_vazio
            )
        with historico_col2:
            if st.button("🔄 Atualizar Histórico"):
                st.rerun()
        with historico_col3:
            if st.button("🗑️ Limpar Histórico", disabled=historico_vazio):
                st.session_state["confirmar_limpar_historico"] = True
        with historico_col4:
            if st.button("🧹 Limpar Arquivos Extraídos", disabled=not outputs_com_arquivos):
                st.session_state["confirmar_limpar_outputs"] = True
        st.markdown("</div>", unsafe_allow_html=True)

        acao_confirmacao = renderizar_confirmacao_acao(
            state_key="confirmar_limpar_historico",
            titulo="Confirmação necessária",
            mensagem=(
                "Esta ação vai apagar todo o histórico recente salvo localmente. "
                "Essa limpeza afeta apenas os registros do histórico e não remove "
                "os arquivos já extraídos nas pastas de saída."
            ),
            confirm_label="✅ Confirmar Limpeza",
            cancel_label="Cancelar",
        )
        if acao_confirmacao == "confirmado":
            if clear_tasks():
                st.success("Histórico limpo com sucesso.")
                st.rerun()
            else:
                st.error("Não foi possível limpar o histórico.")
        elif acao_confirmacao == "cancelado":
            st.rerun()

        acao_limpar_outputs = renderizar_confirmacao_acao(
            state_key="confirmar_limpar_outputs",
            titulo="Confirmação necessária",
            mensagem=(
                f"Esta ação vai remover todos os arquivos e pastas dentro de `{OUTPUTS_DIR}`. "
                "Os registros do histórico continuarão existindo, mas os resultados físicos das extrações "
                "serão apagados."
            ),
            confirm_label="✅ Confirmar Remoção",
            cancel_label="Cancelar",
        )
        if acao_limpar_outputs == "confirmado":
            sucesso_limpeza, total_removido = limpar_arquivos_extraidos()
            if sucesso_limpeza:
                st.success(f"Arquivos extraídos removidos com sucesso. Itens apagados: {total_removido}.")
                st.rerun()
            else:
                st.error("Não foi possível remover todos os arquivos extraídos.")
        elif acao_limpar_outputs == "cancelado":
            st.rerun()

        if df.empty:
            st.markdown(
                """
                <div class="ux-empty">
                    <strong>Nenhum histórico ainda</strong>
                    Assim que você concluir a primeira extração, os registros recentes aparecerão aqui.
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.dataframe(df, width="stretch")
    except Exception:
        st.markdown(
            """
            <div class="ux-empty">
                <strong>Não foi possível carregar o histórico</strong>
                Tente novamente em instantes. Se o problema continuar, vale revisar o banco local da aplicação.
            </div>
                """,
                unsafe_allow_html=True,
            )
    finally:
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

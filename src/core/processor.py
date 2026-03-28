"""
Processor Core - Docling App (Open Source Version)
Funcionalidades:
- Auto-Scroll agressivo para carregar sites React/Next.js.
- Headers reais para evitar bloqueios.
- Controle total: Página Única ou Crawler Recursivo.
"""
import time
import json
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse, urljoin, urlunparse
from datetime import datetime

# Bibliotecas do Motor
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from docling.document_converter import DocumentConverter
from src.core.artifacts import gerar_chunks_rag, salvar_chunks_rag, salvar_manifesto_extracao
from src.config.settings import (
    DEFAULT_IGNORED_EXTENSIONS,
    OUTPUTS_DIR,
    PLAYWRIGHT_PAGE_TIMEOUT_MS,
    PLAYWRIGHT_USER_AGENT,
    PLAYWRIGHT_VIEWPORT,
    RAG_DEFAULT_CHUNK_OVERLAP,
    RAG_DEFAULT_CHUNK_SIZE,
    RAG_DEFAULT_ENABLED,
)

class ProcessorError(Exception):
    pass

def _fragmento_parece_rota(fragmento: str) -> bool:
    """Detecta fragmentos usados como rota em SPAs, como #/blog ou #!/docs."""
    return fragmento.startswith("/") or fragmento.startswith("!/")

def preparar_url_entrada(url: str) -> str:
    """Higieniza a URL digitada pelo usuário e tenta completar o esquema quando fizer sentido."""
    url_limpa = url.strip()
    if not url_limpa:
        return ""

    parsed = urlparse(url_limpa)
    if parsed.scheme:
        return url_limpa

    if " " in url_limpa:
        return ""

    if "." in url_limpa or url_limpa.startswith(("localhost", "127.", "0.0.0.0")):
        return f"https://{url_limpa}"

    return ""

def _normalizar_url(url: str) -> str:
    """
    Normaliza URLs para comparação, fila e nomes de arquivos.
    Preserva fragmentos de rota usados em SPAs e remove âncoras simples/query strings.
    """
    parsed = urlparse(url.strip())

    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return ""

    path = parsed.path.rstrip("/")
    if parsed.netloc and not path:
        path = "/"
    fragment = parsed.fragment.strip()

    if _fragmento_parece_rota(fragment):
        fragment = fragment.lstrip("!").rstrip("/")
    else:
        fragment = ""

    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        path,
        "",
        "",
        fragment
    ))

def validar_url(url: str) -> tuple[bool, str, str]:
    """Valida a URL de entrada e devolve uma versão pronta para uso."""
    url_preparada = preparar_url_entrada(url)
    url_normalizada = _normalizar_url(url_preparada)

    if not url_normalizada:
        return False, "", "URL inválida. Informe um link http:// ou https:// válido."

    parsed = urlparse(url_normalizada)
    if not parsed.netloc:
        return False, "", "URL inválida. Não foi possível identificar o domínio informado."

    return True, url_normalizada, ""

def _normalizar_lista_caminhos(caminhos: list[str] | None) -> list[str]:
    """Padroniza filtros de caminho para comparação consistente."""
    if not caminhos:
        return []

    caminhos_normalizados = []
    for caminho in caminhos:
        item = caminho.strip()
        if not item:
            continue

        item = item.replace("\\", "/")
        if not item.startswith("/"):
            item = f"/{item}"
        caminhos_normalizados.append(item.rstrip("/") or "/")

    return caminhos_normalizados

def _extrair_caminho_logico(url: str) -> str:
    """Retorna o caminho principal da URL, combinando rota SPA quando existir."""
    parsed = urlparse(url)
    caminho = parsed.path.rstrip("/") or "/"
    fragmento = parsed.fragment.lstrip("!/").strip("/")

    if fragmento:
        if caminho == "/":
            return f"/{fragmento}"
        return f"{caminho}/{fragmento}"

    return caminho

def _link_tem_extensao_bloqueada(url: str, ignored_extensions: set[str] | None) -> bool:
    """Bloqueia arquivos que normalmente não representam páginas HTML úteis para crawl."""
    if not ignored_extensions:
        return False

    caminho = urlparse(url).path.lower()
    return any(caminho.endswith(extensao) for extensao in ignored_extensions)

def _link_passa_filtros(
    url: str,
    include_paths: list[str] | None,
    exclude_paths: list[str] | None,
    ignored_extensions: set[str] | None
) -> bool:
    """Aplica filtros de caminho antes de adicionar links à fila."""
    if _link_tem_extensao_bloqueada(url, ignored_extensions):
        return False

    caminho_logico = _extrair_caminho_logico(url)

    if include_paths and not any(caminho_logico.startswith(prefixo) for prefixo in include_paths):
        return False

    if exclude_paths and any(caminho_logico.startswith(prefixo) for prefixo in exclude_paths):
        return False

    return True

def _slug_da_url(url: str) -> str:
    """Limpa a URL para virar nome de arquivo."""
    parsed = urlparse(_normalizar_url(url))
    partes_slug = []

    path = parsed.path.strip("/")
    if path:
        partes_slug.append(path)

    fragment = parsed.fragment.lstrip("!/").strip("/")
    if fragment:
        partes_slug.append(fragment)

    if not partes_slug:
        return "home"

    base_slug = "_".join(partes_slug)
    # Substitui caracteres estranhos por underline
    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", base_slug)
    return slug[:100]  # Limita tamanho do nome

def _pasta_saida(base_url: str) -> Path:
    """Organiza por Domínio > Data/Hora."""
    domain = urlparse(base_url).netloc.replace("www.", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUTS_DIR / domain / timestamp
    path.mkdir(parents=True, exist_ok=True)
    return path

def _eh_link_interno(base_domain: str, url: str) -> bool:
    """
    Garante que o crawler fique dentro do site alvo.
    Não queremos baixar a internet inteira (Google, Facebook, etc).
    """
    try:
        url_normalizada = _normalizar_url(url)
        if not url_normalizada:
            return False

        p_url = urlparse(url_normalizada)
        netloc = p_url.netloc.replace("www.", "")
        return netloc == base_domain or netloc == ""
    except Exception:
        return False

def _auto_scroll_agressivo(page):
    """
    Rola a página até o final para disparar todos os gatilhos de carregamento.
    Essencial para capturar conteúdo que fica escondido (Lazy Load).
    """
    print("   [Scroll] Forçando carregamento total da página...")
    page.evaluate("""
        async () => {
            await new Promise((resolve) => {
                var totalHeight = 0;
                var distance = 400; // Pula 400px
                var timer = setInterval(() => {
                    var scrollHeight = document.body.scrollHeight;
                    window.scrollBy(0, distance);
                    totalHeight += distance;

                    // Continua até chegar no fim da página
                    if(totalHeight >= scrollHeight){
                        clearInterval(timer);
                        resolve();
                    }
                }, 100); // Rápido: a cada 100ms
            });
        }
    """)
    # Pausa dramática para garantir que as animações terminaram
    time.sleep(2)

def _criar_html_temporario(html_content: str) -> Path:
    """Cria um arquivo temporário único para o Docling processar."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".html",
        prefix="docling_",
        delete=False
    ) as arquivo_temp:
        arquivo_temp.write(html_content)
        return Path(arquivo_temp.name)

def _fechar_recurso_silenciosamente(recurso):
    """Fecha recursos do Playwright sem interromper o processamento."""
    if not recurso:
        return

    try:
        recurso.close()
    except Exception:
        pass

def _emitir_log(mensagem: str, on_log=None):
    """Envia logs tanto para o terminal quanto para a interface, quando disponível."""
    print(mensagem)
    if on_log:
        on_log(mensagem)

def _emitir_progresso(on_progress=None, **payload):
    """Dispara eventos de progresso para a interface sem acoplar o motor ao Streamlit."""
    if on_progress:
        on_progress(payload)

def processar_url(
    url: str,
    formato: str,
    max_pages: int = 10,
    max_depth: int = 2,
    include_paths: list[str] | None = None,
    exclude_paths: list[str] | None = None,
    ignored_extensions: set[str] | None = None,
    generate_rag_artifacts: bool = RAG_DEFAULT_ENABLED,
    rag_chunk_size: int = RAG_DEFAULT_CHUNK_SIZE,
    rag_chunk_overlap: int = RAG_DEFAULT_CHUNK_OVERLAP,
    on_progress=None,
    on_log=None
) -> list[str]:
    """
    Função Principal.
    Se max_pages == 1, roda modo Página Única.
    Se max_pages > 1, roda modo Crawler.
    """
    url_valida, url_normalizada, erro_url = validar_url(url)
    if not url_valida:
        raise ProcessorError(erro_url)

    url = url_normalizada

    if max_pages < 1:
        raise ProcessorError("O limite de páginas deve ser maior que zero.")

    if max_depth < 0:
        raise ProcessorError("A profundidade máxima não pode ser negativa.")

    if rag_chunk_size < 200:
        raise ProcessorError("O tamanho do chunk RAG deve ser de pelo menos 200 caracteres.")

    if rag_chunk_overlap < 0:
        raise ProcessorError("A sobreposição do chunk RAG não pode ser negativa.")

    if rag_chunk_overlap >= rag_chunk_size:
        raise ProcessorError("A sobreposição do chunk RAG deve ser menor que o tamanho do chunk.")

    include_paths = _normalizar_lista_caminhos(include_paths)
    exclude_paths = _normalizar_lista_caminhos(exclude_paths)
    ignored_extensions = ignored_extensions if ignored_extensions is not None else DEFAULT_IGNORED_EXTENSIONS

    domain_base = urlparse(url).netloc.replace("www.", "")
    out_dir = _pasta_saida(url)
    
    fila_urls = [(url, 0)]
    visitados = set()
    arquivos_gerados = []
    paginas_processadas = []
    rag_chunks = []
    
    _emitir_log("--- INICIANDO MOTOR ---", on_log)
    _emitir_log(f"Alvo: {domain_base}", on_log)
    _emitir_log(f"Modo: {'Página Única' if max_pages == 1 else 'Crawler Completo'}", on_log)
    _emitir_log(f"Limite: {max_pages} páginas", on_log)
    _emitir_log(f"Profundidade Máxima: {max_depth}", on_log)
    if generate_rag_artifacts:
        _emitir_log(
            f"RAG: chunks ativados (tamanho={rag_chunk_size}, overlap={rag_chunk_overlap})",
            on_log
        )
    _emitir_progresso(
        on_progress,
        event="startup",
        target=domain_base,
        mode="Página Única" if max_pages == 1 else "Crawler Completo",
        max_pages=max_pages,
        max_depth=max_depth,
        output_dir=str(out_dir)
    )
    
    with sync_playwright() as p:
        browser = None
        context = None

        try:
            # Lança o Chromium em modo Headless (invisível, mas funcional)
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=PLAYWRIGHT_USER_AGENT,
                viewport=PLAYWRIGHT_VIEWPORT
            )
            converter = DocumentConverter()

            while fila_urls and len(visitados) < max_pages:
                current_url, current_depth = fila_urls.pop(0)

                if current_url in visitados:
                    continue

                visitados.add(current_url)
                contador = len(visitados)
                _emitir_log(f"\n>>> Processando {contador}/{max_pages}: {current_url}", on_log)
                _emitir_progresso(
                    on_progress,
                    event="page_start",
                    current_page=contador,
                    max_pages=max_pages,
                    current_depth=current_depth,
                    current_url=current_url,
                    queue_size=len(fila_urls),
                    generated_files=len(arquivos_gerados)
                )

                page = None
                temp_path = None
                try:
                    page = context.new_page()

                    # 1. Acessar Site
                    page.goto(
                        current_url,
                        wait_until="domcontentloaded",
                        timeout=PLAYWRIGHT_PAGE_TIMEOUT_MS
                    )

                    # 2. Executar Auto-Scroll (Libera todo o conteúdo)
                    try:
                        _auto_scroll_agressivo(page)
                    except Exception as e:
                        _emitir_log(f"   [Aviso] Scroll falhou levemente, continuando: {e}", on_log)

                    # 3. Capturar HTML Renderizado (O que o usuário vê)
                    html_content = page.content()

                    # 4. Crawler: Buscar novos links (Só se o limite permitir)
                    # Se max_pages for 1, nem perdemos tempo procurando links.
                    if max_pages > 1 and current_depth < max_depth:
                        soup = BeautifulSoup(html_content, "html.parser")
                        links_novos = 0
                        for a_tag in soup.find_all("a", href=True):
                            link_raw = a_tag["href"]
                            # Resolve caminhos relativos (/contato -> https://site.com/contato)
                            full_link = _normalizar_url(urljoin(current_url, link_raw))
                            if not full_link:
                                continue

                            # Adiciona à fila se for interno e inédito
                            if (full_link not in visitados and
                                all(full_link != url_fila for url_fila, _ in fila_urls) and
                                _eh_link_interno(domain_base, full_link) and
                                _link_passa_filtros(full_link, include_paths, exclude_paths, ignored_extensions)):
                                fila_urls.append((full_link, current_depth + 1))
                                links_novos += 1
                        _emitir_log(f"   [Crawler] {links_novos} novos links adicionados à fila.", on_log)
                        _emitir_progresso(
                            on_progress,
                            event="links_discovered",
                            current_page=contador,
                            current_depth=current_depth,
                            current_url=current_url,
                            new_links=links_novos,
                            queue_size=len(fila_urls)
                        )
                    elif max_pages > 1:
                        _emitir_log("   [Crawler] Profundidade máxima atingida para esta página.", on_log)

                    # 5. Conversão Docling (O Coração do Sistema)
                    # Salva temp para garantir que o Docling leia o arquivo estático
                    temp_path = _criar_html_temporario(html_content)
                    result = converter.convert(str(temp_path))

                    # 6. Salvar Arquivos Finais
                    slug = _slug_da_url(current_url)
                    if slug == "home" and contador > 1:
                        slug = f"page_{contador}" # Evita sobrescrever home se houver redirect
                    arquivos_pagina = []

                    # Salvando JSON
                    if formato.lower() in ["json", "ambos", "both"]:
                        json_path = out_dir / f"{slug}.json"
                        dados = result.document.export_to_dict()
                        dados['metadata_extra'] = {
                            "url_origem": current_url,
                            "data_extracao": str(datetime.now())
                        }
                        json_path.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
                        arquivos_gerados.append(str(json_path))
                        arquivos_pagina.append(str(json_path))
                        _emitir_log(f"   [Salvo] JSON: {json_path.name}", on_log)

                    # Salvando Markdown
                    texto_md = ""
                    if formato.lower() in ["markdown", "ambos", "both"]:
                        md_path = out_dir / f"{slug}.md"
                        try:
                            texto_md = result.document.export_to_markdown()
                        except Exception:
                            texto_md = str(result.document) # Fallback

                        # Cabeçalho informativo
                        cabecalho = f"\n\n\n"
                        md_path.write_text(cabecalho + texto_md, encoding="utf-8")
                        arquivos_gerados.append(str(md_path))
                        arquivos_pagina.append(str(md_path))
                        _emitir_log(f"   [Salvo] Markdown: {md_path.name}", on_log)
                    else:
                        try:
                            texto_md = result.document.export_to_markdown()
                        except Exception:
                            texto_md = str(result.document)

                    paginas_processadas.append({
                        "url": current_url,
                        "slug": slug,
                        "depth": current_depth,
                        "files": arquivos_pagina,
                    })

                    if generate_rag_artifacts and texto_md.strip():
                        novos_chunks = gerar_chunks_rag(
                            texto_md,
                            source_url=current_url,
                            source_slug=slug,
                            chunk_size=rag_chunk_size,
                            chunk_overlap=rag_chunk_overlap
                        )
                        rag_chunks.extend(novos_chunks)

                    _emitir_progresso(
                        on_progress,
                        event="page_done",
                        current_page=contador,
                        max_pages=max_pages,
                        current_depth=current_depth,
                        current_url=current_url,
                        queue_size=len(fila_urls),
                        generated_files=len(arquivos_gerados)
                    )

                except Exception as e:
                    _emitir_log(f"   [ERRO] Falha ao processar {current_url}: {e}", on_log)
                    _emitir_progresso(
                        on_progress,
                        event="page_error",
                        current_page=contador,
                        max_pages=max_pages,
                        current_depth=current_depth,
                        current_url=current_url,
                        queue_size=len(fila_urls),
                        generated_files=len(arquivos_gerados),
                        error=str(e)
                    )
                    continue

                finally:
                    _fechar_recurso_silenciosamente(page)
                    if temp_path and temp_path.exists():
                        temp_path.unlink()

        finally:
            _fechar_recurso_silenciosamente(context)
            _fechar_recurso_silenciosamente(browser)

    if not arquivos_gerados:
        raise ProcessorError("Nenhum arquivo gerado. O site pode estar offline ou bloqueando totalmente.")

    manifest_path = salvar_manifesto_extracao(
        out_dir,
        {
            "base_url": url,
            "domain": domain_base,
            "output_format": formato,
            "pages_processed": len(paginas_processadas),
            "page_files_generated": len(arquivos_gerados),
            "rag_enabled": generate_rag_artifacts,
            "rag_chunks_generated": len(rag_chunks),
            "generated_at": str(datetime.now()),
            "pages": paginas_processadas,
        }
    )
    arquivos_gerados.append(str(manifest_path))
    _emitir_log(f"[Manifesto] {manifest_path.name} criado com resumo da extração.", on_log)

    if generate_rag_artifacts and rag_chunks:
        rag_path = salvar_chunks_rag(rag_chunks, out_dir)
        arquivos_gerados.append(str(rag_path))
        _emitir_log(f"[RAG] {rag_path.name} criado com {len(rag_chunks)} chunks.", on_log)

    _emitir_progresso(
        on_progress,
        event="completed",
        total_pages=len(visitados),
        generated_files=len(arquivos_gerados),
        rag_chunks=len(rag_chunks),
        output_dir=str(out_dir)
    )

    return arquivos_gerados

# Função auxiliar para manter compatibilidade
def crawl_internal_links(*args, **kwargs):
    return []

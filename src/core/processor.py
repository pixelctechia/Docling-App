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
from pathlib import Path
from urllib.parse import urlparse, urljoin
from datetime import datetime

# Bibliotecas do Motor
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from docling.document_converter import DocumentConverter

class ProcessorError(Exception):
    pass

# Configuração de Navegador "Power User"
REAL_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
# Viewport Full HD para garantir que o site carregue versão Desktop completa
VIEWPORT_CONFIG = {'width': 1920, 'height': 1080}

def _slug_da_url(url: str) -> str:
    """Limpa a URL para virar nome de arquivo."""
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if not path:
        return "home"
    # Substitui caracteres estranhos por underline
    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", path)
    return slug[:100]  # Limita tamanho do nome

def _pasta_saida(base_url: str) -> Path:
    """Organiza por Domínio > Data/Hora."""
    domain = urlparse(base_url).netloc.replace("www.", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path("outputs") / domain / timestamp
    path.mkdir(parents=True, exist_ok=True)
    return path

def _eh_link_interno(base_domain: str, url: str) -> bool:
    """
    Garante que o crawler fique dentro do site alvo.
    Não queremos baixar a internet inteira (Google, Facebook, etc).
    """
    try:
        p_url = urlparse(url)
        netloc = p_url.netloc.replace("www.", "")
        return netloc == base_domain or netloc == ""
    except:
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

def processar_url(url: str, formato: str, max_pages: int = 10) -> list[str]:
    """
    Função Principal.
    Se max_pages == 1, roda modo Página Única.
    Se max_pages > 1, roda modo Crawler.
    """
    # Normaliza URL inicial (remove barra final para padronizar)
    if url.endswith("/"):
        url = url[:-1]

    domain_base = urlparse(url).netloc.replace("www.", "")
    out_dir = _pasta_saida(url)
    
    fila_urls = [url]
    visitados = set()
    arquivos_gerados = []
    
    print(f"--- INICIANDO MOTOR ---")
    print(f"Alvo: {domain_base}")
    print(f"Modo: {'Página Única' if max_pages == 1 else 'Crawler Completo'}")
    print(f"Limite: {max_pages} páginas")
    
    with sync_playwright() as p:
        # Lança o Chromium em modo Headless (invisível, mas funcional)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=REAL_USER_AGENT, viewport=VIEWPORT_CONFIG)
        
        while fila_urls and len(visitados) < max_pages:
            current_url = fila_urls.pop(0)
            
            if current_url in visitados:
                continue
            
            visitados.add(current_url)
            contador = len(visitados)
            print(f"\n>>> Processando {contador}/{max_pages}: {current_url}")
            
            page = context.new_page()
            try:
                # 1. Acessar Site
                page.goto(current_url, wait_until="domcontentloaded", timeout=60000)
                
                # 2. Executar Auto-Scroll (Libera todo o conteúdo)
                try:
                    _auto_scroll_agressivo(page)
                except Exception as e:
                    print(f"   [Aviso] Scroll falhou levemente, continuando: {e}")

                # 3. Capturar HTML Renderizado (O que o usuário vê)
                html_content = page.content()
                
                # 4. Crawler: Buscar novos links (Só se o limite permitir)
                # Se max_pages for 1, nem perdemos tempo procurando links.
                if max_pages > 1:
                    soup = BeautifulSoup(html_content, "html.parser")
                    links_novos = 0
                    for a_tag in soup.find_all("a", href=True):
                        link_raw = a_tag["href"]
                        # Resolve caminhos relativos (/contato -> https://site.com/contato)
                        full_link = urljoin(current_url, link_raw)
                        # Remove lixo de URL (#ancora, ?query)
                        full_link = full_link.split("#")[0].split("?")[0]
                        if full_link.endswith("/"):
                            full_link = full_link[:-1]

                        # Adiciona à fila se for interno e inédito
                        if (full_link not in visitados and 
                            full_link not in fila_urls and 
                            _eh_link_interno(domain_base, full_link)):
                            fila_urls.append(full_link)
                            links_novos += 1
                    print(f"   [Crawler] {links_novos} novos links adicionados à fila.")

                page.close()

                # 5. Conversão Docling (O Coração do Sistema)
                # Salva temp para garantir que o Docling leia o arquivo estático
                temp_filename = f"temp_{contador}.html"
                Path(temp_filename).write_text(html_content, encoding="utf-8")
                
                # Conversor Padrão (Sem configs manuais para evitar erros de versão)
                converter = DocumentConverter()
                result = converter.convert(temp_filename)
                
                # 6. Salvar Arquivos Finais
                slug = _slug_da_url(current_url)
                if slug == "home" and contador > 1:
                    slug = f"page_{contador}" # Evita sobrescrever home se houver redirect

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
                    print(f"   [Salvo] JSON: {json_path.name}")

                # Salvando Markdown
                if formato.lower() in ["markdown", "ambos", "both"]:
                    md_path = out_dir / f"{slug}.md"
                    try:
                        texto_md = result.document.export_to_markdown()
                    except:
                        texto_md = str(result.document) # Fallback
                    
                    # Cabeçalho informativo
                    cabecalho = f"\n\n\n"
                    md_path.write_text(cabecalho + texto_md, encoding="utf-8")
                    arquivos_gerados.append(str(md_path))
                    print(f"   [Salvo] Markdown: {md_path.name}")

                # Limpeza do temp
                if Path(temp_filename).exists():
                    Path(temp_filename).unlink()

            except Exception as e:
                print(f"   [ERRO] Falha ao processar {current_url}: {e}")
                if 'page' in locals():
                    page.close()
                continue
                
        browser.close()

    if not arquivos_gerados:
        raise ProcessorError("Nenhum arquivo gerado. O site pode estar offline ou bloqueando totalmente.")

    return arquivos_gerados

# Função auxiliar para manter compatibilidade
def crawl_internal_links(*args, **kwargs):
    return []
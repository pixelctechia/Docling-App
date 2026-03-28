"""Artefatos auxiliares para exportação e preparação de dados para RAG."""
import io
import json
import re
import zipfile
from pathlib import Path


def _normalizar_bloco_markdown(bloco: str) -> str:
    """Remove ruído simples e padroniza espaçamento para chunking."""
    linhas = [linha.rstrip() for linha in bloco.splitlines()]
    linhas_validas = [linha for linha in linhas if linha.strip()]
    return "\n".join(linhas_validas).strip()


def _quebrar_texto_longo(texto: str, chunk_size: int, overlap: int) -> list[str]:
    """Divide um texto longo preservando uma sobreposição simples entre blocos."""
    texto = texto.strip()
    if not texto:
        return []

    if len(texto) <= chunk_size:
        return [texto]

    partes = []
    inicio = 0
    passo = max(chunk_size - overlap, 1)

    while inicio < len(texto):
        fim = min(inicio + chunk_size, len(texto))
        if fim < len(texto):
            corte = texto.rfind(" ", inicio, fim)
            if corte > inicio:
                fim = corte

        parte = texto[inicio:fim].strip()
        if parte:
            partes.append(parte)

        if fim >= len(texto):
            break
        inicio = max(fim - overlap, inicio + passo)

    return partes


def gerar_chunks_rag(
    markdown_text: str,
    source_url: str,
    source_slug: str,
    chunk_size: int = 1200,
    chunk_overlap: int = 150
) -> list[dict]:
    """Transforma markdown em chunks com metadados simples para ingestão em RAG."""
    blocos = re.split(r"\n\s*\n", markdown_text)
    blocos_limpos = [_normalizar_bloco_markdown(bloco) for bloco in blocos]
    blocos_limpos = [bloco for bloco in blocos_limpos if bloco]

    chunks = []
    buffer = []
    chunk_index = 0

    def flush_buffer():
        nonlocal buffer, chunk_index
        if not buffer:
            return

        texto = "\n\n".join(buffer).strip()
        for trecho in _quebrar_texto_longo(texto, chunk_size, chunk_overlap):
            chunks.append({
                "chunk_id": f"{source_slug}:{chunk_index}",
                "source_url": source_url,
                "source_slug": source_slug,
                "content": trecho,
                "char_count": len(trecho),
            })
            chunk_index += 1
        buffer = []

    for bloco in blocos_limpos:
        candidato = "\n\n".join(buffer + [bloco]).strip()
        if buffer and len(candidato) > chunk_size:
            flush_buffer()
        buffer.append(bloco)

    flush_buffer()
    return chunks


def salvar_chunks_rag(chunks: list[dict], output_dir: Path) -> Path:
    """Salva todos os chunks consolidados em um arquivo JSONL."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rag_path = output_dir / "rag_chunks.jsonl"
    conteudo = "\n".join(
        json.dumps(chunk, ensure_ascii=False) for chunk in chunks
    )
    rag_path.write_text(conteudo, encoding="utf-8")
    return rag_path


def salvar_manifesto_extracao(output_dir: Path, manifesto: dict) -> Path:
    """Salva um manifesto resumindo a extração e os arquivos produzidos."""
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifesto, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    return manifest_path


def criar_zip_em_memoria(output_dir: Path) -> bytes:
    """Compacta a pasta de saída em memória para download via interface."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for arquivo in sorted(output_dir.rglob("*")):
            if arquivo.is_file():
                zip_file.write(arquivo, arcname=arquivo.relative_to(output_dir))
    buffer.seek(0)
    return buffer.getvalue()

"""Presets de uso para orientar a configuracao da interface."""
from dataclasses import dataclass, field

from src.config.settings import (
    RAG_DEFAULT_CHUNK_OVERLAP,
    RAG_DEFAULT_CHUNK_SIZE,
    UI_DEFAULT_MAX_DEPTH,
    UI_DEFAULT_MAX_PAGES,
)


@dataclass(frozen=True)
class UsagePreset:
    """Representa um conjunto pronto de configuracoes para um objetivo real."""

    key: str
    label: str
    description: str
    extraction_mode: str
    output_format: str
    max_pages: int
    max_depth: int
    include_paths: tuple[str, ...] = field(default_factory=tuple)
    exclude_paths: tuple[str, ...] = field(default_factory=tuple)
    ignore_binary_files: bool = True
    generate_rag_artifacts: bool = True
    rag_chunk_size: int = RAG_DEFAULT_CHUNK_SIZE
    rag_chunk_overlap: int = RAG_DEFAULT_CHUNK_OVERLAP

    def to_ui_state(self) -> dict:
        """Converte o preset para um dicionario pronto para alimentar a UI."""
        return {
            "preset_key": self.key,
            "modo_extracao": self.extraction_mode,
            "output_format": self.output_format,
            "max_pages": self.max_pages,
            "max_depth": self.max_depth,
            "include_paths": list(self.include_paths),
            "exclude_paths": list(self.exclude_paths),
            "ignorar_arquivos_binarios": self.ignore_binary_files,
            "gerar_rag_artifacts": self.generate_rag_artifacts,
            "rag_chunk_size": self.rag_chunk_size,
            "rag_chunk_overlap": self.rag_chunk_overlap,
        }


DEFAULT_PRESET_KEY = "personalizado"

USAGE_PRESETS: dict[str, UsagePreset] = {
    "personalizado": UsagePreset(
        key="personalizado",
        label="Personalizado",
        description="Mantem o controle manual total para ajustar o robo do seu jeito.",
        extraction_mode="Página Única (Apenas o Link)",
        output_format="Ambos",
        max_pages=UI_DEFAULT_MAX_PAGES,
        max_depth=UI_DEFAULT_MAX_DEPTH,
        include_paths=(),
        exclude_paths=(),
        ignore_binary_files=True,
        generate_rag_artifacts=True,
        rag_chunk_size=RAG_DEFAULT_CHUNK_SIZE,
        rag_chunk_overlap=RAG_DEFAULT_CHUNK_OVERLAP,
    ),
    "institucional_chatbot": UsagePreset(
        key="institucional_chatbot",
        label="Site Institucional para Chatbot",
        description="Ideal para capturar paginas institucionais, servicos, contato e suporte.",
        extraction_mode="Site Completo (Crawler)",
        output_format="Ambos",
        max_pages=40,
        max_depth=2,
        include_paths=(),
        exclude_paths=("/login", "/admin", "/privacidade", "/termos"),
        ignore_binary_files=True,
        generate_rag_artifacts=True,
        rag_chunk_size=1000,
        rag_chunk_overlap=120,
    ),
    "documentacao_tecnica": UsagePreset(
        key="documentacao_tecnica",
        label="Documentação Técnica",
        description="Pensado para centrais de ajuda, docs de produto e bases tecnicas.",
        extraction_mode="Site Completo (Crawler)",
        output_format="Ambos",
        max_pages=120,
        max_depth=3,
        include_paths=("/docs", "/doc", "/help", "/api"),
        exclude_paths=("/blog", "/pricing", "/status"),
        ignore_binary_files=True,
        generate_rag_artifacts=True,
        rag_chunk_size=900,
        rag_chunk_overlap=100,
    ),
    "base_rag": UsagePreset(
        key="base_rag",
        label="Base para RAG",
        description="Foca em gerar uma base pronta para embeddings, busca e recuperacao de contexto.",
        extraction_mode="Site Completo (Crawler)",
        output_format="Ambos",
        max_pages=80,
        max_depth=2,
        include_paths=(),
        exclude_paths=("/login", "/admin"),
        ignore_binary_files=True,
        generate_rag_artifacts=True,
        rag_chunk_size=1200,
        rag_chunk_overlap=150,
    ),
}


def get_usage_preset(preset_key: str) -> UsagePreset:
    """Retorna um preset pelo identificador, com fallback seguro para o personalizado."""
    return USAGE_PRESETS.get(preset_key, USAGE_PRESETS[DEFAULT_PRESET_KEY])


def list_usage_presets() -> list[UsagePreset]:
    """Lista os presets na ordem em que devem aparecer para o usuario."""
    return list(USAGE_PRESETS.values())


def get_usage_preset_options() -> list[str]:
    """Retorna apenas os nomes amigaveis dos presets para alimentar seletores da UI."""
    return [preset.label for preset in list_usage_presets()]

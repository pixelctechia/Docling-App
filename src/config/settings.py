"""Configurações centralizadas do Docling App."""
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = PROJECT_ROOT / os.getenv("DOCLING_OUTPUT_DIR", "outputs")
DB_NAME = os.getenv("DOCLING_DB_NAME", "docling_history.db")
DB_PATH = PROJECT_ROOT / DB_NAME

PLAYWRIGHT_USER_AGENT = os.getenv(
    "DOCLING_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)
PLAYWRIGHT_VIEWPORT = {
    "width": int(os.getenv("DOCLING_VIEWPORT_WIDTH", "1920")),
    "height": int(os.getenv("DOCLING_VIEWPORT_HEIGHT", "1080")),
}
PLAYWRIGHT_PAGE_TIMEOUT_MS = int(os.getenv("DOCLING_PAGE_TIMEOUT_MS", "60000"))

UI_MAX_PAGES_LIMIT = int(os.getenv("DOCLING_UI_MAX_PAGES_LIMIT", "500"))
UI_DEFAULT_MAX_PAGES = int(os.getenv("DOCLING_UI_DEFAULT_MAX_PAGES", "50"))
UI_DEFAULT_MAX_DEPTH = int(os.getenv("DOCLING_UI_DEFAULT_MAX_DEPTH", "2"))
RAG_DEFAULT_ENABLED = os.getenv("DOCLING_RAG_ENABLED", "true").lower() == "true"
RAG_DEFAULT_CHUNK_SIZE = int(os.getenv("DOCLING_RAG_CHUNK_SIZE", "1200"))
RAG_DEFAULT_CHUNK_OVERLAP = int(os.getenv("DOCLING_RAG_CHUNK_OVERLAP", "150"))

DEFAULT_IGNORED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".pdf", ".zip", ".rar", ".7z", ".tar", ".gz",
    ".mp3", ".wav", ".ogg", ".mp4", ".avi", ".mov", ".webm",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".csv", ".xml", ".json", ".txt",
    ".css", ".js", ".mjs", ".map",
    ".woff", ".woff2", ".ttf", ".otf", ".eot"
}

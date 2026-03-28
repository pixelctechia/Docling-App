from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from src.config.settings import DB_PATH

Base = declarative_base()

class Task(Base):
    """Tabela para registrar o histórico de conversões."""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    output_format = Column(String, nullable=False)
    status = Column(String, nullable=False)  # 'Sucesso' ou 'Falha'
    result_path = Column(String, nullable=True)
    extraction_mode = Column(String, nullable=True)
    pages_processed = Column(Integer, nullable=True, default=0)
    files_generated = Column(Integer, nullable=True, default=0)
    errors_count = Column(Integer, nullable=True, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True, default=datetime.now)
    finished_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

def _garantir_colunas_tasks():
    """Adiciona novas colunas em bancos SQLite já existentes sem perder dados."""
    colunas_necessarias = {
        "extraction_mode": "VARCHAR",
        "pages_processed": "INTEGER DEFAULT 0",
        "files_generated": "INTEGER DEFAULT 0",
        "errors_count": "INTEGER DEFAULT 0",
        "error_message": "TEXT",
        "started_at": "DATETIME",
        "finished_at": "DATETIME",
        "duration_seconds": "FLOAT"
    }

    with engine.begin() as conexao:
        colunas_existentes = {
            coluna[1] for coluna in conexao.exec_driver_sql("PRAGMA table_info(tasks)").fetchall()
        }

        for nome_coluna, definicao in colunas_necessarias.items():
            if nome_coluna not in colunas_existentes:
                conexao.exec_driver_sql(
                    f"ALTER TABLE tasks ADD COLUMN {nome_coluna} {definicao}"
                )

# Cria a engine, as tabelas e atualiza o schema quando necessário
Base.metadata.create_all(engine)
_garantir_colunas_tasks()

# Configuração da Sessão
SessionLocal = sessionmaker(bind=engine)

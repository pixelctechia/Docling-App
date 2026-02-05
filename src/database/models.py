from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

# Define o local do banco de dados (na raiz do projeto)
DB_NAME = "docling_history.db"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DB_PATH = os.path.join(BASE_DIR, DB_NAME)

Base = declarative_base()

class Task(Base):
    """Tabela para registrar o histórico de conversões."""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    output_format = Column(String, nullable=False)
    status = Column(String, nullable=False)  # 'Sucesso' ou 'Falha'
    result_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

# Cria a engine e as tabelas se não existirem
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Base.metadata.create_all(engine)

# Configuração da Sessão
SessionLocal = sessionmaker(bind=engine)
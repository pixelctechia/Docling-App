import pandas as pd
from src.database.models import SessionLocal, Task

def _formatar_data(data):
    if not data:
        return "-"
    return data.strftime("%d/%m/%Y %H:%M")

def _formatar_duracao(segundos):
    if segundos is None:
        return "-"
    return f"{segundos:.2f}s"

def add_task(
    url: str,
    output_format: str,
    status: str,
    result_path: str = "",
    extraction_mode: str = "",
    pages_processed: int = 0,
    files_generated: int = 0,
    errors_count: int = 0,
    error_message: str = "",
    started_at=None,
    finished_at=None,
    duration_seconds: float | None = None
):
    """
    Adiciona uma nova tarefa ao histórico do banco de dados.
    """
    session = SessionLocal()
    try:
        nova_tarefa = Task(
            url=url,
            output_format=output_format,
            status=status,
            result_path=result_path,
            extraction_mode=extraction_mode or None,
            pages_processed=pages_processed,
            files_generated=files_generated,
            errors_count=errors_count,
            error_message=error_message or None,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration_seconds
        )
        session.add(nova_tarefa)
        session.commit()
    except Exception as e:
        print(f"Erro ao salvar no banco: {e}")
        session.rollback()
    finally:
        session.close()

def get_recent_tasks(limit: int = 10):
    """
    Busca as últimas tarefas para exibir no Dashboard.
    Retorna um DataFrame do Pandas (compatível com st.dataframe).
    """
    session = SessionLocal()
    try:
        # Busca ordenando por data decrescente
        tasks = session.query(Task).order_by(Task.created_at.desc()).limit(limit).all()
        
        if not tasks:
            return pd.DataFrame()

        # Transforma em lista de dicionários para o Pandas
        data = []
        for t in tasks:
            data_execucao = t.finished_at or t.started_at or t.created_at
            data.append({
                "Data": _formatar_data(data_execucao),
                "URL": t.url,
                "Status": t.status,
                "Modo": t.extraction_mode or "-",
                "Formato": t.output_format,
                "Páginas": t.pages_processed if t.pages_processed is not None else "-",
                "Arquivos": t.files_generated if t.files_generated is not None else "-",
                "Erros": t.errors_count if t.errors_count is not None else "-",
                "Duração": _formatar_duracao(t.duration_seconds),
                "Mensagem de Erro": t.error_message or "-",
                "Pasta Salva": t.result_path
            })
        
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Erro ao ler banco: {e}")
        return pd.DataFrame()
    finally:
        session.close()

def clear_tasks() -> bool:
    """
    Remove todos os registros do histórico local.
    """
    session = SessionLocal()
    try:
        session.query(Task).delete()
        session.commit()
        return True
    except Exception as e:
        print(f"Erro ao limpar histórico: {e}")
        session.rollback()
        return False
    finally:
        session.close()

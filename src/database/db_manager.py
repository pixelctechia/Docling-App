import pandas as pd
from src.database.models import SessionLocal, Task

def add_task(url: str, output_format: str, status: str, result_path: str = ""):
    """
    Adiciona uma nova tarefa ao histórico do banco de dados.
    """
    session = SessionLocal()
    try:
        nova_tarefa = Task(
            url=url,
            output_format=output_format,
            status=status,
            result_path=result_path
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
            data.append({
                "Data": t.created_at.strftime("%d/%m/%Y %H:%M"),
                "URL": t.url,
                "Status": t.status,
                "Formato": t.output_format,
                "Pasta Salva": t.result_path
            })
        
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Erro ao ler banco: {e}")
        return pd.DataFrame()
    finally:
        session.close()
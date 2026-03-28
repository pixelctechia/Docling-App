import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from src.database import db_manager


class FakeSortableColumn:
    def desc(self):
        return self


class FakeTaskRecord:
    created_at = FakeSortableColumn()

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.url = kwargs.get("url", "")
        self.output_format = kwargs.get("output_format", "")
        self.status = kwargs.get("status", "")
        self.result_path = kwargs.get("result_path", "")
        self.extraction_mode = kwargs.get("extraction_mode")
        self.pages_processed = kwargs.get("pages_processed", 0)
        self.files_generated = kwargs.get("files_generated", 0)
        self.errors_count = kwargs.get("errors_count", 0)
        self.error_message = kwargs.get("error_message")
        self.started_at = kwargs.get("started_at")
        self.finished_at = kwargs.get("finished_at")
        self.duration_seconds = kwargs.get("duration_seconds")
        self.created_at = kwargs.get("created_at", datetime.now())


class FakeQuery:
    def __init__(self, objetos):
        self.objetos = list(objetos)
        self._limit = None

    def order_by(self, _criterion):
        self.objetos = sorted(self.objetos, key=lambda item: item.created_at, reverse=True)
        return self

    def limit(self, limit):
        self._limit = limit
        return self

    def all(self):
        if self._limit is None:
            return list(self.objetos)
        return list(self.objetos[:self._limit])


class FakeSession:
    def __init__(self, storage):
        self.storage = storage
        self.closed = False
        self.committed = False
        self.rolled_back = False

    def add(self, obj):
        if obj.id is None:
            obj.id = len(self.storage) + 1
        if obj.created_at is None:
            obj.created_at = datetime.now()
        self.storage.append(obj)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True

    def query(self, _model):
        return FakeQuery(self.storage)


class DBManagerTests(unittest.TestCase):
    def test_add_task_salva_campos_ricos(self):
        storage = []

        def factory():
            return FakeSession(storage)

        inicio = datetime.now()
        fim = inicio + timedelta(seconds=4)

        with patch.object(db_manager, "SessionLocal", side_effect=factory), patch.object(
            db_manager, "Task", FakeTaskRecord
        ):
            db_manager.add_task(
                url="https://pixelctech.com.br",
                output_format="Markdown",
                status="Sucesso",
                result_path="outputs/site",
                extraction_mode="Crawler",
                pages_processed=3,
                files_generated=2,
                errors_count=1,
                error_message="erro de teste",
                started_at=inicio,
                finished_at=fim,
                duration_seconds=4.0
            )

        self.assertEqual(len(storage), 1)
        tarefa = storage[0]
        self.assertEqual(tarefa.url, "https://pixelctech.com.br")
        self.assertEqual(tarefa.extraction_mode, "Crawler")
        self.assertEqual(tarefa.pages_processed, 3)
        self.assertEqual(tarefa.files_generated, 2)
        self.assertEqual(tarefa.errors_count, 1)
        self.assertEqual(tarefa.error_message, "erro de teste")
        self.assertEqual(tarefa.duration_seconds, 4.0)

    def test_get_recent_tasks_retorna_dataframe_ordenado(self):
        agora = datetime.now()
        storage = [
            FakeTaskRecord(
                id=1,
                url="https://site-antigo.com",
                output_format="Markdown",
                status="Sucesso",
                result_path="outputs/antigo",
                extraction_mode="Página Única",
                pages_processed=1,
                files_generated=1,
                errors_count=0,
                duration_seconds=1.25,
                created_at=agora - timedelta(hours=2)
            ),
            FakeTaskRecord(
                id=2,
                url="https://site-novo.com",
                output_format="Ambos",
                status="Falha",
                result_path="outputs/novo",
                extraction_mode="Crawler",
                pages_processed=4,
                files_generated=3,
                errors_count=1,
                error_message="timeout",
                duration_seconds=9.5,
                created_at=agora
            ),
        ]

        def factory():
            return FakeSession(storage)

        with patch.object(db_manager, "SessionLocal", side_effect=factory), patch.object(
            db_manager, "Task", FakeTaskRecord
        ):
            dataframe = db_manager.get_recent_tasks(limit=10)

        self.assertEqual(
            list(dataframe.columns),
            [
                "Data",
                "URL",
                "Status",
                "Modo",
                "Formato",
                "Páginas",
                "Arquivos",
                "Erros",
                "Duração",
                "Mensagem de Erro",
                "Pasta Salva",
            ]
        )
        self.assertEqual(dataframe.iloc[0]["URL"], "https://site-novo.com")
        self.assertEqual(dataframe.iloc[0]["Modo"], "Crawler")
        self.assertEqual(dataframe.iloc[0]["Duração"], "9.50s")
        self.assertEqual(dataframe.iloc[0]["Mensagem de Erro"], "timeout")


if __name__ == "__main__":
    unittest.main()

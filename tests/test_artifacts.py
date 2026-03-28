import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from src.core.artifacts import (
    criar_zip_em_memoria,
    gerar_chunks_rag,
    salvar_chunks_rag,
    salvar_manifesto_extracao,
)


class ArtifactsTests(unittest.TestCase):
    def test_gerar_chunks_rag_retorna_metadados_basicos(self):
        markdown = "# Titulo\n\nPrimeiro bloco de texto.\n\n## Secao\n\nSegundo bloco com mais conteudo."

        chunks = gerar_chunks_rag(
            markdown,
            source_url="https://site.com/docs",
            source_slug="docs",
            chunk_size=40,
            chunk_overlap=10
        )

        self.assertGreaterEqual(len(chunks), 2)
        self.assertEqual(chunks[0]["source_url"], "https://site.com/docs")
        self.assertEqual(chunks[0]["source_slug"], "docs")
        self.assertTrue(chunks[0]["content"])
        self.assertGreater(chunks[0]["char_count"], 0)

    def test_salvar_manifesto_e_chunks_rag(self):
        with tempfile.TemporaryDirectory() as diretorio:
            output_dir = Path(diretorio)
            manifest_path = salvar_manifesto_extracao(
                output_dir,
                {"pages_processed": 2, "rag_chunks_generated": 4}
            )
            rag_path = salvar_chunks_rag(
                [{"chunk_id": "home:0", "content": "abc"}],
                output_dir
            )

            self.assertTrue(manifest_path.exists())
            self.assertTrue(rag_path.exists())
            self.assertEqual(
                json.loads(manifest_path.read_text(encoding="utf-8"))["pages_processed"],
                2
            )
            self.assertIn('"chunk_id": "home:0"', rag_path.read_text(encoding="utf-8"))

    def test_criar_zip_em_memoria_compacta_arquivos(self):
        with tempfile.TemporaryDirectory() as diretorio:
            output_dir = Path(diretorio)
            (output_dir / "a.txt").write_text("conteudo-a", encoding="utf-8")
            subdir = output_dir / "sub"
            subdir.mkdir()
            (subdir / "b.txt").write_text("conteudo-b", encoding="utf-8")

            zip_bytes = criar_zip_em_memoria(output_dir)

            with tempfile.NamedTemporaryFile(suffix=".zip") as arquivo_zip:
                arquivo_zip.write(zip_bytes)
                arquivo_zip.flush()

                with zipfile.ZipFile(arquivo_zip.name, "r") as zip_file:
                    nomes = sorted(zip_file.namelist())

            self.assertEqual(nomes, ["a.txt", "sub/b.txt"])


if __name__ == "__main__":
    unittest.main()

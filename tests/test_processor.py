import unittest

from src.core.processor import (
    DEFAULT_IGNORED_EXTENSIONS,
    ProcessorError,
    _criar_html_temporario,
    _extrair_caminho_logico,
    _link_passa_filtros,
    _normalizar_lista_caminhos,
    _slug_da_url,
    preparar_url_entrada,
    processar_url,
    validar_url,
)


class ProcessorHelpersTests(unittest.TestCase):
    def test_preparar_url_entrada_adiciona_https_quando_faltando(self):
        self.assertEqual(
            preparar_url_entrada("pixelctech.com.br"),
            "https://pixelctech.com.br"
        )

    def test_validar_url_rejeita_esquema_invalido(self):
        url_ok, url_normalizada, erro = validar_url("mailto:teste@x.com")

        self.assertFalse(url_ok)
        self.assertEqual(url_normalizada, "")
        self.assertIn("URL inválida", erro)

    def test_slug_preserva_rotas_spa(self):
        self.assertEqual(
            _slug_da_url("https://pixelctech.com.br/#/parcerias"),
            "parcerias"
        )

    def test_normalizar_lista_caminhos_padroniza_barras(self):
        self.assertEqual(
            _normalizar_lista_caminhos(["blog", "/docs/", " /admin "]),
            ["/blog", "/docs", "/admin"]
        )

    def test_extrair_caminho_logico_com_fragmento_spa(self):
        self.assertEqual(
            _extrair_caminho_logico("https://site.com/area#/dashboard"),
            "/area/dashboard"
        )

    def test_link_passa_filtros_com_include_exclude_e_extensao(self):
        include_paths = _normalizar_lista_caminhos(["/blog", "/docs"])
        exclude_paths = _normalizar_lista_caminhos(["/blog/admin"])

        self.assertTrue(
            _link_passa_filtros(
                "https://site.com/blog/post-1",
                include_paths,
                exclude_paths,
                DEFAULT_IGNORED_EXTENSIONS
            )
        )
        self.assertFalse(
            _link_passa_filtros(
                "https://site.com/blog/admin/painel",
                include_paths,
                exclude_paths,
                DEFAULT_IGNORED_EXTENSIONS
            )
        )
        self.assertFalse(
            _link_passa_filtros(
                "https://site.com/imagem/logo.png",
                include_paths,
                exclude_paths,
                DEFAULT_IGNORED_EXTENSIONS
            )
        )

    def test_criar_html_temporario_grava_e_remove_manual(self):
        caminho = _criar_html_temporario("<html><body>ok</body></html>")

        try:
            self.assertTrue(caminho.exists())
            self.assertEqual(caminho.suffix, ".html")
            self.assertIn("docling_", caminho.name)
            self.assertEqual(
                caminho.read_text(encoding="utf-8"),
                "<html><body>ok</body></html>"
            )
        finally:
            if caminho.exists():
                caminho.unlink()


class ProcessorValidationTests(unittest.TestCase):
    def test_processar_url_falha_para_limite_invalido(self):
        with self.assertRaises(ProcessorError) as contexto:
            processar_url("https://pixelctech.com.br", "Markdown", max_pages=0)

        self.assertIn("limite de páginas", str(contexto.exception))

    def test_processar_url_falha_para_profundidade_invalida(self):
        with self.assertRaises(ProcessorError) as contexto:
            processar_url("https://pixelctech.com.br", "Markdown", max_depth=-1)

        self.assertIn("profundidade máxima", str(contexto.exception))


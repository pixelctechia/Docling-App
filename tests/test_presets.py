import unittest

from src.config.presets import (
    DEFAULT_PRESET_KEY,
    UsagePreset,
    get_usage_preset,
    get_usage_preset_options,
    list_usage_presets,
)


class UsagePresetsTests(unittest.TestCase):
    def test_list_usage_presets_retorna_presets_ordenados(self):
        presets = list_usage_presets()

        self.assertGreaterEqual(len(presets), 4)
        self.assertTrue(all(isinstance(preset, UsagePreset) for preset in presets))
        self.assertEqual(presets[0].key, DEFAULT_PRESET_KEY)

    def test_get_usage_preset_faz_fallback_para_personalizado(self):
        preset = get_usage_preset("nao-existe")

        self.assertEqual(preset.key, DEFAULT_PRESET_KEY)
        self.assertEqual(preset.label, "Personalizado")

    def test_get_usage_preset_options_retorna_rotulos_amigaveis(self):
        opcoes = get_usage_preset_options()

        self.assertIn("Personalizado", opcoes)
        self.assertIn("Site Institucional para Chatbot", opcoes)
        self.assertIn("Documentação Técnica", opcoes)
        self.assertIn("Base para RAG", opcoes)

    def test_preset_documentacao_tecnica_possui_valores_esperados(self):
        preset = get_usage_preset("documentacao_tecnica")
        estado_ui = preset.to_ui_state()

        self.assertEqual(estado_ui["modo_extracao"], "Site Completo (Crawler)")
        self.assertEqual(estado_ui["output_format"], "Ambos")
        self.assertEqual(estado_ui["max_depth"], 3)
        self.assertIn("/docs", estado_ui["include_paths"])
        self.assertTrue(estado_ui["gerar_rag_artifacts"])

    def test_preset_personalizado_permite_controle_manual_total(self):
        preset = get_usage_preset(DEFAULT_PRESET_KEY)
        estado_ui = preset.to_ui_state()

        self.assertEqual(estado_ui["modo_extracao"], "Página Única (Apenas o Link)")
        self.assertEqual(estado_ui["output_format"], "Ambos")
        self.assertEqual(estado_ui["include_paths"], [])
        self.assertEqual(estado_ui["exclude_paths"], [])


if __name__ == "__main__":
    unittest.main()

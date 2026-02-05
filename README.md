# 🐬 Docling App - Extrator de Dados Web Open Source

> **Web Scraping Local, Privado e Sem Limites.**
> Transforme sites complexos e dinâmicos (React, Next.js, Vue) em **Markdown** e **JSON** estruturado.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen)
![Technology](https://img.shields.io/badge/Tech-Docling%20%7C%20Playwright%20%7C%20Streamlit-orange)

## 🚀 Sobre o Projeto

O **Docling App** é uma solução robusta para capturar dados da web que roda 100% na sua máquina local. Diferente de scrapers comuns que falham em sites modernos, este sistema utiliza um navegador real automatizado para renderizar JavaScript e capturar o conteúdo real.

### ✨ Funcionalidades Principais

- **🕷️ Crawler Inteligente:** Escolha entre baixar uma **Página Única** ou rastrear o **Site Completo** (segue links internos automaticamente).
- **📜 Auto-Scroll Engine:** Simula o comportamento humano de rolar a página para forçar o carregamento de imagens e textos "Lazy Load" (essencial para sites modernos).
- **🧠 Docling AI:** Utiliza o motor da IBM/Docling para entender tabelas complexas e layout de documentos.
- **🛡️ Anti-Bloqueio:** Navegação via Chromium Headless com Headers de usuário real para evitar detecção básica de robôs.
- **📂 Saída Estruturada:** Gera arquivos `.md` (Markdown) prontos para LLMs e `.json` com metadados.
- **💾 Histórico Local:** Banco de dados SQLite integrado para registrar todas as suas conversões.

---

## 🛠️ Instalação (Passo a Passo)

Siga estes passos para rodar o sistema no seu ambiente (Ubuntu/Linux/Windows).

### 1. Pré-requisitos
Certifique-se de ter o **Python 3.10+** instalado.

### 2. Clone o Repositório
```bash
git clone https://github.com/pixelctechia/Docling-App.git
cd Docling-App

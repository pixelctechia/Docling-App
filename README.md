# 🐬 Docling App - O Extrator Essencial para RAG e LLMs

> **Transforme a Web em Dados para sua IA.**
> A ferramenta definitiva para quem trabalha com **RAG (Retrieval-Augmented Generation)**. Capture sites complexos (React, Next.js) e gere datasets limpos em **Markdown** e **JSON**.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![RAG Ready](https://img.shields.io/badge/RAG-Ready-purple)
![Status](https://img.shields.io/badge/Status-Active%20Dev-orange)

## 🎯 Por que usar este projeto?

Se você trabalha com **LLMs (Large Language Models)** ou está construindo sistemas de **RAG**, sabe que a qualidade da resposta da sua IA depende da qualidade dos dados que você fornece (Garbage In, Garbage Out).

O **Docling App** foi criado para resolver a maior dor de cabeça da engenharia de dados para IA: **Extrair documentação útil de sites modernos e dinâmicos.**

Diferente de scrapers comuns que quebram com JavaScript ou entregam HTML sujo, este sistema entrega:
1.  **Markdown Limpo:** Perfeito para ser "embedado" em bancos vetoriais (ChromaDB, Pinecone).
2.  **JSON Estruturado:** Ideal para fine-tuning e preservação de metadados.

---

## 🚀 Funcionalidades Principais

- **🕷️ Crawler Inteligente:**
    - **Modo Página Única:** Capture uma documentação específica.
    - **Modo Site Completo:** Baixe portais de documentação inteiros recursivamente.
- **📜 Engine de Auto-Scroll:** Simula comportamento humano para capturar conteúdo "Lazy Load" que scrapers tradicionais perdem.
- **🧠 Docling AI:** Preserva a estrutura semântica de tabelas e seções, essencial para que a LLM entenda o contexto.
- **🛡️ Anti-Bloqueio:** Navegação via Chromium Headless com perfil de usuário real.
- **🔮 Roadmap (Em Breve):** O sistema está em evolução constante. Novas funcionalidades para tratamento de dados e integração direta com bancos vetoriais estão no radar.

---

## 🛠️ Instalação (Ubuntu/Linux)

### 1. Clone o Repositório
```bash
git clone [https://github.com/pixelctechia/Docling-App.git
cd Docling-App

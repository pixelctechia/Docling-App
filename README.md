# 🐬 Docling App - Extrator de Dados Web para RAG e IA

> **Transforme a Internet em Dados para sua Inteligência Artificial.**
> A ferramenta definitiva para quem trabalha com **RAG (Retrieval-Augmented Generation)**. Capture sites complexos (React, Next.js, Vue) e gere datasets limpos em **Markdown** e **JSON**.


## 🎯 Por que usar este projeto?

Se você está estudando ou trabalhando com **Inteligência Artificial (LLMs)**, sabe que a IA é tão boa quanto os dados que ela consome. O problema é que a maioria dos sites modernos usa tecnologias dinâmicas que impedem a leitura simples.

O **Docling App** resolve isso simulando um humano navegando. Ele rola a página, carrega todo o conteúdo e entrega:

1. **Markdown Limpo (.md):** Perfeito para alimentar ChatGPT, Claude ou bancos vetoriais (ChromaDB, Pinecone).
2. **JSON Estruturado (.json):** Ideal para preservação de metadados e links.

---

## 🚀 Funcionalidades

- **🕷️ Crawler Inteligente:**
  - **Modo Página Única:** Baixa apenas o link informado.
  - **Modo Site Completo:** Entra no link e navega recursivamente (Blog, Sobre, Docs) para baixar o site todo.
- **📜 Engine de Auto-Scroll:** O robô rola a página até o fim para carregar conteúdo escondido (Lazy Load).
- **🧠 Docling AI:** Preserva a estrutura semântica de tabelas e cabeçalhos.
- **🛡️ Anti-Bloqueio:** Navega usando um navegador real (Chromium) invisível.

---

## 📚 Guia de Instalação Completo (Passo a Passo)

Siga este guia exato para o seu sistema operacional. Não pule etapas.

### Passo 1: Verificar o Python

Você precisa do Python 3.10 ou superior instalado.

- **Windows:** Abra o PowerShell ou CMD e digite `python --version`
- **Linux/Mac:** Abra o Terminal e digite `python3 --version`

---

### Passo 2: Clonar o Repositório

Baixe o código para o seu computador.

```bash
git clone https://github.com/pixelctechia/Docling-App.git
cd Docling-App
```

---

### Passo 3: Criar e Ativar o Ambiente Virtual

O ambiente virtual isola o projeto para não bagunçar seu computador. Escolha o comando do seu sistema:

#### 🪟 Para Windows

```powershell
python -m venv venv
.\venv\Scripts\activate
```

Se der erro de script, rode:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 🐧 Para Linux (Ubuntu) e 🍎 Mac (macOS)

```bash
python3 -m venv venv
source venv/bin/activate
```

Atenção: Após ativar, deve aparecer `(venv)` no começo da linha do seu terminal.

---

### Passo 4: Instalar as Dependências

Com o `(venv)` ativado, instale as bibliotecas do projeto.

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Passo 5: Instalar o Navegador (Playwright)

O sistema usa um navegador "invisível". Este passo é crucial.

#### 🪟 Windows e 🍎 Mac

Rode apenas este comando:

```bash
playwright install chromium
```

#### 🐧 Linux (Ubuntu/Debian)

No Linux, além do navegador, precisamos de algumas bibliotecas de vídeo e fonte. Rode os dois comandos abaixo.

Instale o navegador:

```bash
playwright install chromium
```

Instale as dependências do sistema (copie tudo e cole):

```bash
sudo apt-get update && sudo apt-get install -y libwoff1 libopus0 libwebp6 libwebpdemux2 libenchant-2-2 libsecret-1-0 libhyphen0 libgudev-1.0-0 libgl1 libglib2.0-0 libdbus-glib-1-2
```

---

## 🖥️ Como Usar

Agora que tudo está instalado, vamos rodar o sistema.

Certifique-se que o terminal mostra `(venv)`.

Inicie o Painel de Controle:

```bash
streamlit run src/ui/app.py
```

O sistema vai abrir automaticamente no seu navegador padrão, no endereço: 👉 http://localhost:8501

### 💡 Fluxo de Trabalho

- Cole o link do site alvo.
- No menu lateral (esquerda), escolha "Site Completo (Crawler)".
- Defina o limite de páginas (ex: 20 páginas).
- Clique em INICIAR EXTRAÇÃO.
- Acompanhe o progresso na tela ("Processando página 1/20...").

---

## 📂 Onde estão meus arquivos?

O sistema cria automaticamente uma pasta chamada `outputs` dentro do projeto. Tudo fica organizado por site e data:

```plaintext
Docling-App/
└── outputs/
    └── docs.python.org/       <-- Nome do Site
        └── 20260502_103000/   <-- Data e Hora da extração
            ├── home.md        <-- Conteúdo em Markdown
            ├── home.json      <-- Conteúdo em JSON
            ├── tutorial.md
            └── api.json
```

---

## ❓ Resolução de Problemas Comuns

**Erro: `ModuleNotFoundError` ou `streamlit not found`**

- Causa: Você esqueceu de ativar o ambiente virtual.
- Solução: Refaça o Passo 3 (activate) e tente de novo.

**Erro: O navegador não abre ou dá erro de "Libraries missing" (Linux)**

- Causa: Faltam as bibliotecas do sistema.
- Solução: Rode o comando gigante do Passo 5 (seção Linux) novamente.

---

## 🤝 Contribuição

Este é um projeto Open Source focado na liberdade de dados. Sinta-se à vontade para abrir Issues ou Pull Requests para melhorar o algoritmo.

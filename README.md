# 🐬 Docling App - Extração Web Inteligente para RAG, IA e Dados Estruturados

> **Converta sites modernos em datasets utilizáveis em minutos.**
> O Docling App captura páginas dinâmicas com navegador real, organiza a saída em **Markdown**, **JSON** e **chunks para RAG**, e entrega tudo pronto para uso, análise ou ingestão em pipelines de IA.

## 🆕 Últimas Atualizações

O projeto recebeu uma grande evolução técnica e visual, incluindo:

- crawler mais robusto para sites modernos;
- saída pronta para RAG com `rag_chunks.jsonl`;
- histórico local mais rico;
- tutorial integrado na interface;
- redesign premium da experiência de uso;
- melhorias de responsividade para mobile;
- testes automatizados para os pontos críticos.

Para ver o resumo completo das entregas, acesse o [CHANGELOG.md](CHANGELOG.md).

## 🎯 Por Que o Docling App Existe?

Se você trabalha com **LLMs**, **RAG**, automação, análise de mercado, monitoramento de conteúdo ou engenharia de dados, sabe que o maior gargalo quase nunca é a IA em si. O gargalo é conseguir dados limpos, consistentes e aproveitáveis.

O problema é que muitos sites atuais usam **React**, **Vue**, **Next.js**, lazy load, rotas dinâmicas e outros comportamentos que quebram crawlers simples.

O **Docling App** resolve isso com uma abordagem prática:

1. Abre o site com um navegador real
2. Executa auto-scroll para carregar o conteúdo
3. Captura o HTML renderizado
4. Converte a saída em formatos úteis para IA e documentação
5. Organiza tudo em uma estrutura pronta para uso

Em vez de perder tempo montando scripts frágeis para cada site, você ganha um fluxo visual e reutilizável para transformar páginas web em ativos de dados.

## 💼 Ideal Para

- Times que estão construindo **bases de conhecimento para RAG**
- Agências e consultorias que precisam **mapear sites e documentações**
- Profissionais que querem **coletar conteúdo estruturado sem depender de scraping manual**
- Operações que precisam de **Markdown e JSON limpos** para IA, busca ou arquivo interno
- Projetos que exigem **entregáveis rápidos**, como ZIP, chunks e histórico local

---

## ✨ Proposta de Valor

Com o Docling App, você consegue:

- **Extrair uma única página ou um site inteiro**
- **Controlar profundidade e escopo do crawl**
- **Gerar dados prontos para pipelines de IA**
- **Reduzir retrabalho com saídas já organizadas**
- **Ter visibilidade da execução em tempo real**
- **Salvar histórico e resultados de forma local**

---

## 🚀 Funcionalidades

- **🕷️ Crawler Inteligente**
  - Modo página única para extrações rápidas
  - Modo crawler para navegar recursivamente por links internos

- **🎯 Controle Total da Coleta**
  - limite máximo de páginas
  - profundidade máxima
  - filtros de inclusão e exclusão de caminhos
  - bloqueio de arquivos não HTML comuns

- **📜 Captura Real de Conteúdo**
  - navegador Chromium headless
  - auto-scroll para conteúdo lazy load
  - melhor compatibilidade com sites modernos

- **🧠 Saída Estruturada para IA**
  - `Markdown` limpo para leitura e ingestão
  - `JSON` com metadados úteis
  - `rag_chunks.jsonl` opcional para pipelines RAG
  - `manifest.json` com resumo da execução

- **📊 Operação com Visibilidade**
  - progresso em tempo real
  - logs durante o processamento
  - métricas de páginas, arquivos, fila, erros e chunks
  - histórico local das execuções

- **⬇️ Entrega Prática**
  - pasta organizada automaticamente
  - download dos resultados em `.zip`

---

## 🧩 O Que Você Recebe no Final

Ao final de uma extração, o projeto pode entregar:

- arquivos `Markdown` por página
- arquivos `JSON` por página
- `manifest.json` com resumo da execução
- `rag_chunks.jsonl` para ingestão em RAG
- histórico local com status, duração e métricas
- um pacote `.zip` para compartilhar ou armazenar

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
streamlit run streamlit_app.py
```

O sistema vai abrir automaticamente no seu navegador padrão, no endereço: 👉 http://localhost:8501

### 💡 Fluxo de Trabalho Atual

- Cole a URL do site alvo.
- Escolha entre **Página Única** ou **Site Completo (Crawler)**.
- Defina o limite de páginas e, se quiser, a profundidade máxima.
- Use filtros opcionais de caminhos para restringir o crawl.
- Escolha o formato de saída: **Markdown**, **JSON** ou **Ambos**.
- Ative a geração de **chunks para RAG** se quiser o arquivo `rag_chunks.jsonl`.
- Clique em INICIAR EXTRAÇÃO.
- Acompanhe o progresso, os logs e as métricas em tempo real.
- Ao final, abra a pasta local ou baixe tudo em **ZIP**.

### Resultado Esperado

Você sai da interface com:

- conteúdo extraído
- arquivos organizados por domínio e data
- artefatos para RAG quando ativados
- histórico salvo localmente
- pacote pronto para download ou uso imediato

### Entrypoint Recomendado

O comando recomendado é:

```bash
streamlit run streamlit_app.py
```

O projeto também tem compatibilidade para execução direta da UI:

```bash
streamlit run src/ui/app.py
```

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
            ├── manifest.json  <-- Resumo da extração
            ├── rag_chunks.jsonl <-- Chunks para RAG (opcional)
            ├── tutorial.md
            └── api.json
```

### Tipos de Arquivo Gerados

- `*.md`: conteúdo em Markdown
- `*.json`: conteúdo estruturado com metadados extras
- `manifest.json`: resumo da execução e páginas processadas
- `rag_chunks.jsonl`: chunks para ingestão em pipelines RAG

---

## ⚙️ Configuração Opcional

O projeto possui configurações centralizadas em `src/config/settings.py` e aceita variáveis de ambiente via `.env`.

Principais variáveis:

```env
DOCLING_OUTPUT_DIR=outputs
DOCLING_DB_NAME=docling_history.db
DOCLING_PAGE_TIMEOUT_MS=60000
DOCLING_VIEWPORT_WIDTH=1920
DOCLING_VIEWPORT_HEIGHT=1080
DOCLING_UI_MAX_PAGES_LIMIT=500
DOCLING_UI_DEFAULT_MAX_PAGES=50
DOCLING_UI_DEFAULT_MAX_DEPTH=2
DOCLING_RAG_ENABLED=true
DOCLING_RAG_CHUNK_SIZE=1200
DOCLING_RAG_CHUNK_OVERLAP=150
```

---

## ✅ Testes

O projeto já possui testes automatizados para:

- validação de URL
- filtros do crawler
- geração de artefatos para RAG
- exportação ZIP
- camada de histórico

Para rodar a suíte:

```bash
venv/bin/python -m unittest discover -s tests -v
```

---

## ❓ Resolução de Problemas Comuns

**Erro: `ModuleNotFoundError: No module named 'src'`**

- Causa: Você executou a interface de um jeito em que a raiz do projeto não foi encontrada no path.
- Solução: Prefira `streamlit run streamlit_app.py`. A UI também já tem bootstrap para `streamlit run src/ui/app.py`.

**Erro: `ModuleNotFoundError` ou `streamlit not found`**

- Causa: Você esqueceu de ativar o ambiente virtual.
- Solução: Refaça o Passo 3 (activate) e tente de novo.

**Erro: O navegador não abre ou dá erro de "Libraries missing" (Linux)**

- Causa: Faltam as bibliotecas do sistema.
- Solução: Rode o comando gigante do Passo 5 (seção Linux) novamente.

**Erro: a extração gera poucos resultados**

- Causa: O site pode estar usando rotas internas, filtros muito restritivos ou profundidade pequena.
- Solução: Revise os filtros de inclusão/exclusão, aumente a profundidade e confira se o modo selecionado é `Site Completo (Crawler)`.

**Erro: o arquivo ZIP demora para aparecer**

- Causa: Saídas maiores exigem mais processamento para compactação.
- Solução: Aguarde a finalização da extração e tente baixar após a pasta de saída aparecer na interface.

---

## 🤝 Contribuição

Este é um projeto Open Source focado na liberdade de dados. Sinta-se à vontade para abrir Issues ou Pull Requests para melhorar o algoritmo.

Desenvolvido por **Pixelc Tech** - [www.pixelctech.com.br](https://www.pixelctech.com.br)

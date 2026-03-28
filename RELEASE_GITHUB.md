# Release GitHub

## Título sugerido

`v1.1.0 - Extração web mais robusta, presets de uso, RAG e nova interface`

## Descrição pronta para publicar

Esta release representa uma grande evolução do **Docling App** como produto e como ferramenta técnica.

O projeto saiu de uma base funcional de extração web para uma aplicação mais robusta, visualmente mais madura e muito mais preparada para uso em **documentação**, **automação**, **bases de conhecimento** e **fluxos com IA/RAG**.

### Destaques desta versão

- crawler mais confiável para sites modernos;
- melhor tratamento de URLs e rotas SPA;
- filtros mais avançados para controlar a coleta;
- presets de uso para objetivos reais;
- geração de artefatos prontos para RAG;
- histórico local mais rico e mais útil;
- tutorial integrado para facilitar o uso por qualquer pessoa;
- redesign completo da interface com identidade mais forte;
- melhorias de responsividade para telas menores;
- base inicial de testes automatizados.

### O que foi melhorado

#### Extração e crawler

- correção do tratamento de rotas com `#` em sites SPA;
- validação e normalização de URLs mais segura;
- bloqueio de links inválidos como `mailto:`, `tel:` e `javascript:`;
- suporte a profundidade máxima do crawler;
- suporte a filtros de inclusão e exclusão de caminhos;
- opção para ignorar arquivos não HTML comuns;
- limpeza mais segura de temporários;
- fechamento mais robusto de recursos do navegador.

#### Saídas e artefatos

- geração de arquivos em `Markdown`;
- geração de arquivos em `JSON`;
- criação de `manifest.json` com resumo da extração;
- criação opcional de `rag_chunks.jsonl` para uso em RAG;
- download dos resultados em `.zip`.

#### Interface e experiência de uso

- nova tela principal com visual mais profissional;
- sidebar com identidade visual premium;
- presets de uso com configuração automática;
- novo menu `Tutorial`;
- tutorial completo em linguagem simples;
- resumo visual das configurações atuais;
- troca automática para modo `Personalizado` quando o usuário altera um preset;
- melhor organização da área de execução;
- melhorias nas mensagens, estados vazios e ações finais;
- ajustes para melhorar a experiência em mobile.

#### Histórico e rastreabilidade

- histórico local mais completo em SQLite;
- registro de modo de extração, páginas processadas, arquivos gerados e erros;
- armazenamento de duração, timestamps e mensagens de falha;
- visualização mais rica do histórico na interface.

#### Estrutura e qualidade

- centralização de configurações do projeto;
- criação de camada dedicada para presets de uso;
- criação de módulo dedicado para artefatos;
- entrypoint principal mais claro com `streamlit_app.py`;
- atualização do README;
- criação de suíte inicial de testes automatizados.

### Validação

Validação executada no ambiente virtual do projeto:

```bash
venv/bin/python -m unittest discover -s tests -v
```

Resultado:

- 19 testes executados
- 19 testes aprovados

### Observação

Para rodar a aplicação e os testes corretamente, o recomendado é usar sempre o ambiente virtual do projeto.

### Links úteis

- [README](README.md)
- [CHANGELOG](CHANGELOG.md)

## Versão curta para release rápida

`v1.1.0` entrega uma evolução grande no Docling App: crawler mais robusto, presets de uso para cenários reais, melhor tratamento de URLs, geração de artefatos para RAG, histórico local enriquecido, tutorial integrado, redesign premium da interface e melhorias para mobile. Também amplia a suíte automatizada e melhora a estrutura geral do projeto para uso mais confiável no dia a dia.

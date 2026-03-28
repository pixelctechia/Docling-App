# Changelog

Todas as mudanças relevantes do projeto serão documentadas aqui.

## 2026-03-28 - Grande Atualização de Produto, Extração e UX

### Resumo Executivo

Esta atualização transformou o Docling App de um extrator funcional em uma plataforma muito mais completa para captura web, organização de conteúdo e preparação de dados para IA/RAG.

Os principais ganhos desta entrega foram:

- crawler mais confiável para sites modernos;
- melhor tratamento de URLs e rotas SPA;
- histórico local mais rico;
- central de histórico com ações operacionais;
- geração de artefatos para RAG;
- presets de uso para cenarios reais;
- interface mais clara, premium e amigável;
- tutorial integrado para usuários iniciantes;
- melhorias de responsividade para mobile;
- base inicial de testes automatizados.

### Melhorias no Motor de Extração

- correção do tratamento de rotas SPA com `#`;
- validação e normalização melhor de URLs;
- bloqueio de links inválidos como `mailto:`, `tel:` e `javascript:`;
- suporte a limite de profundidade do crawler;
- filtros de inclusão e exclusão de caminhos;
- opção para ignorar arquivos não HTML comuns;
- fechamento mais seguro de recursos do navegador;
- limpeza mais confiável de arquivos temporários;
- callbacks de progresso e logs para integração com a interface.

### Melhorias de Saída e Artefatos

- geração de arquivos em `Markdown`;
- geração de arquivos em `JSON`;
- criação de `manifest.json` com resumo da extração;
- criação opcional de `rag_chunks.jsonl` para fluxos de RAG;
- download dos resultados em `.zip`.

### Melhorias de Banco e Histórico

- enriquecimento do histórico local em SQLite;
- registro de modo de extração, páginas processadas, arquivos gerados e erros;
- armazenamento de duração, datas de início/fim e mensagem de falha;
- exibição mais completa do histórico na interface.
- suporte para limpeza completa dos registros do histórico.

### Melhorias de Interface e UX

- redesign visual da home principal;
- identidade visual reforçada para a Pixelc Tech;
- sidebar com estilo premium;
- novo menu `Tutorial` na lateral;
- tutorial completo em linguagem simples;
- resumo visual das configurações antes da execução;
- melhor organização da área de execução;
- mensagens de estado vazio mais claras;
- fluxo final de ações melhor organizado;
- nova central de histórico com visual unificado;
- exportação do histórico em CSV;
- ação manual para atualizar o histórico na interface;
- confirmação visual premium para ações sensíveis;
- botão para limpar histórico com confirmação;
- botão para limpar arquivos extraídos em `outputs` com confirmação;
- mini cards com contadores de registros, pastas e arquivos;
- novo sistema de presets de uso na sidebar;
- presets iniciais para chatbot institucional, documentação técnica e base para RAG;
- aplicação automática das configurações do preset na interface;
- mudança automática para modo `Personalizado` quando o usuário altera manualmente um preset aplicado;
- melhorias de legibilidade e uso em telas menores.

### Qualidade e Estrutura do Projeto

- criação do módulo de artefatos em `src/core/artifacts.py`;
- centralização de configurações em `src/config/settings.py`;
- criação do entrypoint `streamlit_app.py`;
- ajuste de imports absolutos para execução mais estável;
- endurecimento do import da camada de histórico na UI para evitar falhas de carregamento com reload do Streamlit;
- atualização do `README.md` com linguagem mais comercial;
- criação de `CHANGELOG.md` e `RELEASE_GITHUB.md` para documentação de releases;
- criação de testes automatizados com `unittest`.
- criação de testes automatizados para a camada de presets.

### Validação

Validação principal executada no ambiente virtual do projeto:

```bash
venv/bin/python -m unittest discover -s tests -v
```

Resultado da última validação:

- 19 testes executados;
- 19 testes aprovados.
- compilações locais de verificação executadas com `python -m compileall` nos módulos atualizados de UI e banco.

### Observações

- Ao rodar os testes fora do `venv`, algumas dependências do projeto podem não estar disponíveis no Python global da máquina.
- A forma recomendada de validar o projeto continua sendo pelo ambiente virtual local.

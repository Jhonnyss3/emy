# Documentação — Finances

Este diretório reúne os guidelines e padrões do projeto **Finances**, uma
aplicação web de finanças pessoais em Django 6. O objetivo é que qualquer
pessoa que acesse o repositório consiga entender como o projeto é
organizado e como contribuir seguindo os padrões estabelecidos.

## Índice

| Documento | Conteúdo |
|---|---|
| [getting-started.md](getting-started.md) | Como instalar dependências e rodar o projeto localmente. |
| [architecture.md](architecture.md) | Stack, estrutura de pastas e responsabilidade de cada app. |
| [data-model.md](data-model.md) | Models, enums, constraints e regras de integridade. |
| [coding-guidelines.md](coding-guidelines.md) | Idioma do código, ordem de implementação e estilo. |
| [security.md](security.md) | Práticas de segurança obrigatórias. |
| [frontend.md](frontend.md) | TailwindCSS, templates e estado da interface. |
| [workflow.md](workflow.md) | Git, migrations e testes. |

## Visão geral do produto

O Finances permite a um usuário registrar receitas e despesas, organizá-las
em categorias customizáveis e acompanhar o resultado do mês corrente em um
dashboard. Cada conta enxerga apenas os próprios dados.

O documento de requisitos completo está em [PRD.md](../PRD.md), na raiz do
repositório.
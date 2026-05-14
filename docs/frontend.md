# Frontend

## TailwindCSS

- **TailwindCSS v4 via `django-tailwind` no modo standalone** — não há Node.js
  nem `npm` no projeto. O `pytailwindcss` baixa o binário standalone do
  Tailwind CLI; o `django-tailwind` o orquestra.
- O app `theme` foi criado por `python manage.py tailwind init` (template
  "Tailwind v4 Standalone").
- Fonte do CSS: `theme/static_src/src/styles.css` — contém
  `@import "tailwindcss"` e a diretiva `@source` que faz o Tailwind escanear
  os `.html/.py/.js` do projeto em busca de classes utilitárias.
- CSS compilado: `theme/static/css/dist/styles.css` — artefato de build, está
  no `.gitignore`; o build precisa rodar no deploy.
- Settings: `INSTALLED_APPS` inclui `tailwind` e `theme`;
  `TAILWIND_APP_NAME = 'theme'`.
- `finances/templates/base.html` carrega o CSS via `{% load tailwind_tags %}`
  + `{% tailwind_css %}` no `<head>`.

### Comandos

- `python manage.py tailwind build` — build único.
- `python manage.py tailwind start` — modo watch para desenvolvimento.

## Templates

`APP_DIRS=True` — templates ficam em `finances/templates/`. O
`theme/templates/base.html` é gerado pelo `django-tailwind` e não é usado
pelo app `finances`, que tem o seu próprio `base.html`.

| Template | Conteúdo |
|---|---|
| `base.html` | Layout base com header, navegação e bloco de mensagens. |
| `finances/dashboard.html` | Cards de resumo + tabela de recentes. |
| `finances/transaction_list.html` | Tabela de transações + filtros por tipo. |
| `finances/transaction_form.html` | Formulário de criação/edição de transação. |
| `finances/category_list.html` | Tabela de categorias. |
| `finances/category_form.html` | Formulário de criação/edição de categoria. |
| `finances/confirm_delete.html` | Confirmação de exclusão (reusado por transação e categoria). |
| `registration/login.html` | Tela de login. |
| `registration/register.html` | Tela de cadastro. |

## Estado atual da UI

O TailwindCSS já está instalado, configurado e carregado no `base.html`. A
**conversão dos templates** para classes utilitárias do Tailwind ainda é
trabalho pendente — o `base.html` mantém um bloco `<style>` com CSS inline
herdado da v1, que coexiste com o Tailwind até a migração tela a tela
acontecer.

Ao criar template novo, preferir classes Tailwind. Ao editar template
existente, manter coerência com o que já está lá até a migração acontecer. O
design system de referência (cores, tipografia, botões, inputs, grids) está
no [PRD.md](../PRD.md), seção 9.
</content>
</invoke>

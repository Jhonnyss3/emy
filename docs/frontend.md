# Frontend

## TailwindCSS

- **TailwindCSS v4 via `django-tailwind` no modo standalone** — não há Node.js
  nem `npm` no projeto. O `pytailwindcss` baixa o binário standalone do
  Tailwind CLI; o `django-tailwind` o orquestra.
- O app `theme` foi criado por `python manage.py tailwind init` (template
  "Tailwind v4 Standalone").
- Fonte do CSS: `theme/static_src/src/styles.css` — contém
  `@import "tailwindcss"`, a diretiva `@source` que faz o Tailwind escanear
  os `.html/.py/.js` do projeto, e um bloco `@theme` com os tokens de design
  Emy (ver abaixo).
- CSS compilado: `theme/static/css/dist/styles.css` — artefato de build, está
  no `.gitignore`; o build precisa rodar no deploy.
- Settings: `INSTALLED_APPS` inclui `tailwind` e `theme`;
  `TAILWIND_APP_NAME = 'theme'`.
- `finances/templates/base.html` carrega as fontes do Google (Plus Jakarta
  Sans, Instrument Serif, Caveat) e o CSS via `{% load tailwind_tags %}`
  + `{% tailwind_css %}` no `<head>`.

### Comandos

- `python manage.py tailwind build` — build único. **Rodar sempre que mexer
  em template ou em `styles.css`**, senão as classes novas não entram no CSS.
- `python manage.py tailwind start` — modo watch para desenvolvimento.

## Design tokens — Emy / Petal

Os tokens vivem no bloco `@theme` de `theme/static_src/src/styles.css` e são
usados como classes utilitárias normais (`bg-emy-bg`, `text-emy-pink-600`,
`font-serif` etc.).

- **Cores:** `emy-bg` / `emy-bg-warm` / `emy-bg-deep` (off-whites rosados),
  `emy-surface` (branco), `emy-ink` / `emy-ink-soft` / `emy-ink-mute`
  (tinta roxo-escuro), `emy-line` / `emy-line-2` (divisórias),
  `emy-pink-50..700`, `emy-purple-50..700`, `emy-good` (verde) e
  `emy-bad` (vermelho).
- **Fontes:** `font-sans` → Plus Jakarta Sans (corpo), `font-serif` →
  Instrument Serif (destaques editoriais), `font-script` → Caveat
  (toques manuscritos).
- **Identidade "Petal":** off-white rosado, soft/feminino com glow, cards
  bem arredondados (`rounded-[2rem]` e afins), gradiente rosa→roxo
  (`from-emy-pink-500 to-emy-purple-500`) em botões/destaques, nav inferior
  flutuante.

## Templates

`APP_DIRS=True` — templates ficam em `finances/templates/`. O
`theme/templates/base.html` é gerado pelo `django-tailwind` e não é usado
pelo app `finances`, que tem o seu próprio `base.html`.

| Template | Conteúdo |
|---|---|
| `base.html` | Header (logo Emy + pílula de escopo ativo + nome do usuário com link para o perfil + Sair), nav inferior flutuante, bloco de mensagens. A pílula central mostra o escopo atual ("Pessoal" ou o nome do grupo) e leva à troca de escopo. O nome exibido é `first_name` (fallback para `username`). Estilização 100% Tailwind. |
| `finances/scope_switch.html` | Escolha do escopo ativo (Pessoal ou um grupo) + link "Gerenciar grupos". |
| `finances/household_list.html` | Lista dos grupos do usuário + botão "Novo grupo". |
| `finances/household_form.html` | Criação de grupo (nome). |
| `finances/household_detail.html` | Membros do grupo; o dono adiciona membro por e-mail e remove membros. |
| `finances/dashboard.html` | Saudação (usa `first_name`), card de saldo com gradiente (saldo/entrou/saiu/investido) + atalho "Listas da casa" quando o escopo é grupo + lista de lançamentos recentes. |
| `finances/transaction_list.html` | Pills de filtro por tipo + lista de transações em cards arredondados. |
| `finances/transaction_form.html` | Card dividido: toggle Despesa/Receita, valor grande, pills de categoria, data, método, observações. |
| `finances/category_list.html` | Grid de cards de categoria. |
| `finances/category_form.html` | Formulário de categoria (toggle de tipo, cor, ícone, ativo). |
| `finances/profile_form.html` | Formulário de perfil (nome, sobrenome, data de nascimento, telefone). Usado no preenchimento pós-cadastro e na edição. |
| `finances/investment_list.html` | Objetivos de investimento em cards com barra de progresso + total investido. |
| `finances/investment_form.html` | Criação/edição de objetivo (nome, meta, prazo opcional). |
| `finances/investment_detail.html` | Objetivo + progresso + form de aporte + lista de aportes. |
| `finances/list_index.html` | Listas de casa do grupo + botão "Nova lista". |
| `finances/list_form.html` | Criação de lista (nome). |
| `finances/list_detail.html` | Itens da lista com checkbox (toggle via POST) + form para adicionar item. |
| `finances/confirm_delete.html` | Confirmação de exclusão (reusado por transação, categoria, objetivo e lista). |
| `registration/login.html` | Tela de login por e-mail (card dividido com painel de gradiente; o campo mantém `name="username"`, exibido como "E-mail"). |
| `registration/register.html` | Tela de cadastro por e-mail (mesmo padrão do login; campo `email`). |

### Renderização de formulários

Os formulários renderizam cada campo manualmente (não usam `{{ form.as_p }}`)
para ter controle total das classes Tailwind sem tocar em `forms.py`/`views.py`:
cada `<input>`/`<select>` tem o `name=` correto, o valor é reposto via
`form.<campo>.value` e os erros via `form.<campo>.errors`. Os campos `type` e
`category` viram radios estilizados (toggle e pills).

### Botão "Voltar"

Os forms (`transaction_form`, `category_form`, `profile_form`) têm um botão
circular `←` padronizado no topo: fica **fora** do `<form>`, é `type="button"`
e usa `onclick="history.back()"` para voltar à página anterior real. Nos forms
com título fora do `<form>` (`category_form`, `profile_form`) ele fica ao lado
do título; no `transaction_form` (título dentro do card) fica acima do form.

## Estado atual da UI

Os templates foram migrados da v1 (CSS inline) para a identidade visual
**Emy — variação "Petal"**, escolhida entre três explorações de design
(Soft Bloom / Petal / Aurora). O bloco `<style>` inline foi removido do
`base.html`; toda a estilização é via classes Tailwind + tokens `emy-*`.

A migração cobriu **apenas as telas com model atual** (`Category` e
`Transaction`). Features que aparecem no mock de design mas não têm model —
Cartões/faturas, Metas, Insights, Transferência, Recorrência, busca global,
"remember-me" e recuperação de senha — **não** foram incluídas.

A tela de perfil (`profile_form.html`) foi adicionada depois, já na
identidade Petal, junto com o model `Profile`. As telas de grupo
(`scope_switch`, `household_list`, `household_form`, `household_detail`) e a
pílula de escopo no `base.html` vieram com a feature de compartilhamento, na
mesma identidade. O cadastro/login passaram a usar e-mail. Depois vieram as
telas de **investimentos** (`investment_*`) e de **listas de casa**
(`list_*`); a nav inferior ganhou o item "Investir" (Início / Lançamentos /
Investir / Categorias / `+`).

Pendências de UI conhecidas:

- O dashboard não tem o bloco "gastos por categoria" (donut + lista) do mock:
  cabe nos models atuais, mas exige um agregado por categoria na `dashboard`
  view.
- `get_type_display` / `get_payment_method_display` retornam rótulos em
  inglês (labels dos `choices` do model); nos templates isso é contornado
  com pt-BR manual. Correção real seria nos `choices` do model.
- Valores monetários usam `floatformat:2` (ex.: `4832.17`); o formato pt-BR
  (`4.832,17`) depende de configuração de locale.

Ao criar template novo, usar classes Tailwind e os tokens Emy. Ao editar um
existente, manter coerência com o padrão Petal já aplicado.

# Frontend

## TailwindCSS

- **TailwindCSS v4 via `django-tailwind` no modo standalone** — não há Node.js
  nem `npm` no projeto. O `pytailwindcss` baixa o binário standalone do
  Tailwind CLI; o `django-tailwind` o orquestra.
- O app `theme` foi criado por `python manage.py tailwind init` (template
  "Tailwind v4 Standalone").
- Fonte do CSS: `theme/static_src/src/styles.css` — contém
  `@import "tailwindcss"`, a diretiva `@source` que faz o Tailwind escanear
  os `.html/.py/.js` do projeto, um bloco `@theme` com os tokens de design
  Emy (ver abaixo) e um `@layer utilities` com a utility `.no-scrollbar`
  (esconde a barra de rolagem mantendo o scroll — usada no app shell).
- CSS compilado: `theme/static/css/dist/styles.css` — artefato de build, está
  no `.gitignore`; o build precisa rodar no deploy. Na imagem Docker o
  `tailwind build` roda antes do `collectstatic`. Em produção os estáticos são
  servidos pelo **WhiteNoise** (`CompressedManifestStaticFilesStorage`), que
  comprime e versiona com hash; por isso o `collectstatic` é obrigatório no
  build e os templates referenciam o CSS pelo manifest.
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

## Layout / app shell

O `base.html` monta um **app shell** de altura fixa: o `<body>` é
`h-[100dvh] flex flex-col overflow-hidden` (a página nunca rola) e o `<main>`
é a única área rolável (`flex-1 min-h-0 overflow-y-auto no-scrollbar`) — então
não aparece scrollbar e a estrutura fica sempre "numa tela". O conteúdo do
`main` é centralizado na vertical via `my-auto` (centra quando cabe; quando é
maior que a tela, volta ao topo e rola por dentro, sem barra visível).

- **Header (topo):** logo · **seletor de escopo (dropdown)** · nome do
  usuário/Sair. O seletor é um `<details>` que abre um menu com "Pessoal" + os
  grupos do usuário (✓ no ativo, troca via POST para `scope_switch`) +
  "Criar novo grupo" / "Gerenciar grupos". Fecha ao clicar fora (JS).
- **Nav inferior:** barra flutuante de ícones (Início / Lançamentos / Previsão /
  Investir / Categorias + botão `+`), centralizada, presente no mobile **e** no
  desktop. Cada item tem ícone (SVG) sempre visível e rótulo que aparece a
  partir de `sm:`. Item ativo via `request.resolver_match`.
- **Navegação por mês:** o dashboard e a lista de lançamentos têm setas ‹ › com
  o rótulo do mês (pt-BR) e atalho "Hoje"; trocam o mês via `?month=AAAA-MM`.
  As contas fixas se materializam ao abrir o mês.
- **Barra de loading:** `#page-loader` no topo (gradiente) disparada por
  cliques em links internos e submits; finaliza no `pageshow`.

### Responsividade — desktop 50/50

Mobile é coluna única; a partir de `lg:` as telas usam **duas colunas**
(`lg:grid lg:grid-cols-2 lg:gap-6`). Padrões por tipo de tela:

- **Dashboard:** cabeçalho + linha de 4 cards de stat (Saldo em destaque,
  Entrou, Saiu, Investido) em `lg:grid-cols-4`; abaixo, "Lançamentos recentes"
  (2/3) + card "Listas da casa" (1/3, só em grupo).
- **Listas/detalhe:** controles/resumo/forms à esquerda, lista à direita
  (colunas de altura igual onde faz sentido).
- **Forms:** padrão "card dividido" (`md:grid-cols-2`) — painel de gradiente
  com título à esquerda, campos à direita; empilha no mobile.

## Templates

`APP_DIRS=True` — templates ficam em `finances/templates/`. O
`theme/templates/base.html` é gerado pelo `django-tailwind` e não é usado
pelo app `finances`, que tem o seu próprio `base.html`.

| Template | Conteúdo |
|---|---|
| `base.html` | App shell: header (logo + seletor de escopo em dropdown + usuário/Sair), `main` rolável sem barra com conteúdo centralizado, nav inferior de ícones (mobile e desktop), barra de loading e bloco de mensagens. Ver seção **Layout / app shell**. |
| `finances/scope_switch.html` | Escolha do escopo ativo (Pessoal ou um grupo) + link "Gerenciar grupos". |
| `finances/household_list.html` | Lista dos grupos do usuário + botão "Novo grupo". |
| `finances/household_form.html` | Criação/edição de grupo (nome); rótulo do botão via `submit_label`. |
| `finances/household_detail.html` | Membros do grupo; o dono edita/exclui o grupo (ações no topo), adiciona membro por e-mail e remove membros. |
| `finances/dashboard.html` | Cabeçalho (saudação + navegação por mês + "+ Lançar"), linha de 4 cards de stat (Saldo destaque / Entrou / Saiu / Investido) do mês selecionado e área inferior com lançamentos do mês (selo "2/12" nas parcelas) + card "Listas da casa" (em grupo). Layout 50/50 no desktop. |
| `finances/forecast.html` | Previsão dos próximos 6 meses em cards (saldo previsto + entrou/saiu); cada card abre o mês no dashboard; mês atual em gradiente. |
| `finances/transaction_list.html` | Navegação por mês + pills de filtro por tipo (preservam o mês) + atalho "Contas fixas" + lista de transações (selo "2/12" nas parcelas). |
| `finances/transaction_form.html` | Card dividido: toggle Despesa/Receita, valor grande, pills de categoria, data, método, parcelas (só na criação), observações. |
| `finances/recurring_list.html` | Grid de cards das contas fixas (valor, dia, ativa/pausada) + ações. |
| `finances/recurring_form.html` | Card dividido de conta fixa (tipo, valor mensal, categoria, a partir de, método, ativa). |
| `finances/category_list.html` | Grid de cards de categoria. |
| `finances/category_form.html` | Formulário de categoria (toggle de tipo, cor, ícone, ativo). |
| `finances/profile_form.html` | Formulário de perfil (nome, sobrenome, data de nascimento, telefone). Usado no preenchimento pós-cadastro e na edição. |
| `finances/investment_list.html` | Objetivos de investimento em cards com barra de progresso + total investido. |
| `finances/investment_form.html` | Criação/edição de objetivo (nome, meta, prazo opcional). |
| `finances/investment_detail.html` | Objetivo + progresso + form de aporte + lista de aportes. |
| `finances/list_index.html` | Listas de casa do grupo + botão "Nova lista". |
| `finances/list_form.html` | Criação de lista (nome). |
| `finances/list_detail.html` | Itens da lista com checkbox (toggle via POST) + form para adicionar item. |
| `finances/confirm_delete.html` | Confirmação de exclusão (reusado por transação, categoria, objetivo, lista e grupo; grupo mostra aviso de exclusão em cascata). |
| `registration/login.html` | Tela de login por e-mail (card dividido com painel de gradiente; o campo mantém `name="username"`, exibido como "E-mail"). |
| `registration/register.html` | Tela de cadastro por e-mail (mesmo padrão do login; campo `email`). |

### Renderização de formulários

Os formulários renderizam cada campo manualmente (não usam `{{ form.as_p }}`)
para ter controle total das classes Tailwind sem tocar em `forms.py`/`views.py`:
cada `<input>`/`<select>` tem o `name=` correto, o valor é reposto via
`form.<campo>.value` e os erros via `form.<campo>.errors`. Os campos `type` e
`category` viram radios estilizados (toggle e pills).

### Botão "Voltar"

Os forms têm um botão circular `←` padronizado no topo: fica **fora** do
`<form>`, é `type="button"` e usa `onclick="history.back()"` para voltar à
página anterior real. Como todos os forms adotaram o **card dividido**
(`md:grid-cols-2`, painel de gradiente com título à esquerda + campos à
direita), o botão fica acima do card.

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
(`list_*`); a nav inferior ganhou o item "Investir".

Por fim, houve um **retrabalho de layout** (ver seção **Layout / app shell**):
a página virou app shell sem scrollbar; a nav inferior passou a ser de ícones
(rótulo só no desktop); o seletor de escopo virou dropdown; e o desktop adotou
o padrão **50/50** (`lg:grid-cols-2`), com o dashboard redesenhado em cards de
stat. O mobile permanece em coluna única.

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

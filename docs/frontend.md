# Frontend

## TailwindCSS

- **TailwindCSS v4 via `django-tailwind` no modo standalone** — o `pytailwindcss`
  baixa o binário standalone do Tailwind CLI; o `django-tailwind` o orquestra. O
  CSS **não** depende de Node; só o JS (Vite, ver seção **JavaScript / Vite**)
  usa Node/npm.
- O app `theme` foi criado por `python manage.py tailwind init` (template
  "Tailwind v4 Standalone").
- Fonte do CSS: `theme/static_src/src/styles.css` — contém
  `@import "tailwindcss"`, a diretiva `@source` que faz o Tailwind escanear
  os `.html/.py/.js` do projeto, um bloco `@theme` com os tokens de design
  Emy (cores, fontes e as **sombras nomeadas** `--shadow-card` e `--shadow-btn`,
  usadas como `shadow-card`/`shadow-btn` em vez das sombras arbitrárias antigas),
  um `@layer components` com as classes reutilizáveis `.card`
  (`bg-emy-surface` arredondado com `shadow-card`) e `.btn-primary` (botão
  gradiente rosa→roxo), e um `@layer utilities` com a utility `.no-scrollbar`
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

## JavaScript / Vite

- O JS do projeto é empacotado com **Vite** e integrado ao Django via
  **`django-vite`**. Antes era `<script>` inline nos templates; agora vive em
  módulos sob `frontend/src/`.
- Fonte: `frontend/src/main.js` (entry) importa os módulos de
  `frontend/src/modules/`:
  - `pageLoader` — barra de loading no topo (navegação/submits);
  - `scopeMenu` — fecha o dropdown de escopo ao clicar fora;
  - `passwordToggle` — mostra/oculta a senha no login;
  - `colorSwatches` — paleta de cores no form de categoria (botões
    `.color-swatch[data-color]` setam o `<input type="color">`);
  - `moneyMask` — máscara de moeda (campo visível formatado + `<input hidden>`
    com o valor numérico), via `data-money-display`/`data-money-target` (usado no
    campo Meta de investimento e nos campos de valor de **lançamento** e **conta
    fixa** — "quanto foi?" / "valor mensal"). O `<input hidden>` renderiza o valor
    com `|unlocalize` para não localizar o decimal (`1.234,56`) e quebrar o parse;
  - `categoryDonut` — desenha um donut (SVG puro, sem lib) de gastos por
    categoria no dashboard, lendo os dados de um `{% json_script %}`
    (`#category-data`);
  - `categorySelect` — dropdown customizado de categoria nos forms de lançamento
    e conta fixa (`[data-category-select]`): bolinha de cor, escreve no
    `<input hidden name="category">` e **filtra pela aba Despesa/Receita**
    selecionada, limpando a escolha incompatível;
  - `filterForm` — auto-submete o form de filtros ao mudar um controle marcado
    com `data-autosubmit` (usado na lista de lançamentos);
  - `selectWidget` — **enriquece todo `<select>` nativo** num dropdown
    estilizado (ver seção **Componentes de seleção**);
  - `dateWidget` — **widget de data** no padrão Emy (`[data-date-widget]`): um
    botão mostra a data em `dd/mm/aaaa`, um `<input hidden>` carrega o valor ISO
    (`AAAA-MM-DD`) que o form envia, e um popover desenha um calendário do mês
    em JS puro (navegação ‹ ›, "Hoje", "Limpar") — sem `<input type="date">`
    nativo, sem lib. Substitui os inputs de data de lançamento, conta fixa,
    perfil, investimento e aporte (e resolve na raiz o bug de localização da
    data na edição). Markup no partial `_date_field.html`;
  - `launchModal` — **modal global de lançamento** (desktop): abre/fecha o modal,
    alterna as abas Manual/Conta fixa e submete os forms via **AJAX** (ver seção
    **Modal de lançamento**).
  - `editModal` — **modal de edição por transação** (desktop) na lista de
    lançamentos: os gatilhos `[data-open-edit="<pk>"]` abrem o
    `[data-edit-modal="<pk>"]` correspondente (fechando os demais), e o submit é
    por AJAX para `transaction_update` (erros nos slots `[data-edit-error]`); no
    mobile o link segue para a página do form (ver seção **Modal de lançamento**).
  Cada módulo é guard-claused, então o bundle único roda em qualquer página.
- Build: `npm run build` gera `frontend/dist/` (bundle + `manifest.json`) —
  **artefato de build, no `.gitignore`**. **Recompilar sempre que mexer em JS**
  (análogo ao `tailwind build`). `npm run watch` recompila no desenvolvimento;
  `npm install` instala as deps na primeira vez.
- `base.html` carrega o bundle com `{% load django_vite %}` +
  `{% vite_asset 'frontend/src/main.js' %}` no `<head>`.
- Settings: `INSTALLED_APPS` inclui `django_vite`; `STATICFILES_DIRS = [('dist',
  BASE_DIR/'frontend'/'dist')]` mapeia o build para `/static/dist/`;
  `DJANGO_VITE` com `dev_mode` via `DJANGO_VITE_DEV_MODE` (default `False` — usa o
  bundle buildado, sem dev server), `manifest_path` em
  `frontend/dist/manifest.json` e `static_url_prefix='dist'`. O `collectstatic`
  coleta o `dist` e o WhiteNoise versiona/serve em produção.
- Na imagem Docker, um stage `assets` (Node) roda `npm ci && npm run build` e
  copia o `dist` antes do `collectstatic`.

## Componentes reutilizáveis

### Classes de componente (`@layer components`)

Padrões repetidos viram classe em `styles.css`, não utilitário copiado:

- `.card` — card de conteúdo (`bg-emy-surface` arredondado + `shadow-card`).
- `.btn-primary` — botão de ação principal (gradiente rosa→roxo, pill, branco).
- Sombras nomeadas `shadow-card` / `shadow-btn` (tokens `@theme`) substituem as
  sombras arbitrárias longas.

Botões de tamanho/contexto diferente (submits dos forms etc.) seguem como
utilitários; a classe cobre o caso canônico.

### Partials (`{% include %}`)

Trechos de markup repetidos viram partial parametrizado em `finances/templates/finances/`:

- `_back_button.html` — botão circular "Voltar" (`history.back()`), usado nos
  forms e telas com título.
- `_empty_state.html` — estado vazio centralizado; aceita `message`,
  `action_url`, `action_label` e `extra_classes`.
- `_progress_bar.html` — barra de progresso; aceita `percent` e `track_class`
  (altura/margem).
- `_category_select.html` — dropdown de categoria dos forms (ver
  **Componentes de seleção**); agrupa as opções por natureza Fixa/Variável.
- `_date_field.html` — **widget de data** (ver módulo `dateWidget`); aceita
  `name`, `value` (data ou string ISO) e `input_id` opcional.
- `_launch_modal.html` — **modal global de lançamento** com abas Manual/Conta
  fixa; incluído no `base.html` (ver **Modal de lançamento**).
- `_edit_modal.html` — **modal de edição de transação**, renderizado por item no
  loop da lista de lançamentos (a partir do objeto `t`); reusa o
  `_category_select.html` (com `categories` + `selected`), o `_date_field.html` e
  a máscara de moeda (ver **Modal de lançamento**).

### Formatação de dinheiro (`brl`)

Valores monetários usam o filtro `brl` (templatetag em
`finances/templatetags/money.py`): `{{ valor|brl }}` → `R$ 1.234,56` (pt-BR,
com milhar e sinal). Carregar com `{% load money %}` no template. Substitui o
antigo `R$ {{ x|floatformat:2 }}`.

## Componentes de seleção e dados dinâmicos

> **Regra:** todo componente de seleção é um **widget estilizado** no padrão
> Emy — nunca o controle nativo cru. Vale para os dropdowns de hoje e para
> futuros toggles/checkboxes (que devem adotar a mesma abordagem de widget +
> tokens Emy quando criados).

- **Todo `<select>` nativo vira widget** automaticamente pelo módulo
  `selectWidget`: o `<select>` é escondido (segue como fonte do valor para o
  submit e dispara `change`), e o JS desenha um botão + painel estilizados,
  herdando as classes do `<select>` para combinar com o contexto. Opções com
  `data-color` ganham bolinha de cor. Como o nativo permanece no DOM, o
  `data-autosubmit` (auto-submit de filtros) continua funcionando.
- **Exceções já-widget:** o dropdown de categoria dos forms
  (`_category_select.html` + módulo `categorySelect`, com filtro por tipo e
  **agrupamento por natureza Fixa/Variável** — o `categorySelect` esconde o
  cabeçalho de um grupo quando o filtro de tipo zera suas opções) e o seletor de
  escopo no header (`<details>` em `base.html`) já são widgets no mesmo padrão
  visual — não usam o `selectWidget` genérico.
- **Campo de parcelas:** o campo "Parcelas" do lançamento é um `<select>`
  (enum estático "À vista (1x)" a "24x"), enriquecido pelo `selectWidget` — não
  mais um `<input type="number">` cru.
- **Campo de data:** ver o módulo `dateWidget` / partial `_date_field.html` — é
  o widget de seleção de data no padrão Emy (não usa o `<input type="date">`).
- **Regra de dado dinâmico (criado pelo usuário):** todo select de dado
  dinâmico (ex.: categorias) deve **sempre** oferecer, na própria listagem do
  widget, a opção de **criar um novo** — não só quando a lista está vazia. No
  `selectWidget` genérico isso vem das data-attrs `data-create-url`
  (obrigatória) e `data-create-label` (opcional), que adicionam um item "+ Criar
  …" no rodapé do painel. No `_category_select.html` o link "Criar nova
  categoria" é fixo no rodapé. Selects de **enum estático** (ex.: forma de
  pagamento) **não** recebem esse item. O mesmo espírito vale para o seletor de
  escopo, que sempre traz "Criar novo grupo".

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
  cliques em links internos e submits; finaliza no `pageshow`. A lógica vive no
  módulo `pageLoader` (bundle do Vite), não mais inline.

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

## Modal de lançamento

O lançamento é o **form padrão do sistema** e vive num **modal global**
(`_launch_modal.html`, incluído no `base.html` para o usuário autenticado),
com abas **Manual** (`TransactionForm`) e **Conta fixa** (`RecurringTransactionForm`).

- **Abertura:** os botões de lançar (`+ Lançar` no dashboard, `+ Lançamento` na
  lista, `+` da nav inferior) levam `data-open-launch`. No **desktop** (≥ `lg`,
  1024px) o módulo `launchModal` intercepta o clique e abre o modal; no
  **mobile** o link segue para a página do form (comportamento padrão).
- **Forms no contexto:** o context processor `finances.context_processors.scope`
  expõe `launch_transaction_form` e `launch_recurring_form` (não vinculados,
  no escopo ativo; o manual já vem com `date` = hoje). Por isso o modal renderiza
  em qualquer página. Os campos usam ids prefixados (`id_lm_tx_*`/`id_lm_rt_*`)
  para não colidir entre as duas abas.
- **Submit por AJAX:** o `launchModal` envia via `fetch` com
  `X-Requested-With: XMLHttpRequest`. As views `transaction_create`/`recurring_create`
  respondem JSON quando é AJAX: `{"ok": true}` no sucesso (o JS recarrega a
  página atual, e a `messages.success` aparece no reload) e
  `{"ok": false, "errors": {...}}` (HTTP 400) na validação — o JS injeta as
  mensagens nos slots `[data-launch-error="<campo>"]` do modal **sem recarregar**,
  preservando o que foi digitado. Fora do AJAX (mobile/fallback) as views seguem
  renderizando a página e redirecionando como antes.
- Dentro do modal os componentes novos rodam normalmente (widget de data,
  máscara de valor, select de categoria agrupado, `selectWidget`).

### Edição (modal por transação)

A edição na lista de lançamentos espelha o modal de criação, com o mesmo padrão
de AJAX, mas para `transaction_update`:

- **Renderização server-side por item:** o `_edit_modal.html` é incluído no loop
  da lista, um modal por transação, preenchido a partir do objeto `t` (e das
  `categories` do escopo já no contexto — **sem** instanciar um `TransactionForm`
  por item). Optou-se por isso porque os widgets (data/categoria/moeda/
  `selectWidget`) são inicializados uma vez no load e não têm API para repopular;
  renderizar pronto no servidor é mais robusto que injetar HTML por AJAX ou
  "setar" widgets via JS. Não tem abas nem parcelas (não se aplicam à edição); os
  ids são prefixados pela pk (`id_em_*_<pk>`) para não colidir entre os modais.
- **Abertura:** "Editar" (ou clicar na descrição) leva `data-open-edit="<pk>"`;
  no desktop o `editModal` abre o `[data-edit-modal="<pk>"]`; no mobile segue para
  a página do form.
- **Submit por AJAX:** igual ao create — `{"ok": true}` recarrega; erros vão para
  os slots `[data-edit-error="<campo>"]` sem recarregar.
- **Trade-off:** um modal por transação no DOM (coerente com a lista, que carrega
  o mês inteiro sem paginação); se pesar, evoluir para um único modal sob demanda.

## Templates

`APP_DIRS=True` — templates ficam em `finances/templates/`. O
`theme/templates/base.html` é gerado pelo `django-tailwind` e não é usado
pelo app `finances`, que tem o seu próprio `base.html`.

| Template | Conteúdo |
|---|---|
| `base.html` | App shell: header (logo + seletor de escopo em dropdown + usuário/Sair), `main` rolável sem barra com conteúdo centralizado, nav inferior de ícones (mobile e desktop), barra de loading, bloco de mensagens e o **modal global de lançamento** (`_launch_modal.html`). Ver **Layout / app shell** e **Modal de lançamento**. |
| `finances/scope_switch.html` | Escolha do escopo ativo (Pessoal ou um grupo) + link "Gerenciar grupos". |
| `finances/household_list.html` | Lista dos grupos do usuário + botão "Novo grupo". |
| `finances/household_form.html` | Criação/edição de grupo (nome); rótulo do botão via `submit_label`. |
| `finances/household_detail.html` | Membros do grupo; o dono edita/exclui o grupo (ações no topo), adiciona membro por e-mail e remove membros. |
| `finances/dashboard.html` | Cabeçalho (saudação + navegação por mês + "+ Lançar"), linha de 4 cards de stat (Saldo destaque / Entrou / Saiu / Investido), card do total no **cartão de crédito** do mês, lançamentos do mês (selo "2/12") + card "Listas da casa" (em grupo), e dois recortes de despesa do mês: **gastos por categoria** (com **donut** SVG) e **por forma de pagamento**. Layout 50/50 no desktop. |
| `finances/forecast.html` | Previsão dos próximos 6 meses em cards (saldo previsto + entrou/saiu); cada card abre o mês no dashboard; mês atual em gradiente. |
| `finances/transaction_list.html` | Layout 50/50: **painel de filtros + resumo** à esquerda (fixo no desktop — navegação por mês, **ordenação Data \| Valor**, resumo Entrou/Saiu/Saldo do período filtrado, filtros combináveis de tipo/categoria/forma de pagamento/busca, "Contas fixas" e "Limpar filtros") e a lista de transações à direita (selo "2/12"; com cabeçalhos Receitas/Despesas quando ordenado por valor). Os filtros e a ordenação preservam o mês e auto-submetem. No desktop, "Editar" abre o **modal de edição** (`_edit_modal.html`) da transação; no mobile vai para a página do form. |
| `finances/transaction_form.html` | Card dividido: toggle Despesa/Receita, valor grande com **máscara de moeda**, **dropdown de categoria** (widget filtrado por tipo e agrupado por natureza), **widget de data**, método, **parcelas como `<select>`** (só na criação), observações. |
| `finances/_back_button.html`, `_empty_state.html`, `_progress_bar.html`, `_category_select.html`, `_date_field.html`, `_launch_modal.html`, `_edit_modal.html` | Partials reutilizáveis (ver **Componentes reutilizáveis**, **Componentes de seleção** e **Modal de lançamento**). |
| `finances/recurring_list.html` | Grid de cards das contas fixas (valor, dia, ativa/pausada) + ações. |
| `finances/recurring_form.html` | Card dividido de conta fixa (tipo, valor mensal, categoria, a partir de, método, ativa). |
| `finances/category_list.html` | Cards de categoria agrupados por **natureza** (seções Fixa/Variável). |
| `finances/category_form.html` | Formulário de categoria (toggle de tipo, **toggle de natureza Fixa/Variável**, cor, ícone, ativo). |
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

Depois vieram ajustes de UI: ícone da categoria virou **upload de imagem**
(`ImageField`), o form de categoria ganhou uma **paleta de cores** prontas, o
campo Meta de investimento ganhou **máscara de moeda**, os cards "Entrou/Saiu"
do dashboard viraram atalhos para a lista filtrada por tipo, e o JS inline foi
migrado para o **Vite** (ver seção **JavaScript / Vite**).

A leva mais recente (UI v0.2): o dashboard ganhou o total no **cartão de
crédito** e os recortes de **gastos por categoria** (com **donut** SVG) e por
**forma de pagamento**; o dinheiro passou a usar o filtro **`brl`** (pt-BR
`R$ 1.234,56`); padrões repetidos viraram **classes de componente**
(`.card`/`.btn-primary`, sombras nomeadas) e **partials**
(`_back_button`/`_empty_state`/`_progress_bar`); a **lista de lançamentos** foi
redesenhada com painel de filtros + resumo; a seleção de categoria virou
**dropdown widget** e **todo `<select>` passou a ser widget**
(ver **Componentes de seleção**); e o app ganhou **favicon** SVG e o selo
**Beta V0.2**.

A leva mais recente (rodada de ajustes do tester): os campos de valor de
**lançamento** e **conta fixa** ganharam **máscara de moeda**; os inputs de data
viraram um **widget de data** próprio (`dateWidget`/`_date_field.html`),
corrigindo na raiz o bug da data sumir na edição; a **descrição** parou de cortar
(quebra em até 2 linhas na lista e no dashboard); a lista de lançamentos ganhou
**ordenação Data \| Valor** (em Valor, agrupa Receitas/Despesas, maior→menor);
`Category` ganhou **natureza Fixa/Variável** (grupos fixos) que agrupa a listagem
e o select de categoria; o campo **Parcelas** virou `<select>` (widget); e o
**lançamento virou um modal global** (abas Manual/Conta fixa, AJAX, desktop)
com fallback por URL no mobile (ver **Modal de lançamento**).

A leva mais recente: a **edição** de lançamento na lista também virou **modal**
(desktop), espelhando o de criação — um modal por transação renderizado no loop,
preenchido a partir do objeto e submetido por AJAX para `transaction_update`
(`editModal` / `_edit_modal.html`); o `_category_select.html` foi generalizado
para aceitar `categories` + `selected` (ver seção **Modal de lançamento** →
**Edição**).

Pendências de UI conhecidas:

- Nenhuma das anteriores em aberto (donut e formato pt-BR já entregues). Itens do
  mock sem model (Cartões/faturas, Metas, Insights, Transferência) seguem fora
  de escopo.

Ao criar template novo, usar classes Tailwind e os tokens Emy, reaproveitando as
**classes de componente** (`.card`, `.btn-primary`), os **partials** e o filtro
**`brl`**. Componentes de seleção sempre como **widget** (ver **Componentes de
seleção**); selects de dado dinâmico sempre com a opção de **criar**. Ao editar
um existente, manter coerência com o padrão Petal já aplicado.

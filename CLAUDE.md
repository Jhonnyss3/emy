# CLAUDE.md — Finances

## Idioma e Comunicação

- Sempre responder em português (pt-BR).
- Ser direto e objetivo, sem enrolação.
- Explicar o "por que" de decisões técnicas somente quando solicitado.
- Nunca usar emojis nas respostas.
- Ao responder com passo a passo, enviar somente 1 passo por vez e aguardar comando para o próximo.
- O código é sempre escrito em inglês e a interface ao usuário em português — ver seção **Idioma do Código**.

---

## Ordem de Implementação (Django)

Ao adicionar ou editar funcionalidades em qualquer app, seguir sempre esta ordem:

**model → form → view → url → template**

---

## Idioma do Código

- **Todo o código é escrito em inglês, sem exceção.** Isso vale para nomes de models, campos de banco de dados, classes, funções, métodos, variáveis, argumentos, constantes, nomes de templates, nomes de rotas (`name=`), `app_name`, arquivos e diretórios.
- Comentários e docstrings (quando existirem) também em inglês.
- A **interface exibida ao usuário** é em português (pt-BR): labels de formulário, mensagens de `messages`, textos de template, `verbose_name`, `help_text`, opções de choices voltadas ao usuário.
- Em resumo: identificador de código → inglês; texto que o usuário lê na tela → português.
- Não misturar os dois idiomas em um mesmo identificador (`criar_transaction`, `transaction_lista` etc. são proibidos).

---

## Estilo de Código

- Incluir comentários apenas onde a lógica não for autoevidente.
- Não adicionar docstrings, type annotations ou comentários em código que não foi alterado.
- Não adicionar tratamento de erros ou validações para cenários fora do escopo atual.
- Preferir editar arquivos existentes a criar novos.
- Não criar arquivos de documentação (*.md) salvo quando explicitamente solicitado.
- Validações de domínio ficam centralizadas em `Model.clean()`, não espalhadas nas views.

---

## Comportamento Geral

- Nunca fazer mais do que foi pedido. Sem refatorações ou melhorias não solicitadas.
- Não usar abstrações ou utilitários para operações pontuais.
- Soluções devem ter o mínimo de complexidade necessária para a tarefa atual.
- Confirmar antes de executar ações destrutivas ou irreversíveis.

---

## Segurança

- **Segredos nunca no código nem no versionamento.** `SECRET_KEY`, credenciais de banco, chaves de API e afins vêm de variáveis de ambiente (`os.environ`). `.env` deve estar no `.gitignore`.
- **`DEBUG = False` em produção.** `DEBUG = True` expõe stack traces e settings; só em desenvolvimento. `ALLOWED_HOSTS` deve ser restrito em produção.
- **Isolamento de dados por escopo é obrigatório.** Toda query de `Category`/`Transaction` passa pelos managers de escopo — `Model.objects.in_scope(request.user, household)`, com `household = get_active_household(request)` (que valida a membership). No escopo pessoal filtra por `user` + `household IS NULL`; no de grupo, por `household`. Use `get_object_or_404(Model.objects.in_scope(request.user, household), pk=pk)`; nunca confiar em `pk` da URL sem o filtro de escopo.
- **Toda view de dados leva `@login_required`.** Views públicas são a exceção e devem ser conscientes.
- **CSRF em todo formulário POST** — `{% csrf_token %}` no template; nunca desabilitar a proteção CSRF.
- **Ações destrutivas (delete) só via POST**, nunca GET — com tela/etapa de confirmação.
- **Senhas**: sempre via `django.contrib.auth` (hash PBKDF2). Nunca armazenar, logar ou trafegar senha em texto puro. Manter os `AUTH_PASSWORD_VALIDATORS` ativos.
- **Proteção contra brute force no login** via `django-axes`: bloqueio após `AXES_FAILURE_LIMIT` (5) tentativas falhas pela combinação IP + username, com cooloff de 1h e reset no sucesso. `AxesStandaloneBackend` é o primeiro em `AUTHENTICATION_BACKENDS` e `AxesMiddleware` é o último em `MIDDLEWARE`. Não remover nem reordenar sem entender o impacto.
- **Nunca interpolar input do usuário em SQL/HTML cru.** Usar o ORM (que parametriza) e a auto-escape do template engine. Evitar `raw()`, `extra()`, `mark_safe`, `|safe` e `format_html` com dado não confiável.
- **Validar e tipar todo input** via `Form`/`ModelForm` antes de tocar no banco. Não construir objetos direto de `request.POST`.
- **Uploads**: hoje há um upload de imagem (ícone de categoria, `ImageField` + Pillow). Restringir a imagens (o template usa `accept="image/*"`), nunca servir arquivo de usuário como executável, e guardar fora do diretório de código (em produção, no volume do Railway via `MEDIA_ROOT`). A mídia é servida por uma rota própria (`media/...` → `django.views.static.serve`) porque o WhiteNoise só serve estáticos, não mídia de usuário.
- **Não logar dados sensíveis** (senhas, tokens, PII desnecessária).
- Em produção: HTTPS obrigatório. O `settings.py` tem um bloco `if not DEBUG:` que ativa automaticamente `SECURE_SSL_REDIRECT` (configurável via env), `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS` (configurável via env, default 1 ano) + `INCLUDE_SUBDOMAINS`/`PRELOAD` e `SECURE_PROXY_SSL_HEADER` (confia no `X-Forwarded-Proto` do proxy que termina o TLS — o edge do Railway). Em desenvolvimento (`DEBUG=True`) o bloco fica inerte. No Railway o TLS é terminado no edge e o healthcheck bate por HTTP interno, então `SECURE_SSL_REDIRECT` é definido como `False` por env (senão o healthcheck toma 302). Ver seção **Deploy**.
- Antes de cada release: rodar `python manage.py check --deploy` e resolver os apontamentos (hoje retorna 0 com `DEBUG=False` + `ALLOWED_HOSTS` preenchido).

---

## Boas Práticas Python/Django

- **Seguir a PEP 8** e as convenções idiomáticas do Django. Nomes: `snake_case` para funções/variáveis, `PascalCase` para classes, `UPPER_SNAKE` para constantes.
- **"Fat models, thin views".** Regra de negócio e validação ficam no model (`clean()`, métodos, properties); a view orquestra request/response e delega.
- **Validação de domínio centralizada em `Model.clean()`** — para que admin, forms e scripts compartilhem a mesma regra. Forms só cuidam de apresentação e input.
- **Não repetir o ORM nas views.** Lógica de query reutilizada vira método de `Manager`/`QuerySet` ou função auxiliar — uma única fonte de verdade.
- **Evitar consultas N+1**: usar `select_related` (FK/OneToOne) e `prefetch_related` (M2M/reverse FK) sempre que iterar sobre relações em template ou view.
- **Nunca consultar o banco dentro de loop de template.** Preparar os dados na view.
- **`Decimal` para dinheiro**, nunca `float`. Já é o caso de `Transaction.amount`.
- **Datas/horas com timezone** — usar `django.utils.timezone` (`timezone.now()`, `timezone.localdate()`), nunca `datetime.now()`. `USE_TZ = True`.
- **Operações destrutivas ou de múltiplas escritas** que precisam ser atômicas usam `transaction.atomic()`.
- **`get_object_or_404`** em vez de `try/except Model.DoesNotExist` espalhado.
- **Constraints no banco** (`UniqueConstraint`, `CheckConstraint`) além da validação no `clean()` — defesa em profundidade; o `clean()` não roda em `bulk_create`/`update`.
- **Migrations versionadas junto com o código.** Toda mudança de model gera migration; revisar o arquivo gerado antes de commitar.
- **Reaproveitar o que o Django já oferece** (auth, forms, generic views, messages, paginação) antes de escrever solução própria.
- **Settings sensíveis a ambiente** não ficam hardcoded — vêm de variável de ambiente com default seguro para desenvolvimento.
- **Toda nova funcionalidade tem teste** (`TestCase`), cobrindo o caminho feliz e as validações de `clean()`/constraints.
- Não deixar `print()` de depuração no código — usar o módulo `logging` quando necessário.

---

## Git

- Somente criar commits quando explicitamente solicitado.
- Nunca usar `--no-verify` ou pular hooks.
- Nunca fazer force push para main/master sem confirmação explícita.
- Sempre criar commits novos, nunca amend sem instrução direta.
- Mensagem de commit: concisa, focada no "por que", em português.
- Nunca incluir a linha `Co-Authored-By` nas mensagens de commit (vale tanto para commits criados quanto para mensagens geradas a pedido).

---

## Migrations

- Rodar `python manage.py makemigrations` e revisar o arquivo gerado antes de `migrate`.
- Não editar migrations já aplicadas em algum ambiente.
- Data migrations destrutivas (mover dados antes de remover coluna/tabela) devem fazer backup do banco antes do deploy.
- Reproduzir o `migrate` global (sem nome de app) antes do deploy para validar a ordem topológica.

---

## Deploy

- **Produção no Railway**, a partir do `Dockerfile` (multi-stage: builder com venv + stage `assets` com Node para o build do JS + runtime mínimo rodando como usuário **não-root**). `railway.json` define o builder (`DOCKERFILE`) e o healthcheck (`/accounts/login/`). Push na branch `main` do GitHub dispara o rebuild.
- O stage `assets` roda `npm ci && npm run build` (gera `frontend/dist`); o runtime copia esse `dist`, roda `tailwind build` e depois `collectstatic` (com um `SECRET_KEY` descartável só para o settings importar durante o build). O `entrypoint.sh` cria o `MEDIA_ROOT` (volume), roda `migrate --noinput` no start e então entrega ao `CMD` (gunicorn). Não rodar `migrate` manualmente no deploy.
- Estáticos servidos por **WhiteNoise**; **mídia de usuário** (uploads) gravada num **volume do Railway** montado em `MEDIA_ROOT` (filesystem do container é efêmero — sem volume os uploads somem a cada deploy) e servida pela rota `media/...`; banco **PostgreSQL** via `DATABASE_URL`; servidor **Gunicorn** (porta de `${PORT}`).
- **Variáveis no painel do Railway** (serviço web): `SECRET_KEY`, `DEBUG=False`, `DATABASE_URL`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SECURE_SSL_REDIRECT=False`, `MEDIA_ROOT` (= mount path do volume, ex.: `/data`), `PORT`. Criar também o **Volume** apontando para esse mount path. O healthcheck do Railway usa `Host: healthcheck.railway.app` (já tratado no `settings.py`). Detalhes em `docs/security.md` e `docs/getting-started.md`.
- **Stack local com Docker:** `docker-compose.yml` sobe `web` (gunicorn) + `db` (PostgreSQL); variáveis em `.env.docker` (modelo `.env.docker.example`). `docker compose up --build`.
- O **login automático pós-cadastro** (`register`) precisa do backend explícito (`login(request, user, backend="django.contrib.auth.backends.ModelBackend")`) porque há múltiplos backends (`django-axes`) — sem ele, 500.

---

## Visão Geral do Projeto

**Finances** é uma aplicação web de finanças pessoais. O usuário registra receitas e despesas, organiza-as em categorias customizáveis e acompanha o resultado do mês em um dashboard. Cada conta tem suas finanças pessoais privadas e pode participar de **grupos** (`Household`) — espaços compartilhados onde os membros lançam e acompanham contas em conjunto (ex.: a conta da casa de um casal). Há ainda **investimentos com objetivos** (pessoal e grupo, fluxo separado do caixa) e **listas de casa** (checklists compartilhadas, só em grupo). O cadastro e o login são por **e-mail**.

**Stack:**
- Python 3.14 / Django 6.0.5
- SQLite (desenvolvimento) — `db.sqlite3`
- PostgreSQL (produção — via `DATABASE_URL` + `dj-database-url`; mesmo ORM, sem mudança de modelo)
- Frontend: Django Template Language (sem framework JS separado); o JavaScript é empacotado com **Vite** (ver seção Frontend)
- Estilização: TailwindCSS v4 via `django-tailwind` no **modo standalone** (binário próprio, independente do Node — ver seção Frontend / TailwindCSS)
- JavaScript: **Vite** + `django-vite` empacota os módulos de `frontend/src/` (Node usado só no build do JS; o Tailwind segue standalone)
- Imagens enviadas pelo usuário (ícone de categoria): `ImageField` + **Pillow**, servidas via `MEDIA_URL`; em produção o `MEDIA_ROOT` aponta para um volume do Railway (ver seção Deploy)
- Autenticação: `django.contrib.auth` com `User` nativo
- Admin: `django.contrib.admin`
- Produção: containerizada (`Dockerfile` multi-stage), servida por **Gunicorn** com **WhiteNoise** para os estáticos, deploy no **Railway** (ver seção Deploy)

**Como rodar localmente:**
```bash
source .venv/bin/activate         # ativa o virtualenv
npm install                       # instala as deps do front (Vite) — uma vez
python manage.py migrate          # aplica migrations
python manage.py tailwind build   # compila o CSS (necessário ao menos uma vez)
npm run build                     # compila o JS (bundle do Vite — necessário ao menos uma vez)
python manage.py createsuperuser  # opcional, para acessar /admin/
python manage.py runserver        # inicia o servidor em localhost:8000
```

Durante o desenvolvimento de UI, manter `python manage.py tailwind start` (recompila o CSS) e `npm run watch` (recompila o JS) rodando em outros terminais.

Dependências Python em `requirements.txt` (Django, asgiref, sqlparse, django-tailwind, pytailwindcss, python-dotenv, django-axes, Pillow, django-vite, pytest, pytest-django, e as de produção: gunicorn, whitenoise, psycopg[binary], dj-database-url). Dependências de front em `package.json` (Vite).

As variáveis sensíveis (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`) ficam num `.env` na raiz (não versionado), carregado pelo `python-dotenv`. Copie o `.env.example` para `.env` e preencha o `SECRET_KEY` antes de rodar. Sem `DATABASE_URL`, usa o SQLite local.

**Rodar com Docker / deploy:** o projeto é containerizado e roda em produção no Railway. Ver a seção **Deploy** e `docs/getting-started.md`.

**Estrutura de pastas:**
```
emy/
├── core/                 # Projeto Django (settings, urls, wsgi/asgi)
├── finances/             # App de domínio
│   ├── models.py         # Category, Transaction, Profile, Household, HouseholdMembership, TransactionType, PaymentMethod
│   ├── forms.py          # RegistrationForm, CategoryForm, TransactionForm, ProfileForm, HouseholdForm, MemberAddForm
│   ├── views.py          # register, profile_edit, dashboard, CRUD, grupos, escopo
│   ├── middleware.py     # ProfileCompletionMiddleware
│   ├── context_processors.py  # scope (active_household + user_households)
│   ├── admin.py          # CategoryAdmin, TransactionAdmin
│   ├── urls.py           # rotas do app (app_name = "finances")
│   ├── migrations/
│   └── templates/        # base.html, finances/, registration/
├── theme/                # App do django-tailwind (gerado por `tailwind init`)
│   ├── static_src/src/styles.css   # fonte do Tailwind (@import + @source)
│   └── static/css/dist/styles.css  # CSS compilado (artefato de build)
├── frontend/             # Fonte e build do JS (Vite)
│   ├── src/main.js       # entry; importa os módulos de src/modules/
│   ├── src/modules/      # pageLoader, scopeMenu, passwordToggle, colorSwatches, moneyMask, categoryDonut, categorySelect, filterForm, selectWidget
│   └── dist/             # bundle compilado + manifest.json (artefato de build, no .gitignore)
├── docs/                 # Documentação de guidelines e padrões (índice em docs/README.md)
├── Dockerfile            # Imagem multi-stage (builder + assets/Node + runtime non-root)
├── entrypoint.sh         # Cria o MEDIA_ROOT, roda migrate no start e entrega para o gunicorn (CMD)
├── docker-compose.yml    # Stack local: web (gunicorn) + db (PostgreSQL)
├── railway.json          # Config de build/healthcheck do Railway
├── package.json          # Deps e scripts do front (Vite)
├── vite.config.js        # Config do Vite (build do JS para frontend/dist)
├── .dockerignore
├── .env.example          # Modelo do .env (desenvolvimento)
├── .env.docker.example   # Modelo do .env.docker (stack docker-compose)
├── manage.py
├── requirements.txt
├── db.sqlite3
├── PRD.md                # Product Requirement Document
└── CLAUDE.md
```

---

## Estrutura de Apps

| App | Responsabilidade |
|---|---|
| `core` | Projeto Django — settings, URLs raiz, wsgi/asgi. Sem models próprios. |
| `finances` | App de domínio — categorias, transações, perfil do usuário, dashboard e telas de autenticação. |
| `theme` | App gerado pelo `django-tailwind` — guarda a fonte e o build do CSS. Sem models nem views próprios. |

Autenticação usa o `User` nativo de `django.contrib.auth` — não há app `accounts` nem custom user model.

---

## Frontend / TailwindCSS

- **TailwindCSS v4 via `django-tailwind` no modo standalone** — o `pytailwindcss` baixa o binário standalone do Tailwind CLI; o `django-tailwind` o orquestra. O CSS **não** depende de Node; só o JS (Vite) usa Node/npm.
- O app `theme` foi criado por `python manage.py tailwind init` (template "Tailwind v4 Standalone").
- Fonte do CSS: `theme/static_src/src/styles.css` — contém `@import "tailwindcss"`, a diretiva `@source` que faz o Tailwind escanear todos os `.html/.py/.js` do projeto, um bloco `@theme` com os **tokens de design Emy**: cores `emy-*` (`emy-bg`, `emy-ink`, `emy-pink-*`, `emy-purple-*`, `emy-good`, `emy-bad` etc.) e fontes `font-sans` (Plus Jakarta Sans), `font-serif` (Instrument Serif), `font-script` (Caveat), e um `@layer utilities` com `.no-scrollbar` (usada no app shell).
- CSS compilado: `theme/static/css/dist/styles.css` — **artefato de build** (no `.gitignore`); o build precisa rodar no deploy. **Recompilar com `python manage.py tailwind build` sempre que mexer em template ou em `styles.css`.** Em produção os estáticos são servidos pelo **WhiteNoise** (`CompressedManifestStaticFilesStorage`); a imagem Docker roda `tailwind build` seguido de `collectstatic` no build, e os templates referenciam o CSS pelo manifest.
- Settings: `INSTALLED_APPS` inclui `tailwind` e `theme`; `TAILWIND_APP_NAME = 'theme'`.
- `finances/templates/base.html` carrega as fontes do Google (Plus Jakarta Sans, Instrument Serif, Caveat) e o CSS via `{% load tailwind_tags %}` + `{% tailwind_css %}` no `<head>`.
- Comandos: `python manage.py tailwind build` (build único) e `python manage.py tailwind start` (modo watch no desenvolvimento).

### JavaScript / Vite

- O JS do projeto é empacotado com **Vite** e integrado ao Django via **`django-vite`**. Antes era `<script>` inline nos templates; agora vive em módulos sob `frontend/src/`.
- Fonte: `frontend/src/main.js` (entry) importa os módulos de `frontend/src/modules/` — `pageLoader` (barra de loading), `scopeMenu` (fecha o dropdown de escopo), `passwordToggle` (login), `colorSwatches` (paleta no form de categoria), `moneyMask` (máscara de moeda no campo Meta de investimento, via `data-money-display`/`data-money-target`), `categoryDonut` (donut SVG de gastos por categoria no dashboard, lê `#category-data` de um `{% json_script %}`), `categorySelect` (dropdown de categoria dos forms, filtrado por tipo Despesa/Receita), `filterForm` (auto-submit de filtros via `data-autosubmit`) e `selectWidget` (transforma todo `<select>` nativo em dropdown estilizado). Cada módulo é guard-claused, então o bundle único roda em qualquer página.
- Build: `npm run build` gera `frontend/dist/` (bundle + `manifest.json`) — **artefato de build, no `.gitignore`**. **Recompilar sempre que mexer em JS** (análogo ao `tailwind build`). `npm run watch` recompila no desenvolvimento.
- **Classes de componente, partials e filtro `brl`:** `styles.css` tem um `@layer components` com `.card` e `.btn-primary`, e sombras nomeadas `shadow-card`/`shadow-btn` no `@theme` (em vez de sombras arbitrárias). Markup repetido vive em partials (`_back_button.html`, `_empty_state.html`, `_progress_bar.html`, `_category_select.html`). Dinheiro usa o filtro `brl` (`finances/templatetags/money.py`): `{{ valor|brl }}` → `R$ 1.234,56` (carregar com `{% load money %}`). Reaproveitar esses padrões ao criar/editar templates. Detalhes em `docs/frontend.md`.
- **Componentes de seleção (regra):** todo componente de seleção é um **widget estilizado** no padrão Emy, nunca o controle nativo cru — vale para os dropdowns atuais e para futuros toggles/checkboxes. Todo `<select>` nativo é enriquecido automaticamente pelo módulo `selectWidget` (o nativo fica escondido como fonte do valor para o submit e o `change`; o JS desenha botão + painel; `data-color` na `<option>` mostra bolinha). O dropdown de categoria dos forms (`_category_select.html` + `categorySelect`) e o seletor de escopo (`<details>`) já são widgets no mesmo padrão.
- **Dado dinâmico no select (regra):** todo select de dado criado pelo usuário (ex.: categorias) deve **sempre** oferecer, na própria listagem do widget, a opção de **criar um novo** — não só quando vazio. No `selectWidget` genérico isso vem de `data-create-url` (+ `data-create-label` opcional), que adiciona um item "+ Criar …" no rodapé; no `_category_select.html` o link "Criar nova categoria" é fixo. Selects de **enum estático** (ex.: forma de pagamento) **não** recebem o item; o seletor de escopo sempre traz "Criar novo grupo".
- `base.html` carrega o bundle com `{% load django_vite %}` + `{% vite_asset 'frontend/src/main.js' %}` no `<head>`.
- Settings: `INSTALLED_APPS` inclui `django_vite`; `STATICFILES_DIRS = [('dist', BASE_DIR/'frontend'/'dist')]` mapeia o build para `/static/dist/`; `DJANGO_VITE` com `dev_mode` controlado por `DJANGO_VITE_DEV_MODE` (default `False` — usa o bundle buildado, sem dev server, igual ao fluxo do Tailwind), `manifest_path` em `frontend/dist/manifest.json` e `static_url_prefix='dist'`. O `collectstatic` coleta o `dist` e o WhiteNoise versiona/serve em produção.
- **Tailwind segue standalone (sem Node); o Node/npm entrou só para o build do JS.** A imagem Docker tem um stage `assets` (Node) que roda `npm ci && npm run build` e copia o `dist` antes do `collectstatic`.

- **Estado atual da UI:** identidade **Emy — variação "Petal"** (off-white rosado, soft com glow, cards arredondados, gradiente rosa→roxo), 100% Tailwind + tokens `emy-*` (sem `<style>` inline). O layout é um **app shell** sem scrollbar (página fixa em `100dvh`, só o `main` rola por dentro sem barra); a navegação tem dois menus (seletor de escopo em dropdown no topo + nav inferior de ícones); o **desktop usa 50/50** (`lg:grid-cols-2`) enquanto o mobile fica em coluna única. Ao criar/editar templates, usar classes Tailwind + tokens Emy e seguir esses padrões (ver `docs/frontend.md`, seção "Layout / app shell").

---

## Modelo de Dados

Diagramas completos (classes e ER) estão em `PRD.md`, seção 8.2.

**Classes base compartilhadas** (em `models.py`, evitam duplicação):
- `ScopedQuerySet` — QuerySet base com `in_scope(user, household)`; usado por `Category`, `Transaction`, `RecurringTransaction` e (estendido) `InvestmentGoal`.
- `NameTrimMixin` — `clean()` que faz trim do `name` e rejeita vazio; usado por `Household`, `Category`, `InvestmentGoal`, `HouseholdList`.
- `ScopedEntryMixin` — `clean()` que faz trim da descrição e valida categoria por escopo + `category.type == type`; usado por `Transaction` e `RecurringTransaction`.

### Enums (`models.TextChoices`)

Os valores são em inglês (banco/código); os **labels são em pt-BR** (exibidos ao usuário via `get_*_display`).

**TransactionType** — `income` (Receita), `expense` (Despesa)
**PaymentMethod** — `cash` (Dinheiro), `debit_card` (Cartão de débito), `credit_card` (Cartão de crédito), `pix` (Pix), `bank_slip` (Boleto), `bank_transfer` (Transferência)

### Category

Bucket definido pelo usuário para classificar transações.

- `user` FK → `auth.User` (`on_delete=CASCADE`, `related_name="categories"`) — criador
- `household` FK → `Household` (`null=True, blank=True`, `on_delete=CASCADE`, `related_name="categories"`) — nulo = pessoal; preenchido = do grupo
- `name` CharField(80)
- `type` CharField(10) — choices de `TransactionType`
- `color` CharField(7) — hex, default `#3498db`, validado por `RegexValidator` (`#rgb` ou `#rrggbb`)
- `icon` ImageField (`upload_to="category_icons/"`, `blank=True, null=True`) — imagem enviada pelo usuário (exige Pillow), opcional
- `is_active` Boolean — default `True`
- `created_at` DateTimeField — `auto_now_add`
- `Meta`: `ordering = ["name"]`, `verbose_name_plural = "categories"`, e duas `UniqueConstraint` condicionais: `unique_personal_category` `(user, name, type)` quando `household IS NULL` e `unique_household_category` `(household, name, type)` quando `household IS NOT NULL`
- Manager `ScopedQuerySet.in_scope(user, household)` (QuerySet base compartilhado por todos os models com escopo)
- `clean()` — vem do `NameTrimMixin` (trim do nome e rejeita nome vazio)
- `__str__` — `"{name} ({type})"`

### Transaction

Lançamento individual de receita ou despesa — pessoal ou compartilhado em grupo.

- `user` FK → `auth.User` (`on_delete=CASCADE`, `related_name="transactions"`) — quem lançou
- `household` FK → `Household` (`null=True, blank=True`, `on_delete=CASCADE`, `related_name="transactions"`) — nulo = pessoal; preenchido = do grupo
- `category` FK → `Category` (`on_delete=PROTECT`, `related_name="transactions"`)
- `description` CharField(200)
- `amount` DecimalField(`max_digits=12`, `decimal_places=2`) — `MinValueValidator(0.01)`
- `date` DateField
- `type` CharField(10) — choices de `TransactionType`
- `payment_method` CharField(15) — choices de `PaymentMethod`, default `cash`
- `notes` TextField — opcional (`blank=True`)
- `installment_group` UUIDField (`null=True`, `db_index=True`, `editable=False`) — agrupa as parcelas de uma mesma compra parcelada
- `installment_number` / `installment_total` PositiveSmallInteger (`null=True`) — ex.: 2 de 12
- `recurring_source` FK → `RecurringTransaction` (`null=True`, `on_delete=SET_NULL`, `related_name="generated"`) — preenchido quando a transação foi gerada por uma conta fixa
- `created_at` DateTimeField — `auto_now_add`
- `updated_at` DateTimeField — `auto_now`
- `Meta`: `ordering = ["-date", "-created_at"]`
- Manager `ScopedQuerySet.in_scope(user, household)`
- `signed_amount` @property — valor com sinal: negativo para despesa, positivo para receita
- `installment_label` @property — `"2/12"` para parcelas, vazio caso contrário
- `clean()` — vem do `ScopedEntryMixin` (compartilhado com `RecurringTransaction`):
  - faz trim da descrição
  - valida a categoria por escopo: com `household`, a categoria deve ser do mesmo grupo; sem, deve ser pessoal e do mesmo `user`
  - valida que `category.type == transaction.type`
- `__str__` — `"{description} - {amount}"`

### RecurringTransaction

Conta fixa (UI: "conta fixa") — despesa/receita aberta que se repete todo mês, sem fim, até ser pausada. Diferente do parcelamento (que tem número de parcelas), a conta fixa é materializada **sob demanda**: ao abrir um mês no dashboard/lista, gera-se a `Transaction` daquele mês se ainda não existir.

- `user` FK → `auth.User` (`on_delete=CASCADE`, `related_name="recurring_transactions"`) — criador
- `household` FK → `Household` (`null=True, blank=True`, `on_delete=CASCADE`, `related_name="recurring_transactions"`) — nulo = pessoal; preenchido = do grupo
- `category` FK → `Category` (`on_delete=PROTECT`, `related_name="recurring_transactions"`)
- `description` CharField(200); `amount` Decimal(12,2) `MinValueValidator(0.01)`
- `type` CharField(10) — choices de `TransactionType`; `payment_method` CharField(15) — choices de `PaymentMethod`, default `cash`
- `start_date` DateField — a partir de quando recorre; o **dia** da cobrança vem dela
- `is_active` Boolean — default `True`; pausar (`False`) interrompe a geração
- `created_at` DateTimeField — `auto_now_add`
- Manager `ScopedQuerySet.in_scope(user, household)`
- `day` @property — `start_date.day`
- `clean()` — vem do `ScopedEntryMixin` (mesmas regras de `Transaction`: trim da descrição + categoria por escopo + `category.type == type`)
- `__str__` — `"{description} (fixo)"`

### Profile

Dados pessoais extras de um usuário, preenchidos logo após o cadastro.

- `user` OneToOneField → `auth.User` (`on_delete=CASCADE`, `related_name="profile"`)
- `birth_date` DateField — obrigatório
- `phone` CharField(20) — obrigatório, validado por `RegexValidator` (`phone_validator`)
- `created_at` DateTimeField — `auto_now_add`
- `updated_at` DateTimeField — `auto_now`
- `__str__` — `"Profile of {username}"`

O `Profile` só existe quando preenchido por completo (`birth_date` e `phone` são obrigatórios). O `ProfileCompletionMiddleware` usa a ausência do `Profile` para forçar o preenchimento.

### Household

Espaço compartilhado (UI: "grupo") onde vários usuários acompanham finanças em conjunto.

- `name` CharField(80)
- `created_by` FK → `auth.User` (`on_delete=CASCADE`, `related_name="created_households"`) — dono
- `created_at` DateTimeField — `auto_now_add`
- `Meta`: `ordering = ["name"]`
- Manager `HouseholdManager.for_user(user)` — grupos dos quais o usuário é membro
- `clean()` — vem do `NameTrimMixin` (trim do nome); `__str__` — `name`

### HouseholdMembership

Liga um usuário a um grupo (o dono também tem membership, criada junto com o grupo).

- `household` FK → `Household` (`on_delete=CASCADE`, `related_name="memberships"`)
- `user` FK → `auth.User` (`on_delete=CASCADE`, `related_name="household_memberships"`)
- `joined_at` DateTimeField — `auto_now_add`
- `Meta`: `UniqueConstraint(household, user)` (`unique_household_member`)

### InvestmentGoal

Objetivo de investimento com meta, pessoal ou de grupo. Fluxo separado das transações.

- `user` FK → `auth.User` (CASCADE, `related_name="investment_goals"`) — criador
- `household` FK → `Household` (`null=True, blank=True`, CASCADE, `related_name="investment_goals"`) — nulo = pessoal; preenchido = grupo
- `name` CharField(80); `target_amount` Decimal(12,2) `MinValueValidator(0.01)`; `target_date` DateField (opcional); `is_active` Bool (default True); `created_at`
- Manager `InvestmentGoalQuerySet` (estende `ScopedQuerySet`): `.in_scope(user, household)` + `.with_invested()` — anota cada objetivo com `invested_total` (`Coalesce(Sum(contributions__amount), 0)`) para evitar N+1 no `investment_list`
- `@property invested` (usa a anotação `invested_total` quando presente; senão soma os aportes); `@property progress` (% da meta, limitado a 100)
- `clean()` vem do `NameTrimMixin` (trim do nome); `__str__` = name

### InvestmentContribution

Aporte individual em um objetivo.

- `goal` FK → `InvestmentGoal` (CASCADE, `related_name="contributions"`)
- `user` FK → `auth.User` (CASCADE, `related_name="contributions"`) — quem aportou
- `amount` Decimal(12,2) `MinValueValidator(0.01)`; `date` DateField; `notes` TextField (blank); `created_at`
- `Meta.ordering = ["-date", "-created_at"]`. O escopo deriva do `goal`; o dashboard soma os aportes do mês no escopo e os subtrai do saldo.

### HouseholdList

Lista nomeada (checklist) de um grupo — só existe em grupo.

- `household` FK → `Household` (CASCADE, `related_name="lists"`); `name` CharField(80); `created_at`
- `clean()` vem do `NameTrimMixin` (trim do nome); `__str__` = name

### HouseholdListItem

Item de uma lista de casa.

- `list` FK → `HouseholdList` (CASCADE, `related_name="items"`); `text` CharField(200); `is_done` Bool (default False); `created_at`
- `Meta.ordering = ["is_done", "created_at"]` (pendentes primeiro)

### Regras de integridade

- `Category`: unicidade por escopo — `unique_personal_category` `(user, name, type)` (pessoal) e `unique_household_category` `(household, name, type)` (grupo).
- `Transaction.category`: `on_delete=PROTECT` — categoria com transações vinculadas não pode ser excluída pelo ORM; a view `category_delete` checa antes e exibe mensagem de erro em vez de quebrar.
- `Transaction.amount`: `MinValueValidator(0.01)` — valor sempre maior que zero.
- `Transaction.clean()`: coerência categoria/escopo e tipo categoria/transação.
- `Profile.user`: `OneToOneField` — um perfil por usuário.
- `HouseholdMembership`: `UniqueConstraint(household, user)` — uma membership por par.

---

## Forms

- **`RegistrationForm`** — herda de `UserCreationForm`; campo `email` (obrigatório, único — checado contra `email`/`username`). No `save()` grava o e-mail (em minúsculas) tanto em `user.email` quanto em `user.username`. É o cadastro por e-mail.
- **`EmailAuthenticationForm`** — herda de `AuthenticationForm`; usado na rota de login (`core/urls.py` aponta a `LoginView` para ele). O `clean_username` normaliza o e-mail (trim + minúsculas) para casar com o `username` gravado em minúsculas no cadastro — login por e-mail **case-insensitive**.
- **`CategoryForm`** — `ModelForm` de `Category`, campos `name`, `type`, `color`, `icon`, `is_active`. Widget `type=color` para `color`; `icon` é `ImageField` (upload de imagem — o template usa `<input type="file">` e o form/view recebem `request.FILES`). Recebe `user=` e `household=` por kwarg no `__init__`; no `clean()` atribui `instance.user`/`instance.household` (apenas no create, para não trocar o criador num update de grupo) e sobrescreve `_get_validation_exclusions` para **não** excluir `user`/`household` — assim o `full_clean` roda as `UniqueConstraint` de escopo e a categoria duplicada vira erro de form (não `IntegrityError`/500).
- **`TransactionForm`** — `ModelForm` de `Transaction`, campos `description`, `amount`, `date`, `type`, `category`, `payment_method`, `notes`. O `__init__` recebe `user=` e `household=` por kwarg e:
  - filtra o queryset de `category` para mostrar apenas categorias **ativas do escopo ativo** (`Category.objects.in_scope(user, household)`);
  - em `clean()`, atribui `self.instance.user` e `self.instance.household` antes de o `Model.clean()` rodar as validações cruzadas.
  - Campo não-model `installments` (1–60): acima de 1, o `amount` informado é o **total** e a view gera N parcelas mensais. O `clean()` rejeita se o valor for insuficiente (cada parcela precisa de pelo menos `0.01`).
  - Widgets: `date` (`type=date`), `amount` (`step=0.01`, `min=0.01`), `notes` (textarea).
- **`RecurringTransactionForm`** — `ModelForm` de `RecurringTransaction`, campos `description`, `amount`, `type`, `category`, `payment_method`, `start_date`, `is_active`. Mesmo padrão do `TransactionForm`: recebe `user=`/`household=`, filtra categorias do escopo e atribui `user`/`household` no `clean()`.
- **`ProfileForm`** — `ModelForm` de `Profile`, campos `birth_date` e `phone`, mais os campos declarados `first_name` e `last_name` (que gravam no `User` nativo, não no `Profile`). O `__init__` recebe `user=` por kwarg e pré-popula `first_name`/`last_name` com os valores atuais do `User`. O `save()` grava o `Profile` e o `User` na mesma chamada. Widgets: `birth_date` (`type=date`), `phone` (placeholder).
- **`HouseholdForm`** — `ModelForm` de `Household`, campo `name`. O `created_by` é atribuído na view.
- **`MemberAddForm`** — `Form` com campo `email`; valida que existe uma conta com aquele e-mail (busca por `email`/`username`) e expõe o usuário encontrado em `self.user`. Mensagem de falha neutra ("Não foi possível adicionar este e-mail ao grupo") para reduzir enumeração de contas.
- **`InvestmentGoalForm`** — `ModelForm` de `InvestmentGoal`: `name`, `target_amount`, `target_date` (`type=date`). Mesmo padrão dos demais forms com escopo: recebe `user=`/`household=` por kwarg e atribui no `clean()` (no create). O campo `target_amount` no template usa máscara de moeda (módulo `moneyMask`: campo visível formatado + hidden com o valor numérico).
- **`ContributionForm`** — `ModelForm` de `InvestmentContribution`: `amount`, `date` (`type=date`), `notes`. `goal`/`user` atribuídos na view.
- **`HouseholdListForm`** — `ModelForm` de `HouseholdList`, campo `name`.
- **`HouseholdListItemForm`** — `ModelForm` de `HouseholdListItem`, campo `text`.

---

## Views

Todas as views de dados são protegidas com `@login_required`. `register` é a única view pública.

| View | Rota (name) | Função |
|---|---|---|
| `register` | `register` | Cadastro via `RegistrationForm` (e-mail); login automático; redireciona para `profile_edit`. |
| `profile_edit` | `finances:profile_edit` | Cria/edita o `Profile` do usuário pelo `ProfileForm`. É a tela que o `register` abre logo após o cadastro. |
| `scope_switch` | `finances:scope_switch` | Troca o escopo ativo (pessoal ou grupo) na sessão. |
| `dashboard` | `finances:dashboard` | Resumo do mês selecionado (`?month=AAAA-MM`, default atual) + lançamentos do mês, no escopo ativo. Materializa as contas fixas do mês ao abrir. Também calcula o total no **cartão de crédito** do mês e os recortes de despesa por **categoria** (`by_category`, alimenta o donut) e por **forma de pagamento** (`by_payment`). |
| `forecast` | `finances:forecast` | Previsão dos próximos 6 meses: transações reais + contas fixas ativas ainda não materializadas (sem dupla contagem). |
| `transaction_list` | `finances:transaction_list` | Lista as transações do mês selecionado (`?month=`) no escopo ativo. **Filtros combináveis** (E): `?type=income\|expense`, `?category=<pk>`, `?payment_method=<valor>` e busca `?q=` (`description__icontains`). Calcula o **resumo** (Entrou/Saiu/Saldo) do conjunto filtrado e o `filter_qs` que a navegação por mês preserva. Materializa as contas fixas do mês. |
| `transaction_create` | `finances:transaction_create` | Cria transação no escopo ativo. |
| `transaction_update` | `finances:transaction_update` | Edita transação dentro do escopo (`get_object_or_404(...in_scope...)`). |
| `transaction_delete` | `finances:transaction_delete` | Exclui transação após confirmação via POST. |
| `category_list` | `finances:category_list` | Lista as categorias do escopo ativo. |
| `category_create` | `finances:category_create` | Cria categoria; `user` e `household` atribuídos na view. |
| `category_update` | `finances:category_update` | Edita categoria dentro do escopo. |
| `category_delete` | `finances:category_delete` | Exclui categoria; bloqueia se houver transações **ou contas fixas** vinculadas (`PROTECT`). |
| `recurring_list` | `finances:recurring_list` | Lista as contas fixas do escopo ativo. |
| `recurring_create/update/delete` | `finances:recurring_*` | CRUD de conta fixa (dentro do escopo); o create materializa o mês corrente. |
| `household_list` | `finances:household_list` | Lista os grupos do usuário. |
| `household_create` | `finances:household_create` | Cria grupo + membership do dono (atômico). |
| `household_detail` | `finances:household_detail` | Membros do grupo; o dono edita/exclui o grupo e adiciona/remove membros. |
| `household_update` | `finances:household_update` | Renomeia o grupo (só o dono). |
| `household_delete` | `finances:household_delete` | Exclui o grupo após confirmação via POST (só o dono); `CASCADE` apaga os dados do grupo e reseta o escopo ativo na sessão. |
| `member_add` | `finances:member_add` | Adiciona membro por e-mail (só o dono). |
| `member_remove` | `finances:member_remove` | Remove membro (só o dono; nunca o dono). |
| `investment_list` | `finances:investment_list` | Objetivos do escopo + total investido. |
| `investment_create/update/delete` | `finances:investment_*` | CRUD de objetivo (dentro do escopo). |
| `investment_detail` | `finances:investment_detail` | Objetivo + progresso + aportes + form de aporte. |
| `contribution_create/delete` | `finances:contribution_*` | Registra/remove aporte. |
| `list_index` | `finances:list_index` | Listas do grupo ativo (redireciona se escopo pessoal). |
| `list_create/detail/delete` | `finances:list_*` | CRUD de lista de casa (só grupo). |
| `list_item_add/toggle/delete` | `finances:list_item_*` | Adiciona/marca/remove item (POST). |

**Padrão obrigatório de isolamento por escopo:** toda query de leitura/escrita de `Category` e `Transaction` passa pelos managers `Model.objects.in_scope(request.user, household)`, com `household = get_active_household(request)`. No escopo pessoal filtra por `user` + `household IS NULL`; no de grupo, por `household` (com a membership já validada). Sem esse filtro, vazam dados pessoais de outros usuários ou de grupos dos quais não se é membro.

Feedback de sucesso/erro é dado via `django.contrib.messages` após cada ação.

---

## URLs

**`core/urls.py`:**
- `admin/` → Django Admin
- `accounts/register/` → `finances.views.register` (name `register`)
- `accounts/login/` → `LoginView` com `EmailAuthenticationForm` (name `login`) — declarada **antes** do `include` para ter precedência (login por e-mail case-insensitive)
- `accounts/` → `include("django.contrib.auth.urls")` (logout, troca de senha; o login do include é sombreado pela rota acima)
- `""` → `include("finances.urls")`

**`finances/urls.py`** (`app_name = "finances"`):
- `""` → `dashboard`
- `profile/` → `profile_edit`
- `forecast/` → `forecast`
- `scope/switch/` → `scope_switch`
- `transactions/` → `transaction_list`
- `transactions/new/` → `transaction_create`
- `transactions/<int:pk>/edit/` → `transaction_update`
- `transactions/<int:pk>/delete/` → `transaction_delete`
- `categories/` → `category_list`
- `categories/new/` → `category_create`
- `categories/<int:pk>/edit/` → `category_update`
- `categories/<int:pk>/delete/` → `category_delete`
- `recurring/`, `recurring/new/`, `recurring/<int:pk>/edit/`, `recurring/<int:pk>/delete/` → contas fixas (`recurring_*`)
- `groups/` → `household_list`
- `groups/new/` → `household_create`
- `groups/<int:pk>/` → `household_detail`
- `groups/<int:pk>/edit/` → `household_update`
- `groups/<int:pk>/delete/` → `household_delete`
- `groups/<int:pk>/members/add/` → `member_add`
- `groups/<int:pk>/members/<int:user_id>/remove/` → `member_remove`
- `investments/`, `investments/new/`, `investments/<int:pk>/`, `investments/<int:pk>/edit/`, `investments/<int:pk>/delete/`, `investments/<int:pk>/contributions/add/`, `investments/<int:pk>/contributions/<int:contrib_pk>/delete/`
- `lists/`, `lists/new/`, `lists/<int:pk>/`, `lists/<int:pk>/delete/`, `lists/<int:pk>/items/add/`, `lists/<int:pk>/items/<int:item_pk>/toggle/`, `lists/<int:pk>/items/<int:item_pk>/delete/`

---

## Templates

`APP_DIRS=True` — templates ficam em `finances/templates/`. O `theme/templates/base.html` é gerado pelo `django-tailwind` e não é usado pelo app `finances` (que tem o seu próprio `base.html`).

Todos os templates abaixo já estão na identidade visual Emy/Petal (ver seção Frontend / TailwindCSS).

- `base.html` — **app shell**: `<body>` em `h-[100dvh] flex flex-col overflow-hidden` (a página nunca rola) e `<main>` como única área rolável (`overflow-y-auto no-scrollbar`, conteúdo centralizado por `my-auto`). Header (logo + selo "Beta V0.1" + **seletor de escopo em dropdown** + usuário/Sair); nav inferior flutuante de **ícones** (Início / Lançamentos / **Previsão** / Investir / Categorias / `+`, item ativo via `request.resolver_match`, rótulo só a partir de `sm:`); barra de loading no topo (disparada por cliques/submits); bloco de mensagens. O seletor de escopo é um `<details>` com Pessoal + grupos (`user_households`) + "Criar novo grupo". Desktop usa layout 50/50 (ver Decisões). Estilização 100% Tailwind, sem `<style>` inline.
- `finances/scope_switch.html` — escolha do escopo ativo (Pessoal ou um grupo) + link "Gerenciar grupos".
- `finances/household_list.html` — lista de grupos + "Novo grupo".
- `finances/household_form.html` — criação/edição de grupo (nome); o rótulo do botão vem de `submit_label` (default "Criar grupo").
- `finances/household_detail.html` — membros do grupo; o dono edita/exclui o grupo (ações no topo), adiciona membro por e-mail e remove membros. A exclusão reusa `confirm_delete.html`.
- `finances/dashboard.html` — saudação (usa `first_name`), **navegação por mês** (setas ‹ ›, atalho "Hoje"), cards de stat (saldo/entrou/saiu/investido), card do total no **cartão de crédito**, atalho "Listas da casa" (só em grupo), lançamentos do mês (selo "2/12") e os recortes de despesa por **categoria** (com **donut** SVG) e por **forma de pagamento**.
- `finances/forecast.html` — previsão dos próximos 6 meses em cards (saldo previsto + entrou/saiu); cada card abre aquele mês no dashboard. Mês atual destacado em gradiente.
- `finances/transaction_list.html` — layout 50/50: **painel de filtros + resumo** à esquerda (mês, resumo Entrou/Saiu/Saldo do período, filtros combináveis de tipo/categoria/forma de pagamento/busca, "Contas fixas", "Limpar filtros") e a lista à direita (selo "2/12"). Filtros preservam o mês e auto-submetem.
- `finances/transaction_form.html` — card dividido: toggle Despesa/Receita, valor grande, **dropdown de categoria** (widget filtrado por tipo), data, método de pagamento, **parcelas** (só na criação) e observações.
- `finances/_back_button.html`, `_empty_state.html`, `_progress_bar.html`, `_category_select.html` — partials reutilizáveis (botão Voltar, estado vazio, barra de progresso, dropdown de categoria).
- `finances/recurring_list.html` — grid de cards das contas fixas (valor, dia, ativa/pausada) + ações.
- `finances/recurring_form.html` — card dividido de conta fixa (tipo, valor mensal, categoria, a partir de, método, ativa).
- `finances/category_list.html` — grid de cards de categoria.
- `finances/category_form.html` — formulário de criação/edição de categoria (toggle de tipo, cor, ícone, ativo).
- `finances/profile_form.html` — formulário de perfil (nome, sobrenome, data de nascimento, telefone). Usado tanto no preenchimento pós-cadastro quanto na edição.
- `finances/investment_list.html` — objetivos em cards com barra de progresso + total investido.
- `finances/investment_form.html` — criação/edição de objetivo (nome, meta, prazo opcional).
- `finances/investment_detail.html` — objetivo + progresso + form de aporte + lista de aportes.
- `finances/list_index.html` — listas de casa do grupo + "Nova lista".
- `finances/list_form.html` — criação de lista (nome).
- `finances/list_detail.html` — itens com checkbox (toggle via POST) + form para adicionar item.
- `finances/confirm_delete.html` — confirmação de exclusão (reusado por transação, categoria, objetivo, lista e grupo; título derivado de `object._meta.model_name`). Para `household` mostra um aviso extra de que a exclusão apaga os dados do grupo para todos os membros.
- `registration/login.html` — tela de login por e-mail (card dividido; campo mantém `name="username"`, exibido como "E-mail").
- `registration/register.html` — tela de cadastro por e-mail (mesmo padrão do login; campo `email`).

**Botão "Voltar" padronizado:** os forms (`transaction_form`, `category_form`, `profile_form`) têm um botão circular `←` no topo (fora do `<form>`, `type="button"`, `onclick="history.back()"`) que volta para a página anterior. Nos forms com título fora do `<form>` ele fica ao lado do título; no `transaction_form` (título dentro do card) fica acima do form.

---

## Admin

`finances/admin.py` registra:
- **`CategoryAdmin`** — `list_display`, `list_filter` (tipo, ativo, grupo, data), `search_fields`, `autocomplete_fields = ("user", "household")`.
- **`TransactionAdmin`** — `list_display`, `list_filter` (tipo, método, data, categoria, grupo), `search_fields`, `autocomplete_fields = ("user", "household", "category")`, `date_hierarchy = "date"`.
- **`HouseholdAdmin`** — com inline de membros (`HouseholdMembership`); e **`HouseholdMembershipAdmin`**.
- **`InvestmentGoalAdmin`** — com inline de aportes (`InvestmentContribution`); e **`InvestmentContributionAdmin`**.
- **`HouseholdListAdmin`** — com inline de itens (`HouseholdListItem`).

---

## Autenticação

- `User` nativo de `django.contrib.auth` — sem custom user model. Dados pessoais extras vivem no model `Profile` (OneToOne).
- **Identificador é o e-mail**: o `RegistrationForm` grava o e-mail em `email` e também em `username` (minúsculas). O login usa o `EmailAuthenticationForm` (subclasse do form padrão) que normaliza o input para minúsculas — login **case-insensitive** sem backend de auth próprio.
- **Brute force**: `django-axes` bloqueia tentativas repetidas de login (ver seção Segurança).
- Login/logout/troca de senha via `django.contrib.auth.urls`; a rota `accounts/login/` é sobrescrita em `core/urls.py` (antes do `include`) para usar o `EmailAuthenticationForm`.
- Cadastro via `RegistrationForm` na view `register`, com login automático após sucesso.
- Após o cadastro, o usuário é redirecionado para `profile_edit` para completar o perfil (nome, data de nascimento, telefone).
- `ProfileCompletionMiddleware` força o preenchimento: usuário autenticado sem `Profile` é redirecionado para `profile_edit` em qualquer rota (exceto `/admin/`, a própria tela de perfil e o `logout`).
- Senhas validadas por `AUTH_PASSWORD_VALIDATORS` (configuração padrão do Django).
- Logout via POST (Django 6 não aceita GET).
- Settings de redirecionamento em `core/settings.py`:
  - `LOGIN_URL = 'login'`
  - `LOGIN_REDIRECT_URL = 'finances:dashboard'`
  - `LOGOUT_REDIRECT_URL = 'login'`
- Não há sistema de permissões granulares — o isolamento é feito por escopo (pessoal x grupo) em cada view, via `in_scope`. A única regra de papel é o dono do grupo (`Household.created_by`) gerenciar membros.

---

## Settings relevantes (`core/settings.py`)

- `INSTALLED_APPS` inclui `finances`, `tailwind`, `theme`, `django_vite` e `axes`.
- `MIDDLEWARE` inclui `whitenoise.middleware.WhiteNoiseMiddleware` (logo após o `SecurityMiddleware`, serve os estáticos em produção), `finances.middleware.ProfileCompletionMiddleware` (logo após o `AuthenticationMiddleware`) e `axes.middleware.AxesMiddleware` (por último).
- `AUTHENTICATION_BACKENDS` = `axes.backends.AxesStandaloneBackend` (primeiro) + `django.contrib.auth.backends.ModelBackend`.
- Config do `django-axes`: `AXES_FAILURE_LIMIT = 5`, `AXES_COOLOFF_TIME = 1` (h), `AXES_LOCKOUT_PARAMETERS = [["ip_address", "username"]]`, `AXES_RESET_ON_SUCCESS = True`.
- `TAILWIND_APP_NAME = 'theme'`.
- `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`.
- `TEMPLATES['OPTIONS']['context_processors']` inclui `finances.context_processors.scope` (expõe `active_household` e `user_households`).
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` vêm de variáveis de ambiente, carregadas de um `.env` na raiz pelo `python-dotenv` (`load_dotenv()` no topo do `settings.py`). `SECRET_KEY` é obrigatória (`os.environ['SECRET_KEY']`); `DEBUG` tem default seguro `False`. O `.env` está no `.gitignore`; o `.env.example` é o modelo versionado.
- No Railway, o `settings.py` lê `RAILWAY_PUBLIC_DOMAIN` e o anexa a `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`; quando há `RAILWAY_ENVIRONMENT`, adiciona `healthcheck.railway.app` ao `ALLOWED_HOSTS` (host do healthcheck — sem ele o deploy não fica saudável).
- Bloco `if not DEBUG:` no fim do arquivo ativa o hardening de produção (SSL redirect configurável, cookies seguros, HSTS via `SECURE_HSTS_SECONDS`, `SECURE_PROXY_SSL_HEADER`).
- Banco: `dj_database_url.config()` lê `DATABASE_URL` (PostgreSQL em Docker/Railway, `conn_max_age=600` + `conn_health_checks`) e cai no SQLite (`BASE_DIR / 'db.sqlite3'`) quando a variável não está definida.
- Estáticos: `STORAGES['staticfiles']` usa `whitenoise.storage.CompressedManifestStaticFilesStorage`; `STATIC_ROOT = BASE_DIR / 'staticfiles'`. `STATICFILES_DIRS = [('dist', BASE_DIR/'frontend'/'dist')]` inclui o build do Vite (servido em `/static/dist/`).
- Vite: `DJANGO_VITE` (`dev_mode` via `DJANGO_VITE_DEV_MODE`, default `False`; `manifest_path` em `frontend/dist/manifest.json`; `static_url_prefix='dist'`). Ver seção **Frontend / Vite**.
- Mídia: `MEDIA_URL = 'media/'`; `MEDIA_ROOT = os.environ.get('MEDIA_ROOT', BASE_DIR/'media')` (em produção aponta para o volume do Railway). A mídia é servida por uma rota em `core/urls.py` (`media/...` → `serve`), pois o WhiteNoise não serve mídia de usuário.

---

## Decisões de Design Registradas

- **`User` nativo, não custom user model**: o diagrama original modelava um `User` «Auth» com campos idênticos ao `auth.User` padrão do Django. Decidiu-se usar o `User` nativo — mais simples e suficiente para o escopo. Trocar `AUTH_USER_MODEL` depois é arriscado; quando surgiu a necessidade de dados pessoais extras (nome, data de nascimento, telefone), optou-se por um model `Profile` (OneToOne) em vez de custom user model.
- **`Profile` como `OneToOneField` com `User`**: dados pessoais extras (data de nascimento, telefone) vivem no `Profile`; o "nome" reaproveita `first_name`/`last_name` do `User` nativo (o `ProfileForm` edita os dois objetos). `birth_date` e `phone` são obrigatórios, então o `Profile` só existe quando completo — o middleware usa isso como sinal de "perfil pendente".
- **Preenchimento de perfil forçado via middleware**: `ProfileCompletionMiddleware` redireciona qualquer usuário autenticado sem `Profile` para `profile_edit`. É a forma idiomática do Django de aplicar uma regra global de acesso sem repetir checagem em cada view; libera apenas `/admin/`, a tela de perfil e o `logout`.
- **Botão "Voltar" padronizado fora do `<form>`**: os forms têm um botão `←` no topo, fora do `<form>` e com `type="button"`, usando `history.back()` para voltar à página anterior real. Fica fora do `<form>` para não submetê-lo e por ser navegação, não ação do formulário.
- **Validações de domínio em `Model.clean()`**: coerência usuário/categoria, tipo categoria/transação e trim de strings vivem no `clean()` dos models, não nas views. Garante que admin, forms e scripts respeitem as mesmas regras. As views/forms chamam essas validações via `full_clean()` no fluxo do `ModelForm`.
- **`Transaction.category` com `on_delete=PROTECT`**: seguindo a cardinalidade `Category "1" → "0..*" Transaction` do diagrama, a categoria é obrigatória e não pode ser excluída enquanto tiver transações. A view `category_delete` faz a checagem explícita e devolve mensagem amigável em vez de deixar o `ProtectedError` estourar.
- **`signed_amount` como @property**: o valor com sinal (negativo para despesa) é calculado na leitura, não persistido — `amount` guarda sempre o valor absoluto e `type` define o sinal. Evita inconsistência entre os dois campos.
- **`UniqueConstraint(user, name, type)` em `Category`**: o mesmo nome pode existir como receita e como despesa (ex.: "Bônus" receita e "Bônus" despesa), e usuários diferentes podem ter categorias homônimas — a unicidade é por trio, não por nome global.
- **`TransactionForm` recebe `user` por kwarg**: o form precisa do usuário para (a) filtrar o seletor de categorias e (b) preencher `instance.user` antes do `Model.clean()`. Passar via `__init__` mantém o form desacoplado do `request`.
- **Isolamento por escopo em vez de sistema de permissões**: cada usuário tem finanças pessoais privadas e pode participar de grupos compartilhados. Não há matriz de permissões; o filtro por escopo (`in_scope`) em cada query é a barreira e é obrigatório. A única regra de papel é o dono do grupo gerenciar membros.
- **Escopo pessoal x grupo via `household` opcional (não tabelas separadas)**: `Category`/`Transaction` ganharam um FK `household` anulável — nulo = pessoal, preenchido = do grupo. O escopo ativo vive na sessão (`active_household_id`), resolvido por `get_active_household(request)` (que valida a membership) e aplicado pelos managers `in_scope(user, household)` / `Household.objects.for_user(user)`. Um context processor expõe o escopo aos templates. Mais simples que duplicar models e mantém o ORM DRY.
- **Login por e-mail sem custom user model**: para padronizar a identidade por e-mail (e permitir adicionar membros por e-mail) sem o risco de trocar `AUTH_USER_MODEL`, o `RegistrationForm` grava o e-mail também no `username`. O login padrão do Django (por `username`) passa a funcionar com o e-mail por serem iguais — sem backend de auth próprio.
- **Gestão do grupo restrita ao dono**: só `Household.created_by` edita o nome (`household_update`), exclui o grupo (`household_delete`) e adiciona/remove membros; o dono não pode ser removido. A exclusão é via POST com tela de confirmação reforçada e, sendo `CASCADE`, apaga todos os dados do grupo (categorias, lançamentos, contas fixas, investimentos, listas) para todos os membros; se o grupo excluído for o escopo ativo, a sessão volta para Pessoal. `created_by` em `CASCADE` (apagar a conta do dono apaga o grupo) é escolha de MVP — ainda não há tela de exclusão de conta.
- **Investimentos como fluxo separado (aporte não vira `Transaction`)**: `InvestmentGoal`/`InvestmentContribution` são models próprios e reusam o escopo (`household` anulável + `in_scope`). O aporte não duplica em `Transaction`; o dashboard soma os aportes do mês no escopo e os subtrai do saldo. Assim a seção de investimentos fica separada (telas/lista próprias) e o aporte ainda reflete como saída de caixa, sem mexer na obrigatoriedade de `category`.
- **Listas de casa só em grupo**: `HouseholdList` tem `household` obrigatório (não há lista pessoal). As views exigem escopo de grupo ativo e restringem o acesso às listas dos grupos do usuário; o acesso é via atalho no dashboard quando o escopo é um grupo.
- **TailwindCSS no modo standalone (sem Node)**: optou-se por `django-tailwind` 4.x + `pytailwindcss` em vez do modo "full" que exige Node/npm — o **CSS** não depende de Node (binário do Tailwind CLI baixado pelo `pytailwindcss`). O Node entrou depois **só para o build do JS** (Vite, ver decisão abaixo); o Tailwind seguiu standalone para não reescrever o pipeline de CSS.
- **Identidade visual "Petal" (TailwindCSS)**: a UI foi migrada da v1 (CSS inline) para a identidade Emy, variação **"Petal"** — off-white rosado, soft/feminino com glow, cards bem arredondados, gradiente rosa→roxo, nav inferior flutuante. Escolhida entre três explorações de design (Soft Bloom / Petal / Aurora). Os tokens (cores `emy-*`, fontes) vivem no bloco `@theme` de `theme/static_src/src/styles.css`; o `<style>` inline do `base.html` foi removido. A migração cobriu só as telas com model atual (`Category`/`Transaction`) — Cartões, Metas, Insights, Transferência e Recorrência aparecem no mock mas não têm model e ficaram fora.
- **App shell sem scrollbar**: o `base.html` usa `h-[100dvh] overflow-hidden` no `<body>` e torna o `<main>` a única área rolável (`overflow-y-auto` + utility `.no-scrollbar` em `styles.css`), com o conteúdo centralizado por `my-auto`. A página nunca rola e não há barra visível; conteúdo maior que a tela rola por dentro. Foco mobile-first com `dvh`.
- **Dois menus (escopo no topo, seções embaixo)**: o topo tem o **seletor de escopo** (dropdown `<details>`: Pessoal/grupos/criar grupo) e a **nav inferior** flutuante de ícones cuida da navegação entre seções (mobile e desktop). Decisão do usuário de manter os dois separados.
- **Desktop 50/50**: a partir de `lg:`, as telas usam duas colunas (`lg:grid-cols-2`); o dashboard tem uma linha de cards de stat (`lg:grid-cols-4`) + recentes/listas; os forms usam "card dividido" (`md:grid-cols-2`). O mobile permanece em coluna única.
- **Barra de loading sem dependência**: `#page-loader` no `base.html` + JS vanilla; dá feedback de navegação no app server-rendered. Mesmo estilo pontual de JS já usado (toggle de senha, fechar dropdown).
- **Inputs renderizados campo a campo nos templates**: para ter controle total das classes Tailwind sem tocar em `forms.py`/`views.py`, os formulários (`login`, `register`, `transaction_form`, `category_form`, `profile_form`, telas de grupo) renderizam cada `<input>`/`<select>` manualmente com o `name=` correto, repondo o valor via `form.<campo>.value` e os erros via `form.<campo>.errors`. `type` e `category` viram radios estilizados (toggle/pills).
- **Validação de unicidade de `Category` no form (não só no banco)**: o `CategoryForm` mantém `user`/`household` fora do `_get_validation_exclusions` para que o `full_clean` rode as `UniqueConstraint` de escopo. Antes, como o `user`/`household` eram setados só na view (após o `is_valid`), a categoria duplicada passava no form e estourava `IntegrityError` (500). Mensagem amigável via `violation_error_message` (pt-BR) nas constraints, que aparece em `non_field_errors`. Defesa em profundidade: a constraint do banco continua sendo a barreira final.
- **Brute force com `django-axes` (não solução caseira)**: escolhido o pacote padrão de mercado em vez de rate limit próprio — robusto e funciona em produção multi-worker (handler em banco). Lockout pela combinação IP + username para não causar DoS de conta (um atacante de outro IP não tranca a vítima) nem trancar todos atrás de um NAT por um único username.
- **Login por e-mail case-insensitive via form, não backend custom**: como o cadastro já grava o `username` em minúsculas, o `EmailAuthenticationForm` só normaliza o input no login. Evita um backend de autenticação próprio (que complicaria a integração com o `django-axes`).
- **Selo "Beta V0.2" no header**: pílula pequena (tokens `emy-purple-*`) ao lado do logo no `base.html`, visível em mobile e desktop. O app tem **favicon SVG** (`finances/static/favicon.svg`) reproduzindo a logo (quadradinho gradiente + "e"), referenciado no `<head>` via `{% static %}`.
- **Componentes de seleção sempre como widget**: nenhum `<select>`/dropdown nativo cru na UI. O módulo `selectWidget` enriquece todo `<select>` num dropdown estilizado mantendo o nativo como fonte do valor (submit + `change`, então `data-autosubmit` segue funcionando); o dropdown de categoria dos forms (`categorySelect`, com filtro por tipo) e o seletor de escopo (`<details>`) já eram widgets. A regra vale também para futuros toggles/checkboxes. **Select de dado dinâmico** (criado pelo usuário, ex.: categoria) sempre traz a opção de **criar** na listagem — via `data-create-url`/`data-create-label` no `selectWidget` ou link fixo no `_category_select.html`; enums estáticos não.
- **DRY de front-end (componentes, partials, filtro `brl`)**: padrões repetidos viraram classes de componente (`.card`, `.btn-primary`, sombras nomeadas `shadow-card`/`shadow-btn`) e partials (`_back_button`, `_empty_state`, `_progress_bar`, `_category_select`); o dinheiro centralizou no filtro `brl` (pt-BR `R$ 1.234,56`), que também resolveu o formato. Reaproveitar antes de copiar utilitário/markup.
- **Cartão de crédito e recortes no dashboard**: a `dashboard` view soma as despesas no crédito do mês (subconjunto de "Saiu", não extra) e agrega as despesas por categoria e por forma de pagamento; o template mostra um donut (SVG via `categoryDonut`) na seção de categoria. O crédito **não** é deslocado para o mês da fatura — conta no mês da compra (modelo de cartão/fatura segue fora de escopo).
- **Lista de lançamentos com filtros combináveis**: a `transaction_list` ganhou filtros de categoria, forma de pagamento e busca, somados ao tipo e ao mês (todos via querystring, AND), com resumo do período filtrado. Server-rendered: os controles auto-submetem (`filterForm`); a navegação por mês preserva os filtros via `filter_qs` montado na view.
- **Parcelamento materializado (N transações reais)**: uma compra "em 12x" gera 12 `Transaction` reais, uma por mês, ligadas por `installment_group` (UUID) e numeradas (`installment_number`/`installment_total`). Reusa toda a infra de escopo/dashboard/lista — cada parcela cai no saldo do seu mês. O `amount` informado é o **total**, dividido igualmente; a última parcela absorve o arredondamento (`ROUND_DOWN` + resto). Geração atômica em `_save_installments`.
- **Conta fixa materializada sob demanda**: `RecurringTransaction` é um template aberto (sem fim). Como não dá para materializar infinitas transações, `_materialize_recurring(user, household, year, month)` cria a ocorrência do mês **quando o mês é aberto** (dashboard/lista), de forma idempotente (checa por `recurring_source` + ano/mês). Não gera antes do `start_date` nem quando `is_active=False`. As ocorrências são `Transaction` reais (editáveis, entram no saldo) com `recurring_source` setado; ao excluir a conta fixa, `SET_NULL` preserva o histórico.
- **Previsão calculada, não materializada**: a tela `forecast` projeta os próximos 6 meses somando transações reais + contas fixas ativas que **ainda não** foram materializadas naquele mês (filtra pelo conjunto de `recurring_source` já presentes), evitando dupla contagem. Não cria nada — o mês só "se concretiza" (materializa) quando aberto na navegação.
- **Navegação por mês**: dashboard e lista passaram de "mês corrente fixo" para `?month=AAAA-MM` (helper `_resolve_month`), com setas e rótulo pt-BR (`MONTHS_PT`, pois `LANGUAGE_CODE` é en-us). É o que permite enxergar parcelas e contas fixas dos meses futuros.
- **Classes base no `models.py` (DRY)**: o filtro de escopo virou um `ScopedQuerySet.in_scope` único (era copiado em 4 QuerySets); o trim/validação de nome virou `NameTrimMixin` e a validação de escopo+tipo da categoria virou `ScopedEntryMixin` (eram `clean()` duplicados). Menos repetição, mesma regra numa fonte só.
- **Ícone da categoria como `ImageField` (upload de imagem)**: era `CharField` de texto livre (confuso). Virou upload de imagem com Pillow; em produção a mídia vive num **volume do Railway** (`MEDIA_ROOT`), pois o filesystem do container é efêmero. A mídia é servida por rota própria (`media/...` → `serve`) já que o WhiteNoise só serve estáticos. Escolheu-se o volume por ser o caminho mais simples e persistente, sem conta/SDK externos (S3/R2 ficam para quando houver escala/CDN).
- **JS com Vite (mantendo o Tailwind standalone)**: o JS inline dos templates foi extraído para módulos em `frontend/src/` e empacotado com **Vite** + `django-vite`. Optou-se por usar o Node **só para o JS** — o Tailwind continua no modo standalone (binário próprio, sem Node) para não reescrever todo o pipeline de CSS. `dev_mode` fica off por padrão (usa o bundle buildado), então o fluxo é `npm run build` (análogo ao `tailwind build`), sem exigir dev server.
- **Interface 100% em pt-BR**: removida a mistura inglês/português que sobrava — `messages`, `title`, mensagens de `ValidationError` dos models e os labels de `TransactionType`/`PaymentMethod` agora são pt-BR (os valores no banco seguem em inglês). `get_*_display` passa a devolver rótulos em português direto, sem contorno manual no template.

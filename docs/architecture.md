# Arquitetura

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.14 |
| Framework web | Django 6.0.5 (MVT, server-rendered) |
| Templates | Django Template Language (sem framework JS) |
| Estilização | TailwindCSS v4 via `django-tailwind` em modo standalone (sem Node) |
| JavaScript | Vite + `django-vite` (bundle de `frontend/src/`); Node usado só no build do JS |
| Uploads | `ImageField` + Pillow; `MEDIA_ROOT` em volume do Railway na produção |
| Autenticação | `django.contrib.auth` com `User` nativo |
| Banco (dev) | SQLite 3 |
| Banco (produção) | PostgreSQL (via `DATABASE_URL` + `dj-database-url`) |
| Servidor (produção) | Gunicorn + WhiteNoise (estáticos), em container Docker no Railway |
| Admin | `django.contrib.admin` |

## Estrutura de pastas

```
emy/
├── core/                 # Projeto Django (settings, urls, wsgi/asgi)
├── finances/             # App de domínio
│   ├── models.py         # Category, Transaction, Profile, Household(+Membership), InvestmentGoal(+Contribution), HouseholdList(+Item), enums, ScopedQuerySet + mixins
│   ├── forms.py          # Registration, Category, Transaction, Profile, Household(+Member), InvestmentGoal, Contribution, HouseholdList(+Item)
│   ├── views.py          # register, profile_edit, dashboard, CRUD, grupos e escopo
│   ├── middleware.py     # ProfileCompletionMiddleware
│   ├── context_processors.py  # scope: active_household + user_households nos templates
│   ├── admin.py          # CategoryAdmin, TransactionAdmin, HouseholdAdmin, HouseholdMembershipAdmin
│   ├── urls.py           # rotas do app (app_name = "finances")
│   ├── tests.py          # testes do app (pytest)
│   ├── migrations/
│   └── templates/        # base.html, finances/, registration/
├── theme/                # App do django-tailwind (fonte + build do CSS)
├── frontend/             # Fonte (src/) e build (dist/) do JS — Vite
├── docs/                 # Esta documentação
├── Dockerfile            # Imagem multi-stage (builder + assets/Node + runtime non-root)
├── entrypoint.sh         # Cria o MEDIA_ROOT, roda migrate no start e entrega para o gunicorn (CMD)
├── docker-compose.yml    # Stack local: web (gunicorn) + db (PostgreSQL)
├── railway.json          # Config de build/healthcheck do Railway
├── .dockerignore
├── .env.example          # Modelo do .env (desenvolvimento)
├── .env.docker.example   # Modelo do .env.docker (stack docker-compose)
├── package.json          # Deps e scripts do front (Vite)
├── vite.config.js        # Config do Vite (build do JS para frontend/dist)
├── manage.py
├── requirements.txt
├── db.sqlite3
├── PRD.md
└── CLAUDE.md
```

## Apps

| App | Responsabilidade |
|---|---|
| `core` | Projeto Django — settings, URLs raiz, wsgi/asgi. Sem models próprios. |
| `finances` | App de domínio — categorias, transações, perfil do usuário, dashboard e telas de autenticação. |
| `theme` | App gerado pelo `django-tailwind` — guarda a fonte e o build do CSS. Sem models nem views próprios. |

A autenticação usa o `User` nativo de `django.contrib.auth` — não há app
`accounts` nem custom user model. O identificador é o **e-mail**, gravado
também como `username` (ver [security.md](security.md)).

## Escopo (pessoal x grupo)

As telas de dados operam num **escopo ativo**: pessoal (`household IS NULL`) ou
um grupo (`Household`) do qual o usuário é membro. O escopo ativo fica na
sessão (`request.session["active_household_id"]`).

- `get_active_household(request)` (em `views.py`) resolve o escopo, validando a
  membership; cai em pessoal se o id for inválido.
- Os managers `Transaction/Category/InvestmentGoal.objects.in_scope(user, household)`
  e `Household.objects.for_user(user)` centralizam o filtro. O `in_scope` vem de
  um `ScopedQuerySet` base compartilhado (uma fonte só). Investimentos reusam o
  mesmo escopo (objetivos pessoais ou de grupo).
- O context processor `finances.context_processors.scope` expõe
  `active_household` e `user_households` a todos os templates (pílula de escopo
  no `base.html`).
- O dashboard soma os aportes do mês no escopo ativo e os subtrai do saldo
  (aporte conta como saída de caixa). Listas de casa existem só em grupo.

## Views e rotas

Todas as views de dados são protegidas com `@login_required`. `register` é a
única view pública.

| View | Rota (name) | Função |
|---|---|---|
| `register` | `register` | Cadastro via `RegistrationForm` (e-mail); login automático; redireciona para `profile_edit`. |
| `profile_edit` | `finances:profile_edit` | Cria/edita o `Profile` do usuário; é a tela aberta logo após o cadastro. |
| `scope_switch` | `finances:scope_switch` | Troca o escopo ativo (pessoal ou grupo) na sessão. |
| `dashboard` | `finances:dashboard` | Resumo do mês selecionado (`?month=AAAA-MM`) + lançamentos do mês; materializa as contas fixas do mês. |
| `forecast` | `finances:forecast` | Previsão dos próximos 6 meses (transações reais + contas fixas projetadas, sem dupla contagem). |
| `transaction_list` | `finances:transaction_list` | Lista as transações do mês selecionado (`?month=`); filtro por tipo via `?type=income\|expense`; materializa as contas fixas do mês. |
| `transaction_create` | `finances:transaction_create` | Cria transação no escopo ativo. |
| `transaction_update` | `finances:transaction_update` | Edita transação dentro do escopo. |
| `transaction_delete` | `finances:transaction_delete` | Exclui transação após confirmação via POST. |
| `category_list` | `finances:category_list` | Lista categorias do escopo ativo. |
| `category_create` | `finances:category_create` | Cria categoria; `user` e `household` atribuídos na view. |
| `category_update` | `finances:category_update` | Edita categoria dentro do escopo. |
| `category_delete` | `finances:category_delete` | Exclui categoria; bloqueia se houver transações ou contas fixas vinculadas. |
| `recurring_list` | `finances:recurring_list` | Lista as contas fixas do escopo ativo. |
| `recurring_create/update/delete` | `finances:recurring_*` | CRUD de conta fixa; o create materializa o mês corrente. |
| `household_list` | `finances:household_list` | Lista os grupos do usuário. |
| `household_create` | `finances:household_create` | Cria grupo + membership do dono (atômico). |
| `household_detail` | `finances:household_detail` | Membros do grupo; o dono edita/exclui o grupo e adiciona/remove. |
| `household_update` | `finances:household_update` | Renomeia o grupo (só o dono). |
| `household_delete` | `finances:household_delete` | Exclui o grupo após confirmação via POST (só o dono); reseta o escopo ativo se for o do grupo. |
| `member_add` | `finances:member_add` | Adiciona membro por e-mail (só o dono). |
| `member_remove` | `finances:member_remove` | Remove membro (só o dono; nunca o dono). |
| `investment_list` | `finances:investment_list` | Objetivos do escopo + total investido. |
| `investment_create/update/delete` | `finances:investment_*` | CRUD de objetivo (dentro do escopo). |
| `investment_detail` | `finances:investment_detail` | Objetivo + progresso + aportes + form de aporte. |
| `contribution_create/delete` | `finances:contribution_*` | Registra/remove aporte num objetivo. |
| `list_index` | `finances:list_index` | Listas do grupo ativo (redireciona se escopo pessoal). |
| `list_create/detail/delete` | `finances:list_*` | CRUD de lista de casa (só grupo). |
| `list_item_add/toggle/delete` | `finances:list_item_*` | Adiciona/marca/remove item (POST). |

### URLs

`core/urls.py`:
- `admin/` → Django Admin
- `accounts/register/` → `register`
- `accounts/login/` → `LoginView` com `EmailAuthenticationForm` (name `login`), antes do `include` para ter precedência (login por e-mail case-insensitive)
- `accounts/` → `django.contrib.auth.urls` (logout, troca de senha)
- `""` → `finances.urls`

`finances/urls.py` (`app_name = "finances"`):
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
- `investments/`, `investments/new/`, `investments/<int:pk>/`,
  `investments/<int:pk>/edit/`, `investments/<int:pk>/delete/`,
  `investments/<int:pk>/contributions/add/`,
  `investments/<int:pk>/contributions/<int:contrib_pk>/delete/`
- `lists/`, `lists/new/`, `lists/<int:pk>/`, `lists/<int:pk>/delete/`,
  `lists/<int:pk>/items/add/`, `lists/<int:pk>/items/<int:item_pk>/toggle/`,
  `lists/<int:pk>/items/<int:item_pk>/delete/`

## Admin

`finances/admin.py` registra:
- `CategoryAdmin` — `list_display`, `list_filter` (tipo, ativo, grupo, data),
  `search_fields`, `autocomplete_fields = ("user", "household")`.
- `TransactionAdmin` — `list_display`, `list_filter` (tipo, método, data,
  categoria, grupo), `search_fields`,
  `autocomplete_fields = ("user", "household", "category")`,
  `date_hierarchy = "date"`.
- `HouseholdAdmin` — com inline de membros (`HouseholdMembership`).
- `HouseholdMembershipAdmin`.
- `InvestmentGoalAdmin` — com inline de aportes (`InvestmentContribution`);
  `InvestmentContributionAdmin`.
- `HouseholdListAdmin` — com inline de itens (`HouseholdListItem`).

## Settings relevantes (`core/settings.py`)

- `INSTALLED_APPS` inclui `finances`, `tailwind`, `theme`, `django_vite` e `axes`.
- `MIDDLEWARE` inclui `whitenoise.middleware.WhiteNoiseMiddleware` logo após o
  `SecurityMiddleware` (serve os estáticos em produção),
  `finances.middleware.ProfileCompletionMiddleware`, logo após o
  `AuthenticationMiddleware` — força usuário autenticado sem `Profile` a
  completar o perfil — e `axes.middleware.AxesMiddleware` por último.
- `AUTHENTICATION_BACKENDS`: `axes.backends.AxesStandaloneBackend` (primeiro) + `django.contrib.auth.backends.ModelBackend`.
- `django-axes`: `AXES_FAILURE_LIMIT = 5`, `AXES_COOLOFF_TIME = 1` (h), `AXES_LOCKOUT_PARAMETERS = [["ip_address", "username"]]`, `AXES_RESET_ON_SUCCESS = True` — ver [security.md](security.md).
- `TAILWIND_APP_NAME = 'theme'`.
- `DJANGO_VITE` (`dev_mode` via `DJANGO_VITE_DEV_MODE`, default `False`;
  `manifest_path` em `frontend/dist/manifest.json`; `static_url_prefix='dist'`) —
  ver [frontend.md](frontend.md).
- `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`.
- `AUTH_PASSWORD_VALIDATORS` com a configuração padrão do Django.
- Redirecionamentos de autenticação: `LOGIN_URL = 'login'`,
  `LOGIN_REDIRECT_URL = 'finances:dashboard'`, `LOGOUT_REDIRECT_URL = 'login'`.
- Banco: `dj_database_url.config()` lê `DATABASE_URL` (PostgreSQL em
  Docker/Railway) e cai no SQLite local (`BASE_DIR / 'db.sqlite3'`) quando a
  variável não está definida. Usa `conn_max_age=600` e `conn_health_checks`.
- Estáticos: `STORAGES['staticfiles']` usa
  `whitenoise.storage.CompressedManifestStaticFilesStorage` (comprime e versiona
  com hash para cache longo). `STATIC_ROOT = BASE_DIR / 'staticfiles'`.
  `STATICFILES_DIRS = [('dist', BASE_DIR/'frontend'/'dist')]` inclui o bundle do
  Vite (servido em `/static/dist/`). O `collectstatic` roda no build da imagem
  Docker.
- Mídia: `MEDIA_URL = 'media/'`; `MEDIA_ROOT = os.environ.get('MEDIA_ROOT',
  BASE_DIR/'media')` (em produção, o mount path de um volume do Railway). A
  mídia é servida por uma rota em `core/urls.py` (`media/...` → `serve`), pois o
  WhiteNoise não serve mídia de usuário.
- `SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS` vêm de variáveis de ambiente,
  carregadas de um `.env` na raiz pelo `python-dotenv`. `CSRF_TRUSTED_ORIGINS`
  também vem do ambiente. No Railway, o `settings.py` lê `RAILWAY_PUBLIC_DOMAIN`
  e o anexa a `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`; quando detecta o ambiente
  Railway (`RAILWAY_ENVIRONMENT`), adiciona `healthcheck.railway.app` ao
  `ALLOWED_HOSTS` para o healthcheck passar. Bloco `if not DEBUG:` ativa o
  hardening de produção — ver [security.md](security.md).
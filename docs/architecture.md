# Arquitetura

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.14 |
| Framework web | Django 6.0.5 (MVT, server-rendered) |
| Templates | Django Template Language (sem framework JS) |
| Estilização | TailwindCSS v4 via `django-tailwind` em modo standalone |
| Autenticação | `django.contrib.auth` com `User` nativo |
| Banco (dev) | SQLite 3 |
| Admin | `django.contrib.admin` |

## Estrutura de pastas

```
emy/
├── core/                 # Projeto Django (settings, urls, wsgi/asgi)
├── finances/             # App de domínio
│   ├── models.py         # Category, Transaction, Profile, Household(+Membership), InvestmentGoal(+Contribution), HouseholdList(+Item), enums
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
├── docs/                 # Esta documentação
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
  e `Household.objects.for_user(user)` centralizam o filtro. Investimentos
  reusam o mesmo escopo (objetivos pessoais ou de grupo).
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
| `dashboard` | `finances:dashboard` | Resumo do mês + 10 recentes, no escopo ativo. |
| `transaction_list` | `finances:transaction_list` | Lista transações do escopo ativo; filtro por tipo via `?type=income\|expense`. |
| `transaction_create` | `finances:transaction_create` | Cria transação no escopo ativo. |
| `transaction_update` | `finances:transaction_update` | Edita transação dentro do escopo. |
| `transaction_delete` | `finances:transaction_delete` | Exclui transação após confirmação via POST. |
| `category_list` | `finances:category_list` | Lista categorias do escopo ativo. |
| `category_create` | `finances:category_create` | Cria categoria; `user` e `household` atribuídos na view. |
| `category_update` | `finances:category_update` | Edita categoria dentro do escopo. |
| `category_delete` | `finances:category_delete` | Exclui categoria; bloqueia se houver transações vinculadas. |
| `household_list` | `finances:household_list` | Lista os grupos do usuário. |
| `household_create` | `finances:household_create` | Cria grupo + membership do dono (atômico). |
| `household_detail` | `finances:household_detail` | Membros do grupo; o dono adiciona/remove. |
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
- `accounts/` → `django.contrib.auth.urls` (login, logout, troca de senha)
- `""` → `finances.urls`

`finances/urls.py` (`app_name = "finances"`):
- `""` → `dashboard`
- `profile/` → `profile_edit`
- `scope/switch/` → `scope_switch`
- `transactions/` → `transaction_list`
- `transactions/new/` → `transaction_create`
- `transactions/<int:pk>/edit/` → `transaction_update`
- `transactions/<int:pk>/delete/` → `transaction_delete`
- `categories/` → `category_list`
- `categories/new/` → `category_create`
- `categories/<int:pk>/edit/` → `category_update`
- `categories/<int:pk>/delete/` → `category_delete`
- `groups/` → `household_list`
- `groups/new/` → `household_create`
- `groups/<int:pk>/` → `household_detail`
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

- `INSTALLED_APPS` inclui `finances`, `tailwind` e `theme`.
- `MIDDLEWARE` inclui `finances.middleware.ProfileCompletionMiddleware`, logo após o `AuthenticationMiddleware` — força usuário autenticado sem `Profile` a completar o perfil.
- `TAILWIND_APP_NAME = 'theme'`.
- `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`.
- `AUTH_PASSWORD_VALIDATORS` com a configuração padrão do Django.
- Redirecionamentos de autenticação: `LOGIN_URL = 'login'`,
  `LOGIN_REDIRECT_URL = 'finances:dashboard'`, `LOGOUT_REDIRECT_URL = 'login'`.
- Banco: SQLite em `BASE_DIR / 'db.sqlite3'`.
- `SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS` vêm de variáveis de ambiente,
  carregadas de um `.env` na raiz pelo `python-dotenv` — ver
  [security.md](security.md).
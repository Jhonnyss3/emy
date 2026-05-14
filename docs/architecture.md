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
│   ├── models.py         # Category, Transaction, TransactionType, PaymentMethod
│   ├── forms.py          # CategoryForm, TransactionForm
│   ├── views.py          # register, dashboard, CRUD de transações e categorias
│   ├── admin.py          # CategoryAdmin, TransactionAdmin
│   ├── urls.py           # rotas do app (app_name = "finances")
│   ├── tests.py          # testes do app
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
| `finances` | App de domínio — categorias, transações, dashboard e telas de autenticação. |
| `theme` | App gerado pelo `django-tailwind` — guarda a fonte e o build do CSS. Sem models nem views próprios. |

A autenticação usa o `User` nativo de `django.contrib.auth` — não há app
`accounts` nem custom user model.

## Views e rotas

Todas as views de dados são protegidas com `@login_required`. `register` é a
única view pública.

| View | Rota (name) | Função |
|---|---|---|
| `register` | `register` | Cadastro via `UserCreationForm`; login automático; redireciona usuário já autenticado para o dashboard. |
| `dashboard` | `finances:dashboard` | Resumo do mês corrente (receita, despesa, saldo) + 10 transações mais recentes. |
| `transaction_list` | `finances:transaction_list` | Lista as transações do usuário; filtro opcional por tipo via `?type=income\|expense`. |
| `transaction_create` | `finances:transaction_create` | Cria transação pelo `TransactionForm`. |
| `transaction_update` | `finances:transaction_update` | Edita transação restrita ao dono. |
| `transaction_delete` | `finances:transaction_delete` | Exclui transação após confirmação via POST. |
| `category_list` | `finances:category_list` | Lista as categorias do usuário. |
| `category_create` | `finances:category_create` | Cria categoria; `user` atribuído na view. |
| `category_update` | `finances:category_update` | Edita categoria restrita ao dono. |
| `category_delete` | `finances:category_delete` | Exclui categoria; bloqueia se houver transações vinculadas. |

### URLs

`core/urls.py`:
- `admin/` → Django Admin
- `accounts/register/` → `register`
- `accounts/` → `django.contrib.auth.urls` (login, logout, troca de senha)
- `""` → `finances.urls`

`finances/urls.py` (`app_name = "finances"`):
- `""` → `dashboard`
- `transactions/` → `transaction_list`
- `transactions/new/` → `transaction_create`
- `transactions/<int:pk>/edit/` → `transaction_update`
- `transactions/<int:pk>/delete/` → `transaction_delete`
- `categories/` → `category_list`
- `categories/new/` → `category_create`
- `categories/<int:pk>/edit/` → `category_update`
- `categories/<int:pk>/delete/` → `category_delete`

## Admin

`finances/admin.py` registra:
- `CategoryAdmin` — `list_display`, `list_filter` (tipo, ativo, data),
  `search_fields`, `autocomplete_fields = ("user",)`.
- `TransactionAdmin` — `list_display`, `list_filter` (tipo, método, data,
  categoria), `search_fields`, `autocomplete_fields = ("user", "category")`,
  `date_hierarchy = "date"`.

## Settings relevantes (`core/settings.py`)

- `INSTALLED_APPS` inclui `finances`, `tailwind` e `theme`.
- `TAILWIND_APP_NAME = 'theme'`.
- `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`.
- `AUTH_PASSWORD_VALIDATORS` com a configuração padrão do Django.
- Redirecionamentos de autenticação: `LOGIN_URL = 'login'`,
  `LOGIN_REDIRECT_URL = 'finances:dashboard'`, `LOGOUT_REDIRECT_URL = 'login'`.
- Banco: SQLite em `BASE_DIR / 'db.sqlite3'`.
- `DEBUG = True` e `SECRET_KEY` hardcoded — pendência de segurança, ver
  [security.md](security.md).
</content>
</invoke>

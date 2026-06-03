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
- **Uploads** (quando houver): restringir extensão/tamanho, nunca servir arquivo de usuário como executável, e guardar fora do diretório de código.
- **Não logar dados sensíveis** (senhas, tokens, PII desnecessária).
- Em produção: HTTPS obrigatório. O `settings.py` tem um bloco `if not DEBUG:` que ativa automaticamente `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS` (configurável via env, default 1 ano) + `INCLUDE_SUBDOMAINS`/`PRELOAD` e `SECURE_PROXY_SSL_HEADER` (para o Nginx). Em desenvolvimento (`DEBUG=True`) o bloco fica inerte.
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

## Visão Geral do Projeto

**Finances** é uma aplicação web de finanças pessoais. O usuário registra receitas e despesas, organiza-as em categorias customizáveis e acompanha o resultado do mês em um dashboard. Cada conta tem suas finanças pessoais privadas e pode participar de **grupos** (`Household`) — espaços compartilhados onde os membros lançam e acompanham contas em conjunto (ex.: a conta da casa de um casal). Há ainda **investimentos com objetivos** (pessoal e grupo, fluxo separado do caixa) e **listas de casa** (checklists compartilhadas, só em grupo). O cadastro e o login são por **e-mail**.

**Stack:**
- Python 3.14 / Django 6.0.5
- SQLite (desenvolvimento) — `db.sqlite3`
- PostgreSQL (produção, futuro — mesmo ORM, sem mudança de modelo)
- Frontend: Django Template Language (sem framework JS separado)
- Estilização: TailwindCSS v4 via `django-tailwind` no **modo standalone** (sem Node.js — ver seção Frontend / TailwindCSS)
- Autenticação: `django.contrib.auth` com `User` nativo
- Admin: `django.contrib.admin`

**Como rodar localmente:**
```bash
source .venv/bin/activate         # ativa o virtualenv
python manage.py migrate          # aplica migrations
python manage.py tailwind build   # compila o CSS (necessário ao menos uma vez)
python manage.py createsuperuser  # opcional, para acessar /admin/
python manage.py runserver        # inicia o servidor em localhost:8000
```

Durante o desenvolvimento de UI, manter `python manage.py tailwind start` rodando em outro terminal — recompila o CSS automaticamente a cada alteração de template.

Dependências em `requirements.txt` (Django, asgiref, sqlparse, django-tailwind, pytailwindcss, python-dotenv, django-axes, pytest, pytest-django).

As variáveis sensíveis (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`) ficam num `.env` na raiz (não versionado), carregado pelo `python-dotenv`. Copie o `.env.example` para `.env` e preencha o `SECRET_KEY` antes de rodar.

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
├── docs/                 # Documentação de guidelines e padrões (índice em docs/README.md)
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

- **TailwindCSS v4 via `django-tailwind` no modo standalone** — não há Node.js nem `npm` no projeto. O `pytailwindcss` baixa o binário standalone do Tailwind CLI; o `django-tailwind` o orquestra.
- O app `theme` foi criado por `python manage.py tailwind init` (template "Tailwind v4 Standalone").
- Fonte do CSS: `theme/static_src/src/styles.css` — contém `@import "tailwindcss"`, a diretiva `@source` que faz o Tailwind escanear todos os `.html/.py/.js` do projeto, um bloco `@theme` com os **tokens de design Emy**: cores `emy-*` (`emy-bg`, `emy-ink`, `emy-pink-*`, `emy-purple-*`, `emy-good`, `emy-bad` etc.) e fontes `font-sans` (Plus Jakarta Sans), `font-serif` (Instrument Serif), `font-script` (Caveat), e um `@layer utilities` com `.no-scrollbar` (usada no app shell).
- CSS compilado: `theme/static/css/dist/styles.css` — **artefato de build** (no `.gitignore`); o build precisa rodar no deploy. **Recompilar com `python manage.py tailwind build` sempre que mexer em template ou em `styles.css`.**
- Settings: `INSTALLED_APPS` inclui `tailwind` e `theme`; `TAILWIND_APP_NAME = 'theme'`.
- `finances/templates/base.html` carrega as fontes do Google (Plus Jakarta Sans, Instrument Serif, Caveat) e o CSS via `{% load tailwind_tags %}` + `{% tailwind_css %}` no `<head>`.
- Comandos: `python manage.py tailwind build` (build único) e `python manage.py tailwind start` (modo watch no desenvolvimento).
- **Estado atual da UI:** identidade **Emy — variação "Petal"** (off-white rosado, soft com glow, cards arredondados, gradiente rosa→roxo), 100% Tailwind + tokens `emy-*` (sem `<style>` inline). O layout é um **app shell** sem scrollbar (página fixa em `100dvh`, só o `main` rola por dentro sem barra); a navegação tem dois menus (seletor de escopo em dropdown no topo + nav inferior de ícones); o **desktop usa 50/50** (`lg:grid-cols-2`) enquanto o mobile fica em coluna única. Ao criar/editar templates, usar classes Tailwind + tokens Emy e seguir esses padrões (ver `docs/frontend.md`, seção "Layout / app shell").

---

## Modelo de Dados

Diagramas completos (classes e ER) estão em `PRD.md`, seção 8.2.

### Enums (`models.TextChoices`)

**TransactionType** — `income`, `expense`
**PaymentMethod** — `cash`, `debit_card`, `credit_card`, `pix`, `bank_slip`, `bank_transfer`

### Category

Bucket definido pelo usuário para classificar transações.

- `user` FK → `auth.User` (`on_delete=CASCADE`, `related_name="categories"`) — criador
- `household` FK → `Household` (`null=True, blank=True`, `on_delete=CASCADE`, `related_name="categories"`) — nulo = pessoal; preenchido = do grupo
- `name` CharField(80)
- `type` CharField(10) — choices de `TransactionType`
- `color` CharField(7) — hex, default `#3498db`, validado por `RegexValidator` (`#rgb` ou `#rrggbb`)
- `icon` CharField(50) — opcional (`blank=True`)
- `is_active` Boolean — default `True`
- `created_at` DateTimeField — `auto_now_add`
- `Meta`: `ordering = ["name"]`, `verbose_name_plural = "categories"`, e duas `UniqueConstraint` condicionais: `unique_personal_category` `(user, name, type)` quando `household IS NULL` e `unique_household_category` `(household, name, type)` quando `household IS NOT NULL`
- Manager `CategoryQuerySet.in_scope(user, household)`
- `clean()` — faz trim do nome e rejeita nome vazio
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
- Manager `TransactionQuerySet.in_scope(user, household)`
- `signed_amount` @property — valor com sinal: negativo para despesa, positivo para receita
- `installment_label` @property — `"2/12"` para parcelas, vazio caso contrário
- `clean()`:
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
- Manager `RecurringTransactionQuerySet.in_scope(user, household)`
- `day` @property — `start_date.day`
- `clean()` — trim da descrição + valida categoria por escopo e `category.type == type` (mesmas regras de `Transaction`)
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
- `clean()` — trim do nome; `__str__` — `name`

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
- Manager `InvestmentGoalQuerySet.in_scope(user, household)`
- `@property invested` (soma dos aportes); `@property progress` (% da meta, limitado a 100)
- `clean()` trim do nome; `__str__` = name

### InvestmentContribution

Aporte individual em um objetivo.

- `goal` FK → `InvestmentGoal` (CASCADE, `related_name="contributions"`)
- `user` FK → `auth.User` (CASCADE, `related_name="contributions"`) — quem aportou
- `amount` Decimal(12,2) `MinValueValidator(0.01)`; `date` DateField; `notes` TextField (blank); `created_at`
- `Meta.ordering = ["-date", "-created_at"]`. O escopo deriva do `goal`; o dashboard soma os aportes do mês no escopo e os subtrai do saldo.

### HouseholdList

Lista nomeada (checklist) de um grupo — só existe em grupo.

- `household` FK → `Household` (CASCADE, `related_name="lists"`); `name` CharField(80); `created_at`
- `clean()` trim; `__str__` = name

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
- **`CategoryForm`** — `ModelForm` de `Category`, campos `name`, `type`, `color`, `icon`, `is_active`. Widget `type=color` para `color`. Recebe `user=` e `household=` por kwarg no `__init__`; no `clean()` atribui `instance.user`/`instance.household` (apenas no create, para não trocar o criador num update de grupo) e sobrescreve `_get_validation_exclusions` para **não** excluir `user`/`household` — assim o `full_clean` roda as `UniqueConstraint` de escopo e a categoria duplicada vira erro de form (não `IntegrityError`/500).
- **`TransactionForm`** — `ModelForm` de `Transaction`, campos `description`, `amount`, `date`, `type`, `category`, `payment_method`, `notes`. O `__init__` recebe `user=` e `household=` por kwarg e:
  - filtra o queryset de `category` para mostrar apenas categorias **ativas do escopo ativo** (`Category.objects.in_scope(user, household)`);
  - em `clean()`, atribui `self.instance.user` e `self.instance.household` antes de o `Model.clean()` rodar as validações cruzadas.
  - Campo não-model `installments` (1–60): acima de 1, o `amount` informado é o **total** e a view gera N parcelas mensais. O `clean()` rejeita se o valor for insuficiente (cada parcela precisa de pelo menos `0.01`).
  - Widgets: `date` (`type=date`), `amount` (`step=0.01`, `min=0.01`), `notes` (textarea).
- **`RecurringTransactionForm`** — `ModelForm` de `RecurringTransaction`, campos `description`, `amount`, `type`, `category`, `payment_method`, `start_date`, `is_active`. Mesmo padrão do `TransactionForm`: recebe `user=`/`household=`, filtra categorias do escopo e atribui `user`/`household` no `clean()`.
- **`ProfileForm`** — `ModelForm` de `Profile`, campos `birth_date` e `phone`, mais os campos declarados `first_name` e `last_name` (que gravam no `User` nativo, não no `Profile`). O `__init__` recebe `user=` por kwarg e pré-popula `first_name`/`last_name` com os valores atuais do `User`. O `save()` grava o `Profile` e o `User` na mesma chamada. Widgets: `birth_date` (`type=date`), `phone` (placeholder).
- **`HouseholdForm`** — `ModelForm` de `Household`, campo `name`. O `created_by` é atribuído na view.
- **`MemberAddForm`** — `Form` com campo `email`; valida que existe uma conta com aquele e-mail (busca por `email`/`username`) e expõe o usuário encontrado em `self.user`. Mensagem de falha neutra ("Não foi possível adicionar este e-mail ao grupo") para reduzir enumeração de contas.
- **`InvestmentGoalForm`** — `ModelForm` de `InvestmentGoal`: `name`, `target_amount`, `target_date` (`type=date`). `user`/`household` atribuídos na view.
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
| `dashboard` | `finances:dashboard` | Resumo do mês selecionado (`?month=AAAA-MM`, default atual) + lançamentos do mês, no escopo ativo. Materializa as contas fixas do mês ao abrir. |
| `forecast` | `finances:forecast` | Previsão dos próximos 6 meses: transações reais + contas fixas ativas ainda não materializadas (sem dupla contagem). |
| `transaction_list` | `finances:transaction_list` | Lista as transações do mês selecionado (`?month=`) no escopo ativo; filtro por tipo via `?type=income\|expense`. Materializa as contas fixas do mês. |
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
| `household_detail` | `finances:household_detail` | Membros do grupo; o dono adiciona/remove. |
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
- `finances/household_form.html` — criação de grupo (nome).
- `finances/household_detail.html` — membros do grupo; o dono adiciona membro por e-mail e remove membros.
- `finances/dashboard.html` — saudação (usa `first_name`), **navegação por mês** (setas ‹ ›, atalho "Hoje"), card de saldo com gradiente (saldo/entrou/saiu/investido) + atalho "Listas da casa" (só em escopo de grupo) + lançamentos do mês selecionado (com selo "2/12" nas parcelas).
- `finances/forecast.html` — previsão dos próximos 6 meses em cards (saldo previsto + entrou/saiu); cada card abre aquele mês no dashboard. Mês atual destacado em gradiente.
- `finances/transaction_list.html` — navegação por mês + pills de filtro por tipo (preservam o mês) + atalho "Contas fixas" + lista de transações (selo "2/12" nas parcelas).
- `finances/transaction_form.html` — card dividido: toggle Despesa/Receita, valor grande, pills de categoria, data, método de pagamento, **parcelas** (só na criação) e observações.
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
- `finances/confirm_delete.html` — confirmação de exclusão (reusado por transação, categoria, objetivo e lista; título derivado de `object._meta.model_name`).
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

- `INSTALLED_APPS` inclui `finances`, `tailwind`, `theme` e `axes`.
- `MIDDLEWARE` inclui `finances.middleware.ProfileCompletionMiddleware` (logo após o `AuthenticationMiddleware`) e `axes.middleware.AxesMiddleware` (por último).
- `AUTHENTICATION_BACKENDS` = `axes.backends.AxesStandaloneBackend` (primeiro) + `django.contrib.auth.backends.ModelBackend`.
- Config do `django-axes`: `AXES_FAILURE_LIMIT = 5`, `AXES_COOLOFF_TIME = 1` (h), `AXES_LOCKOUT_PARAMETERS = [["ip_address", "username"]]`, `AXES_RESET_ON_SUCCESS = True`.
- `TAILWIND_APP_NAME = 'theme'`.
- `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`.
- `TEMPLATES['OPTIONS']['context_processors']` inclui `finances.context_processors.scope` (expõe `active_household` e `user_households`).
- `SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS` vêm de variáveis de ambiente, carregadas de um `.env` na raiz pelo `python-dotenv` (`load_dotenv()` no topo do `settings.py`). `SECRET_KEY` é obrigatória (`os.environ['SECRET_KEY']`); `DEBUG` tem default seguro `False`. O `.env` está no `.gitignore`; o `.env.example` é o modelo versionado.
- Bloco `if not DEBUG:` no fim do arquivo ativa o hardening de produção (SSL redirect, cookies seguros, HSTS via `SECURE_HSTS_SECONDS`, `SECURE_PROXY_SSL_HEADER`).
- Banco: SQLite em `BASE_DIR / 'db.sqlite3'`.

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
- **Gestão de membros restrita ao dono**: só `Household.created_by` adiciona/remove membros; o dono não pode ser removido. `created_by` em `CASCADE` é escolha de MVP (apagar a conta do dono apaga o grupo) — sem tela de exclusão de grupo/conta ainda.
- **Investimentos como fluxo separado (aporte não vira `Transaction`)**: `InvestmentGoal`/`InvestmentContribution` são models próprios e reusam o escopo (`household` anulável + `in_scope`). O aporte não duplica em `Transaction`; o dashboard soma os aportes do mês no escopo e os subtrai do saldo. Assim a seção de investimentos fica separada (telas/lista próprias) e o aporte ainda reflete como saída de caixa, sem mexer na obrigatoriedade de `category`.
- **Listas de casa só em grupo**: `HouseholdList` tem `household` obrigatório (não há lista pessoal). As views exigem escopo de grupo ativo e restringem o acesso às listas dos grupos do usuário; o acesso é via atalho no dashboard quando o escopo é um grupo.
- **TailwindCSS no modo standalone (sem Node.js)**: optou-se por `django-tailwind` 4.x + `pytailwindcss` em vez do modo "full" que exige Node/npm. Mantém o ambiente de desenvolvimento 100% Python — só `pip install` e os comandos `manage.py tailwind`. O binário do Tailwind CLI é baixado pelo `pytailwindcss`.
- **Identidade visual "Petal" (TailwindCSS)**: a UI foi migrada da v1 (CSS inline) para a identidade Emy, variação **"Petal"** — off-white rosado, soft/feminino com glow, cards bem arredondados, gradiente rosa→roxo, nav inferior flutuante. Escolhida entre três explorações de design (Soft Bloom / Petal / Aurora). Os tokens (cores `emy-*`, fontes) vivem no bloco `@theme` de `theme/static_src/src/styles.css`; o `<style>` inline do `base.html` foi removido. A migração cobriu só as telas com model atual (`Category`/`Transaction`) — Cartões, Metas, Insights, Transferência e Recorrência aparecem no mock mas não têm model e ficaram fora.
- **App shell sem scrollbar**: o `base.html` usa `h-[100dvh] overflow-hidden` no `<body>` e torna o `<main>` a única área rolável (`overflow-y-auto` + utility `.no-scrollbar` em `styles.css`), com o conteúdo centralizado por `my-auto`. A página nunca rola e não há barra visível; conteúdo maior que a tela rola por dentro. Foco mobile-first com `dvh`.
- **Dois menus (escopo no topo, seções embaixo)**: o topo tem o **seletor de escopo** (dropdown `<details>`: Pessoal/grupos/criar grupo) e a **nav inferior** flutuante de ícones cuida da navegação entre seções (mobile e desktop). Decisão do usuário de manter os dois separados.
- **Desktop 50/50**: a partir de `lg:`, as telas usam duas colunas (`lg:grid-cols-2`); o dashboard tem uma linha de cards de stat (`lg:grid-cols-4`) + recentes/listas; os forms usam "card dividido" (`md:grid-cols-2`). O mobile permanece em coluna única.
- **Barra de loading sem dependência**: `#page-loader` no `base.html` + JS vanilla; dá feedback de navegação no app server-rendered. Mesmo estilo pontual de JS já usado (toggle de senha, fechar dropdown).
- **Inputs renderizados campo a campo nos templates**: para ter controle total das classes Tailwind sem tocar em `forms.py`/`views.py`, os formulários (`login`, `register`, `transaction_form`, `category_form`, `profile_form`, telas de grupo) renderizam cada `<input>`/`<select>` manualmente com o `name=` correto, repondo o valor via `form.<campo>.value` e os erros via `form.<campo>.errors`. `type` e `category` viram radios estilizados (toggle/pills).
- **Validação de unicidade de `Category` no form (não só no banco)**: o `CategoryForm` mantém `user`/`household` fora do `_get_validation_exclusions` para que o `full_clean` rode as `UniqueConstraint` de escopo. Antes, como o `user`/`household` eram setados só na view (após o `is_valid`), a categoria duplicada passava no form e estourava `IntegrityError` (500). Mensagem amigável via `violation_error_message` (pt-BR) nas constraints, que aparece em `non_field_errors`. Defesa em profundidade: a constraint do banco continua sendo a barreira final.
- **Brute force com `django-axes` (não solução caseira)**: escolhido o pacote padrão de mercado em vez de rate limit próprio — robusto e funciona em produção multi-worker (handler em banco). Lockout pela combinação IP + username para não causar DoS de conta (um atacante de outro IP não tranca a vítima) nem trancar todos atrás de um NAT por um único username.
- **Login por e-mail case-insensitive via form, não backend custom**: como o cadastro já grava o `username` em minúsculas, o `EmailAuthenticationForm` só normaliza o input no login. Evita um backend de autenticação próprio (que complicaria a integração com o `django-axes`).
- **Selo "Beta V0.1" no header**: pílula pequena (tokens `emy-purple-*`) ao lado do logo no `base.html`, visível em mobile e desktop (compacta o bastante para não exigir variação por breakpoint).
- **Parcelamento materializado (N transações reais)**: uma compra "em 12x" gera 12 `Transaction` reais, uma por mês, ligadas por `installment_group` (UUID) e numeradas (`installment_number`/`installment_total`). Reusa toda a infra de escopo/dashboard/lista — cada parcela cai no saldo do seu mês. O `amount` informado é o **total**, dividido igualmente; a última parcela absorve o arredondamento (`ROUND_DOWN` + resto). Geração atômica em `_save_installments`.
- **Conta fixa materializada sob demanda**: `RecurringTransaction` é um template aberto (sem fim). Como não dá para materializar infinitas transações, `_materialize_recurring(user, household, year, month)` cria a ocorrência do mês **quando o mês é aberto** (dashboard/lista), de forma idempotente (checa por `recurring_source` + ano/mês). Não gera antes do `start_date` nem quando `is_active=False`. As ocorrências são `Transaction` reais (editáveis, entram no saldo) com `recurring_source` setado; ao excluir a conta fixa, `SET_NULL` preserva o histórico.
- **Previsão calculada, não materializada**: a tela `forecast` projeta os próximos 6 meses somando transações reais + contas fixas ativas que **ainda não** foram materializadas naquele mês (filtra pelo conjunto de `recurring_source` já presentes), evitando dupla contagem. Não cria nada — o mês só "se concretiza" (materializa) quando aberto na navegação.
- **Navegação por mês**: dashboard e lista passaram de "mês corrente fixo" para `?month=AAAA-MM` (helper `_resolve_month`), com setas e rótulo pt-BR (`MONTHS_PT`, pois `LANGUAGE_CODE` é en-us). É o que permite enxergar parcelas e contas fixas dos meses futuros.

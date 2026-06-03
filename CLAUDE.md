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
- **Isolamento de dados por usuário é obrigatório.** Toda query de `Category`/`Transaction` (e de qualquer model com dono) filtra por `request.user` — `.filter(user=request.user)` ou `get_object_or_404(Model, pk=pk, user=request.user)`. Nunca confiar em `pk` vindo da URL sem checar a posse.
- **Toda view de dados leva `@login_required`.** Views públicas são a exceção e devem ser conscientes.
- **CSRF em todo formulário POST** — `{% csrf_token %}` no template; nunca desabilitar a proteção CSRF.
- **Ações destrutivas (delete) só via POST**, nunca GET — com tela/etapa de confirmação.
- **Senhas**: sempre via `django.contrib.auth` (hash PBKDF2). Nunca armazenar, logar ou trafegar senha em texto puro. Manter os `AUTH_PASSWORD_VALIDATORS` ativos.
- **Nunca interpolar input do usuário em SQL/HTML cru.** Usar o ORM (que parametriza) e a auto-escape do template engine. Evitar `raw()`, `extra()`, `mark_safe`, `|safe` e `format_html` com dado não confiável.
- **Validar e tipar todo input** via `Form`/`ModelForm` antes de tocar no banco. Não construir objetos direto de `request.POST`.
- **Uploads** (quando houver): restringir extensão/tamanho, nunca servir arquivo de usuário como executável, e guardar fora do diretório de código.
- **Não logar dados sensíveis** (senhas, tokens, PII desnecessária).
- Em produção: HTTPS obrigatório e habilitar `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`.
- Antes de cada release: rodar `python manage.py check --deploy` e resolver os apontamentos.

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

**Finances** é uma aplicação web de finanças pessoais. O usuário registra receitas e despesas, organiza-as em categorias customizáveis e acompanha o resultado do mês em um dashboard. Cada conta enxerga apenas os próprios dados.

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

Dependências em `requirements.txt` (Django, asgiref, sqlparse, django-tailwind, pytailwindcss, python-dotenv).

As variáveis sensíveis (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`) ficam num `.env` na raiz (não versionado), carregado pelo `python-dotenv`. Copie o `.env.example` para `.env` e preencha o `SECRET_KEY` antes de rodar.

**Estrutura de pastas:**
```
emy/
├── core/                 # Projeto Django (settings, urls, wsgi/asgi)
├── finances/             # App de domínio
│   ├── models.py         # Category, Transaction, Profile, TransactionType, PaymentMethod
│   ├── forms.py          # CategoryForm, TransactionForm, ProfileForm
│   ├── views.py          # register, profile_edit, dashboard, CRUD de transações e categorias
│   ├── middleware.py     # ProfileCompletionMiddleware
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
- Fonte do CSS: `theme/static_src/src/styles.css` — contém `@import "tailwindcss"`, a diretiva `@source` que faz o Tailwind escanear todos os `.html/.py/.js` do projeto, e um bloco `@theme` com os **tokens de design Emy**: cores `emy-*` (`emy-bg`, `emy-ink`, `emy-pink-*`, `emy-purple-*`, `emy-good`, `emy-bad` etc.) e fontes `font-sans` (Plus Jakarta Sans), `font-serif` (Instrument Serif), `font-script` (Caveat).
- CSS compilado: `theme/static/css/dist/styles.css` — **artefato de build** (no `.gitignore`); o build precisa rodar no deploy. **Recompilar com `python manage.py tailwind build` sempre que mexer em template ou em `styles.css`.**
- Settings: `INSTALLED_APPS` inclui `tailwind` e `theme`; `TAILWIND_APP_NAME = 'theme'`.
- `finances/templates/base.html` carrega as fontes do Google (Plus Jakarta Sans, Instrument Serif, Caveat) e o CSS via `{% load tailwind_tags %}` + `{% tailwind_css %}` no `<head>`.
- Comandos: `python manage.py tailwind build` (build único) e `python manage.py tailwind start` (modo watch no desenvolvimento).
- **Estado atual da UI:** os templates foram migrados para a identidade visual **Emy — variação "Petal"**: off-white rosado, soft/feminino com glow, cards bem arredondados, gradiente rosa→roxo, nav inferior flutuante. O bloco `<style>` inline da v1 foi **removido** do `base.html` — toda estilização agora é via classes utilitárias do Tailwind + tokens `emy-*`. Escopo da migração: apenas as telas cobertas pelos models atuais (`Category`/`Transaction`); features do mock sem model (Cartões, Metas, Insights, Transferência, Recorrência) ficaram de fora. Ao criar/editar templates, usar classes Tailwind e os tokens Emy.

---

## Modelo de Dados

Diagramas completos (classes e ER) estão em `PRD.md`, seção 8.2.

### Enums (`models.TextChoices`)

**TransactionType** — `income`, `expense`
**PaymentMethod** — `cash`, `debit_card`, `credit_card`, `pix`, `bank_slip`, `bank_transfer`

### Category

Bucket definido pelo usuário para classificar transações.

- `user` FK → `auth.User` (`on_delete=CASCADE`, `related_name="categories"`)
- `name` CharField(80)
- `type` CharField(10) — choices de `TransactionType`
- `color` CharField(7) — hex, default `#3498db`, validado por `RegexValidator` (`#rgb` ou `#rrggbb`)
- `icon` CharField(50) — opcional (`blank=True`)
- `is_active` Boolean — default `True`
- `created_at` DateTimeField — `auto_now_add`
- `Meta`: `ordering = ["name"]`, `verbose_name_plural = "categories"`, `UniqueConstraint(user, name, type)` (`unique_category_per_user`)
- `clean()` — faz trim do nome e rejeita nome vazio
- `__str__` — `"{name} ({type})"`

### Transaction

Lançamento individual de receita ou despesa, pertencente a um usuário.

- `user` FK → `auth.User` (`on_delete=CASCADE`, `related_name="transactions"`)
- `category` FK → `Category` (`on_delete=PROTECT`, `related_name="transactions"`)
- `description` CharField(200)
- `amount` DecimalField(`max_digits=12`, `decimal_places=2`) — `MinValueValidator(0.01)`
- `date` DateField
- `type` CharField(10) — choices de `TransactionType`
- `payment_method` CharField(15) — choices de `PaymentMethod`, default `cash`
- `notes` TextField — opcional (`blank=True`)
- `created_at` DateTimeField — `auto_now_add`
- `updated_at` DateTimeField — `auto_now`
- `Meta`: `ordering = ["-date", "-created_at"]`
- `signed_amount` @property — valor com sinal: negativo para despesa, positivo para receita
- `clean()`:
  - faz trim da descrição
  - valida que `category.user == transaction.user`
  - valida que `category.type == transaction.type`
- `__str__` — `"{description} - {amount}"`

### Profile

Dados pessoais extras de um usuário, preenchidos logo após o cadastro.

- `user` OneToOneField → `auth.User` (`on_delete=CASCADE`, `related_name="profile"`)
- `birth_date` DateField — obrigatório
- `phone` CharField(20) — obrigatório, validado por `RegexValidator` (`phone_validator`)
- `created_at` DateTimeField — `auto_now_add`
- `updated_at` DateTimeField — `auto_now`
- `__str__` — `"Profile of {username}"`

O `Profile` só existe quando preenchido por completo (`birth_date` e `phone` são obrigatórios). O `ProfileCompletionMiddleware` usa a ausência do `Profile` para forçar o preenchimento.

### Regras de integridade

- `Category`: `UniqueConstraint(user, name, type)` — sem categorias duplicadas por usuário.
- `Transaction.category`: `on_delete=PROTECT` — categoria com transações vinculadas não pode ser excluída pelo ORM; a view `category_delete` checa antes e exibe mensagem de erro em vez de quebrar.
- `Transaction.amount`: `MinValueValidator(0.01)` — valor sempre maior que zero.
- `Transaction.clean()`: coerência usuário/categoria e tipo categoria/transação.
- `Profile.user`: `OneToOneField` — um perfil por usuário.

---

## Forms

- **`CategoryForm`** — `ModelForm` de `Category`, campos `name`, `type`, `color`, `icon`, `is_active`. Widget `type=color` para `color`. O `user` é atribuído na view (`commit=False`), não pelo form.
- **`TransactionForm`** — `ModelForm` de `Transaction`, campos `description`, `amount`, `date`, `type`, `category`, `payment_method`, `notes`. O `__init__` recebe `user=` por kwarg e:
  - filtra o queryset de `category` para mostrar apenas categorias **ativas do próprio usuário**;
  - em `clean()`, atribui `self.instance.user` antes de o `Model.clean()` rodar as validações cruzadas.
  - Widgets: `date` (`type=date`), `amount` (`step=0.01`, `min=0.01`), `notes` (textarea).
- **`ProfileForm`** — `ModelForm` de `Profile`, campos `birth_date` e `phone`, mais os campos declarados `first_name` e `last_name` (que gravam no `User` nativo, não no `Profile`). O `__init__` recebe `user=` por kwarg e pré-popula `first_name`/`last_name` com os valores atuais do `User`. O `save()` grava o `Profile` e o `User` na mesma chamada. Widgets: `birth_date` (`type=date`), `phone` (placeholder).

---

## Views

Todas as views de dados são protegidas com `@login_required`. `register` é a única view pública.

| View | Rota (name) | Função |
|---|---|---|
| `register` | `register` | Cadastro via `UserCreationForm`; login automático; redireciona para `profile_edit` após o cadastro e usuário já autenticado para o dashboard. |
| `profile_edit` | `finances:profile_edit` | Cria/edita o `Profile` do usuário pelo `ProfileForm`. É a tela que o `register` abre logo após o cadastro. |
| `dashboard` | `finances:dashboard` | Resumo do mês corrente (receita, despesa, saldo via `Sum`) + 10 transações mais recentes (`select_related("category")`). |
| `transaction_list` | `finances:transaction_list` | Lista as transações do usuário; filtro opcional por tipo via querystring `?type=income\|expense`. |
| `transaction_create` | `finances:transaction_create` | Cria transação pelo `TransactionForm`. |
| `transaction_update` | `finances:transaction_update` | Edita transação; `get_object_or_404(..., user=request.user)`. |
| `transaction_delete` | `finances:transaction_delete` | Exclui transação após confirmação via POST. |
| `category_list` | `finances:category_list` | Lista as categorias do usuário. |
| `category_create` | `finances:category_create` | Cria categoria; `user` atribuído na view. |
| `category_update` | `finances:category_update` | Edita categoria; restrita ao dono. |
| `category_delete` | `finances:category_delete` | Exclui categoria; bloqueia se houver transações vinculadas (`PROTECT`). |

**Padrão obrigatório de isolamento por usuário:** toda query de leitura/escrita de `Category` e `Transaction` deve filtrar por `request.user` (`.filter(user=request.user)` ou `get_object_or_404(Model, pk=pk, user=request.user)`). Permissão de leitura sem esse filtro vaza dados de outros usuários.

Feedback de sucesso/erro é dado via `django.contrib.messages` após cada ação.

---

## URLs

**`core/urls.py`:**
- `admin/` → Django Admin
- `accounts/register/` → `finances.views.register` (name `register`)
- `accounts/` → `include("django.contrib.auth.urls")` (login, logout, troca de senha)
- `""` → `include("finances.urls")`

**`finances/urls.py`** (`app_name = "finances"`):
- `""` → `dashboard`
- `profile/` → `profile_edit`
- `transactions/` → `transaction_list`
- `transactions/new/` → `transaction_create`
- `transactions/<int:pk>/edit/` → `transaction_update`
- `transactions/<int:pk>/delete/` → `transaction_delete`
- `categories/` → `category_list`
- `categories/new/` → `category_create`
- `categories/<int:pk>/edit/` → `category_update`
- `categories/<int:pk>/delete/` → `category_delete`

---

## Templates

`APP_DIRS=True` — templates ficam em `finances/templates/`. O `theme/templates/base.html` é gerado pelo `django-tailwind` e não é usado pelo app `finances` (que tem o seu próprio `base.html`).

Todos os templates abaixo já estão na identidade visual Emy/Petal (ver seção Frontend / TailwindCSS).

- `base.html` — layout base: header (logo Emy + nome do usuário com link para o perfil + Sair), nav inferior flutuante (Início / Lançamentos / Categorias / botão `+`, com item ativo via `request.resolver_match`), bloco de mensagens. O nome exibido é `first_name` (com fallback para `username`). Estilização 100% Tailwind, sem `<style>` inline.
- `finances/dashboard.html` — saudação (usa `first_name`), card de saldo com gradiente (saldo/entrou/saiu) + lista de lançamentos recentes.
- `finances/transaction_list.html` — pills de filtro por tipo + lista de transações em cards arredondados.
- `finances/transaction_form.html` — card dividido: toggle Despesa/Receita, valor grande, pills de categoria, data, método de pagamento e observações.
- `finances/category_list.html` — grid de cards de categoria.
- `finances/category_form.html` — formulário de criação/edição de categoria (toggle de tipo, cor, ícone, ativo).
- `finances/profile_form.html` — formulário de perfil (nome, sobrenome, data de nascimento, telefone). Usado tanto no preenchimento pós-cadastro quanto na edição.
- `finances/confirm_delete.html` — confirmação de exclusão (reusado por transação e categoria; título derivado de `object._meta.model_name`).
- `registration/login.html` — tela de login (card dividido com painel de gradiente).
- `registration/register.html` — tela de cadastro (mesmo padrão do login).

**Botão "Voltar" padronizado:** os forms (`transaction_form`, `category_form`, `profile_form`) têm um botão circular `←` no topo (fora do `<form>`, `type="button"`, `onclick="history.back()"`) que volta para a página anterior. Nos forms com título fora do `<form>` ele fica ao lado do título; no `transaction_form` (título dentro do card) fica acima do form.

---

## Admin

`finances/admin.py` registra:
- **`CategoryAdmin`** — `list_display`, `list_filter` (tipo, ativo, data), `search_fields`, `autocomplete_fields = ("user",)`.
- **`TransactionAdmin`** — `list_display`, `list_filter` (tipo, método, data, categoria), `search_fields`, `autocomplete_fields = ("user", "category")`, `date_hierarchy = "date"`.

---

## Autenticação

- `User` nativo de `django.contrib.auth` — sem custom user model. Dados pessoais extras vivem no model `Profile` (OneToOne).
- Login/logout/troca de senha via `django.contrib.auth.urls`.
- Cadastro via `UserCreationForm` na view `register`, com login automático após sucesso.
- Após o cadastro, o usuário é redirecionado para `profile_edit` para completar o perfil (nome, data de nascimento, telefone).
- `ProfileCompletionMiddleware` força o preenchimento: usuário autenticado sem `Profile` é redirecionado para `profile_edit` em qualquer rota (exceto `/admin/`, a própria tela de perfil e o `logout`).
- Senhas validadas por `AUTH_PASSWORD_VALIDATORS` (configuração padrão do Django).
- Logout via POST (Django 6 não aceita GET).
- Settings de redirecionamento em `core/settings.py`:
  - `LOGIN_URL = 'login'`
  - `LOGIN_REDIRECT_URL = 'finances:dashboard'`
  - `LOGOUT_REDIRECT_URL = 'login'`
- Não há sistema de permissões granulares — o isolamento é feito por `request.user` em cada view. O `Profile` guarda dados pessoais, não papéis nem permissões.

---

## Settings relevantes (`core/settings.py`)

- `INSTALLED_APPS` inclui `finances`, `tailwind` e `theme`.
- `MIDDLEWARE` inclui `finances.middleware.ProfileCompletionMiddleware` (logo após o `AuthenticationMiddleware`).
- `TAILWIND_APP_NAME = 'theme'`.
- `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`.
- `SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS` vêm de variáveis de ambiente, carregadas de um `.env` na raiz pelo `python-dotenv` (`load_dotenv()` no topo do `settings.py`). `SECRET_KEY` é obrigatória (`os.environ['SECRET_KEY']`); `DEBUG` tem default seguro `False`. O `.env` está no `.gitignore`; o `.env.example` é o modelo versionado.
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
- **Isolamento por `request.user` em vez de sistema de permissões**: o produto é single-tenant por conta — cada usuário só vê o que é seu. Não há perfis nem matriz de permissões; o filtro por `user` em cada query é a única barreira e é obrigatório.
- **TailwindCSS no modo standalone (sem Node.js)**: optou-se por `django-tailwind` 4.x + `pytailwindcss` em vez do modo "full" que exige Node/npm. Mantém o ambiente de desenvolvimento 100% Python — só `pip install` e os comandos `manage.py tailwind`. O binário do Tailwind CLI é baixado pelo `pytailwindcss`.
- **Identidade visual "Petal" (TailwindCSS)**: a UI foi migrada da v1 (CSS inline) para a identidade Emy, variação **"Petal"** — off-white rosado, soft/feminino com glow, cards bem arredondados, gradiente rosa→roxo, nav inferior flutuante. Escolhida entre três explorações de design (Soft Bloom / Petal / Aurora). Os tokens (cores `emy-*`, fontes) vivem no bloco `@theme` de `theme/static_src/src/styles.css`; o `<style>` inline do `base.html` foi removido. A migração cobriu só as telas com model atual (`Category`/`Transaction`) — Cartões, Metas, Insights, Transferência e Recorrência aparecem no mock mas não têm model e ficaram fora.
- **Inputs renderizados campo a campo nos templates**: para ter controle total das classes Tailwind sem tocar em `forms.py`/`views.py`, os formulários (`login`, `register`, `transaction_form`, `category_form`, `profile_form`) renderizam cada `<input>`/`<select>` manualmente com o `name=` correto, repondo o valor via `form.<campo>.value` e os erros via `form.<campo>.errors`. `type` e `category` viram radios estilizados (toggle/pills).

# Modelo de dados

Definido em [finances/models.py](../finances/models.py). Diagramas de classe
e ER completos estão no [PRD.md](../PRD.md), seção 8.2.

## Enums (`models.TextChoices`)

**TransactionType** — `income`, `expense`

**PaymentMethod** — `cash`, `debit_card`, `credit_card`, `pix`, `bank_slip`,
`bank_transfer`

## Category

Bucket definido pelo usuário para classificar transações.

| Campo | Tipo | Observação |
|---|---|---|
| `user` | FK → `auth.User` | `on_delete=CASCADE`, `related_name="categories"` (criador) |
| `household` | FK → `Household` | `null=True, blank=True`, `on_delete=CASCADE`, `related_name="categories"` — nulo = categoria pessoal; preenchido = categoria do grupo |
| `name` | CharField(80) | |
| `type` | CharField(10) | choices de `TransactionType` |
| `color` | CharField(7) | hex, default `#3498db`, validado por `RegexValidator` (`#rgb` ou `#rrggbb`) |
| `icon` | CharField(50) | opcional (`blank=True`) |
| `is_active` | Boolean | default `True` |
| `created_at` | DateTimeField | `auto_now_add` |

- `Meta`: `ordering = ["name"]`, `verbose_name_plural = "categories"`, duas
  `UniqueConstraint` condicionais: `unique_personal_category` em
  `(user, name, type)` quando `household IS NULL`, e `unique_household_category`
  em `(household, name, type)` quando `household IS NOT NULL`.
- Manager `CategoryQuerySet.in_scope(user, household)` — categorias do escopo
  ativo (pessoal ou grupo).
- `clean()` — faz trim do nome e rejeita nome vazio.
- `__str__` — `"{name} ({type})"`.

## Transaction

Lançamento individual de receita ou despesa, pertencente a um usuário.

| Campo | Tipo | Observação |
|---|---|---|
| `user` | FK → `auth.User` | `on_delete=CASCADE`, `related_name="transactions"` (quem lançou) |
| `household` | FK → `Household` | `null=True, blank=True`, `on_delete=CASCADE`, `related_name="transactions"` — nulo = lançamento pessoal; preenchido = lançamento do grupo |
| `category` | FK → `Category` | `on_delete=PROTECT`, `related_name="transactions"` |
| `description` | CharField(200) | |
| `amount` | DecimalField(12, 2) | `MinValueValidator(0.01)` |
| `date` | DateField | |
| `type` | CharField(10) | choices de `TransactionType` |
| `payment_method` | CharField(15) | choices de `PaymentMethod`, default `cash` |
| `notes` | TextField | opcional (`blank=True`) |
| `created_at` | DateTimeField | `auto_now_add` |
| `updated_at` | DateTimeField | `auto_now` |

- `Meta`: `ordering = ["-date", "-created_at"]`.
- Manager `TransactionQuerySet.in_scope(user, household)` — lançamentos do
  escopo ativo (pessoal ou grupo).
- `signed_amount` @property — valor com sinal: negativo para despesa,
  positivo para receita. Calculado na leitura, não persistido.
- `clean()`:
  - faz trim da descrição;
  - valida a categoria por escopo: se há `household`, a categoria deve ser do
    mesmo grupo; se é pessoal, a categoria deve ser pessoal e do mesmo `user`;
  - valida que `category.type == transaction.type`.
- `__str__` — `"{description} - {amount}"`.

## Profile

Dados pessoais extras de um usuário, preenchidos logo após o cadastro.

| Campo | Tipo | Observação |
|---|---|---|
| `user` | OneToOneField → `auth.User` | `on_delete=CASCADE`, `related_name="profile"` |
| `birth_date` | DateField | obrigatório |
| `phone` | CharField(20) | obrigatório, validado por `RegexValidator` (`phone_validator`) |
| `created_at` | DateTimeField | `auto_now_add` |
| `updated_at` | DateTimeField | `auto_now` |

- `__str__` — `"Profile of {username}"`.
- O "nome" do usuário não fica aqui — reaproveita `first_name`/`last_name` do
  `User` nativo (o `ProfileForm` edita os dois objetos).
- Como `birth_date` e `phone` são obrigatórios, o `Profile` só existe quando
  preenchido por completo. O `ProfileCompletionMiddleware` usa a ausência do
  `Profile` para forçar o preenchimento após o cadastro.

## Household

Espaço compartilhado (UI: "grupo") onde vários usuários acompanham finanças em
conjunto. Ex.: a conta da casa de um casal.

| Campo | Tipo | Observação |
|---|---|---|
| `name` | CharField(80) | |
| `created_by` | FK → `auth.User` | `on_delete=CASCADE`, `related_name="created_households"` (dono do grupo) |
| `created_at` | DateTimeField | `auto_now_add` |

- `Meta`: `ordering = ["name"]`.
- Manager `HouseholdManager.for_user(user)` — grupos dos quais o usuário é
  membro (`memberships__user=user`).
- `clean()` — faz trim do nome e rejeita nome vazio.
- `__str__` — `name`.

## HouseholdMembership

Liga um usuário a um grupo. O dono (`Household.created_by`) também tem uma
membership, criada junto com o grupo.

| Campo | Tipo | Observação |
|---|---|---|
| `household` | FK → `Household` | `on_delete=CASCADE`, `related_name="memberships"` |
| `user` | FK → `auth.User` | `on_delete=CASCADE`, `related_name="household_memberships"` |
| `joined_at` | DateTimeField | `auto_now_add` |

- `Meta`: `UniqueConstraint(household, user)` (`unique_household_member`).

## InvestmentGoal

Objetivo de investimento com meta de valor, pessoal ou compartilhado em grupo.
Vive num fluxo separado das transações.

| Campo | Tipo | Observação |
|---|---|---|
| `user` | FK → `auth.User` | `on_delete=CASCADE`, `related_name="investment_goals"` (criador) |
| `household` | FK → `Household` | `null=True, blank=True`, `on_delete=CASCADE`, `related_name="investment_goals"` — nulo = pessoal; preenchido = grupo |
| `name` | CharField(80) | |
| `target_amount` | DecimalField(12,2) | `MinValueValidator(0.01)` — meta |
| `target_date` | DateField | prazo opcional (`null=True, blank=True`) |
| `is_active` | Boolean | default `True` |
| `created_at` | DateTimeField | `auto_now_add` |

- Manager `InvestmentGoalQuerySet.in_scope(user, household)` (mesma lógica de Category/Transaction).
- `@property invested` — soma dos `amount` dos aportes; `@property progress` —
  `invested / target_amount * 100`, limitado a 100.
- `clean()` trim do nome; `Meta.ordering = ["name"]`; `__str__` = name.

## InvestmentContribution

Aporte individual em um objetivo.

| Campo | Tipo | Observação |
|---|---|---|
| `goal` | FK → `InvestmentGoal` | `on_delete=CASCADE`, `related_name="contributions"` |
| `user` | FK → `auth.User` | `on_delete=CASCADE`, `related_name="contributions"` (quem aportou) |
| `amount` | DecimalField(12,2) | `MinValueValidator(0.01)` |
| `date` | DateField | |
| `notes` | TextField | opcional (`blank=True`) |
| `created_at` | DateTimeField | `auto_now_add` |

- `Meta.ordering = ["-date", "-created_at"]`.
- O escopo deriva do `goal`. No dashboard, os aportes do mês corrente no escopo
  ativo são somados e **subtraídos do saldo** (entram como saída de caixa).

## HouseholdList

Lista nomeada (checklist) que pertence a um grupo — existe só em grupo.

| Campo | Tipo | Observação |
|---|---|---|
| `household` | FK → `Household` | `on_delete=CASCADE`, `related_name="lists"` |
| `name` | CharField(80) | |
| `created_at` | DateTimeField | `auto_now_add` |

- `clean()` trim do nome; `Meta.ordering = ["name"]`; `__str__` = name.

## HouseholdListItem

Item de uma lista de casa.

| Campo | Tipo | Observação |
|---|---|---|
| `list` | FK → `HouseholdList` | `on_delete=CASCADE`, `related_name="items"` |
| `text` | CharField(200) | |
| `is_done` | Boolean | default `False` |
| `created_at` | DateTimeField | `auto_now_add` |

- `Meta.ordering = ["is_done", "created_at"]` (pendentes primeiro).

## Regras de integridade

- `Category`: unicidade **por escopo** — `unique_personal_category`
  `(user, name, type)` quando pessoal e `unique_household_category`
  `(household, name, type)` quando do grupo. O mesmo nome pode existir como
  receita e despesa, e em escopos diferentes.
- `Transaction.category`: `on_delete=PROTECT` — categoria com transações
  vinculadas não pode ser excluída pelo ORM; a view `category_delete` checa
  antes e exibe mensagem de erro em vez de quebrar.
- `Transaction.amount`: `MinValueValidator(0.01)` — valor sempre maior que zero.
- `Transaction.clean()`: coerência categoria/escopo e tipo
  categoria/transação.
- `Category.color`: `RegexValidator` de hex (`#rgb` ou `#rrggbb`).
- `Profile.user`: `OneToOneField` — um perfil por usuário.
- `HouseholdMembership`: `UniqueConstraint(household, user)` — uma membership
  por par usuário/grupo.
- `InvestmentGoal.target_amount` / `InvestmentContribution.amount`:
  `MinValueValidator(0.01)`.
- `InvestmentGoal.household` anulável → nulo = pessoal, preenchido = grupo
  (mesmo padrão de escopo de Category/Transaction).

## Decisões de design

- **`User` nativo, não custom user model** — mais simples e suficiente para o
  escopo atual. Dados pessoais extras (data de nascimento, telefone) vivem no
  model `Profile` (OneToOne), não em um custom user model.
- **`Profile` como `OneToOneField` com `User`** — quando surgiu a necessidade
  de campos pessoais extras, optou-se por estendê-lo via `Profile` em vez de
  trocar `AUTH_USER_MODEL` (arriscado depois do projeto iniciado). O "nome"
  reaproveita `first_name`/`last_name` do `User`. `birth_date`/`phone`
  obrigatórios fazem o `Profile` só existir quando completo — o
  `ProfileCompletionMiddleware` usa isso como sinal de "perfil pendente".
- **Validações de domínio em `Model.clean()`** — coerência usuário/categoria,
  tipo categoria/transação e trim de strings vivem no `clean()` dos models,
  não nas views. Garante que admin, forms e scripts respeitem as mesmas regras.
- **`signed_amount` como @property** — `amount` guarda sempre o valor absoluto
  e `type` define o sinal; o valor com sinal é calculado na leitura, evitando
  inconsistência entre os dois campos.
- **`UniqueConstraint` por trio** — a unicidade não é por nome global:
  usuários diferentes podem ter categorias homônimas.
- **Escopo pessoal x grupo via `household` opcional** — em vez de tabelas
  separadas, `Category`/`Transaction` ganharam um FK `household` anulável:
  nulo = pessoal (privado do `user`), preenchido = do grupo (compartilhado
  entre os membros). Os managers `in_scope(user, household)` e
  `Household.objects.for_user(user)` centralizam o filtro de escopo, evitando
  repetir a regra nas views. O escopo ativo vive na sessão (ver
  [architecture.md](architecture.md)).
- **`Household` separado de `User`** — o grupo é uma entidade própria com
  membros via `HouseholdMembership` (M2M explícita, para guardar `joined_at` e
  permitir regras de dono). O `created_by` em `CASCADE` é uma escolha de MVP:
  se o dono apagar a conta, o grupo some — aceitável enquanto não há tela de
  exclusão de grupo/conta.
- **Investimentos como fluxo separado** — `InvestmentGoal`/`InvestmentContribution`
  são models próprios (não `Transaction` com flag). O aporte NÃO vira uma
  `Transaction` duplicada; em vez disso, o dashboard soma os aportes do mês no
  escopo ativo e os subtrai do saldo. Assim a seção de investimentos é separada
  (telas e lista próprias) e o aporte ainda reflete como saída de caixa, sem
  duplicação nem alterar a obrigatoriedade de `category` em `Transaction`.
- **Listas de casa só em grupo** — `HouseholdList` tem FK obrigatória para
  `Household` (não há lista pessoal). As views exigem escopo de grupo ativo e
  restringem o acesso às listas dos grupos do usuário
  (`HouseholdList.objects.filter(household__in=Household.objects.for_user(user))`).

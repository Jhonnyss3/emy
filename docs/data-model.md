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
| `user` | FK → `auth.User` | `on_delete=CASCADE`, `related_name="categories"` |
| `name` | CharField(80) | |
| `type` | CharField(10) | choices de `TransactionType` |
| `color` | CharField(7) | hex, default `#3498db`, validado por `RegexValidator` (`#rgb` ou `#rrggbb`) |
| `icon` | CharField(50) | opcional (`blank=True`) |
| `is_active` | Boolean | default `True` |
| `created_at` | DateTimeField | `auto_now_add` |

- `Meta`: `ordering = ["name"]`, `verbose_name_plural = "categories"`,
  `UniqueConstraint(user, name, type)` (`unique_category_per_user`).
- `clean()` — faz trim do nome e rejeita nome vazio.
- `__str__` — `"{name} ({type})"`.

## Transaction

Lançamento individual de receita ou despesa, pertencente a um usuário.

| Campo | Tipo | Observação |
|---|---|---|
| `user` | FK → `auth.User` | `on_delete=CASCADE`, `related_name="transactions"` |
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
- `signed_amount` @property — valor com sinal: negativo para despesa,
  positivo para receita. Calculado na leitura, não persistido.
- `clean()`:
  - faz trim da descrição;
  - valida que `category.user == transaction.user`;
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

## Regras de integridade

- `Category`: `UniqueConstraint(user, name, type)` — sem categorias
  duplicadas por usuário. O mesmo nome pode existir como receita e como
  despesa.
- `Transaction.category`: `on_delete=PROTECT` — categoria com transações
  vinculadas não pode ser excluída pelo ORM; a view `category_delete` checa
  antes e exibe mensagem de erro em vez de quebrar.
- `Transaction.amount`: `MinValueValidator(0.01)` — valor sempre maior que zero.
- `Transaction.clean()`: coerência usuário/categoria e tipo
  categoria/transação.
- `Category.color`: `RegexValidator` de hex (`#rgb` ou `#rrggbb`).
- `Profile.user`: `OneToOneField` — um perfil por usuário.

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
- **`UniqueConstraint(user, name, type)`** — a unicidade é por trio, não por
  nome global: usuários diferentes podem ter categorias homônimas.
</content>
</invoke>

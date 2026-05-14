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

## Decisões de design

- **`User` nativo, não custom user model** — mais simples e suficiente para o
  escopo atual.
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

# Guidelines de código

## Idioma do código

- **Todo o código é escrito em inglês, sem exceção.** Vale para models,
  campos de banco, classes, funções, métodos, variáveis, argumentos,
  constantes, nomes de templates, nomes de rotas (`name=`), `app_name`,
  arquivos e diretórios.
- Comentários e docstrings (quando existirem) também em inglês.
- A **interface exibida ao usuário** é em português (pt-BR): labels de
  formulário, mensagens de `messages`, textos de template, `verbose_name`,
  `help_text`, opções de choices voltadas ao usuário.
- Resumo: identificador de código → inglês; texto que o usuário lê na tela →
  português. Não misturar os dois idiomas em um mesmo identificador.

## Ordem de implementação (Django)

Ao adicionar ou editar funcionalidades em qualquer app, seguir sempre esta
ordem:

```
model → form → view → url → template
```

## Estilo de código

- Seguir a **PEP 8** e as convenções idiomáticas do Django. Nomes:
  `snake_case` para funções/variáveis, `PascalCase` para classes,
  `UPPER_SNAKE` para constantes.
- Incluir comentários apenas onde a lógica não for autoevidente.
- Não adicionar docstrings, type annotations ou comentários em código que
  não foi alterado.
- Não adicionar tratamento de erros ou validações para cenários fora do
  escopo atual.
- Preferir editar arquivos existentes a criar novos.
- Não criar arquivos de documentação (`*.md`) salvo quando explicitamente
  solicitado.
- Não deixar `print()` de depuração no código — usar o módulo `logging`
  quando necessário.

## Padrões Django

- **"Fat models, thin views".** Regra de negócio e validação ficam no model
  (`clean()`, métodos, properties); a view orquestra request/response e
  delega.
- **Validação de domínio centralizada em `Model.clean()`** — para que admin,
  forms e scripts compartilhem a mesma regra. Forms só cuidam de apresentação
  e input.
- **Não repetir o ORM nas views.** Lógica de query reutilizada vira método de
  `Manager`/`QuerySet` ou função auxiliar.
- **Evitar consultas N+1**: usar `select_related` (FK/OneToOne) e
  `prefetch_related` (M2M/reverse FK) ao iterar sobre relações. Nunca
  consultar o banco dentro de loop de template — preparar os dados na view.
- **`Decimal` para dinheiro**, nunca `float`.
- **Datas/horas com timezone** — usar `django.utils.timezone`
  (`timezone.now()`, `timezone.localdate()`), nunca `datetime.now()`.
  `USE_TZ = True`.
- **Operações destrutivas ou de múltiplas escritas** que precisam ser
  atômicas usam `transaction.atomic()`.
- **`get_object_or_404`** em vez de `try/except Model.DoesNotExist`
  espalhado.
- **Constraints no banco** (`UniqueConstraint`, `CheckConstraint`) além da
  validação no `clean()` — o `clean()` não roda em `bulk_create`/`update`.
- **Reaproveitar o que o Django já oferece** (auth, forms, generic views,
  messages, paginação) antes de escrever solução própria.
- **Settings sensíveis a ambiente** não ficam hardcoded — vêm de variável de
  ambiente com default seguro para desenvolvimento.

## Comportamento geral

- Nunca fazer mais do que foi pedido. Sem refatorações ou melhorias não
  solicitadas.
- Não usar abstrações ou utilitários para operações pontuais.
- Soluções devem ter o mínimo de complexidade necessária para a tarefa atual.
- Confirmar antes de executar ações destrutivas ou irreversíveis.

## Forms

- `CategoryForm` — `ModelForm` de `Category`, campos `name`, `type`, `nature`,
  `color`, `icon`, `is_active`. Widget `type=color` para `color`; `nature`
  (Fixa/Variável) renderiza como toggle no template. Recebe `user=` e
  `household=` por kwarg; no `clean()` atribui `instance.user`/`instance.household`
  (só no create) e mantém esses campos fora do `_get_validation_exclusions`, para
  que o `full_clean` rode as `UniqueConstraint` de escopo e a categoria duplicada
  vire erro de form em vez de `IntegrityError` (500).
- `TransactionForm` — `ModelForm` de `Transaction`. Recebe `user=`/`household=`
  por kwarg no `__init__` e:
  - filtra o queryset de `category` para mostrar apenas categorias ativas do
    escopo ativo, ordenadas por `nature` (para o select agrupar Fixa/Variável);
  - em `clean()`, atribui `self.instance.user`/`self.instance.household` antes
    de o `Model.clean()` rodar as validações cruzadas;
  - campo não-model `installments`: `TypedChoiceField` (coerce `int`, "À vista
    (1x)" a "24x", default 1), renderizado como `<select>`. Acima de 1, o
    `amount` é o total e a view gera N parcelas mensais (`_save_installments`).
  - Widgets: `date` (`type=date`), `amount` (`step=0.01`, `min=0.01`),
    `notes` (textarea).
- `RecurringTransactionForm` — `ModelForm` de `RecurringTransaction` (conta
  fixa). Mesmo padrão: recebe `user=`/`household=`, filtra categorias do escopo
  e atribui `user`/`household` no `clean()`.
- `ProfileForm` — `ModelForm` de `Profile`, campos `birth_date` e `phone`,
  mais os campos declarados `first_name` e `last_name` (que gravam no `User`
  nativo, não no `Profile`). Recebe `user=` por kwarg no `__init__` e
  pré-popula `first_name`/`last_name` com os valores atuais do `User`. O
  `save()` grava o `Profile` e o `User` na mesma chamada. Widgets:
  `birth_date` (`type=date`), `phone` (placeholder).

## Front-end (componentes)

Convenções detalhadas em [frontend.md](frontend.md). Em resumo, ao escrever
templates/JS:

- **Reaproveitar antes de copiar:** classes de componente (`.card`,
  `.btn-primary`, `shadow-card`/`shadow-btn`), partials (`_back_button`,
  `_empty_state`, `_progress_bar`, `_category_select`, `_date_field`,
  `_launch_modal`) e o filtro `brl` (`{{ valor|brl }}` para dinheiro, com
  `{% load money %}`).
- **Componentes de seleção sempre como widget**, nunca o controle nativo cru —
  todo `<select>` é enriquecido pelo módulo `selectWidget`; **datas** usam o
  widget próprio (`dateWidget`/`_date_field.html`), nunca `<input type="date">`;
  **valores em dinheiro** usam a máscara `moneyMask`. Vale também para futuros
  toggles/checkboxes (mesma abordagem de widget + tokens Emy).
- **Select de dado dinâmico** (criado pelo usuário) **sempre** oferece a opção de
  **criar** na listagem do widget (`data-create-url`/`data-create-label`, ou
  link fixo como no `_category_select.html`); enums estáticos não.
- Recompilar os artefatos ao mexer em UI: `tailwind build` (CSS) e
  `npm run build` (JS).
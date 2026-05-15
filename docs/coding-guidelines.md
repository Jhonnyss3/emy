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

- `CategoryForm` — `ModelForm` de `Category`, campos `name`, `type`, `color`,
  `icon`, `is_active`. Widget `type=color` para `color`. O `user` é atribuído
  na view (`commit=False`), não pelo form.
- `TransactionForm` — `ModelForm` de `Transaction`. Recebe `user=` por kwarg
  no `__init__` e:
  - filtra o queryset de `category` para mostrar apenas categorias ativas do
    próprio usuário;
  - em `clean()`, atribui `self.instance.user` antes de o `Model.clean()`
    rodar as validações cruzadas.
  - Widgets: `date` (`type=date`), `amount` (`step=0.01`, `min=0.01`),
    `notes` (textarea).
- `ProfileForm` — `ModelForm` de `Profile`, campos `birth_date` e `phone`,
  mais os campos declarados `first_name` e `last_name` (que gravam no `User`
  nativo, não no `Profile`). Recebe `user=` por kwarg no `__init__` e
  pré-popula `first_name`/`last_name` com os valores atuais do `User`. O
  `save()` grava o `Profile` e o `User` na mesma chamada. Widgets:
  `birth_date` (`type=date`), `phone` (placeholder).
</content>
</invoke>

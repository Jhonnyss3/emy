# Workflow

## Git

- Somente criar commits quando explicitamente solicitado.
- Nunca usar `--no-verify` ou pular hooks.
- Nunca fazer force push para `main`/`master` sem confirmação explícita.
- Sempre criar commits novos, nunca `amend` sem instrução direta.
- Mensagem de commit: concisa, focada no "por que", em português.

### .gitignore

O repositório não versiona: `__pycache__/` e `*.pyc`, `.venv/`, `db.sqlite3`,
`/media/` e `/staticfiles/`, arquivos `.env` (exceto `.env.example`), o CSS
compilado em `theme/static/css/dist/`, e arquivos de IDE/OS.

## Migrations

- Rodar `python manage.py makemigrations` e revisar o arquivo gerado antes de
  `migrate`.
- Toda mudança de model gera migration; revisar o arquivo gerado antes de
  commitar.
- Migrations versionadas junto com o código.
- Não editar migrations já aplicadas em algum ambiente.
- Data migrations destrutivas (mover dados antes de remover coluna/tabela)
  devem fazer backup do banco antes do deploy.
- Reproduzir o `migrate` global (sem nome de app) antes do deploy para
  validar a ordem topológica.

## Testes

- Toda nova funcionalidade tem teste (`TestCase`), cobrindo o caminho feliz e
  as validações de `clean()`/constraints.
- Os testes do app ficam em [finances/tests.py](../finances/tests.py).
- Rodar com `python manage.py test`.

## Antes de cada release

- Rodar `python manage.py check` (e `check --deploy` para produção) sem
  erros.
</content>
</invoke>

# Workflow

## Git

- Somente criar commits quando explicitamente solicitado.
- Nunca usar `--no-verify` ou pular hooks.
- Nunca fazer force push para `main`/`master` sem confirmação explícita.
- Sempre criar commits novos, nunca `amend` sem instrução direta.
- Mensagem de commit: concisa, focada no "por que", em português.

### .gitignore

O repositório não versiona: `__pycache__/` e `*.pyc`, `.venv/`, `db.sqlite3`,
`/media/` e `/staticfiles/`, arquivos `.env*` (exceto `.env.example` e
`.env.docker.example`), o CSS compilado em `theme/static/css/dist/`, e arquivos
de IDE/OS.

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

- Toda nova funcionalidade tem teste, cobrindo o caminho feliz e as validações
  de `clean()`/constraints.
- Os testes rodam com **pytest** (`pytest-django`). Config em
  [pytest.ini](../pytest.ini): `DJANGO_SETTINGS_MODULE = core.settings` e
  `python_files = tests.py test_*.py *_tests.py`.
- Os testes do app ficam em [finances/tests.py](../finances/tests.py) — estilo
  pytest (funções + fixtures, `pytestmark = pytest.mark.django_db`).
- Rodar com `pytest` (ou `python -m pytest`).
- Fixtures de usuário criam um `Profile` completo, senão o
  `ProfileCompletionMiddleware` redireciona os testes de view para a tela de
  perfil.

## Deploy

- Produção roda no **Railway** a partir do `Dockerfile` (ver
  [getting-started.md](getting-started.md), seção "Docker e deploy"). Push na
  branch `main` do GitHub dispara o rebuild.
- O build da imagem roda `tailwind build` + `collectstatic`; o `entrypoint.sh`
  roda `migrate` no start. Não rodar `migrate` manualmente no deploy — o
  entrypoint cuida disso.
- Variáveis sensíveis ficam no painel do Railway, nunca no repositório.
- Reproduzir o build localmente com `docker compose up --build` antes de
  mudanças que toquem `Dockerfile`/`requirements.txt`.

## Antes de cada release

- Rodar `python manage.py check` (e `check --deploy` para produção) sem
  erros.
- Rodar a suíte de testes (`pytest`). Os testes renderizam templates que
  referenciam o CSS via manifest do WhiteNoise; rodar `tailwind build` +
  `collectstatic` antes, senão falham com "Missing staticfiles manifest entry".
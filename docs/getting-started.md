# Como rodar o projeto

## Pré-requisitos

- Python 3.14
- Node.js (LTS) — usado **só para o build do JS** (Vite). O TailwindCSS roda em
  modo standalone via `pytailwindcss` (binário do Tailwind CLI baixado
  automaticamente, sem Node).

## Dependências

Listadas em [requirements.txt](../requirements.txt):

```
asgiref==3.11.1
dj-database-url==3.0.1
Django==6.0.5
django-axes==8.3.1
django-tailwind==4.4.2
django-vite==3.1.0
gunicorn==23.0.0
Pillow==12.2.0
psycopg[binary]==3.2.10
pytailwindcss==0.3.0
pytest==9.0.3
pytest-django==4.12.0
python-dotenv==1.2.2
sqlparse==0.5.5
whitenoise==6.11.0
```

`Pillow` é exigido pelo `ImageField` (ícone de categoria); `django-vite` integra
o bundle do Vite. As dependências de **front** (Vite) ficam em
[package.json](../package.json) e são instaladas com `npm install`.

O `django-axes` exige aplicar suas migrations (`python manage.py migrate`) —
o passo a passo abaixo já cobre isso. As dependências de produção
(`gunicorn`, `whitenoise`, `psycopg`, `dj-database-url`) só entram em uso no
deploy em container/Railway — ver a seção **Docker e deploy** abaixo.

## Variáveis de ambiente

O projeto lê `SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS` de um arquivo `.env` na
raiz (carregado pelo `python-dotenv`). O `.env` **não** é versionado; use o
[.env.example](../.env.example) como modelo.

```bash
cp .env.example .env              # cria o .env a partir do modelo
```

Depois, preencha o `SECRET_KEY` no `.env`. Para gerar uma chave nova:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

`SECRET_KEY` é obrigatória — o projeto não sobe sem ela. `DEBUG=True` e
`ALLOWED_HOSTS` vazio são adequados para desenvolvimento.

Em produção (`DEBUG=False`), `core/settings.py` ativa o hardening de segurança
(SSL redirect, cookies seguros, HSTS, proxy header). A variável opcional
`SECURE_HSTS_SECONDS` (default 1 ano) controla o `max-age` do HSTS — comece com
um valor pequeno ao habilitar e aumente depois.

## Passo a passo

```bash
source .venv/bin/activate         # ativa o virtualenv
pip install -r requirements.txt   # instala as dependências Python
npm install                       # instala as dependências do front (Vite)
cp .env.example .env              # cria o .env e preencha o SECRET_KEY
python manage.py migrate          # aplica as migrations
python manage.py tailwind build   # compila o CSS (ao menos uma vez)
npm run build                     # compila o JS (bundle do Vite — ao menos uma vez)
python manage.py createsuperuser  # opcional, para acessar /admin/
python manage.py runserver        # inicia o servidor em localhost:8000
```

## Desenvolvimento de interface

Durante o trabalho de UI, manter rodando em outros terminais:
- `python manage.py tailwind start` — recompila o CSS a cada alteração de template;
- `npm run watch` — recompila o JS a cada alteração em `frontend/src/`.

## Banco de dados

- Desenvolvimento: SQLite (`db.sqlite3`), criado pelo `migrate`.
- O arquivo `db.sqlite3` está no `.gitignore` e não é versionado.
- Produção: PostgreSQL. O `settings.py` usa `dj_database_url.config()` lendo a
  variável `DATABASE_URL`; sem ela, cai no SQLite local. Em Docker/Railway a
  `DATABASE_URL` aponta para o Postgres.

## Docker e deploy

O projeto é containerizado e roda em produção no **Railway** (deploy via
`Dockerfile`; o banco é PostgreSQL).

### Rodar a stack localmente com Docker

`docker-compose.yml` sobe dois serviços: `web` (a aplicação via gunicorn) e
`db` (PostgreSQL 17). As variáveis vêm de um `.env.docker` (modelo em
[.env.docker.example](../.env.docker.example) — copie e preencha; nunca
versione o preenchido).

```bash
cp .env.docker.example .env.docker   # preencha SECRET_KEY, POSTGRES_PASSWORD, DATABASE_URL
docker compose up --build            # sobe web + db; app em http://localhost:8000
```

O `Dockerfile` é multi-stage (builder com venv + stage `assets` com Node para o
build do JS + runtime mínimo rodando como usuário não-root). O stage `assets`
roda `npm ci && npm run build`; o runtime copia o `frontend/dist`, roda
`tailwind build` e `collectstatic` (um `SECRET_KEY` descartável só permite o
settings importar durante o build). O `entrypoint.sh` cria o `MEDIA_ROOT`, roda
`migrate` no start e então sobe o gunicorn. Os estáticos são servidos pelo
**WhiteNoise**; a **mídia de usuário** (uploads) é servida por uma rota própria
(`media/...`) e gravada no `MEDIA_ROOT`.

### Deploy no Railway

- `railway.json` define o builder (`DOCKERFILE`) e o healthcheck
  (`/accounts/login/`).
- Push na branch `main` do GitHub dispara o rebuild.
- O serviço precisa de um PostgreSQL provisionado e das variáveis de ambiente
  no painel (`SECRET_KEY`, `DEBUG=False`, `DATABASE_URL`, `ALLOWED_HOSTS`,
  `CSRF_TRUSTED_ORIGINS`, `SECURE_SSL_REDIRECT=False`, `MEDIA_ROOT`, `PORT`). O
  healthcheck do Railway bate com `Host: healthcheck.railway.app` — o
  `settings.py` adiciona esse host ao `ALLOWED_HOSTS` quando detecta o ambiente
  Railway. Detalhes de segurança em [security.md](security.md).
- **Uploads persistentes:** crie um **Volume** no serviço web e aponte
  `MEDIA_ROOT` para o mount path dele (ex.: `/data`). O filesystem do container é
  efêmero — sem volume, as imagens enviadas somem a cada deploy.
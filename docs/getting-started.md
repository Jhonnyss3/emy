# Como rodar o projeto

## Pré-requisitos

- Python 3.14
- O projeto não usa Node.js. O TailwindCSS roda em modo standalone via
  `pytailwindcss`, que baixa o binário do Tailwind CLI automaticamente.

## Dependências

Listadas em [requirements.txt](../requirements.txt):

```
asgiref==3.11.1
Django==6.0.5
django-tailwind==4.4.2
python-dotenv==1.2.2
pytailwindcss==0.3.0
sqlparse==0.5.5
```

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

## Passo a passo

```bash
source .venv/bin/activate         # ativa o virtualenv
pip install -r requirements.txt   # instala as dependências
cp .env.example .env              # cria o .env e preencha o SECRET_KEY
python manage.py migrate          # aplica as migrations
python manage.py tailwind build   # compila o CSS (ao menos uma vez)
python manage.py createsuperuser  # opcional, para acessar /admin/
python manage.py runserver        # inicia o servidor em localhost:8000
```

## Desenvolvimento de interface

Durante o trabalho de UI, manter `python manage.py tailwind start` rodando
em outro terminal — ele recompila o CSS automaticamente a cada alteração de
template.

## Banco de dados

- Desenvolvimento: SQLite (`db.sqlite3`), criado pelo `migrate`.
- O arquivo `db.sqlite3` está no `.gitignore` e não é versionado.
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
pytailwindcss==0.3.0
sqlparse==0.5.5
```

## Passo a passo

```bash
source .venv/bin/activate         # ativa o virtualenv
pip install -r requirements.txt   # instala as dependências
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
</content>
</invoke>

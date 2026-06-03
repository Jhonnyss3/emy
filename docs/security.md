# Segurança

## Isolamento de dados por usuário

O produto é single-tenant por conta — cada usuário só vê o que é seu. Não há
sistema de perfis nem matriz de permissões; o filtro por `user` em cada query
é a única barreira e é **obrigatório**.

- Toda query de `Category`/`Transaction` (e de qualquer model com dono)
  filtra por `request.user` — `.filter(user=request.user)` ou
  `get_object_or_404(Model, pk=pk, user=request.user)`.
- Nunca confiar em `pk` vindo da URL sem checar a posse.
- Permissão de leitura sem esse filtro vaza dados de outros usuários.

## Autenticação e acesso

- Toda view de dados leva `@login_required`. `register` é a única view
  pública e isso é uma decisão consciente.
- `ProfileCompletionMiddleware` redireciona usuário autenticado sem `Profile`
  para a tela de perfil em qualquer rota (exceto `/admin/`, a própria tela de
  perfil e o `logout`) — é uma regra global de acesso, não substitui o
  `@login_required` de cada view.
- Senhas sempre via `django.contrib.auth` (hash PBKDF2). Nunca armazenar,
  logar ou trafegar senha em texto puro. Manter os `AUTH_PASSWORD_VALIDATORS`
  ativos.
- Logout via POST (Django 6 não aceita GET).

## Formulários e input

- CSRF em todo formulário POST — `{% csrf_token %}` no template; nunca
  desabilitar a proteção CSRF.
- Ações destrutivas (delete) só via POST, nunca GET — com tela/etapa de
  confirmação.
- Validar e tipar todo input via `Form`/`ModelForm` antes de tocar no banco.
  Não construir objetos direto de `request.POST`.
- Nunca interpolar input do usuário em SQL/HTML cru. Usar o ORM (que
  parametriza) e a auto-escape do template engine. Evitar `raw()`, `extra()`,
  `mark_safe`, `|safe` e `format_html` com dado não confiável.

## Segredos e configuração

- Segredos nunca no código nem no versionamento. `SECRET_KEY`, credenciais de
  banco, chaves de API e afins vêm de variáveis de ambiente. O `core/settings.py`
  lê `SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS` de um `.env` na raiz, carregado pelo
  `python-dotenv` via `load_dotenv()`. O `.env` está no `.gitignore`; o
  `.env.example` (sem segredos) serve de modelo e é versionado.
- `SECRET_KEY` é lida com `os.environ['SECRET_KEY']` — obrigatória, o projeto
  não sobe sem ela. `DEBUG` vem de `os.environ.get('DEBUG', 'False') == 'True'`
  (default seguro: `False`). `ALLOWED_HOSTS` é a lista separada por vírgula da
  variável de mesmo nome.
- `DEBUG = False` em produção. `ALLOWED_HOSTS` restrito em produção.
- Não logar dados sensíveis (senhas, tokens, PII desnecessária).
- Em produção: HTTPS obrigatório e habilitar `SECURE_SSL_REDIRECT`,
  `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`.
- Antes de cada release: rodar `python manage.py check --deploy` e resolver
  os apontamentos.
</content>
</invoke>

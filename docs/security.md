# Segurança

## Isolamento de dados por escopo

Os dados pessoais continuam privados por conta; além disso há grupos
(`Household`) compartilhados entre membros. O isolamento agora é por **escopo**,
não só por `request.user` — e continua sendo a barreira central e
**obrigatória**.

- Toda query de `Category`/`Transaction` passa pelos managers de escopo
  `Model.objects.in_scope(request.user, household)`, onde `household` vem de
  `get_active_household(request)`:
  - escopo pessoal → `filter(user=request.user, household__isnull=True)`;
  - escopo de grupo → `filter(household=household)`, e o `household` só é
    resolvido se o usuário for membro (`Household.objects.for_user`).
- `get_object_or_404(Model.objects.in_scope(request.user, household), pk=pk)`
  para edição/exclusão — nunca confiar em `pk` da URL sem o filtro de escopo.
- O acesso a um grupo é sempre validado pela `HouseholdMembership`; trocar o
  escopo para um grupo do qual não se é membro cai em pessoal.
- Gestão de membros (`member_add`/`member_remove`) é restrita ao dono do grupo
  (`Household.created_by`).
- Sem o filtro de escopo, uma query vaza dados pessoais de outros usuários ou
  de grupos dos quais o usuário não participa.

## Autenticação e acesso

- O identificador da conta é o **e-mail**: o `RegistrationForm` grava o e-mail
  em `email` e também em `username` (em minúsculas), validando unicidade. O
  login usa o `EmailAuthenticationForm` (subclasse de `AuthenticationForm` que
  normaliza o input para minúsculas), então o login por e-mail é
  **case-insensitive**. A rota `accounts/login/` é declarada em `core/urls.py`
  antes do `include` de `auth.urls` para usar esse form. Não há custom user
  model nem backend de auth próprio.
- **Brute force**: `django-axes` bloqueia tentativas repetidas de login —
  `AXES_FAILURE_LIMIT = 5`, cooloff de 1h, lockout pela combinação IP +
  username (`AXES_LOCKOUT_PARAMETERS`), reset no sucesso. `AxesStandaloneBackend`
  é o primeiro em `AUTHENTICATION_BACKENDS` e `AxesMiddleware` é o último em
  `MIDDLEWARE`. O bloqueio devolve HTTP 429.
- **Enumeração de contas**: o `member_add` usa mensagem de falha neutra para não
  confirmar a existência de um e-mail. O cadastro ainda informa e-mail já
  usado (necessário para a UX); mitigá-lo por completo exigiria confirmação por
  e-mail (fora do escopo atual).
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
  (default seguro: `False`). `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` (este com
  o esquema, ex.: `https://...`) são listas separadas por vírgula das variáveis
  de mesmo nome.
- `DEBUG = False` em produção. `ALLOWED_HOSTS` restrito em produção.
- Não logar dados sensíveis (senhas, tokens, PII desnecessária).
- Em produção: HTTPS obrigatório. Um bloco `if not DEBUG:` no fim de
  `core/settings.py` ativa automaticamente `SECURE_SSL_REDIRECT` (configurável
  via env), `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`
  (configurável via env, default 1 ano) + `SECURE_HSTS_INCLUDE_SUBDOMAINS`,
  `SECURE_HSTS_PRELOAD` e `SECURE_PROXY_SSL_HEADER` (confia no
  `X-Forwarded-Proto` do proxy que termina o TLS — o edge do Railway).
  Em desenvolvimento (`DEBUG=True`) o bloco fica inerte.
- Antes de cada release: rodar `python manage.py check --deploy` e resolver
  os apontamentos. Com `DEBUG=False` + `ALLOWED_HOSTS` preenchido, hoje
  retorna 0 issues.

## Deploy (Railway / Docker)

- A imagem roda como **usuário não-root** (`Dockerfile`), e os segredos
  (`SECRET_KEY`, `DATABASE_URL` etc.) vêm de variáveis de ambiente do painel do
  Railway — nunca da imagem. O `SECRET_KEY` usado no build é descartável e só
  serve para o settings importar durante `tailwind build`/`collectstatic`.
- **`ALLOWED_HOSTS` no Railway:** o `settings.py` anexa o `RAILWAY_PUBLIC_DOMAIN`
  (domínio público injetado) e, quando há `RAILWAY_ENVIRONMENT`, o host fixo
  `healthcheck.railway.app` que o healthcheck do Railway usa no header `Host` —
  sem ele o healthcheck recebe 400 (DisallowedHost) e o deploy nunca fica
  saudável. Com domínio próprio, informe-o via `ALLOWED_HOSTS`/
  `CSRF_TRUSTED_ORIGINS`.
- **`SECURE_SSL_REDIRECT`:** no Railway o TLS é terminado no edge e o healthcheck
  bate por HTTP interno; mantê-lo `True` faria o healthcheck tomar 302. Por isso
  em produção no Railway ele é definido como `False` (o edge já força HTTPS).
- **Brute force / axes**: o handler do `django-axes` é em banco, então funciona
  em produção multi-worker (gunicorn) sem estado em memória compartilhado.
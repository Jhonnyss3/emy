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
  login usa o form padrão do Django (campo `username`), que funciona com o
  e-mail por serem iguais. Não há custom user model nem backend de auth próprio.
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
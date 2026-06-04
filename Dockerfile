# syntax=docker/dockerfile:1

# ---- Builder: install Python dependencies into an isolated venv ----
FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---- Runtime: minimal image running as an unprivileged user ----
FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=core.settings

# Run as a dedicated non-root user.
RUN groupadd --system app && useradd --system --gid app --no-create-home app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY . .

# Build the Tailwind CSS bundle and collect static files at image build time.
# The throwaway SECRET_KEY only lets Django settings import during the build;
# the real key is provided by the environment at runtime.
RUN SECRET_KEY="build-only-not-a-secret" python manage.py tailwind build \
    && SECRET_KEY="build-only-not-a-secret" python manage.py collectstatic --noinput

RUN chmod +x entrypoint.sh && chown -R app:app /app
USER app

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["sh", "-c", "gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-3} --access-logfile - --error-logfile -"]

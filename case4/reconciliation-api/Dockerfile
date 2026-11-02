# syntax=docker/dockerfile:1
FROM python:3.12-slim
WORKDIR /service
COPY requirements.lock pyproject.toml ./
COPY app ./app
COPY migrations ./migrations
# Managed environments pass the combined public CA bundle as a BuildKit secret.
# On ordinary hosts omit the secret to use the image's default system trust.
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    python -m pip install --no-cache-dir -r requirements.lock && \
    python -m pip install --no-build-isolation --no-deps .
RUN chmod -R a+rX /service/app /service/migrations
USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

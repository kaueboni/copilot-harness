FROM python:3.11-slim

WORKDIR /srv/app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
COPY app ./app

RUN uv sync --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

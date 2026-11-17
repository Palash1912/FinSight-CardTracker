FROM python:3.12-slim

WORKDIR /app

# System deps for asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install dependencies first (cached layer)
COPY pyproject.toml .
# Create minimal package structure for editable install
RUN mkdir -p app && touch app/__init__.py
RUN pip install --no-cache-dir -e ".[dev]"

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

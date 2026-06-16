FROM python:3.10-slim AS builder

WORKDIR /app
COPY pyproject.toml .
COPY novel_runtime/ novel_runtime/
COPY prompts/ prompts/
RUN pip install --no-cache-dir .

FROM python:3.10-slim AS runner

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY novel_runtime/ novel_runtime/
COPY prompts/ prompts/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "novel_runtime.main:app", "--host", "0.0.0.0", "--port", "8000"]

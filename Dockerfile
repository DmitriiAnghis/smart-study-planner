FROM python:3.9-slim
WORKDIR /app
COPY . .
# Если твое приложение — это просто скрипт, оставь так:
CMD ["python", "-m", "http.server", "80"]
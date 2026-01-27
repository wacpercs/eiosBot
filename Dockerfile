FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY telegram_bot.py .
COPY webhook_server.py .
COPY database.py .
COPY eios_integration.py .
COPY miniapp.html .

# Создаем директорию для логов
RUN mkdir -p /app/logs

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1

# Здоровье контейнера
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# По умолчанию запускаем бота
CMD ["python", "telegram_bot.py"]

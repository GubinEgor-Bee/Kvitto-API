FROM python:3.11-slim

WORKDIR /app

# Отключаем буферизацию вывода и создание pyc файлов
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# При запуске контейнера сначала накатываем миграции, потом стартуем сервер
CMD sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"

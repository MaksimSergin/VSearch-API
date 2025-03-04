# Используем официальный образ Python
FROM python:3.12-slim

# Отключаем запись .pyc файлов и буферизацию stdout
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем рабочую директорию
WORKDIR /app

RUN apt-get update \
    && apt-get install -y default-libmysqlclient-dev build-essential libpq-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install poetry

# Копирование зависимостей проекта
COPY pyproject.toml poetry.lock /app/

# Установка зависимостей проекта без создания виртуального окружения
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Копируем весь проект
COPY . /app/

EXPOSE 8000

# Команда запуска Django через gunicorn
CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:8000"]
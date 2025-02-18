FROM python:3.12-slim

# Установка зависимостей для сборки
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Задаём рабочую директорию
WORKDIR /app

# Копирование и установка Python-зависимостей
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копирование остального кода
COPY . /app

# Добавляем volume для сохранения данных (например, база SQLite будет храниться в /app/data)
VOLUME ["/app/data"]

# Команда для запуска приложения
CMD ["python", "main.py"]

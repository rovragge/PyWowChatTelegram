FROM python:3.12-slim

# Устанавливаем минимальный набор для компиляции C++
RUN apt-get update && apt-get install -y --no-install-recommends g++ \
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

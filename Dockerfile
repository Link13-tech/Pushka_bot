# Используем базовый образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Создаем необходимые директории для хранения аудиофайлов
RUN mkdir -p /app/audio/files

# Устанавливаем ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Копируем файлы проекта
COPY . .

# Устанавливаем Poetry
RUN pip install poetry

# Устанавливаем зависимости через Poetry
RUN poetry config virtualenvs.create false && poetry install --only main --no-root

# Указываем точку входа
CMD ["poetry", "run", "python", "bot.py"]
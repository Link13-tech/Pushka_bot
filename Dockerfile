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

# Устанавливаем Poetry через официальный скрипт
RUN curl -sSL https://install.python-poetry.org | python3 -

# Добавляем Poetry в PATH
ENV PATH="${PATH}:/root/.local/bin"

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости через Poetry
RUN poetry install --only main --no-root --no-interaction

# Указываем точку входа
CMD ["poetry", "run", "python", "bot.py"]
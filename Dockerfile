# Используем базовый образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Создаем необходимые директории для хранения аудиофайлов
RUN mkdir -p /app/audio/files

# Устанавливаем ffmpeg и необходимые зависимости для сборки llvmlite
RUN apt-get update && \
    apt-get install -y ffmpeg llvm-10-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

# Копируем файлы проекта в контейнер
COPY . .

# Устанавливаем Poetry
RUN pip install poetry

# Проверяем, что Poetry установлен
RUN poetry --version

# Устанавливаем зависимости через Poetry
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-root

# Указываем точку входа
CMD ["poetry", "run", "python", "bot.py"]
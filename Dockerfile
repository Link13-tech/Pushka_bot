# Используем базовый образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Создаем необходимые директории для хранения аудиофайлов
RUN mkdir -p /app/audio/files

# Устанавливаем ffmpeg, репозиторий LLVM и необходимые пакеты для сборки
RUN apt-get update && \
    apt-get install -y gnupg2 curl build-essential ffmpeg && \
    curl -sSL https://apt.llvm.org/llvm.sh | bash -s -- 10 && \
    apt-get install -y llvm-10 llvm-10-dev llvm-10-tools && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем переменную окружения для указания пути к llvm-config
ENV LLVM_CONFIG=/usr/bin/llvm-config-10

# Копируем файлы проекта
COPY . .

# Устанавливаем Poetry
RUN pip install poetry

# Устанавливаем зависимости через Poetry
RUN poetry config virtualenvs.create false && poetry install --only main --no-root

# Указываем точку входа
CMD ["poetry", "run", "python", "bot.py"]
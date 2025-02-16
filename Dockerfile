# Используем базовый образ Python
FROM python:3.12.2

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Создаем необходимые директории для хранения аудиофайлов
RUN mkdir -p /app/audio/files

# Обновляем пакеты и устанавливаем необходимые зависимости для сборки
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    llvm \
    clang \
    build-essential \
    libclang-dev \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Копируем файлы проекта
COPY . .

# Устанавливаем Poetry
RUN pip install poetry

# Отключаем создание виртуальных окружений и устанавливаем зависимости через Poetry
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-root -v

# Указываем точку входа
CMD ["poetry", "run", "python", "bot.py"]
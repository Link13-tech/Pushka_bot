# Используем базовый образ Python
FROM python:3.12.2

# Устанавливаем рабочую директорию
WORKDIR /app

# Обновляем пакеты и устанавливаем зависимости для сборки
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    llvm \
    clang \
    build-essential \
    libclang-dev \
    libedit-dev \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN pip install poetry

# Копируем файлы poetry.lock и pyproject.toml для кэширования зависимостей
COPY poetry.lock pyproject.toml ./

# Устанавливаем зависимости
RUN poetry install --no-root --only main -v

# Копируем оставшиеся файлы проекта
COPY . .

# Создаем директории для хранения аудиофайлов
RUN mkdir -p /app/audio/files

# Указываем точку входа
CMD ["poetry", "run", "python", "bot.py"]
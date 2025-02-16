# Используем базовый образ Python
FROM python:3.12

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

# Проверяем версию Poetry
RUN poetry --version

# Сначала настраиваем Poetry, чтобы не создавать виртуальные окружения
RUN poetry config virtualenvs.create false

# Затем устанавливаем зависимости
RUN poetry install --only main --no-root -v

# Указываем точку входа
CMD ["poetry", "run", "python", "bot.py"
# Используем базовый образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем Poetry
RUN pip install poetry

# Устанавливаем зависимости через Poetry
RUN poetry config virtualenvs.create false && poetry install --no-dev

# Указываем точку входа
CMD ["poetry", "run", "python", "bot.py"]
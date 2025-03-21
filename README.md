
# PushkaRGB Bot

PushkaRGB — это Telegram-бот для изучения стихотворений А.С. Пушкина с использованием голосовых записей и уровней сложности. Бот поможет улучшить память и выучить стихотворения с весельем и пользой, а также отслеживать прогресс через статистику.

## Описание

Этот бот создан для любителей поэзии, которые хотят учить стихи и совершенствовать память с помощью современных технологий. Основная цель — предоставить пользователю возможность учить стихотворения, тренируя память с помощью голосовых записей.

## Структура проекта

```
.
├── audio/                 # Папка с аудиофайлами
│   ├── files/             # Загружаемые и временные аудиофайлы
│   └── processing.py      # Логика распознования голоса и сравнения с эталоном
├── commands/              # Команды для бота
│   └── commands.py        # Логика работы с командами для админа и юзера
├── database/              # Работа с базой данных
│   ├── database.py        # Создание сессий для БД
│   ├── user_db.py         # Логика работы с пользователями
│   └── voice_db.py        # Логика работы с голосовыми записями
├── handlers/              # Обработчики команд и сообщений
│   ├── start.py           # Приветственное сообщение и /start
│   ├── admin.py           # Обработчики для админов
│   ├── poems.py           # Обработчики для выбора стихотворений и их изучения
│   ├── share.py           # Обработчик для кнопок "Поделиться"
│   └── voice.py           # Обработчики для работы с голосом
├── levels/                # Логика уровней сложности
│   └── training_levels.py # Настройка уровней
├── migrations/            # Миграции базы данных
├── models/                # Модели базы данных
│   ├── base.py            # Базовая модель
│   ├── poem.py            # Модель стихотворения
│   ├── user.py            # Модель пользователя
│   └── user_poem.py       # Модель пользователь-стих
├── stats/                 # Сбор статистики
│   └── stats....xlsx      # Сохранение файлов со статистикой
├── .env                   # Конфигурации и переменные окружения
├── alembic.ini            # Конфигурация Alembic для миграций
├── poetry.lock            # Зависимости проекта
├── pyproject.toml         # Конфигурация Poetry
├── bot.py                 # Основной файл бота
└── README.md              # Описание бота
```

## Установка

Клонируйте репозиторий:

```bash
git clone https://github.com/Link13-tech/Pushka_bot.git
cd pushka_bot
```

Установите зависимости с помощью Poetry:

```bash
poetry install
```
Создайте базу данных.

Создайте файл `.env` и добавьте ваш Telegram Token и URL базы данных:

```
BOT_TOKEN=your-telegram-bot-token
DATABASE_URL=your-database-arl-adress
```

Примените миграции для базы данных:

```bash
alembic upgrade head
```
Заполните таблицу poem данными.

## Запуск

Для запуска бота используйте команду:

```bash
poetry run python bot.py
```

После этого бот начнет слушать команды и сообщения в вашем Telegram-чате.

## Команды

for user:

- `/start`       — Приветственное сообщение и кнопка для выбора стихотворений.
- `/description` — Описание бота и его функционала.
- `/contact`     — Контакты для связи.

for admin:

- `/start`       — Приветственное сообщение и кнопка для выбора стихотворений.
- `/description` — Описание бота и его функционала.
- `/contact`     — Контакты для связи.
- `/setrole`     — Изменить роль пользователя
- `/stats`       — Статистика

## Основные особенности

- **Выбор стихотворений** — Пользователи могут выбрать стихотворение по алфавиту или случайным образом.
- **Уровни сложности** — Бот предлагает несколько уровней сложности, каждый из которых помогает постепенно учить стихотворение, скрывая часть текста.
- **Голосовая запись** — Пользователи могут записать свой голос для проверки, как хорошо они запомнили стихотворение.
- **Статистика** — Сбор статистики о прогрессе пользователей и популярности стихотворений. Администраторы могут получить отчеты и графики.
- **Поделиться стихотворением** — Кнопки для быстрого деления стихами через социальные сети (VK, Одноклассники).

## Статистика

Бот собирает следующие данные:

- Количество пользователей, использующих бота.
- Популярность стихотворений.

Администраторы могут просматривать статистику в боте, а также генерировать отчеты в формате Excel.

## Автор

Разработчик: THE FIRST COMMAND (Link13-PDEV)

---

✨ Изучай поэзию с удовольствием! ✨

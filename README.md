# Система бронирования столов

Мини-система бронирования ресторана на Python + PostgreSQL с GUI на tkinter.

**Уровни:** базовый (CRUD, автосоздание таблиц) и средний (полный CRUD, проверка доступности стола, GUI).

## Структура репозитория

```
postgres_driver.py   — драйвер PostgreSQL (CRUD)
backend.py           — бизнес-логика и API
models/              — модели User, Table, Booking
app.py               — графический интерфейс (tkinter)
gui/                 — вкладки GUI
seed_data.py         — тестовые данные для сдачи
check_availability_cli.py — CLI-проверка доступности
requirements.txt
.env.example
screenshots/         — скриншоты для сдачи (см. screenshots/README.md)
```

## Требования

- Python 3.10+
- PostgreSQL 12+
- PgAdmin (для демонстрации данных)

## Быстрый старт

### 1. Клонирование и зависимости

```bash
git clone <URL-вашего-репозитория>
cd Booking
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Настройка базы данных

```bash
cp .env.example .env
```

Отредактируйте `.env` — укажите свои параметры PostgreSQL:

| Переменная    | Описание        |
|---------------|-----------------|
| `DB_HOST`     | Хост сервера    |
| `DB_PORT`     | Порт (5432)     |
| `DB_NAME`     | Имя базы        |
| `DB_USER`     | Пользователь    |
| `DB_PASSWORD` | Пароль          |

База `DB_NAME` должна существовать в PostgreSQL.

### 3. Инициализация таблиц

```bash
python backend.py
```

Создаёт таблицы `users`, `restaurant_tables`, `bookings`.

### 4. Тестовые данные (для сдачи)

```bash
python seed_data.py
```

Добавляет ≥3 пользователей, ≥3 столов, ≥2 бронирований.

### 5. Запуск GUI

```bash
python app.py
```

или:

```bash
python main.py
```

## Основные команды

| Команда | Описание |
|---------|----------|
| `python backend.py` | Создать таблицы в PostgreSQL |
| `python seed_data.py` | Заполнить БД тестовыми данными |
| `python app.py` | Запустить графический интерфейс |
| `python check_availability_cli.py --table 1 --datetime "2026-06-10 19:00:00" --duration 60` | Проверить доступность стола (CLI) |
| `python scripts/export_submission_data.py` | Вывести список бронирований для скриншота |

## API backend

### Пользователи
`create_user`, `get_user`, `get_all_users`, `update_user`, `delete_user`

### Столы
`create_table` / `create_restaurant_table`, `get_restaurant_table`, `get_all_restaurant_tables`, `update_restaurant_table`, `delete_restaurant_table`

### Бронирования
`create_booking`, `get_booking`, `get_all_bookings`, `update_booking`, `delete_booking`

### Проверка доступности (средний уровень)
`check_table_availability`, `get_conflicting_bookings`

При создании и обновлении бронирования пересекающиеся по времени брони на одном столе запрещены.

## Скриншоты для сдачи

Инструкция: [screenshots/README.md](screenshots/README.md)

Нужно 3 скриншота:

1. Таблицы `users`, `restaurant_tables`, `bookings` в PgAdmin
2. Список бронирований (GUI или SQL)
3. GUI или CLI с кнопкой/командой «Проверить доступность»

## Дополнительная документация

- [ИНСТРУКЦИЯ.md](ИНСТРУКЦИЯ.md) — драйвер PostgreSQL
- [ИНСТРУКЦИЯ_GUI.md](ИНСТРУКЦИЯ_GUI.md) — работа с графическим интерфейсом

## Ссылка на GitHub

**https://github.com/PavelKoff2025/booking-system**

Файл `.env` в репозиторий не попадает (см. `.gitignore`). Секреты храните только локально.

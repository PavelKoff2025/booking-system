# Скриншоты для сдачи проекта

Нужно **3 скриншота**. Сохраните их в эту папку с именами:

| Файл | Что снять |
|------|-----------|
| `01_pgadmin_tables.png` | Таблицы `users`, `restaurant_tables`, `bookings` в PgAdmin |
| `02_bookings_list.png` | Список бронирований (GUI или PgAdmin / Query Tool) |
| `03_availability_check.png` | GUI или CLI с проверкой доступности стола |

## Подготовка данных

```bash
python seed_data.py
python scripts/export_submission_data.py
```

## Скриншот 1 — таблицы в PgAdmin

1. Откройте PgAdmin, подключитесь к базе из `.env` (`DB_NAME`).
2. Разверните: **Databases → booking → Schemas → public → Tables**.
3. Убедитесь, что видны таблицы: `users`, `restaurant_tables`, `bookings`.
4. Сделайте скриншот дерева таблиц (можно раскрыть каждую таблицу).

## Скриншот 2 — список бронирований

**Вариант A (GUI):**

```bash
python app.py
```

Вкладка **Бронирования** → кнопка **Обновить список** → скриншот таблицы слева.

**Вариант B (PgAdmin):**

```sql
SELECT * FROM bookings ORDER BY id;
```

В Query Tool → Execute → скриншот результата.

**Вариант C (терминал):**

```bash
python scripts/export_submission_data.py
```

Скриншот вывода в терминале (файл `02_bookings_list.txt` создаётся автоматически).

## Скриншот 3 — проверка доступности

**Вариант A (GUI, рекомендуется):**

```bash
python app.py
```

1. Вкладка **Бронирования**.
2. Заполните: **ID стола** = `1`, **Дата/время** = `2026-06-10 19:00:00`, **Длительность** = `60`.
3. Нажмите **Проверить доступность**.
4. Скриншот формы и диалога «Стол занят» или «Стол свободен».

**Вариант B (CLI):**

```bash
python check_availability_cli.py --table 1 --datetime "2026-06-10 19:00:00" --duration 60
```

Скриншот терминала с результатом `СТОЛ ЗАНЯТ` или `СТОЛ СВОБОДЕН`.

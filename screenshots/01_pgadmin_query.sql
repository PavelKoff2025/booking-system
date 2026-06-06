-- Выполните в PgAdmin Query Tool для скриншота 1–2

-- Список таблиц
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Список бронирований (скриншот 2)
SELECT id, user_id, table_id, booked_at, duration_minutes, guests_count, status, notes
FROM bookings
ORDER BY id;

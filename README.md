# hotel-django
 
Простой сервис для управления номерами отеля и их бронированиями. HTTP JSON API без авторизации.
 
## Стек
 
- Python 3.12
- Django + Django REST Framework
- PostgreSQL 16
- Poetry (управление зависимостями)
- Docker, docker-compose
- Gunicorn (сервер приложения в Docker)
## Запуск
 
### Через Docker (рекомендуется)
 
```bash
docker compose up --build
```
 
Сервис будет доступен на `http://localhost:9000`. Миграции применяются автоматически при старте контейнера. Данные Postgres хранятся в томе `pgdata` и не теряются при перезапуске.
 
Остановить:
 
```bash
docker compose down        # данные сохранятся
docker compose down -v     # удалить вместе с данными
```
 
### Локально (для разработки)
 
```bash
poetry install
docker compose up -d db                              # поднять только Postgres
cd src
poetry run python manage.py migrate
poetry run python manage.py runserver 9000
```
 
Параметры подключения к базе берутся из переменных окружения, значения по умолчанию совпадают с `docker-compose.yml`:
 
| Переменная          | По умолчанию |
|---------------------|--------------|
| `POSTGRES_DB`       | `hotel`      |
| `POSTGRES_USER`     | `hotel`      |
| `POSTGRES_PASSWORD` | `hotel`      |
| `POSTGRES_HOST`     | `localhost`  |
| `POSTGRES_PORT`     | `5432`       |
 
## Структура проекта
 
```
hotel-django/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── poetry.lock
├── schema.sql              # SQL создания таблиц (сгенерирован из миграций)
└── src/
    ├── manage.py
    ├── config/             # настройки проекта, корневые URL
    └── hotel/
        ├── models.py       # модели Room и Booking
        ├── serializers.py  # валидация входных данных и формат ответов
        ├── services.py     # бизнес-логика (создание брони с проверкой пересечения)
        ├── views.py        # HTTP-хендлеры
        ├── urls.py
        └── migrations/
```
 
## Схема базы данных
 
Таблицы создаются миграциями Django (`python manage.py migrate`). Для удобства SQL-запросы создания всех таблиц лежат в файле `schema.sql`.
 
- `hotel_room` — номера: `id`, `description`, `price numeric(10, 2)`, `created_at`. Индексы на `price` и `created_at` для сортировки.
- `hotel_booking` — брони: `id`, `room_id` (внешний ключ на `hotel_room`), `date_start`, `date_end`. Составной индекс `(room_id, date_start)` для выборки броней номера с сортировкой по дате начала. Ограничение `CHECK (date_end > date_start)`.

### Номера
 
#### Создать номер
 
`POST /rooms/create`
 
| Параметр      | Тип    | Описание                                  |
|---------------|--------|-------------------------------------------|
| `description` | строка | Описание номера, обязательно, не пустое   |
| `price`       | число  | Цена за ночь, больше 0, до 2 знаков после запятой |
 
```bash
curl -X POST -d "description=Standard room" -d "price=3500" http://localhost:9000/rooms/create
```
 
Ответ `201 Created`:
 
```json
{"room_id": 4}
```
 
#### Список номеров
 
`GET /rooms/list`
 
| Параметр   | Описание |
|------------|----------|
| `ordering` | Необязательно. `price`, `-price`, `created_at`, `-created_at`. Минус означает сортировку по убыванию. По умолчанию `created_at` (по возрастанию). |
 
```bash
curl "http://localhost:9000/rooms/list?ordering=-price"
```
 
Ответ `200 OK`:
 
```json
[
  {"id": 2, "description": "Люкс", "price": "9000.00", "created_at": "2026-10-31T15:10:50.903409Z"},
  {"id": 4, "description": "Standard room", "price": "3500.00", "created_at": "2026-11-04T15:48:11.111605Z"}
]
```
 
#### Удалить номер и все его брони
 
`DELETE /rooms/<room_id>/delete`
 
```bash
curl -X DELETE http://localhost:9000/rooms/4/delete
```
 
Ответ `200 OK`:
 
```json
{"deleted_room_id": 4}
```
 
Если номера нет — `404 Not Found`.
 
### Брони
 
#### Создать бронь
 
`POST /bookings/create`
 
| Параметр     | Тип    | Описание |
|--------------|--------|----------|
| `room_id`    | число  | ID существующего номера |
| `date_start` | строка | Дата начала в формате `ГГГГ-ММ-ДД` |
| `date_end`   | строка | Дата окончания в формате `ГГГГ-ММ-ДД`, строго позже `date_start` |
 
```bash
curl -X POST -d "room_id=4" -d "date_start=2021-12-30" -d "date_end=2022-01-02" http://localhost:9000/bookings/create
```
 
Ответ `201 Created`:
 
```json
{"booking_id": 1444}
```
 
Если номер уже забронирован на пересекающиеся даты — `409 Conflict`:
 
```json
{"detail": "Room is already booked for these dates."}
```
 
#### Удалить бронь
 
`DELETE /bookings/<booking_id>/delete`
 
```bash
curl -X DELETE http://localhost:9000/bookings/1444/delete
```
 
Ответ `200 OK`:
 
```json
{"deleted_booking_id": 1444}
```
 
Если брони нет — `404 Not Found`.
 
#### Список броней номера
 
`GET /bookings/list?room_id=<room_id>`
 
Брони отсортированы по дате начала.
 
```bash
curl "http://localhost:9000/bookings/list?room_id=4"
```
 
Ответ `200 OK`:
 
```json
[
  {"booking_id": 1444, "date_start": "2021-12-30", "date_end": "2022-01-02"},
  {"booking_id": 1450, "date_start": "2022-01-05", "date_end": "2022-01-07"}
]
```
 
Если у номера нет броней — пустой список `[]`.
 
### Формат ошибок
 
Ошибки валидации (`400 Bad Request`) группируются по полям, для каждого поля возвращается список сообщений:
 
```json
{"description": ["This field is required."], "price": ["A valid number is required."]}
```
 
Остальные ошибки (`404`, `405`, `409`) возвращаются в виде:
 
```json
{"detail": "No Room matches the given query."}
```
 

 
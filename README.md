# Async Payments Service

Асинхронный сервис обработки платежей.

Сервис принимает запрос на создание платежа, сохраняет платеж в БД со статусом `pending`, публикует событие через Outbox Pattern в RabbitMQ, обрабатывает платеж через consumer и отправляет результат на `webhook_url`.

## Стек

* FastAPI
* Pydantic v2
* SQLAlchemy 2.0 async
* PostgreSQL
* RabbitMQ + FastStream
* Alembic
* Docker / Docker Compose

## Запуск через Docker

Все необходимые переменные окружения уже заданы в `docker-compose.yml`.

Для запуска достаточно выполнить:


```bash
docker compose up --build
```
Будут запущены:

* PostgreSQL;
* RabbitMQ;
* REST API;
* Consumer.

## Настройка локального окружения

Для локального запуска приложения или тестов создайте файл `.env`:

```env
DB_HOST=localhost
DB_PORT=5435
DB_NAME=payments_db
DB_USER=test_user
DB_PASSWORD=12345

RABBITMQ_URL=amqp://admin:12345@localhost:5672/payments

API_KEY=test-api-key
```

Приложение будет доступно по адресу:

```text
http://localhost:8010
```

Swagger:

```text
http://localhost:8010/docs
```
Для выполнения запросов необходимо указать заголовки `X-API-Key` и `Idempotency-Key`.

## Миграции

Если миграции не накатываются автоматически при старте контейнера, выполнить:

```bash
docker compose exec payments_service_api alembic upgrade head
```

## RabbitMQ UI

RabbitMQ Management UI доступен по адресу:

```text
http://localhost:15672
```

Логин и пароль:

```text
admin / 12345
```

После запуска приложения будут созданы очереди:

```text
payments.new
payments.dlq
```

## Создание платежа

Endpoint:

```http
POST /api/v1/payments
```

Обязательные заголовки:

```http
X-API-Key: <your-api-key>
Idempotency-Key: <unique-request-key>
```

Пример запроса:

```bash
curl -X POST "http://localhost:8010/api/v1/payments" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -H "Idempotency-Key: 12345" \
  -d '{
    "amount": "1500.50",
    "currency": "RUB",
    "description": "Test payment",
    "metadata": {
      "order_id": "order-123"
    },
    "webhook_url": "https://webhook.site/<your-webhook-id>"
  }'
```

Пример ответа:

```json
{
  "payment_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "pending",
  "created_at": "2026-07-01T13:28:32.233Z"
}
```

## Получение платежа

Endpoint:

```http
GET /api/v1/payments/{payment_id}
```

Пример:

```bash
curl -X GET "http://localhost:8010/api/v1/payments/3fa85f64-5717-4562-b3fc-2c963f66afa6" \
  -H "X-API-Key: test-api-key"
```

Пример ответа:

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "amount": "1500.50",
  "currency": "RUB",
  "description": "Test payment",
  "metadata": {
    "order_id": "order-123"
  },
  "status": "succeeded",
  "idempotency_key": "12345",
  "webhook_url": "https://webhook.site/<your-webhook-id>",
  "created_at": "2026-07-01T13:28:32.233Z",
  "processed_at": "2026-07-01T13:28:36.100Z"
}
```

## Проверка webhook

Для проверки webhook можно использовать сервис:

```text
https://webhook.site
```

1. Открыть `https://webhook.site`.
2. Скопировать уникальный URL (Your unique URL).
3. Передать его в поле `webhook_url` при создании платежа.
4. После обработки платежа consumer отправит POST-запрос на этот URL.
5. На странице https://webhook.site появится тело webhook-уведомления.

Пример payload:

```json
{
  "payment_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "succeeded",
  "amount": "1500.50",
  "currency": "RUB",
  "processed_at": "2026-07-01T13:28:36.100Z"
}
```

## Idempotency-Key

`Idempotency-Key` защищает от дублей.

Если повторно отправить тот же запрос с тем же ключом:

```http
Idempotency-Key: 12345
```

новый платеж создан не будет. API вернет уже существующий платеж.

## Outbox Pattern

При создании платежа сервис сохраняет в одной транзакции:

* запись в `payments`;
* событие в `outbox`.

Publisher периодически (по расписанию) читает неопубликованные события из `outbox`, отправляет их в RabbitMQ в очередь `payments.new` и помечает событие как опубликованное.

## Consumer

Consumer:

1. получает сообщение из очереди `payments.new`;
2. эмулирует обработку платежа в течение 2–5 секунд;
4. эмулирует работу платежного шлюза:
   - с вероятностью 90% платеж получает статус `succeeded`;
   - с вероятностью 10% — `failed`;
4. обновляет платеж в БД;
5. отправляет webhook на `webhook_url`;
6. повторяет отправку webhook до 3 раз с экспоненциальной задержкой.

## Dead Letter Queue

Если сообщение не удалось окончательно обработать, оно попадает в очередь:

```text
payments.dlq
```

Сообщение попадает в payments.dlq, если consumer не смог завершить его обработку. В текущей реализации это происходит, например, когда после трёх попыток не удалось доставить webhook.


## Запуск тестов

Перед запуском тестов убедитесь, что:

- создан и настроен файл `.env`;
- запущен контейнер PostgreSQL.

Запуск тестов:

```bash
poetry run pytest
```

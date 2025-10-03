Быстрый старт (5 минут для проверяющего)

Предусловия
	•	Docker + Docker Compose
	•	make, git
	•	(опц.) Node 18+/pnpm для фронта локально
	•	(опц.) curl, jq

1) Клонирование

git clone git@github.com:tduhfajd/sql-guard.git
cd sql-guard

2) Поднять инфраструктуру

Поднимем Keycloak, pgbouncer, БД аудита и т.п.:

make up         # эквивалент docker compose up -d
# Подождать 10–20 сек, пока сервисы прогреются

Проверка статуса:

docker compose ps

3) Запуск бекенда и фронтенда (dev)

В двух отдельных терминалах:

make dev-backend   # uvicorn api.app:app --reload (порт, напр., 8000)

make dev-frontend  # vite dev (порт, напр., 5173)

URL’ы:
	•	Backend OpenAPI: http://localhost:8000/docs
	•	Frontend: http://localhost:5173

4) Быстрая авторизация (dev-режим)

Для демо доступен dev-auth (без реального OIDC) — одна из опций:

export SQL_GUARD_DEV_AUTH=1
# (если используется .env — уже включено)

Создадим пользователей и роли через CLI:

# admin
make cli ARGS='admin users create --email admin@demo --name "Admin" --roles admin,approver,operator'
# viewer
make cli ARGS='admin users create --email viewer@demo --name "Viewer" --roles viewer'
# operator
make cli ARGS='admin users create --email operator@demo --name "Operator" --roles operator'

(В dev-режиме UI даст выбрать пользователя из выпадающего списка «Login as …» или токен будет подставлен автоматически.)

5) Демо-сценарий (3 минуты)

5.1 Консоль SELECT (безопасный режим)
	1.	Открыть SQL Console.
	2.	Выбрать БД stage_analytics (или alias из списка).
	3.	Ввести запрос:

SELECT id, email, created_at FROM users ORDER BY created_at DESC;


	4.	Нажать Execute.
Ожидаемо:
	•	авто-LIMIT (напр., 1000) сработает, если не указан LIMIТ;
	•	результат с маскированием e-mail (для Viewer/Operator).

5.2 Шаблон и апрув (боевой сценарий)
	1.	Зайти в Templates → Create (под админом) и добавить шаблон:
	•	name: update_order_status
	•	sql:

UPDATE orders SET status = :new_status WHERE id = :order_id


	•	params: order_id:int required, new_status:str enum[pending,paid,cancelled]
	•	requires_approval: true

	2.	Переключиться на Operator, открыть шаблон → Run:
	•	db: prod_billing
	•	params: { "order_id": 12345, "new_status": "paid" }
	•	результат: создана заявка (PENDING).
	3.	Переключиться на Approver/Admin, раздел Approvals:
	•	открыть заявку, проверить SQL-превью, нажать Approve.
	•	результат: статус EXECUTED OK, 1 строка изменена.
	4.	Открыть Audit:
	•	фильтр по пользователю/БД → видно событие, masked-поля, длительность, строки.

6) API «на ощупь» (curl)

Получить список шаблонов (пример):

TOKEN="$(make print-dev-token)"          # утилита для dev-токена, если есть
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/templates

Выполнить SELECT:

curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"db_id":"stage_analytics","sql":"SELECT id, email FROM users ORDER BY id DESC","params":{}}' \
  http://localhost:8000/api/queries/execute | jq .

Экспорт аудита:

curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/audit/export?format=csv&from=2025-10-01&to=2025-10-03" -o audit.csv

7) Политики безопасности (быстрая проверка)

Установим таймаут и авто-LIMIT для роли operator:

make cli ARGS='admin policy set --scope role --ref operator --key statement_timeout_ms --value 30000'
make cli ARGS='admin policy set --scope role --ref operator --key auto_limit --value true'
make cli ARGS='admin policy set --scope role --ref operator --key max_rows --value 1000'

Проверка блок-листа (попытка DDL в консоли должна блокироваться):

DROP TABLE users;   -- UI disable, API -> {"error":"BLOCKED_BY_POLICY",...}

Проверка запрета UPDATE/DELETE без WHERE (для шаблонов):
	•	Попробовать сохранить шаблон без WHERE → должно отклониться валидатором.

8) Тесты за 1 команду

make test-backend   # pytest
make test-frontend  # unit-тесты фронта
make test-e2e       # Playwright: логин → SELECT → шаблон → апрув → аудит

9) Полезные make-цели

make up            # docker compose up -d
make down          # docker compose down -v
make dev-backend   # локальный backend
make dev-frontend  # локальный frontend
make fmt           # black + isort + flake8 / prettier+eslint
make lint
make cli ARGS='...'# обёртка над CLI (typer/click)

10) Коллекция API

Postman/Thunder Client коллекция:

/tools/api-collection.json

Импортируйте и используйте готовые запросы: auth, queries, templates, approvals, audit, policies.

⸻

Ожидаемые проверки (чек-лист для приёмки)
	•	Авторизация: вход в dev-режиме работает; роли ограничивают видимость разделов.
	•	Консоль: произвольные SELECT выполняются, DDL/DML блокируются, авто-LIMIT и таймаут работают.
	•	Шаблоны: создаются/версируются, параметры валидируются; на prod — только через апрув.
	•	Апрув: заявка видна в очереди, есть SQL-превью, approve/ reject с комментарием, после approve — исполнение.
	•	Аудит: всё логируется (кто/когда/что/БД/строки/длительность/статус), экспорт работает, PII маскировано.
	•	Политики: через CLI/админку меняются, реально применяются рантаймом (timeout/limit/blocklist/require-WHERE/mask).
	•	Иммутабельность журнала: записи аудита не редактируются.
	•	Тесты: базовый набор проходит (backend/e2e).

⸻

Частые проблемы и быстрые решения
	•	Пусто в списке БД → проверь .env/конфиг с alias и доступностью stage_*/prod_*.
	•	Не открывается фронт → порт 5173 занят; поменяй VITE_PORT или закрой другой процесс.
	•	Auth не пускает → включи dev-auth SQL_GUARD_DEV_AUTH=1 или проверь Keycloak realm/clients.
	•	DDL не блокируется → проверь политики blocklist и включён ли AST-валидатор.
	•	Нет маскирования → убедись, что в политиках задан mask_columns и роль не security/admin.

⸻

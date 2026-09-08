# ADR-001: PostgreSQL как движок БД noema

## Status

Accepted

## Date

2026-09-08

## Context

Изначальный дизайн-док зафиксировал SQLite (один файл в Docker volume, WAL + `busy_timeout`, web и stdio-MCP процессы шарят один файл). При реализации каркаса (тикет #19) всплыла проблема: `better-sqlite3` — нативный модуль, прямая вставка которого в SSR-бандл TanStack Start ломает продакшен-сборку (`__dirname is not defined`, HTTP 500). Корректная обвязка потребовала бы server-function/RPC-изоляции нативного кода от SSR.

Одновременно требование «web + MCP-сервер могут читать/писать БД одновременно» при SQLite решается WAL/busy_timeout с оговорками; PostgreSQL решает это архитектурно (сервер БД с конкурентным доступом).

## Decision

Заменить SQLite на PostgreSQL. Core-слой использует `drizzle-orm/node-postgres` (чистый JS, `pg` — без нативных postinstall-сборок), что не ломает SSR-бандл. Одна БД-инициализация — connection pool в `packages/core` (`createDbPool`), подключение строкой `DATABASE_URL` (env). В Docker compose появляется сервис `postgres`; web и stdio-MCP подключаются к нему по `DATABASE_URL`.

## Alternatives Considered

- **SQLite (прежний выбор)**: zero-ops, один файл, один контейнер. Отклонён после воспроизведения поломки SSR при прямой вставке нативного модуля и из-за ручной топологии «один процесс трогает файл».
- **PostgreSQL**: отдельный сервис в compose (+1 контейнер), но чистый JS-драйвер, конкурентный доступ без WAL-костылей, надёжный бэкап (`pg_dump`/`pg_basebackup`) и экспорт — соответствует требованию OSS-бэкапа из дизайна. Выбран.

## Consequences

- **Positive:** SSR-бандл не ломается (нет нативных модулей); web + MCP делят БД конкурентно без SQLITE_BUSY; бэкап/восстановление через стандартные PG-инструменты; `DATABASE_URL` — стандартный конфиг для self-hosting.
- **Negative:** +1 сервис (postgres) в Docker compose и на bare-metal (нужен запущенный PG); «один Docker-образ» дизайна превращается в compose с двумя сервисами; перенос данных с будущих SQLite-инсталляций потребует миграции.
- **Follow-up:** обновить дизайн-док (упоминания SQLite → PostgreSQL); в compose добавить volume для PG-данных и healthcheck; тест-сид (seam) перевести на `TEST_DATABASE_URL` с graceful skip; при первом реальном деплое — инструкция по бэкапу `pg_dump` в README.

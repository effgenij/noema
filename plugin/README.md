# Cortex — Hermes Desktop plugin

Гибридная папка: agent half + backend + desktop half.

## Структура

- `plugin.yaml` + `__init__.py` — агентная половина (инструменты добавляются следующими тикетами)
- `dashboard/plugin_api.py` — бэкенд, монтируется в `/api/plugins/cortex/`
- `desktop/plugin.js` — десктоп-половина (ROUTES_AREA + SIDEBAR_NAV_AREA, без JSX)

## Деплой

```bash
ln -s ~/dev/personal/cortex/plugin ~/.hermes/plugins/cortex
```

- Добавить `cortex` в `plugins.enabled` в `~/.hermes/config.yaml` — бэкенд монтируется при старте gateway.
- Десктоп-половина: Settings → Plugins → включить Cortex; ⌘K → Reload desktop plugins.

## Проверка

- `hermes plugins list` — cortex в статусе `enabled`.
- Health: `curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:PORT/api/plugins/cortex/health` → `{"status":"ok","plugin":"cortex"}`. Токен — `HERMES_DASHBOARD_SESSION_TOKEN` из env gateway-процесса.

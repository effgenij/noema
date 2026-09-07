# Исследование: API эмиссии gateway-события из Python-инструмента плагина

**Дата:** 2026-09-07 · **Профиль:** default · **Метод:** первоисточники — локальное дерево `~/.hermes/hermes-agent` (исходники Python-гейтвея, десктоп-SDK `apps/desktop/src/`, документация `website/docs/`).

**Вопрос (из `effgenij-cortex-design-20260907-201842.md`, строка 107):** каким API Python-инструмент (зарегистрированный через `ctx.register_tool`) эмитит gateway-событие, которое страница плагина получает через `host.onEvent`? Если такого API нет — подтвердить, что fallback (polling 3с) остаётся единственным путём.

---

## TL;DR — ответ

**Такого API не существует.** Python-инструмент плагина **не может** эмитить gateway-событие, которое десктопная страница получит через `host.onEvent`. В SDK есть два **разных, не связанных между собой** механизма событий, и моста между ними нет:

1. **`ctx.emit()` / `ctx.subscribe()`** (`hermes_cli/plugins.py:944,965`) — внутрипроцессная шина событий **плагин↔плагин** внутри Python-гейтвея. До десктопа не доходит.
2. **`host.onEvent`** (десктоп) — поток событий **гейтвея** (`message.start`, `session.info`, `skin.changed`, `sessions.changed`, `bot_relay.outbox.pending`…), который эмитится **внутренними** функциями гейтвея, недоступными плагинам.

Для сценария «агент записал в БД → страница перерисовалась» единственный штатный путь — **polling активной вьюхи** (3с), либо собственный WebSocket-неймспейс плагина `ctx.socket` (не gateway-событие, а свой `/api/plugins/<id>/` канал).

---

## 1. Две независимые системы событий

### 1.1 Шина событий плагинов: `ctx.emit` / `ctx.subscribe`

`PluginContext` (фасад, который получает `register(ctx)`) действительно имеет метод `emit`:

```python
# hermes_cli/plugins.py:944
def emit(self, event: str, payload: Optional[dict] = None) -> int:
    """Publish bare *event* as ``<plugin_key>:<event>`` (namespace FORCED to this plugin); return
    the subscriber count scheduled. ... Delivery is fire-and-forget via a
    single-worker queue: order preserved, a blocking subscriber cannot stall the emitter."""
    ...
    return self._manager._dispatch_event(f"{plugin_key}:{event}", payload or {})
```

и парный `subscribe` (`hermes_cli/plugins.py:965`). Но это **внутрипроцессная** шина:

- `_dispatch_event` (`hermes_cli/plugins_dispatch.py:353`) кладёт событие в `queue.Queue` и раздаёт подписчикам из `self._subscriptions` (`_deliver_event`, `hermes_cli/plugins_dispatch.py`).
- Подписчики регистрируются только через `ctx.subscribe` → `_subscribe_event` (`hermes_cli/plugins_dispatch.py:262`), т.е. **другими Python-плагинами в том же процессе гейтвея**.
- Неймспейс жёстко ограничен: `emit` запрещает `:` в имени, а `hermes:` зарезервирован за ядром (`HERMES_EVENT_NAMESPACE = "hermes"`, `hermes_cli/plugins_dispatch.py:88`). Плагин может эмитить только под своим `<plugin_key>:`.

**Ключевое:** `_dispatch_event` вызывается **только** из `ctx.emit` (`hermes_cli/plugins.py:963`), а `_subscribe_event` — **только** из `ctx.subscribe` (`hermes_cli/plugins.py:970`). Никакого выхода этой шины на WebSocket гейтвея нет (проверено grep по всему дереву: `_dispatch_event`/`_subscribe_event` не встречаются нигде, кроме этих двух точек и их определений).

### 1.2 Поток событий гейтвея: `host.onEvent`

На десктопе `host.onEvent` — это `onGatewayEvent`:

```ts
// apps/desktop/src/sdk/index.ts:1244
onEvent: onGatewayEvent,
```

```ts
// apps/desktop/src/contrib/events.ts:16
export function onGatewayEvent(type: string, listener: GatewayEventListener): () => void {
```

События в него попадают через `emitGatewayEvent` (`apps/desktop/src/contrib/events.ts:31`), который вызывается **ровно в одном месте** — обработчике входящего события гейтвея:

```ts
// apps/desktop/src/app/contrib/wiring.tsx:771
emitGatewayEvent(event)
```

То есть `host.onEvent` видит **только** события, пришедшие по WebSocket гейтвея (`/api/ws` → `tui_gateway/ws.py:239 handle_ws` → `server.dispatch`).

### 1.3 Кто эмитит события гейтвея

Эмиссия в сторону десктопа — **внутренние** функции гейтвея, не экспонируемые плагинам:

- `_emit(event, sid, payload)` — `tui_gateway/server.py:578` (события, привязанные к сессии: `message.start`, `session.info`, `approval.request`…).
- `_broadcast_global_event(event, payload)` — `tui_gateway/server.py:601` (бессессионные глобальные события: `skin.changed`, `session.reclaimed`…), фанятся на живые WS-транспорты из `_live_transports` (`register_live_transport`, `tui_gateway/server.py:588`).
- Change-watcher — **жёстко закодированный** список событий, порождаемых поллингом сигнатур на диске (`tui_gateway/change_watcher.py:177`):

```python
_CHANGE_WATCHES: dict[str, tuple[float, Any, Any]] = {
    "pet.changed": (2.0, _pet_sig, _pet_changed_payload),
    "cron.changed": (1.0, lambda: _home_mtime_ns("cron", "jobs.json"), lambda: {}),
    "sessions.changed": (0.5, _sessions_sig, lambda: {}),
    "platforms.changed": (2.0, lambda: _home_mtime_ns("gateway_state.json"), lambda: {}),
    "pairing.changed": (2.0, _pairing_sig, lambda: {}),
    "bot_relay.outbox.pending": (1.0, _bot_relay_outbox_sig, lambda: {})}
```

Ни один из этих эмиттеров не вызывается из плагинного кода. `_broadcast_global_event` вызывается только из `change_watcher.py`, `methods_config_set.py:433` (`skin.changed`) и `session_lifecycle.py:280` (`session.reclaimed`) — всё это ядро гейтвея.

---

## 2. Что SDK реально даёт плагину для «протолкнуть» данные в UI

| API | Что делает | Доходит ли до `host.onEvent` |
|---|---|---|
| `ctx.emit(event, payload)` (`plugins.py:944`) | внутрипроцессная шина плагин↔плагин | **нет** |
| `ctx.subscribe(event, cb)` (`plugins.py:965`) | подписка на ту же шину | — |
| `ctx.inject_message(content, …)` (`plugins.py:596`) | впрыскивает **сообщение** в разговор CLI/гейтвея (новый ход агента), не событие | **нет** (это turn, не event) |
| `ctx.rest(path)` / `ctx.socket(path)` (десктоп-SDK) | REST/WebSocket к **собственному** неймспейсу `/api/plugins/<id>/` | **нет** (это свой канал, не gateway-событие) |
| `host.onEvent(type, fn)` (десктоп) | подписка на поток событий гейтвея | — (это приёмник) |

Единственный «push» из Python-плагина в UI — это `ctx.socket` (WebSocket собственного бэкенда `plugin_api.py`), но: (а) это не gateway-событие и не `host.onEvent`; (б) по документации SDK он **no-op на OAuth-remote** и требует polling-fallback в любом случае (`website/docs/developer-guide/desktop-plugin-sdk.md`, раздел «Calling it from the plugin»: «It resolves to a no-op on OAuth remotes … treat the socket as an accelerator over polling, never a replacement»).

---

## 3. Вывод

1. **API эмиссии gateway-события из Python-инструмента не существует.** `ctx.emit` есть, но это отдельная внутрипроцессная шина плагин↔плагин, не связанная с десктопным `host.onEvent` (моста нет — проверено по всем вызовам `_dispatch_event`/`_subscribe_event`/`_broadcast_global_event`).
2. События, которые `host.onEvent` реально получает, эмитятся только внутренними функциями гейтвея (`_emit`, `_broadcast_global_event`) и жёстко закодированным change-watcher'ом (`_CHANGE_WATCHES`). Плагин не может добавить туда своё событие.
3. Для сценария «агент записал в БД → страница перерисовалась» штатные пути:
   - **polling активной вьюхи (3с)** — единственный универсальный путь, работает всегда;
   - **`ctx.socket`** к собственному `plugin_api.py`-бэкенду — ускоритель поверх polling, но не gateway-событие и не работает на OAuth-remote.

**Рекомендация для Cortex:** принять polling 3с как основной механизм обновления UI (риск некритичен, как и помечено в дизайн-доке, строка 107). `host.onEvent` использовать только для уже существующих событий гейтвея (`sessions.changed`, `message.complete` и т.п.), а не как канал «инструмент → страница».

---

## 4. Источники (все — локальное дерево `~/.hermes/hermes-agent`)

- `hermes_cli/plugins.py:449` — `PluginContext.register_tool` (регистрация инструмента)
- `hermes_cli/plugins.py:944` — `PluginContext.emit` (шина плагин↔плагин)
- `hermes_cli/plugins.py:965` — `PluginContext.subscribe`
- `hermes_cli/plugins.py:596` — `PluginContext.inject_message` (впрыск сообщения, не события)
- `hermes_cli/plugins_dispatch.py:88` — `HERMES_EVENT_NAMESPACE = "hermes"` (резерв ядра)
- `hermes_cli/plugins_dispatch.py:262` — `_subscribe_event`
- `hermes_cli/plugins_dispatch.py:353` — `_dispatch_event`
- `tui_gateway/server.py:578` — `_emit` (эмиссия события гейтвея, внутренняя)
- `tui_gateway/server.py:588` — `register_live_transport`
- `tui_gateway/server.py:601` — `_broadcast_global_event` (глобальный фан-аут, внутренний)
- `tui_gateway/change_watcher.py:177` — `_CHANGE_WATCHES` (жёстко закодированный список событий)
- `tui_gateway/ws.py:239` — `handle_ws` (WebSocket-транспорт гейтвея)
- `apps/desktop/src/contrib/events.ts:16` — `onGatewayEvent` (= `host.onEvent`)
- `apps/desktop/src/contrib/events.ts:31` — `emitGatewayEvent`
- `apps/desktop/src/app/contrib/wiring.tsx:771` — единственная точка вызова `emitGatewayEvent`
- `apps/desktop/src/sdk/index.ts:1244` — `onEvent: onGatewayEvent`
- `website/docs/developer-guide/desktop-plugin-sdk.md` — `ctx.socket` no-op на OAuth-remote, polling-fallback

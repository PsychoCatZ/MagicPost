# MagicPost — AI-бот для ведения Telegram-канала о маркетплейсах

Telegram-бот для владельца канала: превращает тему, тезисы или сырой текст в
готовый пост с помощью ИИ, показывает предпросмотр и публикует его в канал —
сразу или по расписанию. Бот предназначен только для владельца канала.

## Возможности

- ✍️ Создать пост по теме
- 📝 Собрать пост из тезисов
- ♻️ Переработать готовый текст (стиль/структура, без искажения фактов)
- 💡 Предложить темы для постов (с возможностью сгенерировать другие варианты)
- 📅 Контент-план на неделю
- Предпросмотр перед публикацией, перегенерация, ручное редактирование текста
- Добавление/замена/удаление изображения к посту
- Публикация сейчас или по расписанию (переживает перезапуск бота)
- Черновики и список запланированных публикаций

## Архитектура

```
app/
├── bot.py                  # сборка Bot/Dispatcher, middleware, старт планировщика
├── config.py                # загрузка и валидация .env
├── logging_config.py
│
├── ai/                       # слой ИИ — единственное место, знающее о конкретном провайдере
│   ├── base.py               # AIProvider (интерфейс), AIResult, AIError
│   ├── factory.py             # get_provider(settings) — выбор провайдера по AI_PROVIDER
│   ├── openai_compatible_provider.py  # реализация под OpenAI/DeepSeek/Qwen
│   ├── prompts.py             # загрузка шаблонов из app/prompts/*.txt
│   └── content_service.py     # бизнес-операции (пост/тезисы/рерайт/идеи/план),
│                               # не зависящие от конкретного провайдера
│
├── prompts/                  # системный и операционные промпты (стиль, тон, факт-чек)
│
├── database/
│   ├── db.py                  # sqlite3-соединение, схема, run_sync() для async-кода
│   ├── models.py               # dataclass Post
│   └── repository.py           # CRUD + логирование обращений к ИИ
│
├── keyboards/                 # reply- и inline-клавиатуры
├── states/                    # aiogram FSM состояния (создание/редактирование/расписание)
│
├── services/
│   ├── access.py               # OwnerOnlyMiddleware — доступ только владельцу
│   ├── rendering.py             # рендер предпросмотра поста с нужной клавиатурой
│   ├── publishing.py            # отправка поста в канал, экранирование HTML
│   ├── scheduler.py             # APScheduler + перезагрузка задач из SQLite при старте
│   └── post_service.py          # orchestration: создать черновик → вызвать ИИ → показать
│
└── handlers/                  # только Telegram-логика, без промптов и SDK
    ├── start.py, generate.py, post_actions.py,
    ├── drafts.py, scheduling.py, content_plan.py, settings.py
```

### Как работает замена AI-провайдера

Бизнес-логика (handlers, drafts, publishing, scheduler, БД) никогда не
импортирует `openai` напрямую — она работает только с интерфейсом
`AIProvider` (`app/ai/base.py`), у которого один метод:

```python
async def generate_text(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> AIResult
```

`ContentService` (`app/ai/content_service.py`) поверх этого интерфейса реализует
конкретные операции (`generate_post`, `generate_from_bullets`, `rewrite_text`,
`suggest_ideas`, `suggest_content_plan`), подставляя шаблоны из `app/prompts/`.
Именно `ContentService`, а не провайдер, знает про промпты — так тюнинг
промптов и смена SDK-провайдера — это две независимые вещи.

Уже готовы три провайдера — переключаются одной строкой в `.env`, без
изменений кода:

| `AI_PROVIDER` | Нужен ключ | `AI_MODEL`, например |
|---|---|---|
| `openai` | `OPENAI_API_KEY` | `gpt-4o-mini` |
| `deepseek` | `DEEPSEEK_API_KEY` | `deepseek-flash` |
| `qwen` | `QWEN_API_KEY` | `qwen3.5-flash` |

DeepSeek и Alibaba Qwen (через DashScope) оба реализуют тот же протокол
chat-completions, что и OpenAI, поэтому все три работают через один класс —
`OpenAICompatibleProvider` (`app/ai/openai_compatible_provider.py`), у
которого просто разный `base_url` и ключ. Отдельный класс на каждого
провайдера не нужен.

**Чтобы добавить провайдера, который НЕ совместим с OpenAI API** (например,
Claude или Gemini с их собственным форматом запроса):

1. Создать `app/ai/<name>_provider.py` с классом `<Name>Provider(AIProvider)`,
   реализующим `generate_text(...)`.
2. Добавить веточку в `app/ai/factory.py`:
   ```python
   if provider_name == "claude":
       from app.ai.claude_provider import ClaudeProvider
       return ClaudeProvider(api_key=settings.claude_api_key, model=settings.ai_model)
   ```
3. Добавить `claude_api_key` в `Settings`/`load_settings()` (`app/config.py`)
   и `CLAUDE_API_KEY=` в `.env`.

Больше никакие файлы (handlers, keyboards, database, scheduler) менять не нужно.

### Как сменить модель

Просто поменять `AI_MODEL` в `.env` (например, `gpt-4o` вместо `gpt-4o-mini`,
или `deepseek-v4-pro` вместо `deepseek-flash`) и перезапустить бота. Модель
нигде не захардкожена в коде. Учтите: при смене `AI_PROVIDER` модель нужно
сменить тоже — имена моделей у провайдеров не совпадают.

### Устройство промптов

- `app/prompts/system.txt` — постоянный системный промпт: автор, тематика,
  стиль, требование не выдумывать факты (комиссии, тарифы, даты изменений
  правил маркетплейсов и т.п.).
- `app/prompts/generate_post.txt`, `from_bullets.txt`, `rewrite.txt`,
  `ideas.txt`, `content_plan.txt` — шаблоны конкретных операций с
  плейсхолдерами (`{topic}`, `{bullets}`, `{source_text}`).

Стиль правится только в этих файлах, без изменений кода.

### Фактическая достоверность

Системный промпт прямо запрещает ИИ придумывать цифры, тарифы, комиссии,
даты изменений правил площадок и статистику. Веб-поиска в первой версии нет:
если пост требует актуальных данных, владелец присылает их сам (текст
источника, тезисы), и на этой основе уже строится публикация.

### SQLite

Файл базы — `data/bot.db` (путь настраивается `DATABASE_PATH`). Таблицы:

**posts**
`id, status, creation_mode, topic, source_text, generated_text, final_text, image_file_id, created_at, updated_at, published_at, scheduled_at`

Статусы: `draft`, `scheduled`, `published`, `cancelled` (cancelled зарезервирован;
в MVP отмена расписания возвращает пост в `draft`, а не удаляет историю).

**settings** — `key, value` (задел на будущее, сейчас не используется).

**ai_usage_log** — `id, provider, model, operation, success, prompt_tokens,
completion_tokens, total_tokens, created_at`. Пишется на каждый вызов ИИ,
включая неуспешные.

Все обращения к SQLite — синхронные (`sqlite3` из стандартной библиотеки),
но вызываются из async-кода через `run_sync()` (`asyncio.to_thread`), чтобы
не блокировать event loop.

### Планировщик и надёжность

`app/services/scheduler.py` держит задачи в APScheduler (`AsyncIOScheduler`),
но источник истины — таблица `posts`: при каждом запуске бот заново читает
все посты со статусом `scheduled` и либо публикует просроченные (если бот был
выключен в момент публикации), либо ставит задачу на будущее время. Поэтому
перезапуск бота не теряет запланированные публикации.

### Уведомление сайта о публикации

Если заданы `SITE_NEWS_API_URL` и `SITE_NEWS_API_KEY`, после каждой успешной
публикации в Telegram (`app/services/publishing.py`) бот дополнительно
отправляет `POST` с текстом и темой поста на этот адрес — так пост попадает
и в ленту новостей на сайте. Это сайд-эффект публикации, а не её условие:
если сайт недоступен, вернул ошибку или переменные не заданы, публикация в
Telegram всё равно проходит, а сбой только логируется. Работает для обоих
сценариев публикации (сразу и по расписанию), поскольку оба идут через одну
и ту же функцию `publish_post()`.

### Доступ

Все функции бота доступны только `OWNER_TELEGRAM_ID` — это проверяется в
`OwnerOnlyMiddleware`, подключённом ко всем сообщениям и callback-кнопкам.
Любой другой пользователь получает сообщение "Этот бот является внутренним
инструментом управления каналом." и не видит меню.

## Установка

1. Python 3.12+.
2. Создать и активировать виртуальное окружение:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```
3. Установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Скопировать `.env.example` в `.env` и заполнить:
   ```bash
   cp .env.example .env
   ```

   | Переменная | Значение |
   |---|---|
   | `BOT_TOKEN` | токен бота от @BotFather |
   | `OWNER_TELEGRAM_ID` | ваш числовой Telegram ID (например, узнать через @userinfobot) |
   | `TARGET_CHANNEL_ID` | ID канала для публикации (обычно вида `-100xxxxxxxxxx`) |
   | `APP_TIMEZONE` | часовой пояс для расписания, например `Asia/Krasnoyarsk` |
   | `DATABASE_PATH` | путь к файлу SQLite, по умолчанию `data/bot.db` |
   | `AUTHOR_NAME` | имя автора публикаций (используется в промптах) |
   | `AI_PROVIDER` | `openai`, `deepseek` или `qwen` |
   | `OPENAI_API_KEY` | ключ OpenAI API (нужен при `AI_PROVIDER=openai`) |
   | `DEEPSEEK_API_KEY` | ключ DeepSeek API (нужен при `AI_PROVIDER=deepseek`) |
   | `QWEN_API_KEY` | ключ Alibaba Qwen / DashScope (нужен при `AI_PROVIDER=qwen`) |
   | `AI_MODEL` | модель выбранного провайдера, например `gpt-4o-mini` / `deepseek-flash` / `qwen3.5-flash` |
   | `SITE_NEWS_API_URL` | необязательно — URL эндпоинта сайта для публикации новости (`/api/news`) |
   | `SITE_NEWS_API_KEY` | необязательно — ключ для авторизации запроса к этому эндпоинту |

## Права бота в Telegram-канале

Бот должен быть добавлен в канал и назначен администратором с правом
**публикации сообщений** (Post Messages). Без этого публикация постов
работать не будет. При старте бот сам проверяет права и пишет предупреждение
в лог, если их не хватает — но UI-проверки в диалоге нет, проверяйте лог
после первого запуска.

Чтобы узнать `TARGET_CHANNEL_ID`: добавьте бота в канал администратором,
перешлите любое сообщение из канала боту типа @userinfobot, либо временно
включите вывод `update.channel_post` в логах.

## Запуск

Локально:
```bash
python run.py
```

## Production-запуск через systemd (Ubuntu 24.04)

1. Разместите проект, например, в `/opt/magicpost`, создайте там `.venv` и
   установите зависимости так же, как в разделе «Установка».
2. Создайте `/etc/systemd/system/magicpost.service`:

   ```ini
   [Unit]
   Description=MagicPost Telegram bot
   After=network-online.target
   Wants=network-online.target

   [Service]
   Type=simple
   User=magicpost
   WorkingDirectory=/opt/magicpost
   ExecStart=/opt/magicpost/.venv/bin/python run.py
   Restart=on-failure
   RestartSec=5
   EnvironmentFile=/opt/magicpost/.env

   [Install]
   WantedBy=multi-user.target
   ```

3. Запустите:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now magicpost
   sudo systemctl status magicpost
   journalctl -u magicpost -f
   ```

Логи также пишутся в `data/logs/bot.log` (ротация по размеру).

## Что реализовано, а что нет

Реализован весь сценарий из ТЗ: тема/тезисы/рерайт → черновик → ИИ →
предпросмотр → публикация сейчас или по расписанию, с черновиками,
изображениями, контент-планом и переживающим перезапуск планировщиком.

Не входит в MVP (как и указано в ТЗ): несколько каналов, веб-поиск,
генерация изображений, CRM, платежи, мультипользовательский режим,
аналитика подписчиков. Раздел «⚙️ Настройки» показывает только
информационную сводку (автор, канал, часовой пояс, статус ИИ) — без
интерактивного редактирования, поскольку в ТЗ такой функционал не описан.

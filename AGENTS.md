# MagicPost — контекст для агентов

Telegram-бот, который делает посты для канала о маркетплейсах (ИИ → предпросмотр → публикация
в канал и/или на сайт, сразу или по расписанию). Проект владельца, боевой: бот сейчас работает
на VPS, им пользуется его сестра (владелец канала). Подробности архитектуры — в `README.md`, здесь
только то, чего в нём нет.

## Общие правила

- Общение с владельцем — по-русски, кратко. Не выдумывать: перед утверждением о состоянии
  сервера/репозитория — проверить командой.
- Коммит и пуш — после проверенных изменений. Код и комментарии в стиле существующего кода.
- Секреты (`.env`, ключи, токены) не читать в вывод, не коммитить и не пересылать. `.env` и `data/`
  в `.gitignore`.
- Проект скопирован со старой системы Windows. Права на файлы уже исправлены (владелец —
  `HOME-PC\Кот`), `safe.directory` в git не нужен. Если снова видно «dubious ownership» или
  «Access denied» — это не баг проекта, сообщите владельцу.

## Где что

| Что | Где |
|---|---|
| Код | `D:\Claude\MagicPost` (репозиторий `github.com/PsychoCatZ/MagicPost`, ветка `master`) |
| Продакшен | VPS Amsterdam (`ssh amsterdam`, root; алиас в `C:\Users\Кот\.ssh\config`) |
| Код на сервере | `/opt/magicpost/app` — git-клон, `origin` по SSH, владелец `magicpost` |
| Виртуальное окружение | `/opt/magicpost/venv` (не внутри `app`) |
| Сервис | `magicpost.service` (systemd, пользователь `magicpost`, `Restart=always`) |
| Конфиг сервера | `/opt/magicpost/app/.env` (`EnvironmentFile` юнита; свой, не совпадает с локальным) |
| База | `/opt/magicpost/app/data/bot.db` (SQLite) |
| Бэкапы | `/opt/magicpost/backups/` (`bot.db.pre-<коммит>-<дата>`) |

Примечание: unit-файл в `README.md` (`/opt/magicpost`, `.venv`) — пример, а не реальность.
Реальная схема — таблица выше.

## Деплой (как делали в последний раз)

1. Изменения закоммичены и запушены в `origin/master`. Перед деплоем убедиться, что локальный `HEAD`
   совпадает с `origin/master`.
2. Сделать **консистентный** бэкап базы через SQLite online backup API
   (`sqlite3.Connection.backup`), а не копированием файла — бот пишет в неё на ходу.
   Положить в `/opt/magicpost/backups/bot.db.pre-<короткий-хеш>-<YYYYMMDD-HHMMSS>`.
3. Обновить код от имени `magicpost`, а не root (иначе git ругается на «dubious ownership»):
   `sudo -u magicpost git -C /opt/magicpost/app pull --ff-only`.
   Как root: `git -c safe.directory=/opt/magicpost/app -C /opt/magicpost/app ...`.
4. Если менялся `requirements.txt` — `/opt/magicpost/venv/bin/pip install -r requirements.txt`.
5. `systemctl restart magicpost`, затем `journalctl -u magicpost -n 50` — убедиться, что бот
   стартовал, планировщик поднял запланированные посты, нет ошибок.
6. Миграции БД аддитивные и идут сами при старте (`init_db` в `app/database/db.py`), например
   `ALTER TABLE posts ADD COLUMN publish_targets`. Новые колонки добавлять так же — с проверкой
   через `PRAGMA table_info`, без потери данных.

Состояние на 2026-09-29: сервер на коммите `18223d0` («Ask where to publish: channel, site or both»),
бэкап перед ним сделан.

## Что важно знать

- Доступ к боту только у `OWNER_TELEGRAM_ID` (`OwnerOnlyMiddleware`). Не ослаблять.
- Публикация «канал / сайт / оба» — `publish_post()` в `app/services/publishing.py`. Порядок для
  «оба»: сначала канал, потом сайт; если сайт упал, пост возвращается в черновики, чтобы можно было
  отправить только на сайт без дубля в канале. У старых записей `publish_targets` пуст = `both`.
- Кнопки сайта видны, только если заданы `SITE_NEWS_API_URL` и `SITE_NEWS_API_KEY`.
- **Не проверено в бою:** сценарий «канал / сайт / оба» задеплоен 2026-09-28, но в Telegram
  ещё не проверялся. Владелец сказал, что сестра проверит утром 2026-09-29. Ждите её отзыв, не
  считайте функцию подтверждённой.
- ИИ-провайдер переключается через `AI_PROVIDER` + `AI_MODEL` в `.env` (openai / deepseek / qwen);
  бизнес-код знает только интерфейс `AIProvider`.
- Бот следит за собой сам: `Restart=always`. После правки `.env` нужен `systemctl restart magicpost`.
- Мониторится приложением DES Control Center (`D:\Claude\DES-control-center`): сервис `magicpost.service`
  на Amsterdam. Если перезапускали сервис — в нём это отобразится как «работает с…».

## Рабочее дерево

В корне иногда остаются файлы `README.md.tmp.<pid>.<hash>` — следы записи другого агента/процесса
(`*.tmp` в `.gitignore`). Их можно удалить, если рядом нет запущенной сессии, пишущей в репозиторий;
не коммитить.

## Проверка перед сдачей

Автотестов в проекте нет. Минимум: `python -m compileall app`, запуск `python run.py` локально
с тестовым токеном (если есть) или чтение логов после деплоя (`journalctl -u magicpost`,
`data/logs/bot.log`).

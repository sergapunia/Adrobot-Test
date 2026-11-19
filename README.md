# Adrobot-Test

Обёртка над Keitaro Admin API: создание кампании с двумя потоками и редактор офферов в потоке.

## Что делает

**Создаватор** принимает название, гео, оффер, домен, группу и источник. В Keitaro появляется кампания:

1. поток с фильтром страны → редирект на Google
2. default-поток → выбранный оффер (share 100%)

Название сохраняется с префиксом `test_ukolov_`. Домен, группу и источник можно выбрать из API или создать новым значением.

**Редактор** тянет потоки из Keitaro. Потоки без офферов показываются как заглушки. Офферы можно добавить, удалить, вернуть, закрепить долю. Изменения локальные, пока не нажаты **Опубликовать** или **Отмена**. Удалённые офферы остаются серыми с долей 0%.

## Требования

- Python 3.11+
- Node.js 18+
- API-ключ Keitaro с доступом к кампаниям, потокам, офферам, доменам, группам и источникам

## Настройка

```bash
cp .env.example .env
```

В `.env`:

```env
KEITARO_BASE_URL=https://tlgk.host
KEITARO_API_KEY=ваш_ключ
DATABASE_URL=sqlite:///./adrobot.db
CORS_ORIGINS=http://localhost:5173
CAMPAIGN_NAME_PREFIX=test_ukolov_
```

`KEITARO_BASE_URL` — адрес админки трекера без `/admin` и без `/admin_api/v1`.

Ключ не коммитить. Этот API-ключ видит только офферы из разрешённых групп; чужой ID оффера даёт 403.

## Миграции

Отдельных миграций нет. SQLite-файл `adrobot.db` и таблицы создаются при старте FastAPI (`Base.metadata.create_all`). Для чистого старта удали `backend/adrobot.db`.

## Запуск

Терминал 1:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Терминал 2:

```bash
cd frontend
npm install
npm run dev
```

UI: http://localhost:5173  
API: http://127.0.0.1:8000

## Тесты

```bash
cd backend
source .venv/bin/activate
pytest -q
```

Покрывают префикс названия, создание кампании по ТЗ (два потока, Google / оффер, домен-группа-источник), пересчёт долей 34/33/33 и 25×4, pin, remove / bring back, cancel, push только active-офферов.

## Стек

FastAPI + SQLAlchemy (SQLite) + React/Vite.

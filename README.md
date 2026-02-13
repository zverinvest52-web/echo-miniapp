# 🔊 Echo Mini App

Голосовой планировщик задач с AI для Telegram

## ✨ Возможности

- 🎯 Быстрое добавление задач
- 📱 Telegram Mini App с визуальным интерфейсом
- 🔄 Шаблоны задач (митинг, код-ревью, спорт и т.д.)
- 📊 Статистика выполнения
- 🎨 Drag & Drop интерфейс
- 🔊 Голосовой ввод
- 🤖 AI-оптимизация

## 🏗 Архитектура

```
Telegram Bot (@echo_miniapp_vercel)
    ↓
Mini App (GitHub Pages)
    ↓
API (Render + FastAPI + SQLite)
```

## 🚀 Быстрый старт

### 1. Настроить GitHub Pages

Перейди: https://github.com/zverinvest52-web/echo-miniapp/settings/pages

- Source: `Deploy from a branch`
- Branch: `master`
- Folder: `/ (root)`
- **Save**

Frontend будет доступен через 1-2 минуты:
https://zverinvest52-web.github.io/echo-miniapp/

### 2. Настроить Telegram Mini App

1. @BotFather → `/newapp`
2. Название: `Echo`
3. Short Name: `echo`
4. URL: `https://zverinvest52-web.github.io/echo-miniapp/`
5. Bot: `@echo_miniapp_vercel`
6. **Create**

### 3. Настроить Telegram Bot

1. @BotFather → `/mybots`
2. Выбери `@echo_miniapp_vercel`
3. **Copy API Token**

### 4. Настроить Render

1. Создай новый Web Service на Render
2. Репозиторий: `https://github.com/zverinvest52-web/echo-miniapp`
3. Runtime: Python
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python bot.py`
6. Environment Variables:
   - `BOT_TOKEN`: *твой токен от BotFather*
   - `RENDER_URL`: *сгенерированный URL Render* (например, https://echo-miniapp.onrender.com)
   - `MINIAPP_URL`: `https://zverinvest52-web.github.io/echo-miniapp/`
7. **Deploy**

## 📱 Как использовать

### Через Telegram

1. Открой бота @echo_miniapp_vercel
2. Нажми `/start`
3. Нажми "📋 Открыть Echo"
4. Добавляй задачи!

### Команды бота

- `/start` - Начать работу
- `/help` - Помощь
- `/tasks` - Список задач
- `/add Название` - Добавить задачу
- Просто напиши текст - создастся задача!

## 🗂 Структура проекта

```
echo-miniapp/
├── bot.py              # Telegram Bot + API (FastAPI)
├── index.html          # Mini App Frontend
├── requirements.txt    # Python зависимости
├── render.yaml         # Render конфиг
├── .github/
│   └── workflows/
│       └── pages.yml   # GitHub Pages
└── README.md
```

## 🔧 Технологии

- **Backend:** FastAPI + Python
- **Frontend:** Vanilla JavaScript + Telegram Web App API
- **Database:** SQLite
- **Hosting:** Render (Backend) + GitHub Pages (Frontend)
- **Bot:** python-telegram-bot

## 📊 API Endpoints

```
GET  /                    - Health check
GET  /health             - Health check
GET  /tasks              - Получить задачи
POST /tasks/{user_id}    - Создать задачу
POST /tasks/quick        - Быстрая задача из шаблона
POST /tasks/{id}/complete - Завершить задачу
DELETE /tasks/{id}       - Удалить задачу
GET  /stats/{user_id}    - Статистика
POST /webhook            - Telegram webhook
```

## 🎨 Mini App Features

- 📋 Список задач с приоритетами
- ✨ Шаблоны задач
- ➕ Модальное окно добавления
- ✓ Кнопки завершения
- ↻ Отложение на 1 час
- 📊 Статистика в реальном времени

## 🤝 Поддержка

По вопросам: @your_support_bot

## 📄 Лицензия

MIT License

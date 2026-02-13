# Echo Mini App 🔊

Голосовой планировщик задач с визуальным интерфейсом. Бот понимает контекст, а мини-приложение управляет задачами.

## 🚀 Быстрый старт

### 1. Создать бота в Telegram
- Открой [@BotFather](https://t.me/BotFather)
- Отправь `/newbot`
- Имя: `echo_miniapp_vercel`
- Токен дай мне

### 2. Настроить бота
```
/setinline     # Включить inline режим
/setprivacy    # Включить privacy mode
/setjoingroup  # Добавить в группы (если нужно)
```

### 3. Получить bot token
- Токен вида: `123456789:ABCdefGHI...`
- Токен обязательно нужен!

---

## 💻 Локальный запуск

### 1. Клонировать проект
```bash
cd ~/Projects
git clone https://github.com/reshtag/echo-miniapp.git
cd echo-miniapp
```

### 2. Установить зависимости
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Запустить бэкенд
```bash
source venv/bin/activate
cd api
python main.py
```

Бэкенд запустится на `http://localhost:8000`

### 4. Запустить фронтенд
```bash
cd ..
# Просто открой index.html в браузере
# Или используй Live Server
python3 -m http.server 3000
```

---

## 🌐 Деплой

### Frontend (GitHub Pages - бесплатно)

#### Шаг 1: Пуш на GitHub
```bash
git init
git add .
git commit -m "Initial commit - Echo Mini App"
git remote add origin https://github.com/reshtag/echo-miniapp.git
git push -u origin main
```

#### Шаг 2: Включить GitHub Pages
1. Открой репозиторий на GitHub
2. Settings → Pages
3. Build and deployment → Source: Deploy from a branch
4. Branch: `main`
5. Save
6. Подожди 1-2 минуты
7. Сайт будет доступен на `https://reshtag.github.io/echo-miniapp`

### Backend (Render - бесплатно)

#### Шаг 1: Создать аккаунт на Render
1. Открой [render.com](https://render.com)
2. Зарегистрируй (бесплатно)

#### Шаг 2: Создать Web Service
1. New + → Web Service
2. Repository: `https://github.com/reshtag/echo-miniapp.git`
3. Branch: `main`
4. Root Directory: `api`
5. Build Command: `pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
7. Region: Frankfurt (ближе к России)
8. Create Free Web Service

#### Шаг 3: Получить URL
- Render выдаст URL вида: `https://echo-api.onrender.com`
- Этот URL будет backend API

---

## ⚙️ Настройка Mini App

### 1. Редактировать `index.html`
Найди строку 50:
```javascript
const response = await fetch(`https://api.echoapp.com/tasks?user_id=${user.id}`);
```

Замени на Render URL:
```javascript
const response = await fetch(`https://echo-api.onrender.com/tasks?user_id=${user.id}`);
```

### 2. Обновить manifest.json
В `index.html` найди строки ~350:
```javascript
  "bot_username": "echo_miniapp_vercel",
```

Замени на имя твоего бота:
```javascript
  "bot_username": "echo_miniapp_vercel",  // или что ты создал
```

### 3. Пуш изменений
```bash
git add .
git commit -m "Update backend URL and bot username"
git push
```

---

## 🔧 Конфигурация бота

### Environment Variables (для Render)
В Render.com → echo-api → Environment:
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHI...  # Твой токен
OWNER_CHAT_ID=7866979307  # Твой Telegram ID
```

### Получить свой Chat ID
1. Отправь сообщение боту
2. Открой в браузере: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. Найди `"chat":{"id":123456789}`
4. Это твой Chat ID

---

## 📱 Использование

### 1. Открыть Mini App
- Открой бота: `@echo_miniapp_vercel`
- Отправь: `/start`
- Открой Mini App из меню

### 2. Голосовой ввод
```
Бот, создай задачу 'Подготовить презентацию' на завтра в 10
Бот, список задач на сегодня
Бот, напомни через час про презентацию
```

### 3. Управление в Mini App
- **Swipe вправо** → выполнить задачу
- **Swipe влево** → удалить задачу
- **Долгое нажатие** → изменить дедлайн
- **Кнопки шаблонов** → быстрое создание задач

---

## 📊 API Endpoints

### Backend API (`https://echo-api.onrender.com`)

#### GET /health
Проверка здоровья API
```json
{"status": "ok", "timestamp": "2026-02-13T14:00:00Z"}
```

#### GET /tasks/{user_id}
Получить все задачи пользователя
```json
{
  "tasks": [...],
  "count": 5
}
```

#### POST /tasks/{user_id}
Создать новую задачу
```json
{
  "title": "Задача",
  "description": "Описание",
  "deadline": "2026-02-14T10:00:00",
  "priority": 5
}
```

#### PUT /tasks/{task_id}
Обновить задачу
```json
{
  "status": "completed",
  "deadline": "2026-02-15T10:00:00"
}
```

#### DELETE /tasks/{task_id}
Удалить задачу

#### GET /stats/{user_id}
Статистика продуктивности
```json
{
  "date": "2026-02-13",
  "total": 5,
  "completed": 3,
  "efficiency": 60
}
```

---

## 🎨 Кастомизация

### Изменить цвета
В `index.html` найди CSS переменные:
```css
:root {
    --tg-theme-bg-color: #ffffff;
    --tg-theme-text-color: #000000;
    --tg-theme-button-color: #2481cc;
}
```

### Изменить шаблоны
В `api/main.py` найди словарь `templates`:
```python
templates = {
    "Код-ревью": {"title": "Код-ревью", "priority": 7, "deadline_hours": 1},
    # ... добавь свои шаблоны
}
```

---

## 🔐 Безопасность

### Environment Variables
- Никогда не коммить токены в Git
- Используй `.env` файлы
- В Render настрой Environment Variables

### HTTPS
- GitHub Pages использует HTTPS автоматически
- Render использует HTTPS автоматически

### Authentication
- Telegram Mini App автоматически проверяет пользователя
- API проверяет `user_id` перед операциями

---

## 🚨 Troubleshooting

### Mini App не открывается
1. Проверь GitHub Pages URL
2. Подожди 1-2 минуты после деплоя
3. Очисти кэш браузера

### Бот не отвечает
1. Проверь, что бот запущен: `systemctl --user status echo-bot`
2. Проверь токен в настройках Render
3. Проверь Privacy Mode: `/setprivacy`

### API возвращает ошибку
1. Проверь Render logs
2. Проверь Environment Variables
3. Проверь, что backend запущен

---

## 📈 Монетизация

### Free Tier (бесплатно)
- 50 голосовых команд/день
- 7 дней истории
- Базовый AI-контекст

### Pro Tier (299₽/мес)
- Безлимитные команды
- 30 дней истории
- Продвинутый AI
- Статистика продуктивности
- Интеграции (Google Calendar, Notion)

### Enterprise (по запросу)
- Всё из Pro
- Групповые чаты
- Командный режим
- API доступ
- Кастомные интеграции

---

## 🤝 Поддержка

### Telegram
Бот: @echo_miniapp_vercel
Чат: @PlanerPro_Bot (для премиум)

### GitHub
Issues: https://github.com/reshtag/echo-miniapp/issues
Wiki: https://github.com/reshtag/echo-miniapp/wiki

---

## 📄 Лицензия

MIT License - свободно использовать, модифицировать и распространять

---

**Echo — Голосовой планировщик задач, который понимает тебя** 🎙

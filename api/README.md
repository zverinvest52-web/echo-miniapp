# Echo Mini App - Backend API

FastAPI сервер для Echo Mini App с базой данных SQLite.

## 🚀 Quick Start

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Запуск сервера
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Проверка здоровья
API будет доступен по адресу: `http://localhost:8000/health`

## 📊 API Endpoints

### Health
- `GET /health` — Проверка здоровья API

### Tasks
- `GET /tasks/{user_id}` — Получить все задачи пользователя
- `POST /tasks/{user_id}` — Создать новую задачу
- `PUT /tasks/{task_id}` — Обновить задачу (выполнить, отложить)
- `POST /tasks/{user_id}/quick` — Создать задачу из шаблона
- `DELETE /tasks/{task_id}` — Удалить задачу

### Stats
- `GET /stats/{user_id}` — Получить статистику продуктивности

## 🗄 Database

### SQLite Database
- Файл: `echo-bot.db` (в папке приложения)
- Автоматически создаётся при первом запуске
- Поддерживает транзакции

### Schema
- `users` — Пользователи Telegram
- `tasks` — Задачи пользователей
- `productivity` — Статистика продуктивности

## 🔧 Configuration

### Environment Variables
- `TELEGRAM_BOT_TOKEN` — Токен бота Telegram
- `OWNER_CHAT_ID` — Chat ID владельца

### Port
- По умолчанию: `8000`
- Render использует `$PORT`

## 🌐 Deployment

### На Render (Free Tier)
1. Repository: `https://github.com/zverinvest52-web/echo-miniapp.git`
2. Branch: `master`
3. Root Directory: `api`
4. Build Command: `pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Region: Frankfurt

### Настройка переменных среды
В Render Dashboard:
- `TELEGRAM_BOT_TOKEN` = твой токен от @BotFather
- `OWNER_CHAT_ID` = твой Chat ID

## 🤖 Integration with Telegram

### Bot Commands
- `/start` — Приветствие и меню
- `/list` — Список задач
- `/add <задача>` — Добавить задачу
- `/complete <id>` — Выполнить задачу
- `/stats` — Статистика продуктивности

### Mini App
Frontend использует этот API через:
- `https://echo-api.onrender.com/tasks/{user_id}`
- `https://echo-api.onrender.com/tasks/{user_id}/quick`
- `https://echo-api.onrender.com/stats/{user_id}`

## 🛡 Security

- CORS включен для всех источников (можно ограничить)
- SQL Injection защита (prepared statements)
- Rate limiting (можно добавить)

## 📈 Performance

- FastAPI с async/await
- SQLite с connection pooling (можно добавить)
- Лёгкий backend для бесплатного хостинга

## 🐛 Troubleshooting

### База данных не создаётся
- Проверь права доступа к файловой системе
- SQLite должен иметь права на запись

### API недоступен
- Проверь, что порт 8000 не занят
- Проверь firewall

### Render deployment failed
- Проверь Build Logs в Render Dashboard
- Проверь Environment Variables
- Проверь Root Directory (должен быть `api`)

## 📄 License

MIT License

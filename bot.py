"""
Echo Telegram Bot (FREE VERSION)
Голосовой планировщик задач БЕЗ OpenAI
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import aiohttp
import sqlite3
from pathlib import Path

# Telegram Bot API
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Настройки
TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_URL", "https://echo-miniapp.onrender.com")
MINIAPP_URL = os.getenv("MINIAPP_URL", "https://zverinvest52-web.github.io/echo-miniapp/")

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

# База данных
DB_PATH = Path.home() / "echo-bot.db"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- БАЗА ДАННЫХ ---

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Пользователи
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Задачи
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        priority INTEGER DEFAULT 5,
        status TEXT DEFAULT 'active',
        deadline TIMESTAMP,
        category TEXT DEFAULT 'general',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )''')

    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")

def get_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> dict:
    """Получить или создать пользователя"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()

    if not user:
        c.execute('''INSERT INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)''', (user_id, username, first_name, last_name))
        conn.commit()
        logger.info(f"Создан пользователь: {user_id}")
    else:
        c.execute('''UPDATE users SET username = ?, first_name = ?, last_name = ?
            WHERE user_id = ?''', (username, first_name, last_name, user_id))
        conn.commit()

    conn.close()
    return {"user_id": user_id}

# --- ФУНКЦИИ ЗАДАЧ ---

def create_task(user_id: int, title: str, description: str = None, priority: int = 5,
                deadline: str = None, category: str = "general") -> dict:
    """Создать задачу"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''INSERT INTO tasks (user_id, title, description, priority, deadline, category)
        VALUES (?, ?, ?, ?, ?, ?)''',
        (user_id, title, description, priority, deadline, category))

    task_id = c.lastrowid
    conn.commit()
    conn.close()

    logger.info(f"Создана задача: {task_id} для пользователя: {user_id}")
    return {"id": task_id, "title": title, "status": "active", "priority": priority}

def get_tasks(user_id: int, status: str = None) -> list:
    """Получить задачи пользователя"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    query = "SELECT * FROM tasks WHERE user_id = ?"
    params = [user_id]

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY priority DESC, deadline ASC, created_at DESC"

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    tasks = [{
        "id": row[0],
        "user_id": row[1],
        "title": row[2],
        "description": row[3],
        "priority": row[4],
        "status": row[5],
        "deadline": row[6],
        "category": row[7],
        "ai_analyzed": False,
        "created_at": row[8],
        "updated_at": row[9]
    } for row in rows]

    return tasks

def complete_task(task_id: int) -> bool:
    """Завершить задачу"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''UPDATE tasks SET status = 'completed', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?''', (task_id,))

    updated = c.rowcount > 0
    conn.commit()
    conn.close()

    if updated:
        logger.info(f"Задача {task_id} выполнена")
    return updated

def delete_task(task_id: int) -> bool:
    """Удалить задачу"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    deleted = c.rowcount > 0
    conn.commit()
    conn.close()

    if deleted:
        logger.info(f"Задача {task_id} удалена")
    return deleted

# --- TELEGRAM HANDLERS ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start"""
    user = update.effective_user

    get_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    keyboard = [
        [InlineKeyboardButton("📋 Открыть Echo", web_app={"url": MINIAPP_URL})],
        [InlineKeyboardButton("📊 Мои задачи", callback_data="list")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = f"""
🔊 *Echo - Голосовой планировщик*

Привет, {user.first_name}! 👋

Я помогу тебе управлять задачами!

🎤 *Голосовой ввод:*
• Запиши голосовое сообщение
• Текст автоматически превратится в задачу

📋 *Мини-приложение:*
• Красивый интерфейс
• Шаблоны задач
• Статистика

🚀 *Как использовать:*
1. 🎤 Запиши голосовое или напиши текст
2. 📋 Или открой Mini App
3. ✅ Выполняй задачи!

Начни прямо сейчас! 🎯
"""

    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help"""
    help_text = """
📖 *Помощь по Echo*

🔧 *Команды:*
/start - Начать работу
/help - Эта помощь
/tasks - Список задач
/add - Добавить задачу

🎤 *Голосовой ввод:*
Просто запиши голосовое сообщение!

📱 *Mini App:*
Нажми "📋 Открыть Echo" для работы с визуальным интерфейсом

💡 *Советы:*
• Используй шаблоны для быстрого добавления
• Выполняй задачи регулярно
• Следи за статистикой

🆘 *Вопросы?*
Напиши @your_support_bot
"""

    await update.message.reply_text(help_text, parse_mode='Markdown')

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /tasks - список задач"""
    user_id = update.effective_user.id
    tasks = get_tasks(user_id)

    if not tasks:
        await update.message.reply_text("📭 У тебя пока нет задач. Создай первую!")
        return

    # Группируем по статусу
    active = [t for t in tasks if t['status'] == 'active']
    completed = [t for t in tasks if t['status'] == 'completed']

    text = f"📊 *Твои задачи ({len(active)} активных)*\n\n"

    if active:
        text += "🔴 *Активные:*\n"
        for i, task in enumerate(active[:10], 1):
            priority_icon = "🔴" if task['priority'] >= 7 else "🟡" if task['priority'] >= 5 else "🟢"
            text += f"{i}. {priority_icon} {task['title']}\n"

    if completed:
        text += f"\n✅ *Выполнено ({len(completed)})*\n"

    keyboard = [[InlineKeyboardButton("📋 Открыть Echo", web_app={"url": MINIAPP_URL})]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /add - добавить задачу"""
    if not context.args:
        await update.message.reply_text("⚠️ Используй: /add Название задачи")
        return

    user_id = update.effective_user.id
    title = " ".join(context.args)

    result = create_task(user_id, title)

    keyboard = [
        [InlineKeyboardButton("✓ Выполнить", callback_data=f"complete_{result['id']}"),
         InlineKeyboardButton("✗ Удалить", callback_data=f"delete_{result['id']}")],
        [InlineKeyboardButton("📋 Открыть Echo", web_app={"url": MINIAPP_URL})]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ Задача создана!\n\n📝 {result['title']}",
        reply_markup=reply_markup
    )

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка голосовых сообщений"""
    user_id = update.effective_user.id

    if not update.message.voice:
        return

    # Поскольку нет OpenAI Whisper, используем заглушку
    # В реальном продакшене можно использовать бесплатные альтернативы
    # Например: Google Speech-to-Text API (бесплатный тариф)

    await update.message.reply_text("🎤 Голосовое сообщение получено!\n\n⚠️ Для распознавания речи нужен OpenAI API.\n\nПока что используй текстовый ввод или открой Mini App.")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text

    # Проверяем команды
    if text.startswith('/'):
        return

    # Создаем задачу из текста
    result = create_task(user_id, text)

    keyboard = [
        [InlineKeyboardButton("✓ Выполнить", callback_data=f"complete_{result['id']}"),
         InlineKeyboardButton("✗ Удалить", callback_data=f"delete_{result['id']}")],
        [InlineKeyboardButton("📋 Открыть Echo", web_app={"url": MINIAPP_URL})]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ Задача создана!\n\n📝 {result['title']}",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка кнопок"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    if data == "list":
        tasks = get_tasks(user_id)
        if not tasks:
            await query.edit_message_text("📭 У тебя пока нет задач.")
            return

        active = [t for t in tasks if t['status'] == 'active']
        text = f"📊 *Твои задачи ({len(active)} активных)*\n\n"

        for i, task in enumerate(active[:10], 1):
            priority_icon = "🔴" if task['priority'] >= 7 else "🟡" if task['priority'] >= 5 else "🟢"
            text += f"{i}. {priority_icon} {task['title']}\n"

        keyboard = [[InlineKeyboardButton("📋 Открыть Echo", web_app={"url": MINIAPP_URL})]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

    elif data == "help":
        help_text = """
📖 *Помощь по Echo*

🔧 *Команды:*
/start - Начать работу
/help - Эта помощь
/tasks - Список задач
/add - Добавить задачу

💡 Просто напиши мне задачу!
"""
        await query.edit_message_text(help_text, parse_mode='Markdown')

    elif data.startswith("complete_"):
        task_id = int(data.split("_")[1])
        if complete_task(task_id):
            await query.edit_message_text("✅ Задача выполнена! Отличная работа! 💪")
        else:
            await query.edit_message_text("❌ Задача не найдена")

    elif data.startswith("delete_"):
        task_id = int(data.split("_")[1])
        if delete_task(task_id):
            await query.edit_message_text("🗑 Задача удалена")
        else:
            await query.edit_message_text("❌ Задача не найдена")

# --- FASTAPI APP (для API + Webhook) ---

app = FastAPI(title="Echo Bot + API")

# CORS для Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class TaskCreate(BaseModel):
    title: str
    description: str = None
    priority: int = 5
    deadline: str = None
    category: str = "general"

class QuickTask(BaseModel):
    template: str

# API Endpoints
@app.get("/")
async def root():
    return {"status": "running", "service": "Echo Bot + API (FREE)", "version": "4.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/tasks")
async def get_tasks_api(user_id: int):
    tasks = get_tasks(user_id)
    return {"tasks": tasks, "count": len(tasks)}

@app.post("/tasks/{user_id}")
async def create_task_api(user_id: int, task: TaskCreate):
    result = create_task(
        user_id=user_id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        deadline=task.deadline,
        category=task.category
    )
    return result

@app.post("/tasks/quick")
async def quick_task_api(quick: QuickTask, user_id: int):
    templates = {
        "Код-ревью": {"title": "Код-ревью", "priority": 7, "deadline": 1},
        "Митинг": {"title": "Митинг с командой", "priority": 5, "deadline": 2},
        "Обед": {"title": "Обед", "priority": 3, "deadline": 1},
        "Спорт": {"title": "Спорт", "priority": 4, "deadline": 1},
        "Спринт": {"title": "Спринт-планирование", "priority": 8, "deadline": 4},
        "Доклад": {"title": "Отправить доклад", "priority": 6, "deadline": 2},
    }

    template = templates.get(quick.template, {"title": quick.template, "priority": 5, "deadline": 1})

    deadline = (datetime.now() + timedelta(hours=template["deadline"])).isoformat()

    result = create_task(user_id, template["title"], f"Шаблон: {quick.template}", template["priority"], deadline)
    return result

@app.post("/tasks/{task_id}/complete")
async def complete_task_api(task_id: int):
    success = complete_task(task_id)
    return {"status": "completed" if success else "not_found"}

@app.delete("/tasks/{task_id}")
async def delete_task_api(task_id: int):
    success = delete_task(task_id)
    return {"status": "deleted" if success else "not_found"}

@app.get("/stats/{user_id}")
async def get_stats_api(user_id: int):
    tasks = get_tasks(user_id)
    active = len([t for t in tasks if t['status'] == 'active'])
    completed = len([t for t in tasks if t['status'] == 'completed'])

    return {
        "user_id": user_id,
        "active": active,
        "completed": completed,
        "total": len(tasks)
    }

@app.post("/webhook")
async def webhook(request: Request):
    """Telegram webhook endpoint"""
    data = await request.json()

    # Создаем Update объект из данных
    update = Update.de_json(data, application.bot)

    # Обрабатываем обновление
    await application.update_queue.put(update)

    return {"status": "ok"}

# --- MAIN ---

if __name__ == "__main__":
    # Инициализация БД
    init_db()

    # Telegram Application
    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tasks", list_command))
    application.add_handler(CommandHandler("add", add_command))

    # Callback queries
    application.add_handler(CallbackQueryHandler(button_callback))

    # Voice messages
    application.add_handler(MessageHandler(filters.VOICE, voice_handler))

    # Text messages (как задачи)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # Настройка webhook
    async def setup_webhook():
        webhook_url = f"{RENDER_URL}/webhook"
        await application.bot.set_webhook(webhook_url)
        logger.info(f"Webhook установлен: {webhook_url}")

    # Запуск
    import threading

    def run_bot():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(setup_webhook())
        loop.run_until_complete(application.start())
        loop.run_forever()

    # Запуск бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    logger.info("🚀 Echo Bot (FREE VERSION) запускается...")
    logger.info(f"📡 API: {RENDER_URL}")
    logger.info(f"📱 Mini App: {MINIAPP_URL}")
    logger.info(f"💰 Стоимость: 0$ (полностью бесплатно!)")

    # Запуск FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000)

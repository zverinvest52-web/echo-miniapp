"""
Echo Telegram Bot
Голосовой планировщик задач с AI
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

# AI Integration
import openai

# Telegram Bot API
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram import Voice

# Настройки
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RENDER_URL = os.getenv("RENDER_URL", "https://echo-miniapp.onrender.com")
MINIAPP_URL = os.getenv("MINIAPP_URL", "https://zverinvest52-web.github.io/echo-miniapp/")

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

if not OPENAI_API_KEY:
    logger = logging.getLogger(__name__)
    logger.warning("OPENAI_API_KEY не найден - AI функции не будут работать")
else:
    openai.api_key = OPENAI_API_KEY

# База данных
DB_PATH = Path.home() / "echo-bot.db"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- AI ФУНКЦИИ ---

async def analyze_task_with_ai(task_text: str) -> dict:
    """
    Анализирует задачу с помощью AI:
    - Определяет приоритет
    - Предлагает дедлайн
    - Категоризирует
    - Упрощает текст
    """
    if not OPENAI_API_KEY:
        return {
            "title": task_text,
            "priority": 5,
            "deadline": None,
            "category": "general"
        }

    try:
        prompt = f"""
Анализируй задачу и верни JSON:
{{
    "title": "упрощенный заголовок",
    "priority": число от 1 до 10 (где 1 - срочно, 10 - не срочно),
    "deadline": "срок в ISO формате или null",
    "category": "категория (работа, личное, здоровье, обучение, другое)"
}}

Задача: {task_text}

Верни ТОЛЬКО JSON без дополнительного текста.
"""

        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты - AI ассистент для анализа задач. Отвечай только в формате JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )

        result_text = response.choices[0].message.content.strip()
        result = json.loads(result_text)

        return {
            "title": result.get("title", task_text),
            "priority": result.get("priority", 5),
            "deadline": result.get("deadline"),
            "category": result.get("category", "general")
        }

    except Exception as e:
        logger.error(f"AI ошибка: {e}")
        return {
            "title": task_text,
            "priority": 5,
            "deadline": None,
            "category": "general"
        }

async def get_ai_suggestions(user_id: int) -> list:
    """Получить AI рекомендации для продуктивности"""
    if not OPENAI_API_KEY:
        return ["Анализ отключен", "Добавь OPENAI_API_KEY", "Чтобы получить рекомендации"]

    try:
        # Получить задачи пользователя
        tasks = get_tasks(user_id)

        if not tasks:
            return [
                "📝 Создай первую задачу",
                "🎯 Начни с простых целей",
                "📅 Установи дедлайн"
            ]

        active = [t for t in tasks if t['status'] == 'active']

        if not active:
            return ["🎉 Все задачи выполнены!", "💪 Отличная продуктивность!"]

        prompt = f"""
Дай 3 коротких совета для продуктивности:
- У пользователя {len(active)} активных задач
- Приоритеты задач: {[t['priority'] for t in active]}
- Сроки: {[t['deadline'] for t in active if t['deadline']]}

Советы:
1. Совет 1
2. Совет 2
3. Совет 3
"""

        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты - AI коуч по продуктивности."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )

        result = response.choices[0].message.content.strip()
        return result.split('\n')

    except Exception as e:
        logger.error(f"AI рекомендации ошибка: {e}")
        return ["AI недоступен", "Попробуй позже"]

# --- ГОЛОСОВОЙ ВВОД ---

async def transcribe_voice(voice_file: bytes) -> str:
    """
    Преобразует голосовое сообщение в текст
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY не найден для распознавания речи")

    try:
        # Сохранить временный файл
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            temp_file.write(voice_file)
            temp_path = temp_file.name

        # Отправить в OpenAI Whisper
        with open(temp_path, 'rb') as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)

        # Удалить временный файл
        os.unlink(temp_path)

        return transcript['text'].strip()

    except Exception as e:
        logger.error(f"Ошибка распознавания речи: {e}")
        raise

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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ai_enabled INTEGER DEFAULT 1
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
        ai_analyzed INTEGER DEFAULT 0,
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
        # Обновить данные если изменились
        c.execute('''UPDATE users SET username = ?, first_name = ?, last_name = ?
            WHERE user_id = ?''', (username, first_name, last_name, user_id))
        conn.commit()

    conn.close()
    return {"user_id": user_id}

# --- ФУНКЦИИ ЗАДАЧ ---

def create_task(user_id: int, title: str, description: str = None, priority: int = 5,
                deadline: str = None, category: str = "general", ai_analyzed: bool = False) -> dict:
    """Создать задачу"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''INSERT INTO tasks (user_id, title, description, priority, deadline, category, ai_analyzed)
        VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (user_id, title, description, priority, deadline, category, int(ai_analyzed)))

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
        "ai_analyzed": bool(row[8]),
        "created_at": row[9],
        "updated_at": row[10]
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

    # Создаем/обновляем пользователя
    get_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    # Клавиатура
    keyboard = [
        [InlineKeyboardButton("🎤 Голосовой ввод", callback_data="voice")],
        [InlineKeyboardButton("📋 Открыть Echo", web_app={"url": MINIAPP_URL})],
        [InlineKeyboardButton("📊 Мои задачи", callback_data="list")],
        [InlineKeyboardButton("🤖 AI Советы", callback_data="ai_suggestions")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = f"""
🔊 *Echo - AI Голосовой планировщик*

Привет, {user.first_name}! 👋

🎤 *Голосовой ввод:*
• Запиши голосовое сообщение
• AI превратит в задачу
• Автоматически определит приоритет

🤖 *AI возможности:*
• Анализ задач
• Определение приоритетов
• Умные рекомендации
• Распознавание речи

🚀 *Как использовать:*
1. 🎤 Запиши голосовое
2. 📝 Или напиши текст
3. 🤖 AI всё сделает за тебя

Попробуй сейчас! 🎯
"""

    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка голосовых сообщений"""
    user_id = update.effective_user.id

    if not update.message.voice:
        return

    voice_file = await update.message.voice.get_file()
    voice_bytes = await voice_file.download_as_bytearray()

    try:
        # Показываем что обрабатываем
        status_msg = await update.message.reply_text("🎤 Распознаю речь...")

        # Распознаем голос
        text = await transcribe_voice(voice_bytes)

        # Обновляем статус
        await status_msg.edit_text(f"🤖 AI анализирует: {text[:30]}...")

        # Анализируем с AI
        ai_result = await analyze_task_with_ai(text)

        # Создаем задачу
        result = create_task(
            user_id=user_id,
            title=ai_result['title'],
            description=text,  # Исходный текст в описании
            priority=ai_result['priority'],
            deadline=ai_result['deadline'],
            category=ai_result['category'],
            ai_analyzed=True
        )

        # Показываем результат
        priority_emoji = "🔴" if result['priority'] >= 7 else "🟡" if result['priority'] >= 5 else "🟢"

        keyboard = [
            [InlineKeyboardButton("✓ Выполнить", callback_data=f"complete_{result['id']}"),
             InlineKeyboardButton("✗ Удалить", callback_data=f"delete_{result['id']}")],
            [InlineKeyboardButton("📋 Открыть Echo", web_app={"url": MINIAPP_URL})]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        response_text = f"""
🎤 *Распознано:*
{text}

🤖 *AI создал задачу:*
{priority_emoji} *{ai_result['title']}*

📊 Приоритет: {result['priority']}/10
🏷️ Категория: {ai_result['category']}
"""

        await status_msg.edit_text(response_text, parse_mode='Markdown', reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Ошибка обработки голоса: {e}")
        await update.message.reply_text("❌ Ошибка распознавания. Попробуй текстовый ввод.")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка текстовых сообщений с AI"""
    user_id = update.effective_user.id
    text = update.message.text

    # Проверяем команды
    if text.startswith('/'):
        return

    try:
        # Показываем что обрабатываем
        status_msg = await update.message.reply_text("🤖 AI анализирует...")

        # Анализируем с AI
        ai_result = await analyze_task_with_ai(text)

        # Создаем задачу
        result = create_task(
            user_id=user_id,
            title=ai_result['title'],
            description=text if text != ai_result['title'] else None,
            priority=ai_result['priority'],
            deadline=ai_result['deadline'],
            category=ai_result['category'],
            ai_analyzed=True
        )

        # Показываем результат
        priority_emoji = "🔴" if result['priority'] >= 7 else "🟡" if result['priority'] >= 5 else "🟢"

        keyboard = [
            [InlineKeyboardButton("✓ Выполнить", callback_data=f"complete_{result['id']}"),
             InlineKeyboardButton("✗ Удалить", callback_data=f"delete_{result['id']}")],
            [InlineKeyboardButton("📋 Открыть Echo", web_app={"url": MINIAPP_URL})]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        response_text = f"""
🤖 *AI создал задачу:*
{priority_emoji} *{ai_result['title']}*

📊 Приоритет: {result['priority']}/10
🏷️ Категория: {ai_result['category']}
"""

        await status_msg.edit_text(response_text, parse_mode='Markdown', reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Ошибка AI анализа: {e}")
        # Если AI не работает, создаем обычную задачу
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

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /tasks - список задач"""
    user_id = update.effective_user.id
    tasks = get_tasks(user_id)

    if not tasks:
        await update.message.reply_text("📭 У тебя пока нет задач. 🎤 Запиши голосовое или напиши задачу!")
        return

    # Группируем по статусу
    active = [t for t in tasks if t['status'] == 'active']
    completed = [t for t in tasks if t['status'] == 'completed']

    text = f"📊 *Твои задачи ({len(active)} активных)*\n\n"

    if active:
        text += "🔴 *Активные:*\n"
        for i, task in enumerate(active[:10], 1):
            priority_icon = "🔴" if task['priority'] >= 7 else "🟡" if task['priority'] >= 5 else "🟢"
            ai_icon = "🤖" if task['ai_analyzed'] else ""
            text += f"{i}. {priority_icon} {task['title']} {ai_icon}\n"

    if completed:
        text += f"\n✅ *Выполнено ({len(completed)})*\n"

    keyboard = [[InlineKeyboardButton("📋 Открыть Echo", web_app={"url": MINIAPP_URL})]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка кнопок"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    if data == "voice":
        await query.edit_message_text("🎤 Запиши голосовое сообщение\n\nЯ превратю его в задачу с помощью AI!")

    elif data == "list":
        tasks = get_tasks(user_id)
        if not tasks:
            await query.edit_message_text("📭 У тебя пока нет задач.")
            return

        active = [t for t in tasks if t['status'] == 'active']
        text = f"📊 *Твои задачи ({len(active)} активных)*\n\n"

        for i, task in enumerate(active[:10], 1):
            priority_icon = "🔴" if task['priority'] >= 7 else "🟡" if task['priority'] >= 5 else "🟢"
            ai_icon = "🤖" if task['ai_analyzed'] else ""
            text += f"{i}. {priority_icon} {task['title']} {ai_icon}\n"

        keyboard = [[InlineKeyboardButton("📋 Открыть Echo", web_app={"url": MINIAPP_URL})]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

    elif data == "ai_suggestions":
        await query.edit_message_text("🤖 Анализирую твою продуктивность...")

        suggestions = await get_ai_suggestions(user_id)

        text = "🤖 *AI Рекомендации:*\n\n"
        text += "\n".join([f"💡 {s}" for s in suggestions[:5]])

        keyboard = [[InlineKeyboardButton("📋 Открыть Echo", web_app={"url": MINIAPP_URL})]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

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
    return {"status": "running", "service": "Echo AI Bot + API", "version": "3.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/tasks")
async def get_tasks_api(user_id: int):
    tasks = get_tasks(user_id)
    return {"tasks": tasks, "count": len(tasks)}

@app.post("/tasks/{user_id}")
async def create_task_api(user_id: int, task: TaskCreate):
    # AI анализ если включен
    if OPENAI_API_KEY:
        ai_result = await analyze_task_with_ai(task.title)
        return create_task(
            user_id=user_id,
            title=ai_result['title'],
            description=task.description,
            priority=ai_result['priority'],
            deadline=ai_result['deadline'],
            category=ai_result['category'],
            ai_analyzed=True
        )
    else:
        return create_task(
            user_id=user_id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            deadline=task.deadline,
            category=task.category
        )

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

    deadline = (datetime.now() + timedelta(hours=template["deadline_hours"])).isoformat()

    return create_task(user_id, template["title"], f"Шаблон: {quick.template}", template["priority"], deadline)

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

@app.get("/suggestions/{user_id}")
async def get_suggestions_api(user_id: int):
    suggestions = await get_ai_suggestions(user_id)
    return {"suggestions": suggestions}

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
    application.add_handler(CommandHandler("tasks", list_command))

    # Callback queries
    application.add_handler(CallbackQueryHandler(button_callback))

    # Voice messages
    application.add_handler(MessageHandler(filters.VOICE, voice_handler))

    # Text messages (как задачи с AI)
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

    logger.info("🚀 Echo AI Bot запускается...")
    logger.info(f"🎤 Voice input: enabled")
    logger.info(f"🤖 AI analysis: {'enabled' if OPENAI_API_KEY else 'disabled'}")
    logger.info(f"📡 API: {RENDER_URL}")
    logger.info(f"📱 Mini App: {MINIAPP_URL}")

    # Запуск FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000)

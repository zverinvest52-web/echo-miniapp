"""
Echo Bot Backend API
FastAPI для мини-приложения Echo
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path

app = FastAPI(title="Echo API", version="1.0.0")

# Database
DB_PATH = Path.home() / "echo-bot.db"

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        chat_id TEXT,
        first_name TEXT,
        created_at TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        description TEXT,
        deadline TIMESTAMP,
        priority INTEGER DEFAULT 5,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )''')
    
    conn.commit()
    conn.close()

# Models
class User(BaseModel):
    user_id: int
    username: str
    chat_id: str
    first_name: str

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: int = 5

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    title: Optional[str] = None
    deadline: Optional[datetime] = None

class QuickTask(BaseModel):
    template: str

# Initialize database
init_db()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check"""
    return {"status": "healthy", "service": "Echo API", "version": "1.0.0"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT user_id, username, chat_id, first_name FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    
    conn.close()
    
    if user:
        return {"user_id": user[0], "username": user[1], "chat_id": user[2], "first_name": user[3]}
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/users")
async def create_user(user: User):
    """Create new user"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''INSERT INTO users (user_id, username, chat_id, first_name, created_at)
            VALUES (?, ?, ?, ?, ?)''', (user.user_id, user.username, user.chat_id, user.first_name, datetime.now()))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # User exists
    
    conn.close()
    return {"status": "created", "user_id": user.user_id}

@app.get("/tasks/{user_id}")
async def get_tasks(user_id: int):
    """Get all tasks for user"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT id, title, description, deadline, priority, status, created_at, updated_at
        FROM tasks
        WHERE user_id = ? AND status = 'active'
        ORDER BY priority DESC, deadline ASC
    ''', (user_id,))
    
    rows = c.fetchall()
    conn.close()
    
    tasks = [{
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "deadline": row[3],
        "priority": row[4],
        "status": row[5],
        "created_at": row[6],
        "updated_at": row[7]
    } for row in rows]
    
    return {"tasks": tasks, "count": len(tasks)}

@app.post("/tasks/{user_id}")
async def create_task(user_id: int, task: TaskCreate):
    """Create new task"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    now = datetime.now()
    
    c.execute('''
        INSERT INTO tasks (user_id, title, description, deadline, priority, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, task.title, task.description, task.deadline, task.priority, 'active', now, now))
    
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": task_id, "status": "created"}

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task_update: TaskUpdate):
    """Update task (complete, postpone, etc.)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    update_fields = []
    update_values = []
    
    if task_update.status:
        update_fields.append("status = ?")
        update_values.append(task_update.status)
    
    if task_update.deadline:
        update_fields.append("deadline = ?")
        update_values.append(task_update.deadline)
    
    if task_update.title:
        update_fields.append("title = ?")
        update_values.append(task_update.title)
    
    if update_fields:
        update_values.append(datetime.now())
        c.execute(f'''
            UPDATE tasks
            SET {', '.join(update_fields)}, updated_at = ?
            WHERE id = ?
        ''', update_values + [task_id])
        conn.commit()
    
    conn.close()
    
    return {"status": "updated"}

@app.post("/tasks/{user_id}/quick")
async def create_quick_task(user_id: int, quick: QuickTask):
    """Create task from template"""
    templates = {
        "Код-ревью": {"title": "Код-ревью", "priority": 7, "deadline_hours": 1},
        "Митинг": {"title": "Митинг с командой", "priority": 5, "deadline_hours": 2},
        "Обед": {"title": "Обед", "priority": 3, "deadline_hours": 1},
        "Спринт": {"title": "Спринт-планирование", "priority": 8, "deadline_hours": 4},
        "Доклад": {"title": "Отправить доклад", "priority": 6, "deadline_hours": 2},
        "Упражнение": {"title": "Упражнение", "priority": 4, "deadline_hours": 1},
    }
    
    template = templates.get(quick.template, {"title": quick.template, "priority": 5, "deadline_hours": 1})
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    now = datetime.now()
    deadline = now + timedelta(hours=template["deadline_hours"])
    
    c.execute('''
        INSERT INTO tasks (user_id, title, description, deadline, priority, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, template["title"], f"Шаблон: {quick.template}", deadline, template["priority"], 'active', now, now))
    
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": task_id, "template": quick.template}

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """Delete task"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    
    return {"status": "deleted"}

@app.get("/stats/{user_id}")
async def get_stats(user_id: int):
    """Get user productivity stats"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get today's tasks
    today = datetime.now().date()
    c.execute('''
        SELECT COUNT(*) as total,
               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
        FROM tasks
        WHERE user_id = ? AND DATE(created_at) = ?
    ''', (user_id, today))
    
    stats = c.fetchone()
    conn.close()
    
    return {
        "user_id": user_id,
        "date": today.isoformat(),
        "total": stats[0] or 0,
        "completed": stats[1] or 0,
        "efficiency": round((stats[1] / stats[0] * 100) if stats[0] > 0 else 0)
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Echo API starting...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

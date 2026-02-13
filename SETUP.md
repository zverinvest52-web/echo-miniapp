# 🚀 Настройка Echo Mini App

## СТАТУС:
- ✅ GitHub Pages - настроен (https://zverinvest52-web.github.io/echo-miniapp/)
- ✅ Frontend - готов
- ✅ Backend код - готов (bot.py)
- ✅ Git репозиторий - обновлен
- ❌ Render - нужно настроить
- ❌ Mini App - нужно создать

---

## 📋 ЧЕК-ЛИСТ НАСТРОЙКИ

### 1️⃣ Создать Telegram Mini App

1. Открой @BotFather в Telegram
2. Напиши `/newapp`
3. Название: `Echo`
4. Short Name: `echo`
5. Description: (опционально) `Голосовой планировщик задач`
6. URL: `https://zverinvest52-web.github.io/echo-miniapp/`
7. Bot: Выбери `@echo_miniapp_vercel`
8. **Create**

**Результат:** Mini App готов для использования

---

### 2️⃣ Получить Bot Token

1. Открой @BotFather
2. Напиши `/mybots`
3. Выбери `@echo_miniapp_vercel`
4. Нажми **API Token**
5. **Copy** токен

**Результат:** Токен скопирован

---

### 3️⃣ Настроить Render (Backend + Bot)

1. Открой https://dashboard.render.com/
2. Нажми **New +**
3. Выбери **Web Service**
4. **GitHub** → **Connect account**
5. Найди репозиторий: `echo-miniapp`
6. Нажми **Connect**

**Настройки:**

- **Name:** `echo-miniapp`
- **Region:** (ближайшая к тебе)
- **Runtime:** `Python`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python bot.py`

**Environment Variables:**

1. BOT_TOKEN = *твой токен от BotFather*
2. RENDER_URL = *сгенерированный URL* (появится после деплоя, например: https://echo-miniapp.onrender.com)
3. MINIAPP_URL = `https://zverinvest52-web.github.io/echo-miniapp/`

**Нажми Create Web Service**

---

### 4️⃣ Подтвердить Webhook

После успешного деплоя Render:

1. Зайди в сервис `echo-miniapp` на Render
2. Открой **Logs**
3. Должно быть: `🚀 Echo Bot запускается...`
4. Скопируй URL: `https://echo-miniapp-xxxx.onrender.com`

Если нужно добавить RENDER_URL:

1. Render → Services → echo-miniapp
2. Environment → Add Environment Variable
3. Key: `RENDER_URL`
4. Value: *твой URL Render*
5. **Save Changes**
6. **Manual Deploy**

---

## ✅ ПРОВЕРКА

### Проверить Frontend:
Открой: https://zverinvest52-web.github.io/echo-miniapp/
Должно быть:
- Кнопки шаблонов
- Кнопка "Добавить задачу"
- Статистика

### Проверить Backend:
Открой: https://echo-miniapp.onrender.com/
Должно быть:
```json
{
  "status": "running",
  "service": "Echo Bot + API",
  "version": "2.0.0"
}
```

### Проверить Bot:
Открой @echo_miniapp_vercel в Telegram
Нажми `/start`
Должно быть меню с кнопками

---

## 🎯 РЕЗУЛЬТАТ

После настройки:
1. ✅ Telegram бот работает
2. ✅ Mini App открывается через бота
3. ✅ API работает
4. ✅ Задачи сохраняются в БД
5. ✅ Все функции работают

---

## 🆘 ТРУБЛЕШУТИНГ

### Bot не отвечает:
- Проверь токен в Render Environment
- Проверь Logs на Render
- Перезапусти сервис: Render → Manual Deploy

### Mini App не загружает задачи:
- Проверь что Render работает
- Проверь API_URL в index.html: `https://echo-miniapp.onrender.com`
- Открой консоль браузера (F12) → Console

### Webhook не работает:
- RENDER_URL должен быть правильным
- Проверь что PORT=8000 (стандартный)
- Перезапусти сервис

---

## 📞 СВЯЗЬ

Вопросы? Пиши @your_support_bot

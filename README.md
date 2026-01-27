# 🎓 Telegram-бот ЭИОС КемГУ с Mini App

Telegram-бот для получения уведомлений об оценках и работы с электронной информационно-образовательной средой вуза.

## 📋 Возможности

- ✅ **Уведомления о новых оценках** - мгновенные push-уведомления при выставлении оценок
- 📊 **Mini App** - веб-приложение внутри Telegram для просмотра успеваемости
- 🔔 **Гибкие настройки уведомлений** - включение/выключение уведомлений
- 📈 **Статистика** - средний балл, количество оценок, дни до сессии
- 💬 **Комментарии преподавателей** - отображение комментариев к оценкам
- 🔐 **Безопасная авторизация** - интеграция с системой ЭИОС

## 🏗️ Архитектура

```
┌─────────────────┐
│  Telegram Bot   │ ← Пользователи взаимодействуют через Telegram
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
┌────────▼────────┐  ┌────▼──────────┐
│   Mini App      │  │  Bot Server   │
│  (HTML/JS)      │  │  (Python)     │
└────────┬────────┘  └────┬──────────┘
         │                 │
         │           ┌─────▼──────┐
         │           │  Database  │
         │           │ (PostgreSQL)│
         │           └─────┬──────┘
         │                 │
    ┌────▼─────────────────▼─────┐
    │   Webhook Server (FastAPI) │
    └────────┬───────────────────┘
             │
    ┌────────▼────────┐
    │   ЭИОС Portal   │ ← Портал отправляет webhook'и о новых оценках
    └─────────────────┘
```

## 🚀 Быстрый старт

### 1. Требования

- Python 3.10+
- PostgreSQL 13+ (или SQLite для разработки)
- Redis (опционально, для продакшена)
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))

### 2. Установка

```bash
# Клонируйте репозиторий или скопируйте файлы
cd eios-telegram-bot

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt
```

### 3. Настройка

Скопируйте `.env.example` в `.env` и заполните настройки:

```bash
cp .env.example .env
nano .env  # или используйте любой редактор
```

Основные настройки:
```env
BOT_TOKEN=your_bot_token_here
WEBAPP_URL=https://your-domain.com/miniapp
EIOS_API_URL=https://eios.kemsu.ru/api
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/eios_bot
```

### 4. Инициализация базы данных

```bash
# Создать таблицы
python database.py
```

### 5. Запуск

Вам нужно запустить два сервиса:

**Терминал 1 - Telegram Bot:**
```bash
python telegram_bot.py
```

**Терминал 2 - Webhook Server:**
```bash
uvicorn webhook_server:app --reload --host 0.0.0.0 --port 8080
```

## 📱 Создание бота в Telegram

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Получите токен и вставьте его в `.env` файл
5. Настройте Mini App:
   ```
   /setmenubutton
   [выберите вашего бота]
   Введите текст кнопки: 🎓 Портал ЭИОС
   Введите URL: https://your-domain.com/miniapp
   ```

## 🌐 Развертывание Mini App

Mini App должен быть доступен по HTTPS. Варианты развертывания:

### Вариант 1: Локальное тестирование с ngrok

```bash
# Установите ngrok
# Скачайте с https://ngrok.com/download

# Запустите туннель
ngrok http 8080

# Используйте предоставленный URL (например, https://abc123.ngrok.io)
# Обновите WEBAPP_URL в .env
```

### Вариант 2: Облачный хостинг

Подходящие платформы:
- **Heroku** - бесплатный тариф для небольших проектов
- **Railway** - современная платформа с простым деплоем
- **DigitalOcean** - VPS с полным контролем
- **AWS/GCP/Azure** - для enterprise решений

Пример для Railway:
```bash
# Установите Railway CLI
npm i -g @railway/cli

# Войдите
railway login

# Создайте проект
railway init

# Разверните
railway up
```

## 🔗 Интеграция с порталом ЭИОС

### Способ 1: Webhook (рекомендуется)

Портал ЭИОС должен отправлять POST запрос при выставлении новой оценки:

```http
POST https://your-bot-domain.com/webhook/eios/new_grade
Content-Type: application/json
X-Signature: [HMAC-SHA256 signature]

{
  "student_id": 12345,
  "eios_grade_id": 1001,
  "subject": "Высшая математика",
  "assignment": "Контрольная работа №1",
  "grade": 5,
  "teacher_name": "Иванов И.И.",
  "comment": "Отличная работа!",
  "date": "2026-01-25T10:30:00+07:00"
}
```

Подпись вычисляется как:
```python
import hmac
import hashlib

signature = hmac.new(
    WEBHOOK_SECRET.encode(),
    request_body,
    hashlib.sha256
).hexdigest()
```

### Способ 2: Polling API (альтернатива)

Если webhook'и недоступны, можно использовать периодический опрос:

```python
# В eios_integration.py уже есть пример
async def check_new_grades():
    while True:
        # Запрос к API ЭИОС
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{EIOS_API_URL}/new_grades") as response:
                new_grades = await response.json()
                for grade in new_grades:
                    await send_notification(grade)
        
        await asyncio.sleep(300)  # Проверка каждые 5 минут
```

## 📊 Структура базы данных

### Таблица users
```sql
id              SERIAL PRIMARY KEY
telegram_id     BIGINT UNIQUE NOT NULL
username        VARCHAR(255)
first_name      VARCHAR(255)
student_id      INTEGER
notifications_enabled BOOLEAN DEFAULT TRUE
created_at      TIMESTAMP WITH TIME ZONE
```

### Таблица grades
```sql
id              SERIAL PRIMARY KEY
user_id         INTEGER REFERENCES users(id)
eios_grade_id   INTEGER UNIQUE
subject         VARCHAR(500)
assignment      VARCHAR(500)
grade_value     INTEGER
teacher_name    VARCHAR(255)
comment         TEXT
grade_date      TIMESTAMP WITH TIME ZONE
notification_sent BOOLEAN DEFAULT FALSE
```

## 🎨 Кастомизация

### Изменение дизайна Mini App

Файл `miniapp.html` использует CSS переменные Telegram:
```css
background-color: var(--tg-theme-bg-color);
color: var(--tg-theme-text-color);
```

Вы можете добавить свои стили или полностью переработать интерфейс.

### Добавление новых команд бота

В `telegram_bot.py`:
```python
@dp.message(Command("mystats"))
async def cmd_mystats(message: types.Message):
    """Команда для показа статистики"""
    # Ваша логика
    await message.answer("Ваша статистика...")
```

### Добавление новых типов уведомлений

```python
async def send_deadline_notification(user_id: int, deadline_data: dict):
    """Уведомление о приближающемся дедлайне"""
    notification_text = f"""
⏰ Напоминание о дедлайне!

📘 Предмет: {deadline_data['subject']}
📝 Работа: {deadline_data['assignment']}
⏳ Осталось: {deadline_data['days_left']} дней
"""
    await bot.send_message(user_id, notification_text)
```

## 🔐 Безопасность

### Важные практики:

1. **Никогда не коммитьте `.env` файл** - добавьте его в `.gitignore`
2. **Используйте HTTPS** для Mini App и webhook'ов
3. **Проверяйте подписи webhook'ов** - используйте HMAC
4. **Валидируйте входные данные** - используйте Pydantic модели
5. **Ограничивайте rate limit** - защита от DDoS
6. **Храните пароли в хешированном виде** - используйте bcrypt
7. **Используйте JWT токены** для сессий

### Пример проверки подписи:
```python
def verify_webhook_signature(request_body: bytes, signature: str) -> bool:
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

## 🧪 Тестирование

### Unit тесты
```bash
pytest tests/
```

### Тестирование webhook'ов
```bash
# Используйте curl для отправки тестового webhook'а
curl -X POST http://localhost:8080/webhook/eios/new_grade \
  -H "Content-Type: application/json" \
  -H "X-Signature: your_signature" \
  -d '{
    "student_id": 12345,
    "subject": "Test Subject",
    "assignment": "Test Assignment",
    "grade": 5,
    "date": "2026-01-25T10:30:00+07:00"
  }'
```

## 📈 Мониторинг и логи

### Просмотр логов
```bash
# Логи бота
tail -f logs/bot.log

# Логи webhook сервера
tail -f logs/webhook.log
```

### Метрики (опционально)

Можно добавить Prometheus для сбора метрик:
```python
from prometheus_client import Counter, Histogram

notifications_sent = Counter('notifications_sent_total', 'Total notifications sent')
webhook_latency = Histogram('webhook_processing_seconds', 'Webhook processing time')
```

## 🐛 Решение проблем

### Бот не отвечает
- Проверьте токен бота в `.env`
- Убедитесь, что бот запущен (`python telegram_bot.py`)
- Проверьте интернет-соединение

### Mini App не открывается
- Проверьте, что URL доступен по HTTPS
- Убедитесь, что webhook сервер запущен
- Проверьте настройки CORS в `webhook_server.py`

### Уведомления не приходят
- Проверьте, что уведомления включены у пользователя
- Убедитесь, что webhook от ЭИОС доходят до сервера
- Проверьте логи: `tail -f logs/bot.log`

### Ошибки базы данных
```bash
# Пересоздать таблицы (ОСТОРОЖНО - удалит все данные!)
python -c "from database import Database; import asyncio; db = Database('your_db_url'); asyncio.run(db.drop_tables()); asyncio.run(db.create_tables())"
```

## 🔄 Обновление

```bash
# Остановите сервисы
# Обновите код
git pull  # если используете git

# Обновите зависимости
pip install -r requirements.txt --upgrade

# Примените миграции БД (если есть)
alembic upgrade head

# Перезапустите сервисы
python telegram_bot.py &
uvicorn webhook_server:app --host 0.0.0.0 --port 8080 &
```

## 📚 Дополнительные ресурсы

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Telegram Mini Apps](https://core.telegram.org/bots/webapps)
- [aiogram документация](https://docs.aiogram.dev/)
- [FastAPI документация](https://fastapi.tiangolo.com/)
- [SQLAlchemy документация](https://docs.sqlalchemy.org/)

## 🤝 Вклад в проект

Если вы хотите улучшить бота:

1. Fork репозитория
2. Создайте ветку для фичи (`git checkout -b feature/AmazingFeature`)
3. Commit изменений (`git commit -m 'Add some AmazingFeature'`)
4. Push в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📝 Лицензия

Этот проект распространяется под лицензией MIT.

## 💡 Идеи для развития

- [ ] Интеграция с расписанием занятий
- [ ] Уведомления о домашних заданиях
- [ ] Чат с преподавателями
- [ ] Экспорт оценок в Excel
- [ ] Графики успеваемости
- [ ] Рейтинг среди однокурсников
- [ ] Push-уведомления о дедлайнах
- [ ] Интеграция с электронной библиотекой
- [ ] Оплата за обучение через бота
- [ ] Заказ справок и документов

## 📞 Поддержка

Если у вас возникли вопросы:
- Создайте Issue в GitHub
- Напишите на почту: support@example.com
- Telegram: @support_bot

---

**Сделано с ❤️ для студентов КемГУ**

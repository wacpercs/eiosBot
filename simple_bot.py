"""
Простой Telegram-бот для уведомлений об оценках (на python-telegram-bot)
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ВСТАВЬТЕ СЮДА ВАШ ТОКЕН
BOT_TOKEN = "8252171259:AAHHjeLY8NcGtLK_2bdhNqI1U1PYhIFBKMk"

# URL вашего Mini App
WEBAPP_URL = "https://wacpercs.github.io/eios-bot/miniapp.html"

# База данных пользователей
user_database = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    user_id = user.id
    
    # Сохраняем пользователя
    user_database[user_id] = {
        "telegram_id": user_id,
        "username": user.username,
        "first_name": user.first_name,
        "notifications_enabled": True
    }
    
    # Создаём кнопки
    keyboard = [
        [InlineKeyboardButton("🎓 Открыть ЭИОС", web_app={"url": WEBAPP_URL})],
        [InlineKeyboardButton("📊 Мои оценки", callback_data='grades')],
        [InlineKeyboardButton("👨‍🏫 Связь с преподавателем", callback_data='teachers')],
        [InlineKeyboardButton("🔔 Настройки", callback_data='settings')],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
👋 Привет, {user.first_name}!

Я бот ЭИОС КемГУ. Я помогу тебе:

✅ Получать уведомления о новых оценках
✅ Быстро проверять успеваемость
✅ Отслеживать дедлайны работ

Используй кнопки ниже для навигации!
"""
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'grades':
        grades_text = """
📊 Ваши последние оценки:

📘 Высшая математика
└ Контрольная работа №3: ⭐️ 5 (25.01.2026)
└ Домашнее задание №5: ⭐️ 4 (24.01.2026)

💻 Программирование
└ Лабораторная работа №2: ⭐️ 5 (23.01.2026)

🌍 Иностранный язык
└ Эссе: ⭐️ 4 (22.01.2026)

📈 Средний балл: 4.5
"""
        keyboard = [[InlineKeyboardButton("« Назад", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(grades_text, reply_markup=reply_markup)
    
    elif query.data == 'settings':
        user_id = query.from_user.id
        enabled = user_database.get(user_id, {}).get("notifications_enabled", True)
        
        settings_text = f"""
⚙️ Настройки уведомлений

Статус: {'✅ Включены' if enabled else '❌ Выключены'}

Вы будете получать уведомления о:
• Новых оценках
• Комментариях преподавателей
• Дедлайнах
"""
        keyboard = [
            [InlineKeyboardButton(
                f"{'🔕 Выключить' if enabled else '🔔 Включить'}", 
                callback_data='toggle'
            )],
            [InlineKeyboardButton("« Назад", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(settings_text, reply_markup=reply_markup)
    
    elif query.data == 'help':
        help_text = """
📚 Справка по боту

Доступные команды:
/start - Главное меню
/grades - Показать оценки
/help - Эта справка

💡 Используйте кнопки для навигации!
"""
        keyboard = [[InlineKeyboardButton("« Назад", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(help_text, reply_markup=reply_markup)

    elif query.data == 'teachers':
        teachers_text = """
👨‍🏫 Связь с преподавателями

💻 Программирование
👤 Бурмин Леонид Николаевич
🔗 https://t.me/

💻 Информационные системы и технологии
👤 Илькевич Василий Васильевич
🔗 https://t.me/

📧 Общие вопросы: dekanat@kemsu.ru
"""
        keyboard = [[InlineKeyboardButton("« Назад", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(teachers_text, reply_markup=reply_markup)
    
    elif query.data == 'toggle':
        user_id = query.from_user.id
        if user_id in user_database:
            current = user_database[user_id].get("notifications_enabled", True)
            user_database[user_id]["notifications_enabled"] = not current
            await query.answer(f"✅ Уведомления {'включены' if not current else 'выключены'}!")
            # Возвращаемся к настройкам
            query.data = 'settings'
            await button_handler(update, context)
    
    elif query.data == 'back':
        # Возврат в главное меню
        keyboard = [
            [InlineKeyboardButton("📊 Мои оценки", callback_data='grades')],
            [InlineKeyboardButton("👨‍🏫 Связь с преподавателем", callback_data='teachers')],
            [InlineKeyboardButton("🔔 Настройки", callback_data='settings')],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        menu_text = """
🎓 Главное меню

Выберите нужное действие:
"""
        await query.edit_message_text(menu_text, reply_markup=reply_markup)


async def grades_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /grades"""
    grades_text = """
📊 Ваши последние оценки:

📘 Высшая математика: ⭐️ 5
💻 Программирование: ⭐️ 5
🌍 Иностранный язык: ⭐️ 4

📈 Средний балл: 4.7
"""
    await update.message.reply_text(grades_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
📚 Справка по боту

Доступные команды:
/start - Главное меню
/grades - Показать оценки
/help - Эта справка

💡 Используйте кнопки для удобной навигации!
"""
    await update.message.reply_text(help_text)


def main():
    """Запуск бота"""
    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("grades", grades_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Запускаем бота
    logger.info("🚀 Бот запущен и работает!")
    print("✅ Бот запущен! Нажмите Ctrl+C для остановки")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

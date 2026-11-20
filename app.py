import os
import json
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==========================================
# 1. НАСТРОЙКИ
# ==========================================
# Эти значения мы возьмем из переменных окружения на хостинге
TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

# Ссылка на наш сайт-калькулятор
WEB_APP_URL = "https://sgar7103-byte.github.io/cash/1time.html?v=20261120"
CONTACT_URL = "https://t.me/vsemdobra12345"

# ==========================================
# 2. НАСТРОЙКА FLASK (Чтобы Render не ругался на порты)
# ==========================================
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"

# ==========================================
# 3. ЛОГИКА БОТА
# ==========================================
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "друг"
    
    keyboard = [
        [InlineKeyboardButton("🛠 Заказать услугу (Калькулятор)", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton("📞 Связаться с мастером", url=CONTACT_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"<b>Здравствуйте, {user_name}! 👋</b>\n\n"
        "Я Алексей — мастер на час. 🔧\n"
        "Помогу с ремонтом, сборкой мебели и другими делами.\n\n"
        "Нажмите кнопку ниже, чтобы рассчитать стоимость и оставить заявку:"
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сюда приходят данные с нашего сайта-калькулятора"""
    try:
        # Данные приходят в виде JSON-строки
        data = json.loads(update.effective_message.web_app_data.data)
        
        # Формируем красивое сообщение для тебя (Админа)
        order_text = "<b>🔔 НОВАЯ ЗАЯВКА</b>\n\n"
        order_text += f"👤 <b>Имя:</b> {data.get('name', 'Не указано')}\n"
        order_text += f"📞 <b>Телефон:</b> {data.get('phone', 'Не указан')}\n"
        order_text += f"📍 <b>Адрес:</b> {data.get('address', 'Не указан')}\n"
        order_text += f"🕒 <b>Время:</b> {data.get('time', 'Не указано')}\n\n"
        
        order_text += "<b>🛠 Услуги:</b>\n"
        for service in data.get('services', []):
            order_text += f"• {service.get('name')} ({service.get('quantity')} шт.) — {service.get('price')} ₽\n"
        
        order_text += f"\n💰 <b>Примерная стоимость:</b> {data.get('total', 0)} ₽"
        
        if data.get('urgent'):
            order_text += "\n\n🔥 <b>СРОЧНЫЙ ВЫЗОВ (+20%)</b>"

        # Отправляем заявку тебе
        await context.bot.send_message(chat_id=ADMIN_ID, text=order_text, parse_mode='HTML')
        
        # Отвечаем клиенту
        await update.message.reply_text("✅ <b>Спасибо!</b> Заявка отправлена мастеру. Он скоро свяжется с вами.", parse_mode='HTML')
        
    except Exception as e:
        logging.error(f"Ошибка при обработке заявки: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Если пользователь пишет что-то кроме /start"""
    keyboard = [[InlineKeyboardButton("🛠 Открыть калькулятор", web_app=WebAppInfo(url=WEB_APP_URL))]]
    await update.message.reply_text(
        "Пожалуйста, воспользуйтесь нашим умным калькулятором для расчета стоимости:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==========================================
# 4. ЗАПУСК
# ==========================================
def run_bot():
    application = Application.builder().token(TOKEN).build()
    
    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Запускаем в режиме polling (бот сам опрашивает Telegram)
    application.run_polling()

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке, чтобы Flask мог работать параллельно
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Запускаем Flask (это нужно для хостинга Render)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

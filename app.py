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
TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

WEB_APP_URL = "https://sgar7103-byte.github.io/cash/1time.html?v=20261120"
CONTACT_URL = "https://t.me/vsemdobra12345"
PORTFOLIO_URL = "https://t.me/vsemdobra12345"

# ==========================================
# 2. НАСТРОЙКА FLASK
# ==========================================
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"

# Включаем логи, чтобы видеть ошибки, если что-то пойдет не так
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==========================================
# 3. ЛОГИКА БОТА
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Пишем в логи, что команда получена
    logger.info(f"Получена команда /start от {update.effective_user.id}")
    
    user_name = update.effective_user.first_name or "друг"
    
    keyboard = [
        [InlineKeyboardButton("🛠 Заказать услугу (Калькулятор)", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton("📸 Примеры работ", url=PORTFOLIO_URL)],
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
    logger.info("Получены данные из Mini App!")
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        
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

        await context.bot.send_message(chat_id=ADMIN_ID, text=order_text, parse_mode='HTML')
        await update.message.reply_text("✅ <b>Спасибо!</b> Заявка отправлена мастеру. Он скоро свяжется с вами.", parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Ошибка при обработке заявки: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получен обычный текст от {update.effective_user.id}")
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
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("Бот запускается в режиме Polling...")
    # Вот тут магия: drop_pending_updates=True сбрасывает старые зависшие сообщения
    # allowed_updates=Update.ALL_TYPES разрешает получать команды и данные с сайта
    application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

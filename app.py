import os
import json
import logging
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
WEB_APP_URL = "https://sgar7103-byte.github.io/cash/1time.html?v=20261121"
CONTACT_URL = "https://t.me/vsemdobra12345"

app = Flask(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "друг"
    keyboard = [
        [InlineKeyboardButton("🛠 Рассчитать стоимость", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton("📞 Связаться с мастером", url=CONTACT_URL)]
    ]
    welcome_text = (
        f"<b>Здравствуйте, {user_name}! 👋</b>\n\n"
        "Я Алексей — мастер на час. 🔧\n"
        "Нажмите кнопку ниже, чтобы выбрать услуги и узнать стоимость:"
    )
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        
        order_text = "<b>🔔 НОВАЯ ЗАЯВКА</b>\n\n"
        order_text += f"👤 <b>Имя:</b> {data.get('name')}\n"
        order_text += f"📱 <b>Telegram:</b> @{data.get('telegram_username')}\n"
        order_text += f"📞 <b>Телефон:</b> {data.get('phone')}\n"
        order_text += f"📍 <b>Адрес:</b> {data.get('address')}\n\n"
        order_text += "<b>🛠 Услуги:</b>\n"
        
        for service in data.get('services', []):
            order_text += f"• {service.get('name')} — {service.get('quantity')} шт. ({service.get('price')} ₽)\n"
            
        order_text += f"\n💰 <b>Итого:</b> {data.get('total')} ₽"
        
        await context.bot.send_message(chat_id=ADMIN_ID, text=order_text, parse_mode='HTML')
        await update.message.reply_text("✅ <b>Принято!</b> Я свяжусь с вами в ближайшее время.", parse_mode='HTML')
    except Exception as e:
        logging.error(f"Ошибка: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🛠 Открыть калькулятор", web_app=WebAppInfo(url=WEB_APP_URL))]]
    await update.message.reply_text("Пожалуйста, воспользуйтесь калькулятором:", reply_markup=InlineKeyboardMarkup(keyboard))

application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        async def process():
            await application.initialize()
            await application.start()
            await application.process_update(update)
            await application.stop()
            await application.shutdown()
        asyncio.run(process())
    except Exception as e:
        logging.error(f"Ошибка в вебхуке: {e}")
    return "OK", 200

@app.route('/')
def index(): return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

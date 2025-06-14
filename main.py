import json
import logging
import os
from datetime import datetime, timedelta

import pytz
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

CONFIG_FILE = "config.json"
ADMIN_ID = 1288379477  # замени на свой Telegram ID

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "chat_id": -1002773838097,
        "day": "Friday",
        "time": "10:00"
    }

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def get_sunset_time():
    lat = 55.751244
    lng = 37.618423
    response = requests.get(
        f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lng}&formatted=0"
    )
    data = response.json()
    sunset_utc = datetime.fromisoformat(data["results"]["sunset"])
    moscow_tz = pytz.timezone("Europe/Moscow")
    sunset_moscow = sunset_utc.astimezone(moscow_tz)
    adjusted_time = sunset_moscow - timedelta(hours=1)
    return adjusted_time.strftime("%H:%M")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен. Используйте /set для изменения настроек.")

async def set_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав.")
        return

    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Формат: /set <день> <время>, пример: /set Friday 10:00")
        return

    day, time = args
    config = load_config()
    config["day"] = day
    config["time"] = time
    save_config(config)
    await update.message.reply_text(f"Настройки обновлены: {day} в {time}")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав.")
        return

    config = load_config()
    sunset_time = get_sunset_time()
    message = f"ⲥⲉⲅⲟⲇⲏя ⲃⲥⲧⲣⲉⳡⲁ ⲥⲩⳝⳝⲟⲧы ⲃ  {sunset_time}"
    await context.bot.send_message(chat_id=config["chat_id"], text=message)
    await update.message.reply_text("Тестовое сообщение отправлено.")

# ⚠️ Запуск без asyncio.run — напрямую
logging.basicConfig(level=logging.INFO)

config = load_config()
TOKEN = os.getenv("BOT_TOKEN") or "7209287971:AAEUlDxd-0XwMzxpecpk8BvfhlrGkLbIqrw"
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("set", set_config))
app.add_handler(CommandHandler("test", test_command))

app.run_polling()

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta

import pytz
import requests
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Путь к конфигу
CONFIG_FILE = "config.json"

# ID администратора (твоё)
ADMIN_ID = 1288379477

# Загрузка конфигурации
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "chat_id": -1002773838097,
        "day": "Friday",
        "time": "10:00"
    }

# Сохранение конфигурации
def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

# Получить время захода солнца и вычесть 1 час
def get_sunset_time():
    # Координаты (Москва)
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

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен. Используйте /set для изменения настроек.")

# Команда /set
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

# Команда /test
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав.")
        return

    config = load_config()
    sunset_time = get_sunset_time()
    message = f"Сегодня встреча — суббота в {sunset_time}"
    await context.bot.send_message(chat_id=config["chat_id"], text=message)
    await update.message.reply_text("Тестовое сообщение отправлено.")

# Основной запуск
async def main():
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    TOKEN = os.getenv("BOT_TOKEN") or "7209287971:AAEUlDxd-0XwMzxpecpk8BvfhlrGkLbIqrw"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_config))
    app.add_handler(CommandHandler("test", test_command))

    await app.run_polling()

# Для Render
if __name__ == '__main__':
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError as e:
        print(f"Runtime error: {e}")

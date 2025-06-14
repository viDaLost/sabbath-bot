import json
import os
import pytz
import requests
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
import asyncio

TOKEN = os.getenv("BOT_TOKEN") or "7209287971:AAEUlDxd-0XwMzxpecpk8BvfhlrGkLbIqrw"
CHANNEL_ID = os.getenv("CHANNEL_ID") or "-1002773838097"
ADMIN_ID = int(os.getenv("ADMIN_ID") or "1288379477")
SETTINGS_FILE = "settings.json"

default_settings = {
    "day": "friday",
    "time": "10:00"
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(default_settings)
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)

def get_sunset_time():
    url = "https://api.sunrise-sunset.org/json?lat=55.7558&lng=37.6173&formatted=0"
    response = requests.get(url)
    data = response.json()
    sunset_utc = datetime.fromisoformat(data["results"]["sunset"])
    moscow_tz = pytz.timezone("Europe/Moscow")
    sunset_moscow = sunset_utc.astimezone(moscow_tz)
    adjusted_time = sunset_moscow - timedelta(hours=1)
    return sunset_moscow, adjusted_time

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    _, adjusted_time = get_sunset_time()
    message = f"🕊️Сⲉⲅⲟⲇⲏя ⲃⲥⲧⲣⲉⳡⲁ ⲥⲩⳝⳝⲟⲧы ⲃ ❗️ {adjusted_time.strftime('%H:%M')} ❗️ "
    await context.bot.send_message(chat_id=CHANNEL_ID, text=message)

async def scheduler(app):
    while True:
        now = datetime.now(pytz.timezone("Europe/Moscow"))
        settings = load_settings()
        weekday = now.strftime("%A").lower()
        if weekday == settings["day"]:
            target_time = datetime.strptime(settings["time"], "%H:%M").time()
            if now.time().hour == target_time.hour and now.time().minute == target_time.minute:
                await send_reminder(app.bot)
                await asyncio.sleep(60)
        await asyncio.sleep(30)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Бот работает. Используй /set чтобы изменить день и время.")

async def set_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        day = context.args[0].lower()
        time = context.args[1]
        datetime.strptime(time, "%H:%M")
        settings = load_settings()
        settings["day"] = day
        settings["time"] = time
        save_settings(settings)
        await update.message.reply_text(f"Настройки обновлены: {day}, {time}")
    except:
        await update.message.reply_text("Используй: /set день время\nПример: /set friday 10:00")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    sunset_moscow, adjusted_time = get_sunset_time()
    await update.message.reply_text(
        f"🔍 Проверка уведомления\n"
        f"☀ Заход солнца по МСК: {sunset_moscow.strftime('%H:%M')}\n"
        f"📌 Время встречи (минус 1 час): {adjusted_time.strftime('%H:%M')}"
    )

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_config))
    app.add_handler(CommandHandler("test", test_command))

    # Удаляем возможный webhook
    await app.bot.delete_webhook(drop_pending_updates=True)

    # Запускаем планировщик
    asyncio.create_task(scheduler(app))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

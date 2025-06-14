import json
import datetime
import asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Загрузка конфигурации
with open("config.json", "r") as f:
    cfg = json.load(f)

ADMIN_ID = cfg["admin_id"]
CHAT_ID = cfg["chat_id"]

def save_cfg():
    with open("config.json", "w") as f:
        json.dump(cfg, f, indent=2)

def get_sunset_minus_hour():
    url = f"https://api.sunrise-sunset.org/json?lat={cfg['lat']}&lng={cfg['lon']}&formatted=0"
    r = requests.get(url).json()
    utc = datetime.datetime.fromisoformat(r["results"]["sunset"][:-1])
    return (utc + datetime.timedelta(hours=3) - datetime.timedelta(hours=1))

async def send_msg(app):
    sunset = get_sunset_minus_hour().strftime("%H:%M")
    text = f"Сегодня встреча, суббота в {sunset}"
    await app.bot.send_message(CHAT_ID, text)

async def scheduler(app):
    while True:
        now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)  # МСК
        if now.weekday() == cfg["weekday"] and now.hour == cfg["hour"] and now.minute == cfg["minute"]:
            await send_msg(app)
            await asyncio.sleep(60)
        await asyncio.sleep(5)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text(
            "Команды администратора:\n"
            "/setday <0-6> — день недели (0=Пн … 6=Вс)\n"
            "/settime <ЧЧ:ММ> — время по МСК\n"
            "/setloc <lat> <lon> — координаты\n"
            "/test — тестовая отправка"
        )

async def setday(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        d = int(ctx.args[0])
        if 0 <= d <= 6:
            cfg["weekday"] = d
            save_cfg()
            await update.message.reply_text(f"День недели обновлён: {d}")
        else:
            raise ValueError
    except:
        await update.message.reply_text("Ошибка. Формат: /setday 4")

async def settime(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        h, m = map(int, ctx.args[0].split(":"))
        if 0 <= h < 24 and 0 <= m < 60:
            cfg["hour"], cfg["minute"] = h, m
            save_cfg()
            await update.message.reply_text(f"Время установлено: {h:02}:{m:02} МСК")
        else:
            raise ValueError
    except:
        await update.message.reply_text("Ошибка. Формат: /settime 10:00")

async def setloc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        lat, lon = map(float, ctx.args)
        cfg["lat"], cfg["lon"] = lat, lon
        save_cfg()
        await update.message.reply_text(f"Координаты обновлены: {lat}, {lon}")
    except:
        await update.message.reply_text("Ошибка. Формат: /setloc 55.75 37.61")

async def test(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        sunset = get_sunset_minus_hour().strftime("%H:%M")
        text = f"✅ ТЕСТ: Сегодня встреча, суббота в {sunset}"
        await ctx.bot.send_message(chat_id=CHAT_ID, text=text)
        await update.message.reply_text("Тестовое сообщение отправлено в канал.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при отправке: {e}")

async def main():
    app = Application.builder().token(cfg["bot_token"]).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setday", setday))
    app.add_handler(CommandHandler("settime", settime))
    app.add_handler(CommandHandler("setloc", setloc))
    app.add_handler(CommandHandler("test", test))
    asyncio.create_task(scheduler(app))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json
import os
import asyncio
import aiohttp
from aiohttp import web

TOKEN = os.environ["TOKEN"]
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")  # URL que UptimeRobot va a pingear
PORT = int(os.environ.get("PORT", 10000))
DATA_FILE = "deuda.json"

# Inicializar archivo si no existe
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

def leer_datos():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def guardar_datos(lista):
    with open(DATA_FILE, "w") as f:
        json.dump(lista, f)

# -----------------------
# Comandos del bot
# -----------------------
async def gastamos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usa /gastamos <número> [nota opcional]")
        return
    try:
        cantidad = float(context.args[0])
    except ValueError:
        await update.message.reply_text("El primer argumento debe ser un número.")
        return
    nota = " ".join(context.args[1:]) if len(context.args) > 1 else ""
    usuario = update.message.from_user.username or update.message.from_user.first_name
    datos = leer_datos()
    datos.append({"usuario": usuario, "cantidad": cantidad, "nota": nota})
    guardar_datos(datos)
    total = sum(d["cantidad"] for d in datos)
    await update.message.reply_text(f"Gasto de {cantidad} agregado por {usuario}. Total ahora: {total}")

async def deuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = leer_datos()
    total = sum(d["cantidad"] for d in datos)
    await update.message.reply_text(f"Deuda total: {total}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/gastamos <monto> <nota>\n/deuda\n/dividir\n/datosdeuda\n/resetdeuda")

# -----------------------
# Keep-alive y web server para Render
# -----------------------
async def keep_awake():
    if not RENDER_URL:
        return
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                await session.get(RENDER_URL)
        except Exception as e:
            print("Error ping auto:", e)
        await asyncio.sleep(600)  # cada 10 min

async def web_server():
    async def handle_root(request):
        return web.Response(text="Bot awake!")
    app_web = web.Application()
    app_web.add_routes([web.get("/", handle_root)])
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

# -----------------------
# Configuración del bot
# -----------------------
app_bot = ApplicationBuilder().token(TOKEN).build()
app_bot.add_handler(CommandHandler("gastamos", gastamos))
app_bot.add_handler(CommandHandler("deuda", deuda))
app_bot.add_handler(CommandHandler("help", help_command))

print("Bot iniciado beep beep!")

# -----------------------
# Start polling + tareas async
# -----------------------
loop = asyncio.get_event_loop()
loop.create_task(keep_awake())
loop.create_task(web_server())
loop.create_task(app_bot.run_polling())
loop.run_forever()


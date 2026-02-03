from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json
import os
import asyncio
import aiohttp

# -----------------------
# Configuración
# -----------------------
TOKEN = os.environ["TOKEN"]
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")  # Render la inyecta sola
DATA_FILE = "deuda.json"

# Inicializar archivo si no existe
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

# -----------------------
# Funciones de datos
# -----------------------
def leer_datos():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def guardar_datos(lista):
    with open(DATA_FILE, "w") as f:
        json.dump(lista, f)

# -----------------------
# Comandos
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
    await update.message.reply_text(
        f"Gasto de {cantidad} agregado por {usuario}. Total ahora: {total}"
    )

async def deuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = leer_datos()
    total = sum(d["cantidad"] for d in datos)
    await update.message.reply_text(f"Deuda total: {total}")

async def dividir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = leer_datos()
    if not datos:
        await update.message.reply_text("No hay gastos registrados.")
        return

    gasto_por_usuario = {}
    for d in datos:
        gasto_por_usuario[d["usuario"]] = gasto_por_usuario.get(d["usuario"], 0) + d["cantidad"]

    total = sum(gasto_por_usuario.values())
    promedio = total / len(gasto_por_usuario)

    mensaje = "Balance de pagos:\n"
    for usuario, gasto in gasto_por_usuario.items():
        balance = gasto - promedio
        if balance > 0:
            mensaje += f"{usuario} debería recibir {balance}\n"
        elif balance < 0:
            mensaje += f"{usuario} debería pagar {abs(balance)}\n"
        else:
            mensaje += f"{usuario} está equilibrado\n"

    await update.message.reply_text(mensaje)

async def datosdeuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = leer_datos()
    if not datos:
        await update.message.reply_text("No hay gastos registrados.")
        return

    mensaje = ""
    for d in datos:
        nota = f" - {d['nota']}" if d["nota"] else ""
        mensaje += f"{d['usuario']}: {d['cantidad']}{nota}\n"

    await update.message.reply_text(f"Desglose de gastos:\n{mensaje}")

async def resetdeuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guardar_datos([])
    await update.message.reply_text("Deuda reiniciada a 0.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/gastamos <monto> <nota>\n"
        "/deuda\n"
        "/dividir\n"
        "/datosdeuda\n"
        "/resetdeuda"
    )

# -----------------------
# Keep-alive para Render
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
        await asyncio.sleep(600)  # cada 10 minutos

# -----------------------
# Configuración del bot
# -----------------------


# Hook para iniciar keep_alive cuando el loop esté listo
async def start_keep_awake(app):
    asyncio.create_task(keep_awake())

app = ApplicationBuilder().token(TOKEN).post_init(start_keep_awake).build()

# Handlers
app.add_handler(CommandHandler("gastamos", gastamos))
app.add_handler(CommandHandler("deuda", deuda))
app.add_handler(CommandHandler("dividir", dividir))
app.add_handler(CommandHandler("datosdeuda", datosdeuda))
app.add_handler(CommandHandler("resetdeuda", resetdeuda))
app.add_handler(CommandHandler("help", help_command))


print("Bot iniciado beep beep!")

# -----------------------
# Polling
# -----------------------
app.run_polling()


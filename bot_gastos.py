from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json
import os

# Archivo donde guardamos los datos
DATA_FILE = "deuda.json"

# Inicializar archivo si no existe
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

# Función para leer datos
def leer_datos():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# Función para guardar datos
def guardar_datos(lista):
    with open(DATA_FILE, "w") as f:
        json.dump(lista, f)

# Comando /gastamos <número> [nota opcional]
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

# Comando /deuda
async def deuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = leer_datos()
    total = sum(d["cantidad"] for d in datos)
    await update.message.reply_text(f"Deuda total: {total}")

# Comando /dividir
async def dividir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = leer_datos()
    if not datos:
        await update.message.reply_text("No hay gastos registrados.")
        return

    # Calcular total por usuario
    gasto_por_usuario = {}
    for d in datos:
        gasto_por_usuario[d["usuario"]] = gasto_por_usuario.get(d["usuario"], 0) + d["cantidad"]

    num_usuarios = len(gasto_por_usuario)
    total_general = sum(gasto_por_usuario.values())
    promedio = total_general / num_usuarios

    mensaje = "Balance de pagos:\n"
    for usuario, gasto in gasto_por_usuario.items():
        balance = gasto - promedio
        if balance > 0:
            mensaje += f"{usuario} puso {gasto} → debería recibir {balance}\n"
        elif balance < 0:
            mensaje += f"{usuario} puso {gasto} → debería pagar {abs(balance)}\n"
        else:
            mensaje += f"{usuario} puso {gasto} → está equilibrado\n"

    await update.message.reply_text(mensaje)

# Comando /datosdeuda
async def datosdeuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = leer_datos()
    if not datos:
        await update.message.reply_text("No hay gastos registrados.")
        return
    
    mensaje = ""
    for d in datos:
        nota = f" - {d['nota']}" if d['nota'] else ""
        mensaje += f"{d['usuario']}: {d['cantidad']}{nota}\n"
    
    await update.message.reply_text(f"Desglose de gastos:\n{mensaje}")

# Comando /resetdeuda
async def resetdeuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guardar_datos([])
    await update.message.reply_text("Deuda reiniciada a 0.")

# -----------------------
# Token de BotFather
# -----------------------
TOKEN = "7920157435:AAH_8bvq3tW5Whj_Tk_8mD2NgbzDfj_W0ZQ"  # <-- PONÉ TU TOKEN AQUÍ

# Crear aplicación
app = ApplicationBuilder().token(TOKEN).build()

# Añadir handlers
app.add_handler(CommandHandler("gastamos", gastamos))
app.add_handler(CommandHandler("deuda", deuda))
app.add_handler(CommandHandler("dividir", dividir))
app.add_handler(CommandHandler("datosdeuda", datosdeuda))
app.add_handler(CommandHandler("resetdeuda", resetdeuda))

print("Bot de gastos iniciado...")
app.run_polling()


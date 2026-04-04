import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")

# Menu
menu_keyboard = [["Help", "About"], ["Tools", "Contact"]]
reply_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Choose an option:", reply_markup=reply_markup)

# Commands
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use the buttons or send a message.")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("This is your advanced Telegram bot.")

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if text == "help":
        await update.message.reply_text("Help section.")
    elif text == "about":
        await update.message.reply_text("Built with Python.")
    elif text == "tools":
        await update.message.reply_text("Tools coming soon.")
    elif text == "contact":
        await update.message.reply_text("Contact: yourname")
    else:
        await update.message.reply_text(f"You said: {text}")

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error: {context.error}")

# App
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_error_handler(error_handler)

print("Bot running...")
app.run_polling()
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Get token from environment (Railway will set this)
BOT_TOKEN = os.environ['BOT_TOKEN']

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context):
    await update.message.reply_text("🤖 I'm running 24/7 on Railway!")

async def echo(update: Update, context):
    user_message = update.message.text
    await update.message.reply_text(f"🔊 Echo: {user_message}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    logger.info("Bot starting...")
    app.run_polling()

if __name__ == '__main__':
    main()

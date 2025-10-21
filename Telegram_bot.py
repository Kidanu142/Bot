import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Railway will set this environment variable
BOT_TOKEN = os.environ['BOT_TOKEN']

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context):
    await update.message.reply_text("🤖 Hello! I'm running 24/7 on Railway!")

async def echo(update: Update, context):
    user_message = update.message.text
    await update.message.reply_text(f"🔊 Echo: {user_message}")
    
    # Log the interaction
    logger.info(f"Echoed message from {update.message.from_user.first_name}")

async def error_handler(update: Update, context):
    logger.error(f"Error: {context.error}")

def main():
    logger.info("Starting Telegram Bot...")
    
    # Create bot application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_error_handler(error_handler)
    
    # Start polling
    logger.info("Bot is now running...")
    application.run_polling()

if __name__ == '__main__':
    main()

import os
import json
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("TOKEN")
AUTHORIZED_USER = "viper_5_8"  # Your username

# Store broadcast lists and file history
broadcast_groups = {}  # chat_id -> user_info
file_history = []  # Store sent files for reference

# Admin menu keyboard
admin_keyboard = [
    ["📤 Send File", "📢 Broadcast"],
    ["👥 View Users", "📊 Stats"],
    ["ℹ️ Help"]
]
admin_reply_markup = ReplyKeyboardMarkup(admin_keyboard, resize_keyboard=True)

# User menu keyboard
user_keyboard = [
    ["📁 View Files", "ℹ️ About"],
    ["📞 Contact"]
]
user_reply_markup = ReplyKeyboardMarkup(user_keyboard, resize_keyboard=True)

def is_admin(username: str) -> bool:
    """Check if user is the authorized admin"""
    return username == AUTHORIZED_USER

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username
    
    if is_admin(username):
        await update.message.reply_text(
            f"✅ Welcome back, Master @{username}!\n\n"
            f"📌 **Admin Commands:**\n"
            f"• Send files to users\n"
            f"• Broadcast messages\n"
            f"• View user statistics\n\n"
            f"Use the buttons below:",
            reply_markup=admin_reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"👋 Welcome {user.first_name}!\n\n"
            f"This bot shares files and announcements.\n"
            f"Contact @{AUTHORIZED_USER} for access.\n\n"
            f"Use the buttons below:",
            reply_markup=user_reply_markup
        )
    
    # Track user
    if update.effective_chat.id not in broadcast_groups:
        broadcast_groups[update.effective_chat.id] = {
            'user_id': user.id,
            'username': username,
            'first_name': user.first_name,
            'joined': datetime.now().isoformat()
        }
        save_data()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username
    text = update.message.text
    
    if is_admin(username):
        # Admin commands
        if text == "📤 Send File":
            await update.message.reply_text(
                "📁 **Send File Mode**\n\n"
                "Send me any file (document, photo, video, audio)\n"
                "and I'll forward it to all users.\n\n"
                "Type /cancel to exit.",
                parse_mode='Markdown'
            )
            context.user_data['awaiting_file'] = True
            
        elif text == "📢 Broadcast":
            await update.message.reply_text(
                "📢 **Broadcast Mode**\n\n"
                "Send me a message and I'll broadcast it to all users.\n\n"
                "Type /cancel to exit.",
                parse_mode='Markdown'
            )
            context.user_data['awaiting_broadcast'] = True
            
        elif text == "👥 View Users":
            await view_users(update, context)
            
        elif text == "📊 Stats":
            await show_stats(update, context)
            
        elif text == "ℹ️ Help":
            await admin_help(update, context)
            
        else:
            await update.message.reply_text(
                "Use the buttons below 👇",
                reply_markup=admin_reply_markup
            )
    else:
        # User commands
        if text == "📁 View Files":
            await view_files(update, context)
        elif text == "ℹ️ About":
            await about(update, context)
        elif text == "📞 Contact":
            await contact(update, context)
        else:
            await update.message.reply_text(
                f"Hello {user.first_name}! Use the buttons below 👇",
                reply_markup=user_reply_markup
            )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle files sent by admin"""
    user = update.effective_user
    username = user.username
    
    if not is_admin(username):
        await update.message.reply_text("⛔ You're not authorized to send files!")
        return
    
    if not context.user_data.get('awaiting_file'):
        await update.message.reply_text("⚠️ First press 'Send File' button to upload files.")
        return
    
    # Get the file
    file_obj = None
    file_type = None
    
    if update.message.document:
        file_obj = update.message.document
        file_type = "document"
    elif update.message.photo:
        file_obj = update.message.photo[-1]  # Get highest quality
        file_type = "photo"
    elif update.message.video:
        file_obj = update.message.video
        file_type = "video"
    elif update.message.audio:
        file_obj = update.message.audio
        file_type = "audio"
    elif update.message.voice:
        file_obj = update.message.voice
        file_type = "voice"
    
    if not file_obj:
        await update.message.reply_text("❌ Please send a valid file (document, photo, video, or audio).")
        return
    
    # Send confirmation
    await update.message.reply_text(f"✅ File received! Sending to {len(broadcast_groups)} users...")
    
    # Get caption if any
    caption = update.message.caption or "📁 New file from admin"
    
    # Send to all users
    success_count = 0
    failed_users = []
    
    for chat_id, user_info in broadcast_groups.items():
        try:
            if file_type == "document":
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=file_obj.file_id,
                    caption=caption
                )
            elif file_type == "photo":
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=file_obj.file_id,
                    caption=caption
                )
            elif file_type == "video":
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=file_obj.file_id,
                    caption=caption
                )
            elif file_type == "audio":
                await context.bot.send_audio(
                    chat_id=chat_id,
                    audio=file_obj.file_id,
                    caption=caption
                )
            elif file_type == "voice":
                await context.bot.send_voice(
                    chat_id=chat_id,
                    voice=file_obj.file_id,
                    caption=caption
                )
            
            success_count += 1
            
        except Exception as e:
            failed_users.append(user_info.get('username', str(chat_id)))
    
    # Save to history
    file_history.append({
        'file_type': file_type,
        'file_id': file_obj.file_id,
        'caption': caption,
        'timestamp': datetime.now().isoformat(),
        'sent_to': success_count
    })
    save_data()
    
    # Send report
    report = f"✅ **Delivery Report**\n\n"
    report += f"📤 Sent to: {success_count}/{len(broadcast_groups)} users\n"
    if failed_users:
        report += f"❌ Failed: {', '.join(failed_users[:5])}\n"
    
    await update.message.reply_text(report, parse_mode='Markdown')
    context.user_data['awaiting_file'] = False

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast messages from admin"""
    user = update.effective_user
    username = user.username
    
    if not is_admin(username):
        return
    
    if not context.user_data.get('awaiting_broadcast'):
        return
    
    message = update.message.text
    
    if message.lower() == '/cancel':
        context.user_data['awaiting_broadcast'] = False
        await update.message.reply_text("❌ Broadcast cancelled.")
        return
    
    await update.message.reply_text(f"📢 Broadcasting to {len(broadcast_groups)} users...")
    
    success_count = 0
    for chat_id in broadcast_groups.keys():
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📢 **Announcement**\n\n{message}",
                parse_mode='Markdown'
            )
            success_count += 1
        except:
            pass
    
    await update.message.reply_text(
        f"✅ Broadcast complete!\n"
        f"📤 Sent to: {success_count}/{len(broadcast_groups)} users"
    )
    
    context.user_data['awaiting_broadcast'] = False

async def view_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all registered users"""
    if not broadcast_groups:
        await update.message.reply_text("📭 No users registered yet.")
        return
    
    users_list = "👥 **Registered Users**\n\n"
    for i, (chat_id, info) in enumerate(broadcast_groups.items(), 1):
        username = info.get('username', 'N/A')
        first_name = info.get('first_name', 'Unknown')
        users_list += f"{i}. @{username} - {first_name}\n"
        
        if len(users_list) > 4000:
            users_list += "\n... (truncated)"
            break
    
    await update.message.reply_text(users_list, parse_mode='Markdown')

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics"""
    total_users = len(broadcast_groups)
    total_files = len(file_history)
    
    stats = f"📊 **Bot Statistics**\n\n"
    stats += f"👥 Total Users: {total_users}\n"
    stats += f"📁 Files Sent: {total_files}\n"
    stats += f"📅 Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    if file_history:
        stats += f"**Last 5 Files:**\n"
        for file in file_history[-5:]:
            stats += f"• {file['file_type']} - Sent to {file['sent_to']} users\n"
    
    await update.message.reply_text(stats, parse_mode='Markdown')

async def view_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Users view available files"""
    if not file_history:
        await update.message.reply_text("📭 No files have been shared yet.")
        return
    
    keyboard = []
    for i, file in enumerate(file_history[-10:], 1):  # Last 10 files
        keyboard.append([InlineKeyboardButton(
            f"📁 File {i} - {file['file_type']}",
            callback_data=f"get_file_{i}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📁 **Available Files**\n\nSelect a file to download:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file download requests"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("get_file_"):
        index = int(query.data.split("_")[2]) - 1
        if 0 <= index < len(file_history):
            file_info = file_history[-(index+1)]  # Get from end
            file_type = file_info['file_type']
            file_id = file_info['file_id']
            caption = file_info['caption']
            
            try:
                if file_type == "document":
                    await query.message.reply_document(
                        document=file_id,
                        caption=caption
                    )
                elif file_type == "photo":
                    await query.message.reply_photo(
                        photo=file_id,
                        caption=caption
                    )
                elif file_type == "video":
                    await query.message.reply_video(
                        video=file_id,
                        caption=caption
                    )
                elif file_type == "audio":
                    await query.message.reply_audio(
                        audio=file_id,
                        caption=caption
                    )
                elif file_type == "voice":
                    await query.message.reply_voice(
                        voice=file_id,
                        caption=caption
                    )
            except Exception as e:
                await query.message.reply_text("❌ Failed to load file. It might be expired.")
        else:
            await query.message.reply_text("❌ File not found.")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """About command for users"""
    await update.message.reply_text(
        f"🤖 **About This Bot**\n\n"
        f"This bot is managed by @{AUTHORIZED_USER}\n\n"
        f"📌 **Features:**\n"
        f"• Receive files from admin\n"
        f"• Get announcements\n"
        f"• View shared files\n\n"
        f"📞 Contact: @{AUTHORIZED_USER}",
        parse_mode='Markdown'
    )

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Contact admin"""
    await update.message.reply_text(
        f"📞 **Contact Admin**\n\n"
        f"Username: @{AUTHORIZED_USER}\n\n"
        f"Feel free to reach out for any questions!",
        parse_mode='Markdown'
    )

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help for admin"""
    help_text = (
        "ℹ️ **Admin Commands Guide**\n\n"
        "📤 **Send File** - Upload files to share with all users\n"
        "   • Documents\n"
        "   • Photos\n"
        "   • Videos\n"
        "   • Audio\n\n"
        "📢 **Broadcast** - Send text messages to all users\n\n"
        "👥 **View Users** - See list of registered users\n\n"
        "📊 **Stats** - View bot statistics\n\n"
        "⚠️ **Note:** All files and broadcasts go to ALL users instantly."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    if 'awaiting_file' in context.user_data:
        context.user_data['awaiting_file'] = False
        await update.message.reply_text("❌ File upload cancelled.")
    if 'awaiting_broadcast' in context.user_data:
        context.user_data['awaiting_broadcast'] = False
        await update.message.reply_text("❌ Broadcast cancelled.")

def save_data():
    """Save broadcast groups and file history to file"""
    data = {
        'broadcast_groups': broadcast_groups,
        'file_history': file_history
    }
    try:
        with open('bot_data.json', 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving data: {e}")

def load_data():
    """Load saved data"""
    global broadcast_groups, file_history
    if os.path.exists('bot_data.json'):
        try:
            with open('bot_data.json', 'r') as f:
                data = json.load(f)
                broadcast_groups = data.get('broadcast_groups', {})
                file_history = data.get('file_history', [])
                # Convert string keys back to int
                broadcast_groups = {int(k): v for k, v in broadcast_groups.items()}
        except Exception as e:
            print(f"Error loading data: {e}")

# Main execution
def main():
    # Load saved data
    load_data()
    
    # Create application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_message
    ))
    application.add_handler(MessageHandler(
        filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE,
        handle_file
    ))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Error handler
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f"Error: {context.error}")
    
    application.add_error_handler(error_handler)
    
    print("🤖 Bot is running...")
    print(f"👑 Admin: @{AUTHORIZED_USER}")
    print(f"📊 Loaded {len(broadcast_groups)} users")
    application.run_polling()

if __name__ == "__main__":
    main()
import os
import random
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

# Dictionary to store user states
user_states = {}

@app.route('/')
def index():
    return 'Welcome to BlindBuddy!'

@app.route('/logs')
def logs():
    try:
        with open('chatlog.txt', 'r') as f:
            logs = f.read()
        return logs, 200
    except FileNotFoundError:
        return 'No logs available.', 404

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Welcome! Type /pair to start chatting with a stranger.')

async def pair(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_states[user_id] = 'waiting'
    waiting_users = [user for user, state in user_states.items() if state == 'waiting' and user != user_id]
    if waiting_users:
        other_user = random.choice(waiting_users)
        user_states[user_id] = other_user
        user_states[other_user] = user_id
        await context.bot.send_message(chat_id=user_id, text="You've been paired! Start chatting.")
        await context.bot.send_message(chat_id=other_user, text="You've been paired! Start chatting.")
    else:
        await update.message.reply_text('Waiting for a stranger to join...')

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id in user_states and user_states[user_id] != 'waiting':
        other_user_id = user_states[user_id]
        message = update.message.text or update.message.caption or ""
        try:
            if update.message.photo:
                photo_file = await update.message.photo[-1].get_file()
                await context.bot.send_photo(chat_id=other_user_id, photo=photo_file.file_id)
                message += " [Photo]"
            elif update.message.document and update.message.document.mime_type in ['image/gif', 'video/mp4', 'video/quicktime']:
                document_file = await update.message.document.get_file()
                await context.bot.send_document(chat_id=other_user_id, document=document_file.file_id)
                message += " [Document]"
            elif update.message.sticker:
                await context.bot.send_sticker(chat_id=other_user_id, sticker=update.message.sticker.file_id)
                message += " [Sticker]"
            elif update.message.video:
                video_file = await update.message.video.get_file()
                await context.bot.send_video(chat_id=other_user_id, video=video_file.file_id)
                message += " [Video]"
            else:  # Text message
                await context.bot.send_message(chat_id=other_user_id, text=update.message.text)
            with open("chatlog.txt", "a") as log_file:
                log_file.write(f"User {user_id} to {other_user_id}: {message}\n")
        except Exception as e:
            logging.error(f"Error sending message: {e}")
    else:
        await update.message.reply_text('Type /pair to start chatting with a stranger.')

def run_flask():
    app.run(host='0.0.0.0', port=5000)

def main() -> None:
    token = os.getenv("BOT_API_TOKEN")  # Replace with your actual bot token
    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pair", pair))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_handler))

    # Run Flask app in a separate thread
    Thread(target=run_flask).start()
    application.run_polling()

if __name__ == '__main__':
    main()

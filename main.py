import os
import random
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from keep_alive import keep_alive  # Import the keep_alive function

# Set up logging
logging.basicConfig(level=logging.INFO)

# Dictionary to store user states
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcomes users and guides them to start chatting."""
    await update.message.reply_text('Welcome! Type /pair to start chatting with a stranger.')

async def pair(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Initiates pairing logic for users to chat anonymously."""
    user_id = update.message.from_user.id
    user_states[user_id] = 'waiting'

    # Find another user waiting to be paired
    waiting_users = [user for user, state in user_states.items() if state == 'waiting' and user != user_id]
    if waiting_users:
        try:
            other_user = random.choice(waiting_users)
            user_states[user_id] = other_user
            user_states[other_user] = user_id

            await context.bot.send_message(chat_id=user_id, text="You've been paired! Start chatting.")
            await context.bot.send_message(chat_id=other_user, text="You've been paired! Start chatting.")
        except Exception as e:
            logging.error(f"Error during pairing: {e}")
            await update.message.reply_text("An error occurred while pairing. Please try again.")
    else:
        await update.message.reply_text('Waiting for a stranger to join...')

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles all incoming messages, including text, media (photos, documents - GIFs and videos)."""
    user_id = update.message.from_user.id

    if user_id in user_states and user_states[user_id] != 'waiting':
        other_user_id = user_states[user_id]

        try:
            if update.message.photo:
                photo_file = await update.message.photo[-1].get_file()
                await context.bot.send_photo(chat_id=other_user_id, photo=photo_file.file_id)
            elif update.message.document and update.message.document.mime_type in ['image/gif', 'video/mp4', 'video/quicktime']:
                document_file = await update.message.document.get_file()
                await context.bot.send_document(chat_id=other_user_id, document=document_file.file_id)
            elif update.message.sticker:
                await context.bot.send_sticker(chat_id=other_user_id, sticker=update.message.sticker.file_id)
            elif update.message.video:
                video_file = await update.message.video.get_file()
                await context.bot.send_video(chat_id=other_user_id, video=video_file.file_id)
            else:  # Text message
                await context.bot.send_message(chat_id=other_user_id, text=update.message.text)
        except Exception as e:
            logging.error(f"Error sending message: {e}")
    else:
        await update.message.reply_text('Type /pair to start chatting with a stranger.')

def main() -> None:
    token = os.getenv("BOT_API_TOKEN")  # Replace with your actual bot token
    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pair", pair))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_handler))  # Handle all non-command messages

    keep_alive()  # Start the keep_alive server
    application.run_polling()

if __name__ == '__main__':
    main()

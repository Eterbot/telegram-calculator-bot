import logging
import os
import re
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CopyTextButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Configuration
TOKEN = os.getenv("BOT_TOKEN", "8223310359:AAH6yKOS_gsP0sTC3rjG9E871jf0zSGNvPY") # Using the user provided token

def format_number(number):
    """Formats a number with thousand separators."""
    if isinstance(number, (int, float)):
        if isinstance(number, float) and number.is_integer():
            number = int(number)
        return "{:,}".format(number)
    return str(number)

def safe_eval(expr):
    """Safely evaluate a mathematical expression."""
    # Allow only specific characters
    if not re.match(r'^[\d\+\-\*\/\(\)\.\^ ]+$', expr):
        return None
    try:
        # Replace ^ with ** for Python power operator
        clean_expr = expr.replace('^', '**')
        # Use a limited scope for eval
        result = eval(clean_expr, {"__builtins__": None}, {})
        return result
    except Exception:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎉 Welcome from Mixx's Calculator Bot!\n\n"
        "✅ You can now use all calculator commands in DM.\n"
        "📌 Supported operations:\n"
        "➕ Addition (+)\n"
        "➖ Subtraction (-)\n"
        "✖️ Multiplication (*)\n"
        "➗ Division (/)\n"
        "🔢 Parentheses ( )\n"
        "⬆️ Exponentiation (^)\n\n"
        "💡 Example: 2+3*5 or (10+2)^2"
    )
    if update.message:
        await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    expr = update.message.text.strip()
    
    # Check if it looks like a math expression (contains at least one digit)
    if not any(char.isdigit() for char in expr):
        return

    result = safe_eval(expr)
    
    if result is not None:
        formatted_result = format_number(result)
        
        # Format the display text (removed fire emoji as requested)
        display_text = f"<code>{expr} = {formatted_result}</code>"
        
        # Create keyboard with copy and delete buttons
        # Using standard emojis for better compatibility and stability
        keyboard = [
            [
                InlineKeyboardButton(
                    text="Copy", 
                    callback_data=f"copy_{result}"
                ),
                InlineKeyboardButton(
                    text="❌ Delete", 
                    callback_data="delete"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await update.message.reply_text(display_text, reply_markup=reply_markup, parse_mode='HTML')
        except Exception as e:
            logging.error(f"Error sending message: {e}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "delete":
        try:
            await query.message.delete()
        except Exception as e:
            logging.error(f"Error deleting message: {e}")
    elif query.data.startswith("copy_"):
        result_to_copy = query.data.replace("copy_", "")
        await query.answer(text=f"Copied: {result_to_copy}", show_alert=True)

# Flask for keep-alive
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

async def main():
    # Start Flask in a separate thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("Bot is starting...")
    
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        # Keep the bot running
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass

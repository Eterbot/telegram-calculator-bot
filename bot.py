
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('calculator_history.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            expression TEXT,
            result TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_history(user_id, expression, result):
    conn = sqlite3.connect('calculator_history.db')
    c = conn.cursor()
    c.execute("INSERT INTO history (user_id, expression, result) VALUES (?, ?, ?)", (user_id, expression, result))
    conn.commit()
    conn.close()

def get_history(user_id, limit=5):
    conn = sqlite3.connect('calculator_history.db')
    c = conn.cursor()
    c.execute("SELECT expression, result FROM history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
    history = c.fetchall()
    conn.close()
    return history

# Calculator logic
def evaluate_expression(expression):
    try:
        # Basic validation to prevent arbitrary code execution
        if not all(c.isdigit() or c in '+-*/(). ' for c in expression):
            return "Invalid characters in expression."
        result = str(eval(expression))
        return result
    except Exception as e:
        return f"Error: {e}"

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I am a calculator bot. Send me an arithmetic expression (e.g., `2+2` or `(5*3)-1`).\n\n" \
        "You can also use `/history` to see your last calculations."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Send me an arithmetic expression (e.g., `2+2` or `(5*3)-1`).\n\n" \
        "Commands:\n" \
        "/start - Start the bot\n" \
        "/help - Get help message\n" \
        "/history - View your calculation history"
    )

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    history = get_history(user_id)
    if history:
        response = "Your last calculations:\n"
        for expr, res in history:
            response += f"`{expr}` = `{res}`\n"
    else:
        response = "No history found. Start calculating!"
    await update.message.reply_text(response, parse_mode='Markdown')

async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    expression = update.message.text
    user_id = update.effective_user.id
    result = evaluate_expression(expression)

    if not result.startswith("Error") and not result.startswith("Invalid"):
        add_history(user_id, expression, result)

    keyboard = [
        [InlineKeyboardButton("History", callback_data="history")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"Result: `{result}`", reply_markup=reply_markup, parse_mode='Markdown')

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "history":
        user_id = query.from_user.id
        history = get_history(user_id)
        if history:
            response = "Your last calculations:\n"
            for expr, res in history:
                response += f"`{expr}` = `{res}`\n"
        else:
            response = "No history found. Start calculating!"
        await query.edit_message_text(text=response, parse_mode='Markdown')

def main() -> None:
    # Replace with your actual bot token
    TOKEN = "8223310359:AAH6yKOS_gsP0sTC3rjG9E871jf0zSGNvPY"
    application = Application.builder().token(TOKEN).build()

    # Initialize database
    init_db()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, calculate))
    application.add_handler(CallbackQueryHandler(button))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

import os
import logging
from datetime import datetime
from telebot import TeleBot

# 1. Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 2. Initialize Bot Token from Environment Variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables!")

bot = TeleBot(TOKEN)

# Simple in-memory storage (Resets when server restarts. For production, connect a database!)
user_expenses = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🦙 <b>Welcome to LedgerLlama!</b>\n\n"
        "I help you spit out those bad spending habits. Log your expenses quickly using commands:\n\n"
        "<b>Commands:</b>\n"
        "➕ <code>/log [amount] [category/description]</code>\n"
        "📝 <i>Example:</i> <code>/log 4.50 Coffee</code>\n\n"
        "📊 <code>/view</code> — See your logged expenses for today.\n"
        "🧹 <code>/clear</code> — Clear today's log."
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="HTML")

@bot.message_handler(commands=['log'])
def log_expense(message):
    try:
        # Extract the arguments after /log
        args = message.text.split(maxsplit=2)
        if len(args) < 3:
            bot.send_message(message.chat.id, "❌ <b>Format incorrect.</b> Use: <code>/log [amount] [description]</code>", parse_mode="HTML")
            return
        
        amount_str = args[1]
        description = args[2]
        
        # Validate amount
        amount = float(amount_str)
        user_id = message.from_user.id
        
        if user_id not in user_expenses:
            user_expenses[user_id] = []
            
        timestamp = datetime.now().strftime("%H:%M")
        user_expenses[user_id].append({"amount": amount, "desc": description, "time": timestamp})
        
        bot.send_message(
            message.chat.id, 
            f"✅ <b>Logged!</b>\n💰 <b>Amount:</b> ${amount:.2f}\n📝 <b>For:</b> {description}", 
            parse_mode="HTML"
        )
        logging.info(f"User {user_id} logged ${amount} for {description}")

    except ValueError:
        bot.send_message(message.chat.id, "❌ <b>Error:</b> Please provide a valid number for the amount.", parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error in /log: {e}")
        bot.send_message(message.chat.id, "❌ An error occurred while saving your expense.")

@bot.message_handler(commands=['view'])
def view_expenses(message):
    user_id = message.from_user.id
    expenses = user_expenses.get(user_id, [])
    
    if not expenses:
        bot.send_message(message.chat.id, "🦙 Your ledger is empty today! Use <code>/log</code> to add something.", parse_mode="HTML")
        return
    
    report = "📊 <b>Today's Expenses:</b>\n\n"
    total = 0.0
    for item in expenses:
        report += f"• <code>[{item['time']}]</code> <b>${item['amount']:.2f}</b> — {item['desc']}\n"
        total += item['amount']
        
    report += f"\n📉 <b>Total Spent:</b> ${total:.2f}"
    bot.send_message(message.chat.id, report, parse_mode="HTML")

@bot.message_handler(commands=['clear'])
def clear_expenses(message):
    user_id = message.from_user.id
    if user_id in user_expenses:
        user_expenses[user_id] = []
    bot.send_message(message.chat.id, "🧹 <b>Ledger cleared!</b> Your daily log has been reset.", parse_mode="HTML")

# 3. Start Polling Loop
if __name__ == "__main__":
    logging.info("LedgerLlamaBot is stepping out...")
    # non_stop=True ensures the bot attempts to reconnect if it drops connection
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

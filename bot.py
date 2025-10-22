import os
import dotenv
import requests
import time
from expense_tracker import store_expense, fetch_all_expenses, fetch_monthly_total, format_inr
from ana import process_data
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime

dotenv.load_dotenv()

BOT_TOKEN = os.getenv("bot_token")
AUTHORIZED_CHAT_ID = 5515574299  # Your chat ID

# Store conversation state
user_data = {}

# Base URL for Telegram API
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Helper functions for Telegram API
def send_message(chat_id, text, reply_markup=None, parse_mode='Markdown'):
    """Send a text message"""
    url = f"{BASE_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    response = requests.post(url, json=data)
    return response.json()

def send_photo(chat_id, photo, caption=None):
    """Send a photo"""
    url = f"{BASE_URL}/sendPhoto"
    files = {"photo": photo}
    data = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption
    response = requests.post(url, data=data, files=files)
    return response.json()

def answer_callback_query(callback_query_id):
    """Answer callback query"""
    url = f"{BASE_URL}/answerCallbackQuery"
    data = {"callback_query_id": callback_query_id}
    requests.post(url, json=data)

def get_updates(offset=None):
    """Get updates from Telegram"""
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 30, "offset": offset}
    response = requests.get(url, params=params)
    return response.json()

def create_inline_keyboard(buttons):
    """Create inline keyboard markup"""
    return {"inline_keyboard": buttons}

# Helper function to check authorization
def is_authorized(chat_id):
    return chat_id == AUTHORIZED_CHAT_ID

# Handle /start command
def handle_start(chat_id):
    keyboard = [
        [{"text": "💰 Add Expense", "callback_data": "add_expense"}],
        [{"text": "📊 View All Expenses", "callback_data": "view_expenses"}],
        [{"text": "📈 Monthly Summary", "callback_data": "monthly_summary"}],
        [{"text": "📉 Analytics", "callback_data": "analytics"}],
    ]
    reply_markup = create_inline_keyboard(keyboard)
    
    send_message(
        chat_id,
        "🏦 *Expense Tracker Bot*\n\n"
        "Welcome! Choose an option below:",
        reply_markup=reply_markup
    )

# Handle callback queries (button clicks)
def handle_callback_query(callback_query_id, chat_id, data):
    answer_callback_query(callback_query_id)
    
    if not is_authorized(chat_id):
        send_message(chat_id, "❌ Unauthorized access!")
        return
    
    if data == 'add_expense':
        user_data[chat_id] = {'state': 'waiting_for_expense'}
        send_message(
            chat_id,
            "💰 *Add New Expense*\n\n"
            "Please send expense details in this format:\n"
            "`Category Amount Note`\n\n"
            "Example:\n"
            "`Food 250 Lunch at restaurant`\n"
            "`Transport 50 Auto fare`\n\n"
            "Note is optional!"
        )
    
    elif data == 'view_expenses':
        show_all_expenses(chat_id)
    
    elif data == 'monthly_summary':
        user_data[chat_id] = {'state': 'waiting_for_month'}
        send_message(
            chat_id,
            "📅 *Monthly Summary*\n\n"
            "Please send year and month:\n"
            "`YYYY MM`\n\n"
            "Example: `2025 10`"
        )
    
    elif data == 'analytics':
        show_analytics_menu(chat_id)
    
    elif data == 'ana_category':
        send_category_chart(chat_id)
    
    elif data == 'ana_monthly':
        send_monthly_chart(chat_id)
    
    elif data == 'ana_stats':
        send_statistics(chat_id)
    
    elif data == 'back_menu':
        keyboard = [
            [{"text": "💰 Add Expense", "callback_data": "add_expense"}],
            [{"text": "📊 View All Expenses", "callback_data": "view_expenses"}],
            [{"text": "📈 Monthly Summary", "callback_data": "monthly_summary"}],
            [{"text": "📉 Analytics", "callback_data": "analytics"}],
        ]
        reply_markup = create_inline_keyboard(keyboard)
        send_message(
            chat_id,
            "🏦 *Expense Tracker Bot*\n\nChoose an option:",
            reply_markup=reply_markup
        )

# Show all expenses
def show_all_expenses(chat_id):
    expenses = fetch_all_expenses()
    
    if not expenses:
        send_message(chat_id, "📭 No expenses found!")
        return
    
    # Show last 10 expenses
    text = "📊 *Recent Expenses (Last 10)*\n\n"
    total = 0
    
    for expense in expenses[:10]:
        date = datetime.fromisoformat(expense['time'].split('T')[0]).strftime("%d %b %Y")
        text += f"🗓 {date}\n"
        text += f"📁 {expense['category']}\n"
        text += f"💵 {format_inr(expense['amount'])}\n"
        if expense['note']:
            text += f"📝 {expense['note']}\n"
        text += "━━━━━━━━━━━━━━━━\n"
        total += expense['amount']
    
    text += f"\n*Total (Last 10): {format_inr(total)}*"
    send_message(chat_id, text)

# Show analytics menu
def show_analytics_menu(chat_id):
    keyboard = [
        [{"text": "📊 Category Distribution", "callback_data": "ana_category"}],
        [{"text": "📈 Monthly Trend", "callback_data": "ana_monthly"}],
        [{"text": "📉 Statistics", "callback_data": "ana_stats"}],
        [{"text": "🔙 Back to Menu", "callback_data": "back_menu"}],
    ]
    reply_markup = create_inline_keyboard(keyboard)
    
    send_message(
        chat_id,
        "📈 *Analytics Menu*\n\nChoose a visualization:",
        reply_markup=reply_markup
    )

# Send category distribution chart
def send_category_chart(chat_id):
    try:
        send_message(chat_id, "⏳ Generating category chart...")
        
        all_data = fetch_all_expenses()
        if not all_data:
            send_message(chat_id, "📭 No data available!")
            return
        
        dates, amounts, categories, category_totals, monthly_totals = process_data(all_data)
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(10, 10))
        categories_sorted = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        
        labels = [x[0] for x in categories_sorted[:5]]
        sizes = [x[1] for x in categories_sorted[:5]]
        
        if len(categories_sorted) > 5:
            other_sum = sum(x[1] for x in categories_sorted[5:])
            labels.append('Other')
            sizes.append(other_sum)
        
        colors = ['#2ecc71', '#3498db', '#e74c3c', '#f39c12', '#9b59b6', '#95a5a6']
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors[:len(sizes)])
        ax.set_title('Expense Distribution by Category')
        
        # Save to buffer
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        send_photo(chat_id, buf, caption="📊 Category Distribution")
        
    except Exception as e:
        send_message(chat_id, f"❌ Error generating chart: {str(e)}")

# Send monthly trend chart
def send_monthly_chart(chat_id):
    try:
        send_message(chat_id, "⏳ Generating monthly trend...")
        
        all_data = fetch_all_expenses()
        if not all_data:
            send_message(chat_id, "📭 No data available!")
            return
        
        dates, amounts, categories, category_totals, monthly_totals = process_data(all_data)
        
        # Create line chart
        fig, ax = plt.subplots(figsize=(12, 6))
        months = sorted(monthly_totals.keys())
        values = [monthly_totals[m] for m in months]
        
        ax.plot(months, values, marker='o', linewidth=2, markersize=8)
        ax.set_title('Monthly Expense Trends')
        ax.set_xlabel('Month')
        ax.set_ylabel('Amount (₹)')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        # Save to buffer
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        send_photo(chat_id, buf, caption="📈 Monthly Trend")
        
    except Exception as e:
        send_message(chat_id, f"❌ Error generating chart: {str(e)}")

# Send statistics
def send_statistics(chat_id):
    try:
        all_data = fetch_all_expenses()
        if not all_data:
            send_message(chat_id, "📭 No data available!")
            return
        
        dates, amounts, categories, category_totals, monthly_totals = process_data(all_data)
        
        stats_text = (
            "📊 *EXPENSE STATISTICS*\n\n"
            f"💰 Total Expenses: `{format_inr(sum(amounts))}`\n"
            f"📅 Average Daily: `{format_inr(sum(amounts)/len(amounts))}`\n"
            f"📈 Maximum: `{format_inr(max(amounts))}`\n"
            f"📉 Minimum: `{format_inr(min(amounts))}`\n"
            f"🔢 Transactions: `{len(amounts)}`\n"
            f"🏆 Top Category: `{max(category_totals.items(), key=lambda x: x[1])[0]}`\n"
        )
        
        send_message(chat_id, stats_text)
        
    except Exception as e:
        send_message(chat_id, f"❌ Error generating statistics: {str(e)}")

# Handle text messages
def handle_text_message(chat_id, text):
    if not is_authorized(chat_id):
        send_message(chat_id, "❌ Unauthorized access!")
        return
    
    # Check if user is in a conversation state
    if chat_id in user_data:
        state = user_data[chat_id].get('state')
        
        if state == 'waiting_for_expense':
            handle_expense_input(chat_id, text)
        elif state == 'waiting_for_month':
            handle_month_input(chat_id, text)
    else:
        send_message(chat_id, "Please use /start to see the menu!")

# Handle expense input
def handle_expense_input(chat_id, text):
    try:
        # Parse: Category Amount Note (note is optional)
        parts = text.split(maxsplit=2)
        
        if len(parts) < 2:
            send_message(
                chat_id,
                "❌ Invalid format!\n\n"
                "Use: `Category Amount Note`\n"
                "Example: `Food 250 Lunch`"
            )
            return
        
        category = parts[0]
        amount = float(parts[1])
        note = parts[2] if len(parts) > 2 else ""
        
        store_expense(category, amount, note)
        
        send_message(
            chat_id,
            f"✅ *Expense Added!*\n\n"
            f"📁 Category: {category}\n"
            f"💵 Amount: {format_inr(amount)}\n"
            f"📝 Note: {note if note else 'N/A'}"
        )
        
        # Clear state
        del user_data[chat_id]
        
    except ValueError:
        send_message(chat_id, "❌ Invalid amount! Please enter a valid number.")
    except Exception as e:
        send_message(chat_id, f"❌ Error: {str(e)}")

# Handle month input
def handle_month_input(chat_id, text):
    try:
        parts = text.split()
        if len(parts) != 2:
            send_message(
                chat_id,
                "❌ Invalid format!\n\nUse: `YYYY MM`\nExample: `2025 10`"
            )
            return
        
        year = int(parts[0])
        month = int(parts[1])
        
        if not (1 <= month <= 12):
            send_message(chat_id, "❌ Month must be between 1 and 12!")
            return
        
        total = fetch_monthly_total(year, month)
        
        month_name = datetime(year, month, 1).strftime("%B %Y")
        send_message(
            chat_id,
            f"📅 *{month_name}*\n\n"
            f"💰 Total Expenses: `{format_inr(total if total else 0)}`"
        )
        
        # Clear state
        del user_data[chat_id]
        
    except ValueError:
        send_message(chat_id, "❌ Invalid year or month! Please enter valid numbers.")
    except Exception as e:
        send_message(chat_id, f"❌ Error: {str(e)}")

# Main bot loop
def main():
    print("Starting Expense Tracker Bot...")
    print("Bot is running! Press Ctrl+C to stop.")
    
    last_update_id = None
    
    while True:
        try:
            # Get updates from Telegram
            result = get_updates(last_update_id)
            
            if result.get("ok"):
                updates = result.get("result", [])
                
                for update in updates:
                    last_update_id = update["update_id"] + 1
                    
                    # Handle text messages
                    if "message" in update:
                        message = update["message"]
                        chat_id = message["chat"]["id"]
                        
                        if "text" in message:
                            text = message["text"]
                            
                            if text == "/start":
                                handle_start(chat_id)
                            else:
                                handle_text_message(chat_id, text)
                    
                    # Handle callback queries (button clicks)
                    elif "callback_query" in update:
                        callback_query = update["callback_query"]
                        callback_query_id = callback_query["id"]
                        chat_id = callback_query["message"]["chat"]["id"]
                        data = callback_query["data"]
                        
                        handle_callback_query(callback_query_id, chat_id, data)
            
            time.sleep(0.5)  # Small delay to avoid overwhelming the API
            
        except KeyboardInterrupt:
            print("\nBot stopped by user.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)  # Wait a bit before retrying

if __name__ == "__main__":
    main()
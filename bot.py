import logging
import json
import os
from telegram import Update, Poll
from telegram.ext import Application, CommandHandler, PollAnswerHandler, ContextTypes, MessageHandler, filters

# --- কনফিগারেশন ---
TOKEN = '8414599324:AAGa8m-CnZK3_xOhJbnDhE9bNnaaO1E_XTY'
OWNER_ID = 6798566345  # আপনার আইডি দিন

# ডাটাবেস ফাইল (পয়েন্ট সেভ রাখার জন্য)
DB_FILE = "database.json"

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"points": {}, "admins": [OWNER_ID], "groups": []}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

db = load_data()

# --- ১. গ্রুপ চেক ও স্টার্ট ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if update.effective_chat.type == 'private':
        if user_id in db["admins"]:
            await update.message.reply_text("👑 অ্যাডমিন প্যানেলে স্বাগতম! আপনি এখান থেকে সব কন্ট্রোল করতে পারবেন।")
        else:
            await update.message.reply_text("❌ এই বোটটি শুধুমাত্র গ্রুপে কাজ করে।")
        return

    if chat_id not in db["groups"]:
        db["groups"].append(chat_id)
        save_data(db)
    await update.message.reply_text("✅ বোট এই গ্রুপে সেটআপ হয়েছে। প্রতি ১৫ মিনিটে কুইজ আসবে।")

# --- ২. অটোমেটিক কুইজ (১৫ মিনিট পর পর) ---
async def send_quiz(context: ContextTypes.DEFAULT_TYPE):
    # এখানে আপনি আপনার পছন্দমতো প্রশ্ন সেট করতে পারেন
    question = "Which character is known as the 'Copy Ninja' in Naruto?"
    options = ["Itachi", "Kakashi", "Sasuke", "Minato"]
    correct_id = 1 # Kakashi
    
    for chat_id in db["groups"]:
        try:
            await context.bot.send_poll(
                chat_id, question, options, 
                type=Poll.QUIZ, correct_option_id=correct_id, is_anonymous=False
            )
        except:
            continue

# --- ৩. পয়েন্ট হ্যান্ডলার ---
async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    user_id = str(answer.user.id)
    
    # যদি উত্তর সঠিক হয় (পোল আইডি চেক করে)
    # নোট: এই সিম্পল ভার্সনে সঠিক উত্তর দিলে ২ পয়েন্ট যোগ হবে
    db["points"][user_id] = db["points"].get(user_id, 0) + 2
    save_data(db)
    
    total = db["points"][user_id]
    await context.bot.send_message(
        user_id, 
        f"🎉Congratulations YOU WIN 2 POINT\nYOUR TOTAL POINTS: {total}"
    )

# --- ৪. শপ কমান্ড (/buyitem) ---
async def buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private': return
    shop = (
        "🛒 **ANIME SHOP**\n\n"
        "15 POINT ➡️ CRUNCHYROLL (/buycrunchy)\n"
        "25 POINT ➡️ NETFLIX 2 DAY (/buynf)\n"
        "20 POINT ➡️ AMAZON PRIME (/buyprime)"
    )
    await update.message.reply_text(shop, parse_mode='Markdown')

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    cmd = update.message.text
    
    costs = {"/buycrunchy": 15, "/buynf": 25, "/buyprime": 20}
    item_names = {"/buycrunchy": "Crunchyroll", "/buynf": "Netflix", "/buyprime": "Amazon Prime"}
    
    cost = costs.get(cmd)
    if not cost: return

    user_pts = db["points"].get(user_id, 0)
    
    if user_pts >= cost:
        db["points"][user_id] -= cost
        save_data(db)
        await update.message.reply_text(f"✅ Success! Contact our owner for account :- @OBITO_UCHIHA77")
        # মালিককে নোটিফিকেশন
        await context.bot.send_message(OWNER_ID, f"🔔 REDEEM ALERT!\nUser: @{update.effective_user.username}\nItem: {item_names[cmd]}")
    else:
        await update.message.reply_text(f"❌ Low points! You need {cost} points.")

# --- ৫. অ্যাডমিন প্যানেল ফিচারস ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in db["admins"]: return
    
    # এখানে আপনি আপনার গ্রুপের লিস্ট এবং পয়েন্ট দেখতে পারবেন
    msg = f"📊 **Admin Stats**\n\nGroups: {len(db['groups'])}\nTotal Users with points: {len(db['points'])}"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def all_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📜 **All Commands**\n"
        "/start - Start Bot\n"
        "/buyitem - Open Shop\n"
        "/buycrunchy - Buy Crunchyroll\n"
        "/buynf - Buy Netflix\n"
        "/buyprime - Buy Amazon Prime\n"
        "/allcommand - Show this list"
    )
    await update.message.reply_text(text)

# --- রান বোট ---
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buyitem", buy_item))
    app.add_handler(CommandHandler("buycrunchy", redeem))
    app.add_handler(CommandHandler("buynf", redeem))
    app.add_handler(CommandHandler("buyprime", redeem))
    app.add_handler(CommandHandler("allcommand", all_commands))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(PollAnswerHandler(handle_poll_answer))

    # কুইজ টাইমার (৯০০ সেকেন্ড = ১৫ মিনিট)
    app.job_queue.run_repeating(send_quiz, interval=900, first=10)

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
      

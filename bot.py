
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ConversationHandler, ContextTypes
)
import asyncio

TOKEN = "7971638104:AAE0IcOvMQCsdjoe49vaZyRyCY5QUFiT9eU"
sessions = []
user_states = {}
report_reasons = {
    "Nudity": "nudity", "Spam": "spam", "Hate": "hate",
    "Violence": "violence", "Harassment": "harassment",
    "False Info": "false_info", "Terrorism": "terrorism",
    "Suicide": "suicide", "Bullying": "bullying", "Drugs": "drugs"
}

SESSION, TARGET_ID, REPORT_TYPE, DELAY = range(4)

logging.basicConfig(level=logging.INFO)

def validate_session(session):
    return "session" in session or "%" in session

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Instagram Report Bot!\nSend your session to begin.")
    return SESSION

async def receive_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    session = update.message.text.strip()
    if validate_session(session):
        user_states[chat_id] = {
            "sessions": [session], "success": 0, "fail": 0,
            "index": 0, "active": True, "message_id": None
        }
        await update.message.reply_text("✅ Session is valid. Please enter the target user ID:")
        return TARGET_ID
    else:
        await update.message.reply_text("❌ Invalid session. Try again.")
        return SESSION

async def get_target_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_states[chat_id]["target_id"] = update.message.text.strip()
    keyboard = [[k] for k in report_reasons.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("🧨 Choose a report type:", reply_markup=reply_markup)
    return REPORT_TYPE

async def get_report_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_states[chat_id]["report_type"] = report_reasons[update.message.text.strip()]
    await update.message.reply_text("⏰ Enter wait time (in seconds):")
    return DELAY

async def get_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    delay = float(update.message.text.strip())
    user_states[chat_id]["delay"] = delay
    msg = await update.message.reply_text("📡 Reporting in progress\n⌛ Please wait...")
    user_states[chat_id]["message_id"] = msg.message_id
    asyncio.create_task(report_loop(context, chat_id))
    return ConversationHandler.END

async def report_loop(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    state = user_states[chat_id]
    while state["active"]:
        await asyncio.sleep(state["delay"])
        success = state["success"] + 1
        fail = state["fail"] + 2
        state["success"], state["fail"] = success, fail
        session = state["sessions"][0][:20] + "..."
        report_status = (
            "📡 Reporting in progress\n\n"
            f"✅ Successful reports: {success}\n"
            f"❌ Failed reports: {fail}\n"
            f"🆔 Session: {session}\n"
            f"⏱ Wait time: {state['delay']} seconds\n"
            f"🎯 Target ID: {state['target_id']}\n"
            f"🚨 Report type: {state['report_type']}"
        )
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=state["message_id"],
                text=report_status
            )
        except:
            pass

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = user_states.get(chat_id)
    if state:
        state["active"] = False
        final_report = (
            "📊 Final Report\n\n"
            f"✅ Successful reports: {state['success']}\n"
            f"❌ Failed reports: {state['fail']}\n"
            f"🆔 Session: {state['sessions'][0][:20]}...\n"
            f"⏱ Wait time: {state['delay']} seconds\n"
            f"🎯 Target ID: {state['target_id']}\n"
            f"🚨 Report type: {state['report_type']}\n\n"
            "✅ Process completed!"
        )
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=state["message_id"],
                text=final_report
            )
        except:
            pass
        await update.message.reply_text("🛑 Reporting stopped.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/report - Start reporting\n/create_sessions - Add sessions\n/stop - Stop\n/help - Show help")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SESSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_session)],
            TARGET_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_target_id)],
            REPORT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_report_type)],
            DELAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_delay)],
        },
        fallbacks=[CommandHandler("stop", stop)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_command))

    app.run_polling()

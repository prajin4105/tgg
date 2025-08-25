# commands/gainxp.py
from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import is_admin, gain_xp, get_user

async def gainxp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Usage: <code>/gainxp &lt;amount&gt;</code>", parse_mode="HTML")
        return

    try:
        amount = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Amount must be an integer, e.g., /gainxp 250")
        return

    res = gain_xp(user_id, amount)
    if not res.get("ok"):
        await update.message.reply_text("Failed to update XP. Check sheet columns exist: XP, Level.")
        return

    await update.message.reply_text(
        f"✅ XP updated: +{res['delta']}\n"
        f"📈 XP: {res['xp']}\n"
        f"⭐ Level: {res['level']}"
    )



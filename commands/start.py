# commands/start.py
from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import get_user, register_user
from utils.helpers import update_user_balance, update_user_field
from utils.helpers import claim_daily_reward
import datetime

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or "Player"
    existing = get_user(user_id)
    if existing:
        # Backfill JoinDate if missing for existing users
        if not str(existing.get("JoinDate", "")).strip():
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_user_field(user_id, "JoinDate", now_str)

        # optional: /start reset -> set balance to 1000 for this user
        if context.args and len(context.args) > 0 and str(context.args[0]).lower() == "reset":
            update_user_balance(user_id, 1000)
            updated_user = get_user(user_id) or {"Balance": 1000}
            await update.message.reply_text(
                f"🔄 <b>Balance reset to:</b> {int(updated_user['Balance']):,} Coins",
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            return

        await update.message.reply_text(
            f"👋 <b>Welcome back, {username}!</b>\n"
            f"💰 <b>Balance:</b> {int(existing['Balance']):,} Coins",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        register_user(user_id, username, starting_balance=1000)
        await update.message.reply_text(
            f"👋 <b>Welcome, {username}!</b>\n"
            f"✅ You are registered.\n"
            f"💰 <b>Starting Balance:</b> 1,000 Coins",
            parse_mode="HTML"
        )

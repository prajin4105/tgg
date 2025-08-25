# commands/daily.py
import datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import get_user, claim_daily_reward

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or "Player"

    user = get_user(user_id)
    if not user:
        await update.message.reply_text("You are not registered. Use /start first.", parse_mode="HTML")
        return

    result = claim_daily_reward(user_id, base_reward=500)
    if not result.get("claimed"):
        await update.message.reply_text(
            f"⛔ {result.get('reason','Cannot claim now.')}",
            parse_mode="HTML"
        )
        return

    streak = result.get("streak", 1)
    reward = result.get("reward", 500)
    balance = result.get("balance", 0)
    level = result.get("level", 1)
    xp = result.get("xp", 0)
    xp_gain = result.get("xp_gain", 0)
    await update.message.reply_text(
        f"🎁 <b>Daily Reward Claimed!</b>\n"
        f"────────────────────────\n"
        f"👤 <b>User:</b> {username}\n"
        f"💵 <b>Reward:</b> {reward:,} Coins\n"
        f"🔥 <b>Streak:</b> {streak} day(s)\n"
        f"📈 <b>XP:</b> +{xp_gain:,} (Total {xp:,})  |  <b>Level:</b> {level}\n"
        f"💰 <b>Balance:</b> {balance:,} Coins",
        parse_mode="HTML"
    )



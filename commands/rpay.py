# commands/rpay.py
from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import get_user, repay_active_loan

async def rpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or "Player"

    user = get_user(user_id)
    if not user:
        await update.message.reply_text("You are not registered. Use /start first.")
        return

    res = repay_active_loan(user_id)
    if not res.get("ok"):
        await update.message.reply_text(f"⛔ {res.get('reason','Cannot repay now.')}")
        return

    loan = res["loan"]
    new_balance = res["new_balance"]
    await update.message.reply_text(
        f"✅ <b>Loan Repaid</b>\n"
        f"────────────────\n"
        f"🆔 <b>LoanID:</b> {loan.get('LoanID','-')}\n"
        f"💼 <b>New Balance:</b> {new_balance:,}",
        parse_mode="HTML"
    )



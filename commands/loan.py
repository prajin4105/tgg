# commands/loan.py
from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import get_user, create_loan, get_active_loan

async def loan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or "Player"

    user = get_user(user_id)
    if not user:
        await update.message.reply_text("You are not registered. Use /start first.")
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Usage: <code>/loan &lt;amount&gt;</code>", parse_mode="HTML")
        return

    try:
        amount = int(str(context.args[0]).replace(",", "").strip())
    except ValueError:
        await update.message.reply_text("Amount must be an integer, e.g., /loan 1000")
        return

    res = create_loan(user_id, amount)
    if not res.get("ok"):
        reason = res.get("reason", "Cannot create loan")
        await update.message.reply_text(f"⛔ {reason}")
        return

    loan = res["loan"]
    new_balance = res["new_balance"]
    await update.message.reply_text(
        f"💳 <b>Loan Created</b>\n"
        f"────────────────\n"
        f"👤 <b>User:</b> {username}\n"
        f"🆔 <b>LoanID:</b> {loan['LoanID']}\n"
        f"💵 <b>Amount:</b> {loan['Amount']:,}\n"
        f"📈 <b>Interest:</b> {int(float(loan['InterestRate'])*100)}%\n"
        f"📅 <b>DueDate:</b> {loan['DueDate']}\n"
        f"💰 <b>RepayAmount:</b> {loan['RepayAmount']:,}\n"
        f"💼 <b>New Balance:</b> {new_balance:,}",
        parse_mode="HTML"
    )



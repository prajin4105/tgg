# commands/showloan.py
from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import get_user, get_active_loan, list_loans

async def showloan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or "Player"

    user = get_user(user_id)
    if not user:
        await update.message.reply_text("You are not registered. Use /start first.")
        return

    active = get_active_loan(user_id)
    history = list_loans(user_id, limit=5)

    if not active and not history:
        await update.message.reply_text("No loans found.")
        return

    lines = []
    if active:
        lines.append("<b>Active Loan</b>")
        lines.append(f"🆔 LoanID: {active.get('LoanID','-')}")
        lines.append(f"💵 Amount: {int(active.get('Amount',0)):,}")
        lines.append(f"💰 Repay: {int(active.get('RepayAmount',0)):,}")
        lines.append(f"📅 Due: {active.get('DueDate','-')}")
        lines.append("")

    if history:
        lines.append("<b>Recent Loans</b>")
        for r in history:
            lines.append(f"{r.get('LoanID','-')} | {r.get('Status','-')} | {r.get('RepayAmount','-')} | {r.get('DueDate','-')}")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")



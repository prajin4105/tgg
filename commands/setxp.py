# commands/setxp.py
from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import is_admin, resolve_user_id, set_user_xp, get_user

def _get_target_from_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.reply_to_message and update.message.reply_to_message.from_user:
        return update.message.reply_to_message.from_user.id
    return None

async def setxp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller_id = update.effective_user.id
    text_cmd = update.message.text if update.message and update.message.text else "/setxp"

    if not is_admin(caller_id):
        await update.message.reply_text(f"{text_cmd}\nYou are not authorized to use this command.")
        return

    # Usage: /setxp <username_or_id> <amount> OR reply to a user and /setxp <amount>
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(f"{text_cmd}\nUsage: /setxp <username_or_id> <amount> (or reply with /setxp <amount>)")
        return

    reply_target_id = _get_target_from_context(update, context)
    if reply_target_id is not None:
        if len(context.args) < 1:
            await update.message.reply_text(f"{text_cmd}\nUsage (reply): /setxp <amount>")
            return
        target_id = reply_target_id
        amount_arg = context.args[0]
    else:
        if len(context.args) < 2:
            await update.message.reply_text(f"{text_cmd}\nUsage: /setxp <username_or_id> <amount>")
            return
        identifier = context.args[0]
        amount_arg = context.args[1]
        target_id = resolve_user_id(identifier)
        if not target_id:
            await update.message.reply_text(f"{text_cmd}\nUser not found. Provide valid username or numeric ID.")
            return

    # allow comma-separated numbers
    try:
        cleaned = amount_arg.replace(",", "").strip()
        amount = int(cleaned)
    except ValueError:
        await update.message.reply_text(f"{text_cmd}\nAmount must be an integer.")
        return

    res = set_user_xp(target_id, amount)
    if not res.get("ok"):
        await update.message.reply_text(f"{text_cmd}\nFailed to set XP. Ensure columns XP and Level exist.")
        return

    user = get_user(target_id)
    name = user.get("Username", str(target_id)) if user else str(target_id)
    await update.message.reply_text(
        f"{text_cmd}\n✅ Set {name}'s XP to {res['xp']:,} | Level {res['level']}",
        reply_to_message_id=update.message.message_id
    )



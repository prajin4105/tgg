# commands/setcoin.py
from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import is_admin, resolve_user_id, update_user_balance, get_user

def _get_target_from_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Prefer replied-to message
    if update.message and update.message.reply_to_message and update.message.reply_to_message.from_user:
        return update.message.reply_to_message.from_user.id
    return None

def _parse_int(value: str):
    if value is None:
        raise ValueError("empty")
    cleaned = value.replace(",", "").strip()
    if cleaned.startswith("+") or cleaned.startswith("-"):
        sign = cleaned[0]
        cleaned_digits = cleaned[1:]
        if not cleaned_digits.isdigit():
            raise ValueError("not int")
        return int(sign + cleaned_digits)
    if not cleaned.isdigit():
        raise ValueError("not int")
    return int(cleaned)

async def setcoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller_id = update.effective_user.id
    text_cmd = update.message.text if update.message and update.message.text else "/setcoin"

    if not is_admin(caller_id):
        await update.message.reply_text(f"{text_cmd}\nYou are not authorized to use this command.")
        return

    # Usage: /setcoin <username_or_id> <amount> OR reply to a user and /setcoin <amount>
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(f"{text_cmd}\nUsage: /setcoin <username_or_id> <amount> (or reply with /setcoin <amount>)")
        return

    reply_target_id = _get_target_from_context(update, context)
    if reply_target_id is not None:
        # replied: /setcoin <amount>
        if len(context.args) < 1:
            await update.message.reply_text(f"{text_cmd}\nUsage (reply): /setcoin <amount>")
            return
        target_id = reply_target_id
        amount_arg = context.args[0]
    else:
        # not a reply: /setcoin <identifier> <amount>
        if len(context.args) < 2:
            await update.message.reply_text(f"{text_cmd}\nUsage: /setcoin <username_or_id> <amount>")
            return
        identifier = context.args[0]
        amount_arg = context.args[1]
        target_id = resolve_user_id(identifier)
        if not target_id:
            await update.message.reply_text(f"{text_cmd}\nUser not found. Provide valid username or numeric ID.")
            return

    try:
        amount = _parse_int(amount_arg)
    except ValueError:
        await update.message.reply_text(f"{text_cmd}\nAmount must be an integer.")
        return

    ok = update_user_balance(target_id, amount)
    if not ok:
        await update.message.reply_text(f"{text_cmd}\nFailed to update balance.")
        return

    user = get_user(target_id)
    name = user.get("Username", str(target_id)) if user else str(target_id)
    await update.message.reply_text(f"{text_cmd}\n✅ Set {name}'s balance to {amount:,} Coins", reply_to_message_id=update.message.message_id)



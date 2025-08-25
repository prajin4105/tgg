# commands/makeadmin.py
from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import is_admin, resolve_user_id, add_admin, get_user

async def makeadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller_id = update.effective_user.id
    if not is_admin(caller_id):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Usage: <code>/makeadmin &lt;username_or_id&gt;</code>", parse_mode="HTML")
        return

    identifier = context.args[0]
    target_id = resolve_user_id(identifier)
    if not target_id:
        await update.message.reply_text("User not found in Users sheet. Provide a valid username or numeric ID.")
        return

    # try to fetch username for storage
    user = get_user(target_id)
    username = user.get("Username", "") if user else ""

    ok = add_admin(target_id, username=username, role="admin")
    if not ok:
        await update.message.reply_text("Failed to add admin. Please check the Admins sheet exists and has headers.")
        return

    await update.message.reply_text(f"✅ Added admin: {username or target_id}")



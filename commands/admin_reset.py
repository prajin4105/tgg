# commands/admin_reset.py
import datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import get_user, is_admin, resolve_user_id
from google_sheet import get_worksheet, update_cell

async def reset_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset all user data (admin only)"""
    try:
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
            await update.message.reply_text("❌Nice try, but this button is reserved for the big bosses.")
            return

        if len(context.args) < 1:
            await update.message.reply_text("Usage: <code>/resetall &lt;username_or_id&gt;</code>", parse_mode="HTML")
            return

        target_identifier = context.args[0]
        target_user_id = resolve_user_id(target_identifier)
        
        if not target_user_id:
            await update.message.reply_text(f"❌ User '{target_identifier}' not found.")
            return

        target_user = get_user(target_user_id)
        if not target_user:
            await update.message.reply_text(f"❌ User with ID {target_user_id} not found.")
            return

        # Reset all user data
        ws = get_worksheet("Users")
        headers = ws.row_values(1)
        users = ws.get_all_records()
        
        # Find user row
        target_row_idx = None
        for idx, u in enumerate(users, start=2):
            if str(u.get("UserID")) == str(target_user_id):
                target_row_idx = idx
                break
        
        if not target_row_idx:
            await update.message.reply_text("❌ Error: User row not found in sheet.")
            return

        # Reset all fields to defaults
        reset_values = {
            "Balance": 1000,  # Starting balance
            "XP": 0,
            "Level": 1,
            "TotalBets": 0,
            "LastDaily": "",
            "Streak": 0,
            "Milestone_10000": False,
            "Milestone_20000": False,
            "Milestone_50000": False,
            "Milestone_100000": False,
            "Milestone_1000000": False,
        }

        # Update each field
        for field, value in reset_values.items():
            if field in headers:
                col_idx = headers.index(field) + 1
                cell_ref = f"{chr(64 + col_idx)}{target_row_idx}"
                update_cell("Users", cell_ref, value)

        # Reset loans
        reset_loans(target_user_id)
        
        # Reset betting logs
        reset_betting_logs(target_user_id)
        
        await update.message.reply_text(
            f"🔄 <b>Complete Reset Complete!</b>\n\n"
            f"👤 <b>User:</b> {target_user.get('Username', 'Unknown')}\n"
            f"🆔 <b>ID:</b> {target_user_id}\n"
            f"📊 <b>Reset Fields:</b>\n"
            f"  • Balance → 1,000 coins\n"
            f"  • XP → 0\n"
            f"  • Level → 1\n"
            f"  • Total Bets → 0\n"
            f"  • Daily Streak → 0\n"
            f"  • All Milestones → False\n"
            f"  • Active Loans → Cleared\n"
            f"  • Betting Logs → Cleared\n\n"
            f"✅ User has been completely reset to starting state!",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error during reset: {e}")

async def reset_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset user balance to starting amount (admin only)"""
    try:
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return

        if len(context.args) < 1:
            await update.message.reply_text("Usage: <code>/resetbalance &lt;username_or_id&gt; [amount]</code>", parse_mode="HTML")
            return

        target_identifier = context.args[0]
        target_user_id = resolve_user_id(target_identifier)
        
        if not target_user_id:
            await update.message.reply_text(f"❌ User '{target_identifier}' not found.")
            return

        target_user = get_user(target_user_id)
        if not target_user:
            await update.message.reply_text(f"❌ User with ID {target_user_id} not found.")
            return

        # Get reset amount (default 1000)
        reset_amount = 1000
        if len(context.args) > 1:
            try:
                reset_amount = int(context.args[1])
                if reset_amount < 0:
                    reset_amount = 0
            except ValueError:
                await update.message.reply_text("❌ Invalid amount. Using default 1,000 coins.")
                reset_amount = 1000

        # Update balance
        ws = get_worksheet("Users")
        headers = ws.row_values(1)
        users = ws.get_all_records()
        
        for idx, u in enumerate(users, start=2):
            if str(u.get("UserID")) == str(target_user_id):
                col_idx = headers.index("Balance") + 1
                cell_ref = f"{chr(64 + col_idx)}{idx}"
                update_cell("Users", cell_ref, reset_amount)
                break

        await update.message.reply_text(
            f"💰 <b>Balance Reset Complete!</b>\n\n"
            f"👤 <b>User:</b> {target_user.get('Username', 'Unknown')}\n"
            f"🆔 <b>ID:</b> {target_user_id}\n"
            f"💵 <b>Old Balance:</b> {target_user.get('Balance', 0):,} coins\n"
            f"🔄 <b>New Balance:</b> {reset_amount:,} coins\n\n"
            f"✅ Balance has been reset!",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error during balance reset: {e}")

async def reset_xp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset user XP and level (admin only)"""
    try:
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return

        if len(context.args) < 1:
            await update.message.reply_text("Usage: <code>/resetxp &lt;username_or_id&gt; [xp] [level]</code>", parse_mode="HTML")
            return

        target_identifier = context.args[0]
        target_user_id = resolve_user_id(target_identifier)
        
        if not target_user_id:
            await update.message.reply_text(f"❌ User '{target_identifier}' not found.")
            return

        target_user = get_user(target_user_id)
        if not target_user:
            await update.message.reply_text(f"❌ User with ID {target_user_id} not found.")
            return

        # Get reset values (default 0 XP, level 1)
        reset_xp = 0
        reset_level = 1
        
        if len(context.args) > 1:
            try:
                reset_xp = int(context.args[1])
                if reset_xp < 0:
                    reset_xp = 0
            except ValueError:
                await update.message.reply_text("❌ Invalid XP value. Using default 0.")
                reset_xp = 0

        if len(context.args) > 2:
            try:
                reset_level = int(context.args[2])
                if reset_level < 1:
                    reset_level = 1
            except ValueError:
                await update.message.reply_text("❌ Invalid level value. Using default 1.")
                reset_level = 1

        # Update XP and Level
        ws = get_worksheet("Users")
        headers = ws.row_values(1)
        users = ws.get_all_records()
        
        for idx, u in enumerate(users, start=2):
            if str(u.get("UserID")) == str(target_user_id):
                # Update XP
                if "XP" in headers:
                    col_idx = headers.index("XP") + 1
                    cell_ref = f"{chr(64 + col_idx)}{idx}"
                    update_cell("Users", cell_ref, reset_xp)
                
                # Update Level
                if "Level" in headers:
                    col_idx = headers.index("Level") + 1
                    cell_ref = f"{chr(64 + col_idx)}{idx}"
                    update_cell("Users", cell_ref, reset_level)
                break

        await update.message.reply_text(
            f"⭐ <b>XP Reset Complete!</b>\n\n"
            f"👤 <b>User:</b> {target_user.get('Username', 'Unknown')}\n"
            f"🆔 <b>ID:</b> {target_user_id}\n"
            f"⭐ <b>Old XP:</b> {target_user.get('XP', 0):,}\n"
            f"🔄 <b>New XP:</b> {reset_xp:,}\n"
            f"📊 <b>Old Level:</b> {target_user.get('Level', 1)}\n"
            f"🔄 <b>New Level:</b> {reset_level}\n\n"
            f"✅ XP and Level have been reset!",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error during XP reset: {e}")

async def reset_loan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset user loans (admin only)"""
    try:
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return

        if len(context.args) < 1:
            await update.message.reply_text("Usage: <code>/resetloan &lt;username_or_id&gt;</code>", parse_mode="HTML")
            return

        target_identifier = context.args[0]
        target_user_id = resolve_user_id(target_identifier)
        
        if not target_user_id:
            await update.message.reply_text(f"❌ User '{target_identifier}' not found.")
            return

        target_user = get_user(target_user_id)
        if not target_user:
            await update.message.reply_text(f"❌ User with ID {target_user_id} not found.")
            return

        # Reset loans
        loans_cleared = reset_loans(target_user_id)
        
        await update.message.reply_text(
            f"💳 <b>Loan Reset Complete!</b>\n\n"
            f"👤 <b>User:</b> {target_user.get('Username', 'Unknown')}\n"
            f"🆔 <b>ID:</b> {target_user_id}\n"
            f"🗑️ <b>Loans Cleared:</b> {loans_cleared}\n\n"
            f"✅ All active loans have been cleared!",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error during loan reset: {e}")

async def reset_bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset user betting data (admin only)"""
    try:
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return

        if len(context.args) < 1:
            await update.message.reply_text("Usage: <code>/resetbets &lt;username_or_id&gt;</code>", parse_mode="HTML")
            return

        target_identifier = context.args[0]
        target_user_id = resolve_user_id(target_identifier)
        
        if not target_user_id:
            await update.message.reply_text(f"❌ User '{target_identifier}' not found.")
            return

        target_user = get_user(target_user_id)
        if not target_user:
            await update.message.reply_text(f"❌ User with ID {target_user_id} not found.")
            return

        # Reset betting data
        ws = get_worksheet("Users")
        headers = ws.row_values(1)
        users = ws.get_all_records()
        
        for idx, u in enumerate(users, start=2):
            if str(u.get("UserID")) == str(target_user_id):
                # Reset TotalBets
                if "TotalBets" in headers:
                    col_idx = headers.index("TotalBets") + 1
                    cell_ref = f"{chr(64 + col_idx)}{idx}"
                    update_cell("Users", cell_ref, 0)
                
                # Reset all milestones
                for milestone in [10000, 20000, 50000, 100000, 1000000]:
                    milestone_key = f"Milestone_{milestone}"
                    if milestone_key in headers:
                        col_idx = headers.index(milestone_key) + 1
                        cell_ref = f"{chr(64 + col_idx)}{idx}"
                        update_cell("Users", cell_ref, False)
                break

        # Clear betting logs
        logs_cleared = reset_betting_logs(target_user_id)
        
        await update.message.reply_text(
            f"🎯 <b>Betting Data Reset Complete!</b>\n\n"
            f"👤 <b>User:</b> {target_user.get('Username', 'Unknown')}\n"
            f"🆔 <b>ID:</b> {target_user_id}\n"
            f"📊 <b>Total Bets:</b> 0\n"
            f"🎁 <b>All Milestones:</b> Reset\n"
            f"🗑️ <b>Betting Logs Cleared:</b> {logs_cleared}\n\n"
            f"✅ Betting data has been completely reset!",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error during betting reset: {e}")

async def reset_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset user daily claim data (admin only)"""
    try:
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return

        if len(context.args) < 1:
            await update.message.reply_text("Usage: <code>/resetdaily &lt;username_or_id&gt;</code>", parse_mode="HTML")
            return

        target_identifier = context.args[0]
        target_user_id = resolve_user_id(target_identifier)
        
        if not target_user_id:
            await update.message.reply_text(f"❌ User '{target_identifier}' not found.")
            return

        target_user = get_user(target_user_id)
        if not target_user:
            await update.message.reply_text(f"❌ User with ID {target_user_id} not found.")
            return

        # Reset daily data
        ws = get_worksheet("Users")
        headers = ws.row_values(1)
        users = ws.get_all_records()
        
        for idx, u in enumerate(users, start=2):
            if str(u.get("UserID")) == str(target_user_id):
                # Reset LastDaily
                if "LastDaily" in headers:
                    col_idx = headers.index("LastDaily") + 1
                    cell_ref = f"{chr(64 + col_idx)}{idx}"
                    update_cell("Users", cell_ref, "")
                
                # Reset Streak
                if "Streak" in headers:
                    col_idx = headers.index("Streak") + 1
                    cell_ref = f"{chr(64 + col_idx)}{idx}"
                    update_cell("Users", cell_ref, 0)
                break

        await update.message.reply_text(
            f"📅 <b>Daily Data Reset Complete!</b>\n\n"
            f"👤 <b>User:</b> {target_user.get('Username', 'Unknown')}\n"
            f"🆔 <b>ID:</b> {target_user_id}\n"
            f"📅 <b>Last Daily:</b> Reset\n"
            f"🔥 <b>Streak:</b> 0\n\n"
            f"✅ Daily claim data has been reset!",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error during daily reset: {e}")

def reset_loans(user_id: int) -> int:
    """Reset all loans for a user. Returns number of loans cleared."""
    try:
        ws = get_worksheet("Logs_Loan")
        headers = ws.row_values(1)
        records = ws.get_all_records()
        
        loans_cleared = 0
        for idx, record in enumerate(records, start=2):
            if str(record.get("UserID")) == str(user_id) and str(record.get("Status", "")).lower() == "active":
                # Mark loan as cleared
                if "Status" in headers:
                    col_idx = headers.index("Status") + 1
                    cell_ref = f"{chr(64 + col_idx)}{idx}"
                    update_cell("Logs_Loan", cell_ref, "Cleared")
                    loans_cleared += 1
        
        return loans_cleared
    except Exception as e:
        print(f"Error resetting loans: {e}")
        return 0

def reset_betting_logs(user_id: int) -> int:
    """Reset betting logs for a user. Returns number of logs cleared."""
    try:
        logs_cleared = 0
        
        # Clear logs from different betting games
        game_sheets = ["Logs_Aviator", "Logs_Spin", "Logs_RPS", "Logs_BetRewards"]
        
        for sheet_name in game_sheets:
            try:
                ws = get_worksheet(sheet_name)
                headers = ws.row_values(1)
                records = ws.get_all_records()
                
                # Find and clear user's logs
                for idx, record in enumerate(records, start=2):
                    if str(record.get("UserID")) == str(user_id):
                        # Clear the log by setting UserID to empty
                        if "UserID" in headers:
                            col_idx = headers.index("UserID") + 1
                            cell_ref = f"{chr(64 + col_idx)}{idx}"
                            update_cell(sheet_name, cell_ref, "")
                            logs_cleared += 1
            except Exception as e:
                print(f"Error clearing {sheet_name}: {e}")
                continue
        
        return logs_cleared
    except Exception as e:
        print(f"Error resetting betting logs: {e}")
        return 0

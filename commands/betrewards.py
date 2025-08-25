# commands/betrewards.py
import datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import get_user, update_user_balance, update_user_field, gain_xp
from google_sheet import append_row, get_worksheet, update_cell

# Default betting reward milestones - can be modified via admin commands
DEFAULT_BETTING_MILESTONES = [
    {"threshold": 10000, "reward": 1000, "xp": 100, "description": "10K Betting Milestone", "active": True},
    {"threshold": 20000, "reward": 2500, "xp": 250, "description": "20K Betting Milestone", "active": True},
    {"threshold": 50000, "reward": 7500, "xp": 500, "description": "50K Betting Milestone", "active": True},
    {"threshold": 100000, "reward": 20000, "xp": 1000, "description": "100K Betting Milestone", "active": True},
    {"threshold": 1000000, "reward": 500000, "xp": 10000, "description": "1M Betting Milestone", "active": True},
]

def get_betting_milestones():
    """Get betting milestones from the BettingRewards sheet or use defaults"""
    try:
        ws = get_worksheet("BettingRewards")
        records = ws.get_all_records()
        if records:
            milestones = []
            for record in records:
                if record.get("Active", True):  # Only include active milestones
                    milestones.append({
                        "threshold": int(record.get("Threshold", 0)),
                        "reward": int(record.get("Reward", 0)),
                        "xp": int(record.get("XP", 0)),
                        "description": record.get("Description", ""),
                        "active": record.get("Active", True)
                    })
            # Sort by threshold
            milestones.sort(key=lambda x: x["threshold"])
            return milestones
        else:
            # Initialize default milestones in the sheet
            initialize_betting_rewards_sheet()
            return DEFAULT_BETTING_MILESTONES
    except Exception as e:
        print(f"Error getting betting milestones: {e}")
        # Return defaults if sheet doesn't exist yet
        return DEFAULT_BETTING_MILESTONES

def initialize_betting_rewards_sheet():
    """Initialize the BettingRewards sheet with default milestones"""
    try:
        ws = get_worksheet("BettingRewards")
        # Clear existing data
        ws.clear()
        
        # Add headers
        headers = ["Threshold", "Reward", "XP", "Description", "Active", "LastUpdated"]
        ws.append_row(headers)
        
        # Add default milestones
        for milestone in DEFAULT_BETTING_MILESTONES:
            row = [
                milestone["threshold"],
                milestone["reward"],
                milestone["xp"],
                milestone["description"],
                milestone["active"],
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]
            ws.append_row(row)
        
        print("BettingRewards sheet initialized with default milestones")
    except Exception as e:
        print(f"Error initializing BettingRewards sheet: {e}")

def ensure_logs_sheet_exists():
    """Ensure the Logs_BetRewards sheet exists"""
    try:
        ws = get_worksheet("Logs_BetRewards")
        # Try to get headers to see if sheet exists
        headers = ws.row_values(1)
        if not headers:
            # Initialize the sheet
            headers = ["RewardID", "UserID", "Username", "Threshold", "CoinsAwarded", "XPAwarded", "Timestamp"]
            ws.append_row(headers)
            print("Logs_BetRewards sheet initialized")
    except Exception as e:
        print(f"Error ensuring Logs_BetRewards sheet exists: {e}")

def safe_append_log(sheet_name, row_data):
    """Safely append a row to a sheet, creating it if it doesn't exist"""
    try:
        append_row(sheet_name, row_data)
        return True
    except Exception as e:
        print(f"Error appending to {sheet_name}: {e}")
        return False

async def check_betting_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check and claim available betting rewards for the user"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Player"
        user = get_user(user_id)
        
        if not user:
            await update.message.reply_text("You are not registered. Use /start first.", parse_mode="HTML")
            return

        # Get current total bets
        try:
            current_total_bets = int(user.get("TotalBets", 0)) if str(user.get("TotalBets", "")).strip() != "" else 0
        except ValueError:
            current_total_bets = 0

        if current_total_bets == 0:
            await update.message.reply_text("🎯 <b>Betting Rewards</b>\n\nYou haven't placed any bets yet. Start betting to earn milestone rewards!", parse_mode="HTML")
            return

        # Get current milestones
        milestones = get_betting_milestones()
        
        # Check for available rewards
        available_rewards = []
        total_reward = 0
        total_xp = 0
        
        for milestone in milestones:
            if current_total_bets >= milestone["threshold"]:
                # Check if this milestone was already claimed
                milestone_key = f"Milestone_{milestone['threshold']}"
                if not user.get(milestone_key, False):
                    available_rewards.append(milestone)
                    total_reward += milestone["reward"]
                    total_xp += milestone["xp"]

        if not available_rewards:
            # Show next milestone progress
            next_milestone = None
            for milestone in milestones:
                if current_total_bets < milestone["threshold"]:
                    next_milestone = milestone
                    break
            
            if next_milestone:
                remaining = next_milestone["threshold"] - current_total_bets
                progress_percent = (current_total_bets / next_milestone["threshold"]) * 100
                
                await update.message.reply_text(
                    f"🎯 <b>Betting Rewards</b>\n\n"
                    f"📊 <b>Total Bets:</b> {current_total_bets:,}\n"
                    f"🎁 <b>Next Milestone:</b> {next_milestone['threshold']:,} ({next_milestone['description']})\n"
                    f"📈 <b>Progress:</b> {progress_percent:.1f}%\n"
                    f"⏳ <b>Remaining:</b> {remaining:,}",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(
                    f"🎯 <b>Betting Rewards</b>\n\n"
                    f"🏆 <b>Congratulations!</b>\n"
                    f"📊 <b>Total Bets:</b> {current_total_bets:,}\n"
                    f"You've reached all betting milestones!",
                    parse_mode="HTML"
                )
            return

        # Claim available rewards
        current_balance = int(user.get("Balance", 0))
        new_balance = current_balance + total_reward
        
        # Update balance
        if not update_user_balance(user_id, new_balance):
            await update.message.reply_text("❌ Error updating balance. Please try again later.")
            return

        # Mark milestones as claimed and add XP
        for milestone in available_rewards:
            milestone_key = f"Milestone_{milestone['threshold']}"
            update_user_field(user_id, milestone_key, True)
            
            # Add XP
            xp_result = gain_xp(user_id, milestone["xp"])
            
            # Log the reward claim
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            safe_append_log("Logs_BetRewards", [
                f"REW-{milestone['threshold']}",
                str(user_id),
                username,
                milestone["threshold"],
                milestone["reward"],
                milestone["xp"],
                timestamp
            ])

        # Send success message
        reward_text = "\n".join([f"🎁 {milestone['description']}: +{milestone['reward']:,} coins, +{milestone['xp']} XP" for milestone in available_rewards])
        
        await update.message.reply_text(
            f"🎉 <b>Betting Rewards Claimed!</b>\n\n"
            f"{reward_text}\n\n"
            f"💰 <b>Total Reward:</b> +{total_reward:,} coins\n"
            f"⭐ <b>Total XP:</b> +{total_xp}\n"
            f"📊 <b>New Balance:</b> {new_balance:,} coins\n"
            f"🎯 <b>Total Bets:</b> {current_total_bets:,}",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

async def betting_rewards_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show information about available betting rewards"""
    try:
        user_id = update.effective_user.id
        user = get_user(user_id)
        
        if not user:
            await update.message.reply_text("You are not registered. Use /start first.", parse_mode="HTML")
            return

        # Get current total bets
        try:
            current_total_bets = int(user.get("TotalBets", 0)) if str(user.get("TotalBets", "")).strip() != "" else 0
        except ValueError:
            current_total_bets = 0

        # Get current milestones
        milestones = get_betting_milestones()
        
        # Build milestone info
        milestone_info = []
        for milestone in milestones:
            milestone_key = f"Milestone_{milestone['threshold']}"
            claimed = user.get(milestone_key, False)
            
            if claimed:
                status = "✅ Claimed"
            elif current_total_bets >= milestone["threshold"]:
                status = "🎁 Available"
            else:
                status = "🔒 Locked"
            
            milestone_info.append(
                f"{milestone['description']}:\n"
                f"  💰 +{milestone['reward']:,} coins, +{milestone['xp']} XP\n"
                f"  📊 {milestone['threshold']:,} bets required\n"
                f"  {status}"
            )

        milestone_text = "\n\n".join(milestone_info)
        
        await update.message.reply_text(
            f"🎯 <b>Betting Rewards System</b>\n\n"
            f"📊 <b>Your Total Bets:</b> {current_total_bets:,}\n\n"
            f"<b>Available Milestones:</b>\n{milestone_text}\n\n"
            f"💡 <b>Tip:</b> Use /checkrewards to claim available rewards!",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

async def show_rewards_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the current betting rewards table (admin only)"""
    try:
        user_id = update.effective_user.id
        from utils.helpers import is_admin
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return

        milestones = get_betting_milestones()
        
        table_text = "🎯 <b>Betting Rewards Table</b>\n\n"
        table_text += "| Threshold | Reward | XP | Description | Status |\n"
        table_text += "|-----------|--------|----|-------------|--------|\n"
        
        for milestone in milestones:
            status = "✅ Active" if milestone["active"] else "❌ Inactive"
            table_text += f"| {milestone['threshold']:,} | {milestone['reward']:,} | {milestone['xp']} | {milestone['description']} | {status} |\n"
        
        table_text += "\n💡 <b>Admin Commands:</b>\n"
        table_text += "• /addmilestone &lt;threshold&gt; &lt;reward&gt; &lt;xp&gt; &lt;description&gt;\n"
        table_text += "• /editmilestone &lt;threshold&gt; &lt;field&gt; &lt;value&gt;\n"
        table_text += "• /deletemilestone &lt;threshold&gt;\n"
        table_text += "• /togglemilestone &lt;threshold&gt;\n"
        
        await update.message.reply_text(table_text, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

async def add_milestone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a new betting milestone (admin only)"""
    try:
        user_id = update.effective_user.id
        from utils.helpers import is_admin
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return

        if len(context.args) < 4:
            await update.message.reply_text("Usage: <code>/addmilestone &lt;threshold&gt; &lt;reward&gt; &lt;xp&gt; &lt;description&gt;</code>", parse_mode="HTML")
            return

        try:
            threshold = int(context.args[0])
            reward = int(context.args[1])
            xp = int(context.args[2])
            description = " ".join(context.args[3:])
        except ValueError:
            await update.message.reply_text("❌ Invalid numbers. Use: <code>/addmilestone 15000 3000 300 15K Betting Milestone</code>", parse_mode="HTML")
            return

        # Add to sheet
        try:
            ws = get_worksheet("BettingRewards")
            row = [threshold, reward, xp, description, True, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
            ws.append_row(row)
            
            await update.message.reply_text(
                f"✅ <b>New Milestone Added!</b>\n\n"
                f"🎯 <b>Threshold:</b> {threshold:,}\n"
                f"💰 <b>Reward:</b> {reward:,} coins\n"
                f"⭐ <b>XP:</b> {xp}\n"
                f"📝 <b>Description:</b> {description}",
                parse_mode="HTML"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error adding milestone: {e}")
            
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

async def edit_milestone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit an existing betting milestone (admin only)"""
    try:
        user_id = update.effective_user.id
        from utils.helpers import is_admin
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return

        if len(context.args) < 3:
            await update.message.reply_text("Usage: <code>/editmilestone &lt;threshold&gt; &lt;field&gt; &lt;value&gt;</code>\n\nFields: reward, xp, description, active", parse_mode="HTML")
            return

        try:
            threshold = int(context.args[0])
            field = context.args[1].lower()
            value = context.args[2]
        except ValueError:
            await update.message.reply_text("❌ Invalid threshold number.")
            return

        if field not in ["reward", "xp", "description", "active"]:
            await update.message.reply_text("❌ Invalid field. Use: reward, xp, description, or active")
            return

        # Update in sheet
        try:
            ws = get_worksheet("BettingRewards")
            records = ws.get_all_records()
            
            for idx, record in enumerate(records, start=2):
                if int(record.get("Threshold", 0)) == threshold:
                    # Convert value based on field type
                    if field == "reward" or field == "xp":
                        try:
                            value = int(value)
                        except ValueError:
                            await update.message.reply_text(f"❌ Invalid {field} value. Must be a number.")
                            return
                    elif field == "active":
                        value = value.lower() in ["true", "1", "yes", "on"]
                    
                    # Update the cell
                    col_idx = {"reward": 2, "xp": 3, "description": 4, "active": 5}.get(field)
                    if col_idx:
                        cell_ref = f"{chr(64 + col_idx)}{idx}"
                        update_cell("BettingRewards", cell_ref, value)
                        
                        await update.message.reply_text(
                            f"✅ <b>Milestone Updated!</b>\n\n"
                            f"🎯 <b>Threshold:</b> {threshold:,}\n"
                            f"📝 <b>Field:</b> {field}\n"
                            f"🔄 <b>New Value:</b> {value}",
                            parse_mode="HTML"
                        )
                        return
            
            await update.message.reply_text(f"❌ Milestone with threshold {threshold:,} not found.")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error updating milestone: {e}")
            
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

async def delete_milestone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a betting milestone (admin only)"""
    try:
        user_id = update.effective_user.id
        from utils.helpers import is_admin
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return

        if len(context.args) < 1:
            await update.message.reply_text("Usage: <code>/deletemilestone &lt;threshold&gt;</code>", parse_mode="HTML")
            return

        try:
            threshold = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid threshold number.")
            return

        # Delete from sheet
        try:
            ws = get_worksheet("BettingRewards")
            records = ws.get_all_records()
            
            for idx, record in enumerate(records, start=2):
                if int(record.get("Threshold", 0)) == threshold:
                    # Delete the row
                    ws.delete_rows(idx)
                    
                    await update.message.reply_text(
                        f"✅ <b>Milestone Deleted!</b>\n\n"
                        f"🎯 <b>Threshold:</b> {threshold:,}\n"
                        f"🗑️ <b>Status:</b> Removed from system",
                        parse_mode="HTML"
                    )
                    return
            
            await update.message.reply_text(f"❌ Milestone with threshold {threshold:,} not found.")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error deleting milestone: {e}")
            
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

async def toggle_milestone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle milestone active status (admin only)"""
    try:
        user_id = update.effective_user.id
        from utils.helpers import is_admin
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return

        if len(context.args) < 1:
            await update.message.reply_text("Usage: <code>/togglemilestone &lt;threshold&gt;</code>", parse_mode="HTML")
            return

        try:
            threshold = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid threshold number.")
            return

        # Toggle in sheet
        try:
            ws = get_worksheet("BettingRewards")
            records = ws.get_all_records()
            
            for idx, record in enumerate(records, start=2):
                if int(record.get("Threshold", 0)) == threshold:
                    current_status = record.get("Active", True)
                    new_status = not current_status
                    
                    # Update the active status
                    cell_ref = f"E{idx}"  # Column E is Active
                    update_cell("BettingRewards", cell_ref, new_status)
                    
                    status_text = "✅ Active" if new_status else "❌ Inactive"
                    
                    await update.message.reply_text(
                        f"🔄 <b>Milestone Status Toggled!</b>\n\n"
                        f"🎯 <b>Threshold:</b> {threshold:,}\n"
                        f"📊 <b>New Status:</b> {status_text}",
                        parse_mode="HTML"
                    )
                    return
            
            await update.message.reply_text(f"❌ Milestone with threshold {threshold:,} not found.")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error toggling milestone: {e}")
            
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

def check_and_give_rewards_automatically(user_id: int, new_total_bets: int):
    """
    This function is called automatically when TotalBets is updated
    to check if any new milestones are reached and give rewards
    """
    try:
        user = get_user(user_id)
        if not user:
            return False

        # Get current milestones
        milestones = get_betting_milestones()
        
        current_balance = int(user.get("Balance", 0))
        total_reward = 0
        total_xp = 0
        claimed_milestones = []

        for milestone in milestones:
            if new_total_bets >= milestone["threshold"]:
                # Check if this milestone was already claimed
                milestone_key = f"Milestone_{milestone['threshold']}"
                if not user.get(milestone_key, False):
                    claimed_milestones.append(milestone)
                    total_reward += milestone["reward"]
                    total_xp += milestone["xp"]

        if claimed_milestones:
            # Update balance automatically
            new_balance = current_balance + total_reward
            update_user_balance(user_id, new_balance)

            # Mark milestones as claimed and add XP
            for milestone in claimed_milestones:
                milestone_key = f"Milestone_{milestone['threshold']}"
                update_user_field(user_id, milestone_key, True)
                gain_xp(user_id, milestone["xp"])

                # Log the automatic reward
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                safe_append_log("Logs_BetRewards", [
                    f"AUTO-{milestone['threshold']}",
                    str(user_id),
                    user.get("Username", "Unknown"),
                    milestone["threshold"],
                    milestone["reward"],
                    milestone["xp"],
                    timestamp
                ])

            return True

        return False

    except Exception as e:
        print(f"Error in automatic reward check: {e}")
        return False

# Initialize sheets when module is imported
try:
    ensure_logs_sheet_exists()
except Exception as e:
    print(f"Warning: Could not initialize Logs_BetRewards sheet: {e}")

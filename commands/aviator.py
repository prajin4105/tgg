# commands/aviator.py
import random
import datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import get_user, update_user_balance, update_user_field
from utils.cooldown import is_on_cooldown, set_cooldown
from google_sheet import append_row

async def aviator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 2:
            await update.message.reply_text("Usage: <code>/aviator &lt;amount&gt; &lt;target_multiplier&gt;</code>", parse_mode="HTML")
            return

        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Player"
        user = get_user(user_id)
        if not user:
            await update.message.reply_text("You are not registered. Use /start first.", parse_mode="HTML")
            return

        # cooldown check
        on_cd, remaining = is_on_cooldown(user_id, "aviator")
        if on_cd:
            mins = remaining // 60
            secs = remaining % 60
            await update.message.reply_text(f"⏳ You can play Aviator again in {mins}m {secs}s.")
            return

        # parse args
        try:
            bet_amount = int(str(context.args[0]).replace(",", "").strip())
        except ValueError:
            await update.message.reply_text("Invalid bet amount. Use a number, e.g. <code>/aviator 500 2.5</code>.", parse_mode="HTML")
            return

        try:
            target_multiplier = float(context.args[1])
            if target_multiplier <= 1.0:
                await update.message.reply_text("Target multiplier must be greater than 1.0x")
                return
        except ValueError:
            await update.message.reply_text("Invalid target multiplier. Use a number like 2.5")
            return

        balance = int(user["Balance"])
        if bet_amount <= 0:
            await update.message.reply_text("Bet must be greater than 0.")
            return
        if bet_amount > balance:
            await update.message.reply_text("❌ Insufficient balance!", parse_mode="HTML")
            return

        # Generate crash point (house edge ~5%)
        crash_point = random.uniform(1.0, 10.0)
        if random.random() < 0.05:  # 5% chance of early crash
            crash_point = random.uniform(1.0, 1.5)

        # Determine result
        if crash_point >= target_multiplier:
            result = "WIN"
            payout = int(bet_amount * target_multiplier)
            result_emoji = "🚀 Crashed at {:.2f}x!".format(crash_point)
        else:
            result = "LOSE"
            payout = 0
            result_emoji = "💥 Crashed at {:.2f}x".format(crash_point)

        new_balance = balance - bet_amount + payout
        updated = update_user_balance(user_id, new_balance)
        if not updated:
            await update.message.reply_text("Error updating balance in sheet. Try again later.")
            return

        # Update TotalBets
        try:
            current_bets = int(user.get("TotalBets", 0)) if str(user.get("TotalBets", "")).strip() != "" else 0
        except ValueError:
            current_bets = 0
        new_total_bets = current_bets + bet_amount
        update_user_field(user_id, "TotalBets", new_total_bets)
        
        # Check for automatic betting rewards
        from commands.betrewards import check_and_give_rewards_automatically
        rewards_given = check_and_give_rewards_automatically(user_id, new_total_bets)
        
        # Show reward notification if any were given
        reward_notification = ""
        if rewards_given:
            user = get_user(user_id)  # Get updated user data
            milestones = []
            for milestone in [10000, 20000, 50000, 100000, 1000000]:
                milestone_key = f"Milestone_{milestone}"
                if user.get(milestone_key, False):
                    milestones.append(milestone)
            
            if milestones:
                reward_notification = f"\n🎉 <b>Milestone Rewards Earned!</b>\n"
                for milestone in milestones:
                    if milestone == 10000:
                        reward_notification += f"🎁 10K Milestone: +1,000 coins + 100 XP\n"
                    elif milestone == 20000:
                        reward_notification += f"🎁 20K Milestone: +2,500 coins + 250 XP\n"
                    elif milestone == 50000:
                        reward_notification += f"🎁 50K Milestone: +7,500 coins + 500 XP\n"
                    elif milestone == 100000:
                        reward_notification += f"🎁 100K Milestone: +20,000 coins + 1,000 XP\n"
                    elif milestone == 1000000:
                        reward_notification += f"🎁 1M Milestone: +500,000 coins + 10,000 XP\n"
                reward_notification += f"💰 <b>Rewards automatically added to your balance!</b>"

        # log the round
        bet_id = f"AVI-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        append_row("Logs_Aviator", [bet_id, str(user_id), bet_amount, target_multiplier, crash_point, result, payout, timestamp])

        # set cooldown
        set_cooldown(user_id, "aviator")

        # pretty HTML reply
        await update.message.reply_text(
            f"✈️ <b>Aviator Crash</b>\n"
            f"─────────────────────────────\n"
            f"👤 <b>Target:</b> {target_multiplier:.2f}x\n"
            f"🔸 <b>Result:</b> {result_emoji}\n"
            f"💵 <b>Bet:</b> {bet_amount:,}  ➜  <b>Payout:</b> {payout:,}\n"
            f"─────────────────────────────\n"
            f"💰 <b>New Balance:</b> {new_balance:,} Coins\n"
            f"📊 <b>Total Bets:</b> {new_total_bets:,}{reward_notification}",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

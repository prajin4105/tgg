# bot.py
import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler
from commands.start import start
from commands.daily import daily
from commands.gainxp import gainxp
from commands.makeadmin import makeadmin
from commands.setcoin import setcoin
from commands.setxp import setxp
from commands.loan import loan
from commands.rpay import rpay
from commands.showloan import showloan
from commands.rps import rps
from commands.aviator import aviator
from commands.spin import spin
from commands.betrewards import (
    check_betting_rewards, 
    betting_rewards_info, 
    show_rewards_table,
    add_milestone,
    edit_milestone,
    delete_milestone,
    toggle_milestone
)
from commands.admin_reset import (
    reset_all,
    reset_balance,
    reset_xp,
    reset_loan,
    reset_bets,
    reset_daily
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", lambda update, ctx: start(update, ctx)))  # quick: reuse start for now or implement separate
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("gainxp", gainxp))
    app.add_handler(CommandHandler("makeadmin", makeadmin))
    app.add_handler(CommandHandler("setcoin", setcoin))
    app.add_handler(CommandHandler("setxp", setxp))
    app.add_handler(CommandHandler("loan", loan))
    app.add_handler(CommandHandler("rpay", rpay))
    app.add_handler(CommandHandler("showloan", showloan))
    app.add_handler(CommandHandler("rps", rps))
    app.add_handler(CommandHandler("aviator", aviator))
    app.add_handler(CommandHandler("spin", spin))
    app.add_handler(CommandHandler("checkrewards", check_betting_rewards))
    app.add_handler(CommandHandler("rewards", betting_rewards_info))
    app.add_handler(CommandHandler("rewards_table", show_rewards_table))
    app.add_handler(CommandHandler("addmilestone", add_milestone))
    app.add_handler(CommandHandler("editmilestone", edit_milestone))
    app.add_handler(CommandHandler("deletemilestone", delete_milestone))
    app.add_handler(CommandHandler("togglemilestone", toggle_milestone))
    app.add_handler(CommandHandler("resetall", reset_all))
    app.add_handler(CommandHandler("resetbalance", reset_balance))
    app.add_handler(CommandHandler("resetxp", reset_xp))
    app.add_handler(CommandHandler("resetloan", reset_loan))
    app.add_handler(CommandHandler("resetbets", reset_bets))
    app.add_handler(CommandHandler("resetdaily", reset_daily))

    print("Bot is running...")
    app.run_polling()

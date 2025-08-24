import logging
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== CONFIGURE THIS ==========
TOKEN = "8491091574:AAFz1Fd2brtqMoeAgwk86eCUttBUgBtP9tQ"   # <-- replace with your bot token
CHANNEL_USERNAME = "@earnwithmmme"         # your public channel username (include @)
REF_LINK = "https://1weaou.life/?p=rn3w"
PROMO_CODE = "EARN250"
# ====================================

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def build_mines_board(mines_count=3, stars_count=5, rows=5, cols=5):
    """Generate a Mines game board with emojis"""
    total = rows * cols
    board = ["🟦"] * total

    # place mines
    mine_positions = random.sample(range(total), mines_count)
    for p in mine_positions:
        board[p] = "💣"

    # place stars in empty spots
    empty_positions = [i for i in range(total) if board[i] == "🟦"]
    star_positions = random.sample(empty_positions, stars_count)
    for p in star_positions:
        board[p] = "⭐️"

    # convert to grid format
    grid = []
    for r in range(rows):
        grid.append("".join(board[r*cols:(r+1)*cols]))
    return "\n".join(grid)

async def is_member(bot, user_id):
    """Check if user is member of channel"""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        status = member.status  # 'creator','administrator','member','left','kicked'
        logger.info("User %s membership status in %s: %s", user_id, CHANNEL_USERNAME, status)
        return status in ("creator", "administrator", "member")
    except Exception as e:
        logger.warning("Membership check failed: %s", e)
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or "there"

    text = (
        f"🔥 *Welcome, {name}!* 🔥\n\n"
        f"🎯 *Start getting Mines predictions now!* \n\n"
        f"💰 *Referral Link:* [Claim Bonus]({REF_LINK})\n"
        f"🎁 *Promo Code:* *{PROMO_CODE}*\n\n"
        f"📢 *Join our VIP channel* for daily picks and updates:\n"
        f"{CHANNEL_USERNAME}\n\n"
        f"➡️ After joining, use /prediction to get a new board."
    )

    keyboard = [
        [InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton("Open Referral Link", url=REF_LINK)],
        [InlineKeyboardButton("Get Prediction", callback_data="new_prediction")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def prediction_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bot = context.bot

    if not await is_member(bot, user.id):
        keyboard = [
            [InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
            [InlineKeyboardButton("Check Again", callback_data="check_join")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = (
            "🚫 *Access Restricted*\n\n"
            "You must *join our Telegram channel* to use this bot.\n\n"
            f"{CHANNEL_USERNAME}\n\n"
            "Tap *Join Channel*, then press *Check Again*."
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        return

    await send_prediction(update.effective_chat.id, bot)

async def send_prediction(chat_id, bot, edit_message=None):
    grid = build_mines_board(mines_count=3, stars_count=5)
    attempts = random.randint(1, 5)

    text = (
        "Confirmed Entry  \n"
        "💣 Mines :  3\n"
        f"💎 Attempt: {attempts} \n"
        "⏳ Validity: 15 Minutes \n\n"
        f"{grid}"
    )

    keyboard = [
        [InlineKeyboardButton("New Prediction", callback_data="new_prediction")],
        [InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if edit_message:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=edit_message.message_id,
                text=text,
                reply_markup=reply_markup
            )
            return
        except Exception as e:
            logger.info("Could not edit message; sending new instead: %s", e)

    await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    bot = context.bot
    user = query.from_user
    await query.answer()

    if query.data == "new_prediction":
        if not await is_member(bot, user.id):
            keyboard = [
                [InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
                [InlineKeyboardButton("Check Again", callback_data="check_join")],
            ]
            await query.edit_message_text(
                text=(
                    "🚫 *Access Restricted*\n\n"
                    "You must *join our Telegram channel* to use this bot.\n\n"
                    f"{CHANNEL_USERNAME}\n\n"
                    "Tap *Join Channel*, then press *Check Again*."
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return

        try:
            await send_prediction(
                chat_id=query.message.chat_id,
                bot=bot,
                edit_message=query.message
            )
        except Exception as e:
            logger.error("Error generating prediction: %s", e)
            await query.answer("Error generating prediction.")

    elif query.data == "check_join":
        if await is_member(bot, user.id):
            await query.answer("You are now a member! ✅")
            await send_prediction(chat_id=query.message.chat_id, bot=bot)
        else:
            await query.answer("Still not a member. Please join the channel first.", show_alert=True)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("prediction", prediction_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_error_handler(error_handler)

    logger.info("Bot started (polling). Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == "__main__":
    main()
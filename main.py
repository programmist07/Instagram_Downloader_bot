import os
import instaloader
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters
import requests

BOT_TOKEN = "7796982583:AAG70u8SP552SbAy3GBGu9W-e0TGaLSEgwc"
CHANNEL_1_ID = "@hikvik"
CHANNEL_2_ID = "@hikvik"


USER_DATA_FILE = 'users_data.txt'

DOWNLOAD_DIR = "dowloads"
os.makedirs(DOWNLOAD_DIR,exist_ok=True)

ADMIN_ID = [6393985738]


def save_user_data(user_id,username):
    with open(USER_DATA_FILE,'a') as file:
        file.write(f"{user_id},@{username}\n")

async def is_subsicribe(user_id: int, channel_id:str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember?chat_id={channel_id}&user_id={user_id}"
    response = requests.get(url).json()
    print(f"Response for {channel_id}: {response}")
    return response.get("ok", False) and response.get("result", {}).get("status") in ("member", "administrator", "creator")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user_data(user.id, user.username)

    link_buttons = [
        [InlineKeyboardButton("Channel 1", url=f"https://t.me/{CHANNEL_1_ID[1:]}")],
        [InlineKeyboardButton("Channel 2", url=f"https://t.me/{CHANNEL_2_ID[1:]}")],
        [InlineKeyboardButton("Verify Subscription", callback_data="verify_subscription")]
    ]

    keyboard = InlineKeyboardMarkup(link_buttons)

    await update.message.reply_text(f"Welcome , {user.first_name}! Please subsicribe to the channels and verify your subscription. ",reply_markup=keyboard)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_ID:
        with open(USER_DATA_FILE, 'r') as file:
            data = file.read()
            await update.message.reply_text(f"User Data:\n {data}")
    else:
        await update.message.reply_text("Access denied")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text
    user = update.effective_user

    if "instagram.com" in link:
        subscribed_channel_1 = await  is_subsicribe(user.id, CHANNEL_1_ID)
        subscribed_channel_2 = await  is_subsicribe(user.id, CHANNEL_2_ID)

        if subscribed_channel_1 and subscribed_channel_2:
            await dowload_instagram_content(context, update, link)
        else:
            await start(update, context)

    else:
        await update.message.reply_text("Please send a valid Instagram link!")

async def dowload_instagram_content(context: ContextTypes.DEFAULT_TYPE, update: Update, link: str):
    try:
        loader = instaloader.Instaloader(download_video_thumbnails=False)
        loader.dirname_pattern = DOWNLOAD_DIR

        shortcode = link.split("/")[-2]
        post = instaloader.Post.from_shortcode(loader.context,shortcode)
        loader.download_post(post, target=DOWNLOAD_DIR)

        for root, _, files in os.walk(DOWNLOAD_DIR):
            for file in files:
                if file.endswith((".mp4", ".jpg", ".jpeg", ".png")):
                    file_path = os.path.join(root, file)
                    with open(file_path, "rb") as media:
                        await update.message.reply_text("Sending downloaded Instagram content...")
                        await context.bot.send_document(chat_id=update.message.chat_id, document=media)
                    os.remove(file_path)
                    return
        await update.message.reply_text("Error: Failed to find the downloaded  file!")
    except Exception as e:
        await update.message.reply_text(f"Failed to download Instagram content: {str(e)}")

async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if query.data == "verify_subscription":
        subscribed_channel_1 = await is_subsicribe(user.id,CHANNEL_1_ID)
        subscribed_channel_2 = await is_subsicribe(user.id,CHANNEL_2_ID)

        if subscribed_channel_1 and subscribed_channel_2:
            await query.edit_message_text("You are successfully subscribed to both channels! You can now send links.")
        else:
            await query.edit_message_text(
                "You need to subscribed to both channels to use the bot.\n"
                "Please subscribe and click 'Verify Subscription' again to continue."
            )

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("admin",admin))
app.add_handler(CallbackQueryHandler(inline_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()












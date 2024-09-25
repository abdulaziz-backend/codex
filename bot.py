import os
import logging
from aiogram import Bot, Dispatcher, Router, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
WEBAPP_URL = os.getenv("WEBAPP_URL")

users = set()
daily_active_users = {}

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

@router.message(Command("start"))
async def start(message: types.Message):
    user = message.from_user
    users.add(user.id)
    daily_active_users[user.id] = datetime.now()

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Subscribe to Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
    keyboard.button(text="Check Subscription", callback_data="check_subscription")

    await message.reply(
        f"Hello {user.full_name}! Please subscribe to our channel to use the bot.",
        reply_markup=keyboard.as_markup()
    )

@router.callback_query(lambda c: c.data == 'check_subscription')
async def process_callback_check_subscription(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    if await check_subscription(user_id):
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Open WebApp", web_app={"url": WEBAPP_URL})
        keyboard.button(text="Channel Link", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
        keyboard.button(text="Back", callback_data="start")

        await callback_query.answer()
        await callback_query.message.edit_text("Welcome! Here are your options:", reply_markup=keyboard.as_markup())
    else:
        await callback_query.answer("Please subscribe to the channel first and then click 'Check Subscription' again.", show_alert=True)

@router.message(Command("help"))
async def help_command(message: types.Message):
    help_text = (
        "This bot is an AI-based translator using ChatGPT-4's API. "
        "To use the bot, please subscribe to our channel and then use the provided buttons. "
        "For any issues, please contact the administrator."
    )
    await message.reply(help_text)

@router.message(Command("admin"))
async def admin_command(message: types.Message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        await message.reply("You are not authorized to use this command.")
        return

    if message.reply_to_message:
        for user_id in users:
            try:
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=message.chat.id,
                    message_id=message.reply_to_message.message_id
                )
            except Exception as e:
                logging.error(f"Failed to send message to user {user_id}: {e}")
        await message.reply("Message broadcasted to all users.")
    else:
        total_users = len(users)
        active_today = sum(1 for last_active in daily_active_users.values() if (datetime.now() - last_active) < timedelta(days=1))
        stats = f"📊 Bot Statistics:\n\n" \
                f"👥 Total Users: {total_users}\n" \
                f"🔥 Daily Active Users: {active_today}"
        await message.reply(stats)

@router.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    daily_active_users[user_id] = datetime.now()

    if not await check_subscription(user_id):
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Subscribe to Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
        keyboard.button(text="Check Subscription", callback_data="check_subscription")
        await message.reply("Please subscribe to our channel to use the bot.", reply_markup=keyboard.as_markup())
        return

    await message.reply("AI translation feature is not implemented in this example.")

async def on_startup(bot: Bot):
    await bot.set_webhook(os.environ.get('WEBHOOK_URL'))

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

def main():
    dp.include_router(router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.run_polling(bot)

if __name__ == '__main__':
    main()
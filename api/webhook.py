from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from bot import dp, bot, on_startup, on_shutdown

async def webhook(request):
    try:
        await SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        ).handle(request)
    except Exception as e:
        print(f"Error processing update: {e}")
    return web.Response(text="OK")

async def on_startup_webhook(app):
    await on_startup(bot)
    webhook_path = "/webhook"
    await bot.set_webhook(f"{os.environ.get('WEBHOOK_URL')}{webhook_path}")

async def on_shutdown_webhook(app):
    await on_shutdown(bot)

def init():
    app = web.Application()
    app.router.add_post("/webhook", webhook)
    app.on_startup.append(on_startup_webhook)
    app.on_shutdown.append(on_shutdown_webhook)
    return app

app = init()

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
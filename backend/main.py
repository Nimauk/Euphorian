import asyncio
import logging
import sys
from backend.core.bot import bot, dp
from backend.handlers import base, music

async def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("bot_run.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Register handlers
    dp.include_router(base.router)
    dp.include_router(music.router)

    # Start polling
    logging.info("Starting Euphorian Bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from backend.core.config import settings

# Initialize Bot and Dispatcher
# Note: parse_mode is now set via DefaultBotProperties in newer aiogram versions
bot = Bot(
    token=settings.TELEGRAM_TOKEN, 
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

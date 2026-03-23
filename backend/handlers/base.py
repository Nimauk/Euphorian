from aiogram import Router, types
from aiogram.filters import CommandStart, Command, CommandObject
from backend.handlers.music import handle_music_request

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    """
    Handler for /start command. Supports deep linking for music.
    """
    if command.args:
        # If there are arguments, treat them as a music request
        return await handle_music_request(message, query=command.args)
        
    await message.answer(
        f"Hola {message.from_user.full_name}! 👋\n\n"
        "Soy **Euphorian**, tu bot privado de música.\n"
        "Envíame un nombre de canción o un link de YouTube para empezar."
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """
    Handler for /help command
    """
    await message.answer(
        "**Comandos disponibles:**\n"
        "/start - Iniciar el bot\n"
        "/help - Mostrar esta ayuda\n\n"
        "Simplemente envíame el nombre de una canción o un link de YouTube."
    )

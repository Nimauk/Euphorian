import logging
from typing import Optional, Tuple
from backend.core.config import settings

logger = logging.getLogger(__name__)

async def is_user_allowed(user_id: int) -> bool:
    if not settings.ALLOWED_USER_IDS:
        logger.warning("ALLOWED_USER_IDS is empty. All users are blocked by default.")
        return False
    return user_id in settings.ALLOWED_USER_IDS

async def validate_youtube_url(url: str) -> Tuple[bool, Optional[dict], str]:
    import subprocess
    import json
    import asyncio
    
    # Use subprocess to call yt-dlp directly
    cmd = [
        "venv/bin/yt-dlp",
        "--simulate",
        "--print-json",
        "--no-playlist",
        "--no-check-certificate",
        url
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            logger.error(f"yt-dlp validation error for '{url}': {error_msg}")
            return False, None, error_msg
        
        info = json.loads(stdout.decode())
        
        if not info:
            return False, None, "No se pudo obtener información del vídeo."
            
        # Special check for searches which return a list of entries
        if 'entries' in info:
            if not info['entries'] or info['entries'][0] is None:
                return False, None, "No se encontraron resultados."
            info_to_check = info['entries'][0]
        else:
            info_to_check = info

        if info_to_check.get('is_live'):
            return False, None, "No puedo procesar streamings en directo. 🔴"
        
        duration = info_to_check.get('duration')
        if duration and duration > 900:
            return False, None, "El vídeo es demasiado largo. El límite es de 15 minutos. ⏳"
        
        return True, info, ""
        
    except Exception as e:
        logger.error(f"Error during subprocess validation for '{url}': {e}")
        return False, None, str(e)

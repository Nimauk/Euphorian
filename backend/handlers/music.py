from aiogram import Router, types, F
from aiogram.types import FSInputFile, BufferedInputFile
from backend.utils.validators import is_user_allowed, validate_youtube_url
from backend.services.downloader import downloader
from backend.services.metadata import metadata_service
from backend.utils.file_manager import cleanup_files, file_manager
from backend.core.bot import bot
import logging
import os

router = Router()
logger = logging.getLogger(__name__)

async def _process_and_send_music(message: types.Message, status_msg: types.Message, result: dict):
    """
    Helper to process metadata, apply tags, and send the audio file.
    """
    mp3_path = result['mp3_path']
    thumb_path = result['thumbnail_path']
    
    # 1. Get clean metadata (Spotify-enabled)
    meta = await metadata_service.get_clean_metadata(result.get("original_title", "Unknown"))
    artist = meta["artist"]
    title = meta["title"]
    
    # 2. Download HD cover from Spotify if available
    final_thumb = thumb_path
    if meta.get("cover_url"):
        hd_thumb_path = f"{mp3_path}.jpg"
        if file_manager.download_remote_file(meta["cover_url"], hd_thumb_path):
            final_thumb = hd_thumb_path
            logger.info(f"Using HD Spotify cover: {final_thumb}")
    
    # 3. Apply tags
    metadata_service.apply_tags(mp3_path, artist, title, final_thumb)
    
    # 4. Prepare caption
    caption = f"✅ **{title}**\n👤 {artist}"
    if meta.get("album"):
        caption += f"\n💿 {meta['album']}"
    if meta.get("is_spotify"):
        caption += "\n✨ *Metadatos Premium (Spotify)*"
    
    # 5. Delivery
    try:
        await message.answer_audio(
            BufferedInputFile.from_file(mp3_path),
            caption=caption,
            thumbnail=BufferedInputFile.from_file(final_thumb) if final_thumb and os.path.exists(final_thumb) else None,
            parse_mode="Markdown",
            performer=artist,
            title=title
        )
        if status_msg:
            try:
                await status_msg.delete()
            except:
                pass
    except Exception as e:
        logger.error(f"Error sending audio: {e}")
        if status_msg:
            await status_msg.edit_text("❌ Error al enviar el archivo.")
    finally:
        # Cleanup
        all_to_clean = [mp3_path]
        if thumb_path: all_to_clean.append(thumb_path)
        if final_thumb and final_thumb != thumb_path: all_to_clean.append(final_thumb)
        cleanup_files(*all_to_clean)

@router.message(F.text)
async def handle_music_request(message: types.Message, query: str = None):
    """
    Primary entry point for music links or search text.
    """
    user_id = message.from_user.id
    text_content = query if query else message.text
    logger.info(f"Received message from {user_id}: {text_content[:50]}")
    
    # 1. Authorization Check (Gatekeeper)
    allowed = await is_user_allowed(user_id)
    if not allowed:
        logger.warning(f"Unauthorized access attempt from user_id: {user_id}")
        await message.answer(f"⚠️ Acceso denegado. Tu ID ({user_id}) no está en la lista blanca.")
        return

    content = text_content.strip()
    logger.info(f"Processing content: {content[:50]}")
    
    # 2. Extract URL or query
    if content.startswith(('http://', 'https://')):
        if 'spotify.com' in content:
            status_msg = await message.answer("🎵 Detectada playlist de Spotify. Extrayendo canciones...")
            tracks = await downloader.get_playlist_tracks(content)
            if not tracks:
                await status_msg.edit_text("❌ No pude extraer canciones de ese link de Spotify.")
                return
            
            await status_msg.edit_text(f"✅ Encontradas {len(tracks)} canciones. Empezando descarga secuencial...")
            for i, track in enumerate(tracks):
                track_name = f"{track['artist']} {track['title']}"
                await message.answer(f"📦 Procesando ({i+1}/{len(tracks)}): **{track_name}**")
                
                # Search for the track on YouTube
                search_url = f"ytsearch1:{track_name}"
                is_valid, info, error = await validate_youtube_url(search_url)
                if not is_valid:
                    continue
                
                video_url = info['entries'][0]['webpage_url'] if 'entries' in info else info.get('webpage_url')
                res = await downloader.download_audio(video_url)
                if res.get('success'):
                    mp3 = res['mp3_path']
                    thumb = res['thumbnail_path']
                    # Clean and Tag
                    meta = await metadata_service.get_clean_metadata(info['entries'][0]['title'] if 'entries' in info else info.get('title'))
                    metadata_service.apply_tags(mp3, meta['artist'], meta['title'], thumb)
                    # Send
                    audio = FSInputFile(mp3, filename=f"{meta['artist']} - {meta['title']}.mp3")
                    await message.answer_audio(audio=audio, performer=meta['artist'], title=meta['title'])
                    cleanup_files(mp3, thumb)
            
            await status_msg.edit_text("✅ Migración de playlist completada.")
            return

        status_msg = await message.answer("🔍 Validando enlace...")
        is_valid, info, error = await validate_youtube_url(content)
        
        if not is_valid:
            await status_msg.edit_text(f"❌ {error}")
            return
        
        await status_msg.edit_text(f"📥 Descargando: **{info.get('title', 'Canción')}**...")
        
        result = await downloader.download_audio(content)
        if result.get('success'):
            await _process_and_send_music(message, status_msg, result)
        else:
            await status_msg.edit_text(f"❌ Error en la descarga: {result.get('error')}")
            # Ensure cleanup if partially downloaded (rare but safe)
            cleanup_files(result.get("mp3_path"), result.get("thumbnail_path"))
            
    else:
        # Use AI to parse intent
        status_msg = await message.answer("🤖 Procesando con IA...")
        try:
            intent = await metadata_service.get_intent(content)
        except Exception as e:
            logger.error(f"AI intent parsing failed (likely quota): {e}")
            # Fallback: Treat everything as a search request if AI fails
            intent = {
                "is_download_request": True,
                "search_query": content,
                "response": None
            }
        
        if intent.get("is_download_request"):
            query = intent.get("search_query", content)
            await status_msg.edit_text(f"🔎 Buscando: **{query}**...")
            # Use yt-dlp to find the first result
            search_url = f"ytsearch1:{query}"
            is_valid, info, error = await validate_youtube_url(search_url)
            
            if not is_valid or not info:
                await status_msg.edit_text(f"❌ No encontré resultados para: {query}")
                return
            
            # Now we have a valid video info from search
            try:
                if 'entries' in info and info['entries']:
                    first_entry = info['entries'][0]
                    if first_entry:
                        video_url = first_entry.get('webpage_url')
                        raw_title = first_entry.get('title')
                    else:
                        raise ValueError("La primera entrada del resultado de búsqueda es nula.")
                else:
                    video_url = info.get('webpage_url')
                    raw_title = info.get('title')
                
                if not video_url:
                    raise ValueError("No se pudo extraer la URL del vídeo.")
                
            except (KeyError, IndexError, ValueError) as e:
                logger.error(f"Error parsing search info for '{query}': {e}")
                await status_msg.edit_text(f"❌ Error al procesar el resultado de búsqueda: {str(e)}")
                return
            
            await status_msg.edit_text(f"📥 Descargando...")
            result = await downloader.download_audio(video_url)
            if result.get('success'):
                # result['original_title'] for search flow should be the raw_title from search
                result['original_title'] = raw_title
                await _process_and_send_music(message, status_msg, result)
            else:
                await status_msg.edit_text(f"❌ Error: {result.get('error')}")
                cleanup_files(result.get("mp3_path"), result.get("thumbnail_path"))
        else:
            await status_msg.edit_text(intent.get("response", "¿En qué puedo ayudarte?"))

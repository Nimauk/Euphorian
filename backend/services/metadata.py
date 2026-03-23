import os
import json
import logging
import re
import google.generativeai as genai
from mutagen.id3 import ID3, TIT2, TPE1, APIC, error
from mutagen.mp3 import MP3
from backend.core.config import settings
from backend.services.spotify_service import spotify_service

logger = logging.getLogger(__name__)

class MetadataService:
    def __init__(self):
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
            logger.warning("GEMINI_API_KEY not found or invalid. AI cleaning will be skipped.")

    def _clean_title_fallback(self, title: str) -> dict:
        """
        Regex fallback to clean typical YouTube titles when AI fails.
        """
        # Remove common suffixes and prefixes
        clean = title
        patterns = [
            r'\(?Official (Video|Music Video|Audio|Lyric Video)?\)?',
            r'\[(Official (Video|Music Video|Audio|Lyric Video)?)?\]',
            r'\(?HD\)?', r'\(?4K\)?', r'\(?8K\)?',
            r'\(?Lyirics\)?', r'\(?Letra\)?',
            r'\s*\|\s*.*', # Everything after a pipe
            r'\s*-\s*Official.*',
        ]
        for p in patterns:
            clean = re.sub(p, '', clean, flags=re.IGNORECASE)
        
        # Try to split by "-" for artist and title
        parts = clean.split(' - ', 1)
        if len(parts) == 2:
            return {"artist": parts[0].strip(), "title": parts[1].strip()}
        
        return {"artist": "Unknown Artist", "title": clean.strip()}

    async def get_clean_metadata(self, raw_title: str) -> dict:
        # Step 1: Basic regex clean to have a good search query
        fallback = self._clean_title_fallback(raw_title)
        query = f"{fallback['artist']} {fallback['title']}"
        
        # Step 2: Try Spotify for HD metadata and cover
        spotify_data = spotify_service.search_track(query)
        if spotify_data:
            return {
                "artist": spotify_data["artist"],
                "title": spotify_data["title"],
                "album": spotify_data.get("album"),
                "cover_url": spotify_data.get("cover_url"),
                "is_spotify": True
            }

        # Step 3: Try AI if Spotify fails
        if not self.model:
            return fallback
        
        prompt = (
            f"Extract the real artist and song title from this YouTube video title: '{raw_title}'. "
            "Ignore trash like 'Official Video', '4K', etc. Return ONLY a JSON object with keys 'artist' and 'title'."
        )
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.model.generate_content, prompt)
            text = response.text.strip()
            if text.startswith('```json'):
                text = text.replace('```json', '').replace('```', '').strip()
            data = json.loads(text)
            return {"artist": data.get("artist", "Unknown Artist"), "title": data.get("title", raw_title)}
        except Exception as e:
            logger.error(f"Error calling Gemini for title '{raw_title}': {e}")
            return self._clean_title_fallback(raw_title)

    async def get_intent(self, text: str) -> dict:
        """
        Analyzes user text with a Persona-driven prompt.
        Returns {'is_download_request': bool, 'search_query': str, 'response': str}
        """
        if not self.model:
            return {"is_download_request": False, "search_query": text, "response": "Cerebro desconectado."}

        prompt = (
            "Eres Euphorian, un asistente de música inteligente y con estilo. "
            f"Tu tarea es analizar este mensaje del usuario: '{text}'.\n\n"
            "INSTRUCCIONES:\n"
            "1. Si el usuario quiere buscar/descargar música (o menciona artistas/canciones), "
            "responde con 'is_download_request': true y pon la búsqueda sugerida en 'search_query'.\n"
            "2. Si el usuario te saluda o quiere hablar de música, responde con 'is_download_request': false "
            "y escribe una respuesta con personalidad en 'response' (sé amable, breve y usa algún emoji musical).\n"
            "3. Si el usuario pide algo que no puedes hacer, explícaselo con estilo.\n\n"
            "Responde EXCLUSIVAMENTE en formato JSON plano: "
            "{'is_download_request': bool, 'search_query': 'string', 'response': 'string'}"
        )
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.model.generate_content, prompt)
            text_res = response.text.strip()
            if text_res.startswith('```json'):
                text_res = text_res.replace('```json', '').replace('```', '').strip()
            data = json.loads(text_res)
            return {
                "is_download_request": data.get("is_download_request", False),
                "search_query": data.get("search_query", text),
                "response": data.get("response", "¿Buscamos algo de música? 🎵")
            }
        except Exception as e:
            logger.error(f"Error parsing intent: {e}")
            return {
                "is_download_request": True,
                "search_query": text,
                "response": None
            }

    def apply_tags(self, file_path: str, artist: str, title: str, thumbnail_path: str = None):
        try:
            from mutagen.id3 import ID3, TPE1, TIT2, APIC, error
            try:
                tags = ID3(file_path)
            except error:
                tags = ID3()
            
            tags.add(TPE1(encoding=3, text=artist))
            tags.add(TIT2(encoding=3, text=title))
            
            if thumbnail_path and os.path.exists(thumbnail_path):
                with open(thumbnail_path, 'rb') as img:
                    mime = 'image/jpeg'
                    if str(thumbnail_path).lower().endswith('.png'):
                        mime = 'image/png'
                    tags.add(APIC(encoding=3, mime=mime, type=3, desc='Cover', data=img.read()))
                logger.info(f"Added cover art from {thumbnail_path}")
            
            tags.save(file_path, v2_version=3)
            logger.info(f"Tags applied successfully to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error tagging {file_path}: {e}")
            return False

metadata_service = MetadataService()

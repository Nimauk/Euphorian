import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import logging
from backend.core.config import settings

logger = logging.getLogger(__name__)

class SpotifyService:
    def __init__(self):
        self.sp = None
        if settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET:
            try:
                auth_manager = SpotifyClientCredentials(
                    client_id=settings.SPOTIFY_CLIENT_ID,
                    client_secret=settings.SPOTIFY_CLIENT_SECRET
                )
                self.sp = spotipy.Spotify(auth_manager=auth_manager)
                logger.info("Spotify Service initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Spotify Service: {e}")
        else:
            logger.warning("Spotify credentials not found. Spotify features will be disabled.")

    def search_track(self, query: str) -> dict:
        """
        Search for a track on Spotify and return metadata and high-res cover.
        """
        if not self.sp:
            return None
        
        try:
            results = self.sp.search(q=query, limit=1, type='track')
            tracks = results.get('tracks', {}).get('items', [])
            
            if not tracks:
                logger.info(f"No Spotify results found for: {query}")
                return None
            
            track = tracks[0]
            album = track.get('album', {})
            
            # Get the highest resolution image
            images = album.get('images', [])
            cover_url = images[0]['url'] if images else None
            
            return {
                "artist": track['artists'][0]['name'],
                "title": track['name'],
                "album": album.get('name'),
                "release_date": album.get('release_date'),
                "cover_url": cover_url,
                "spotify_url": track['external_urls'].get('spotify')
            }
        except Exception as e:
            logger.error(f"Error searching Spotify for '{query}': {e}")
            return None

spotify_service = SpotifyService()

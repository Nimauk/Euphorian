import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DownloaderService:
    """
    Service for downloading audio from YouTube using yt-dlp.
    """
    
    def __init__(self, download_path: str = "downloads"):
        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)

    async def download_audio(self, url: str) -> dict:
        import subprocess
        import json
        import asyncio
        
        # Using a unique ID for the filename to avoid collisions
        output_template = str(self.download_path / "%(id)s.%(ext)s")
        
        # Build the command for subprocess
        # We use flags that correspond to the ydl_opts we had before
        cmd = [
            "venv/bin/yt-dlp",
            "--format", "bestaudio/best",
            "--no-check-certificate",
            "--no-playlist",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "192",
            "--write-thumbnail",
            "--convert-thumbnails", "jpg",
            "--embed-thumbnail",
            "--add-metadata",
            "--print-json",
            "--output", output_template,
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
                logger.error(f"yt-dlp download error for '{url}': {error_msg}")
                return {"success": False, "error": error_msg}
            
            # Extract info from json output
            info = json.loads(stdout.decode())
            video_id = info['id']
            mp3_path = self.download_path / f"{video_id}.mp3"
            
            # Thumbnail check
            thumbnail_path = None
            for ext in ['jpg', 'png', 'webp', 'jpeg']:
                potential_thumb = self.download_path / f"{video_id}.{ext}"
                if potential_thumb.exists():
                    thumbnail_path = potential_thumb
                    break
            
            return {
                "success": True,
                "mp3_path": str(mp3_path),
                "thumbnail_path": str(thumbnail_path) if thumbnail_path else None,
                "original_title": info.get('title', 'Unknown Title')
            }
            
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return {"success": False, "error": str(e)}

downloader = DownloaderService()

# Skill: Audio Downloader & Metadata Processor

## Objetivo
Descargar el audio de un vídeo verificado de YouTube, limpiar el título usando IA para extraer artista y canción, e incrustar esta información (junto con la miniatura) en las etiquetas ID3 del archivo MP3.

## Flujo de Trabajo
1. **Input:** Recibe la URL validada del skill `Gatekeeper`.
2. **Descarga:** Ejecuta `yt-dlp` configurado para:
   - Extraer audio en formato MP3 (`libmp3lame`, 192kbps o 320kbps).
   - Descargar el *thumbnail* del vídeo (`--write-thumbnail`).
3. **Procesamiento LLM:** Envía el título original del vídeo a la API de Gemini con un prompt restrictivo (System Instruction) para que devuelva un JSON estricto con las claves `artista` y `titulo`.
4. **Manipulación ID3 (`mutagen`):**
   - Aplica el `artista` y `titulo` devueltos por la IA a las etiquetas del MP3.
   - Lee el *thumbnail* descargado (JPG/PNG), lo recorta a formato cuadrado (opcional) y lo adjunta como etiqueta `APIC` (Attached Picture).
5. **Limpieza Intermedia:** Borra el archivo del *thumbnail* para no dejar rastros, conservando solo el MP3 final.
6. **Output:** Devuelve la ruta absoluta (Path) del archivo MP3 listo en el servidor.
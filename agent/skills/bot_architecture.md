# Arquitectura del Bot de Música



## Objetivo Principal

Crear el backend de un bot de Telegram privado para descargar música desde YouTube, procesar y limpiar sus metadatos usando Inteligencia Artificial, y enviar el archivo final al usuario.



**ESTRICTAMENTE PROHIBIDO:** No usar la API de Spotify, ni `spotipy`, ni ninguna dependencia relacionada con Spotify. Este proyecto es 100% independiente.



## Flujo de Trabajo (Paso a Paso)

1. **Input:** El usuario envía un texto (ej. "Thunderstruck AC/DC") o un enlace de YouTube al bot de Telegram.

2. **Descarga:** El módulo de descargas usa `yt-dlp` para buscar ese texto en YouTube, descargar el mejor audio disponible y convertirlo a formato MP3.

3. **Procesamiento de Texto:** Se extrae el título original del vídeo descargado.

4. **IA Ligera:** Se envía el título a la API de Gemini para que devuelva únicamente un JSON estructurado con el `artista` real y el `titulo` de la canción (ignorando basura como "HD", "Oficial", "Resubido por Juan").

5. **Etiquetado:** Se incrustan esos datos en las etiquetas ID3 del archivo MP3.

6. **Entrega y Limpieza:** El bot envía el MP3 final por el chat de Telegram y, acto seguido, elimina el archivo local del servidor para no ocupar espacio.


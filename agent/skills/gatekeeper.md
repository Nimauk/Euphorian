# Skill: Gatekeeper & Sanity Check

## Objetivo
Actuar como la primera capa de defensa del bot. Valida la identidad del usuario y comprueba que el recurso solicitado en YouTube sea seguro de procesar (no es un directo, no excede la duración máxima).

## Flujo de Trabajo
1. **Autorización:** Intercepta el `user_id` del mensaje de Telegram.
2. **Cruce de Datos:** Compara el `user_id` con una variable de entorno `ALLOWED_USERS` (lista blanca). Si no coincide, rechaza la petición silenciosamente o con un mensaje genérico.
3. **Pre-extracción (Sanity Check):** Si el usuario está autorizado, toma el input (URL o texto) y ejecuta `yt-dlp` en modo simulado (`--dump-json`) para obtener la metadata sin descargar el vídeo.
4. **Validación de Carga:**
   - Si `is_live` es `True` -> Abortar (es un streaming).
   - Si `duration` es mayor a 900 segundos (15 min) -> Abortar (archivo demasiado grande).
5. **Output:** Devuelve al siguiente nodo la URL directa del vídeo verificado y su título original en YouTube.
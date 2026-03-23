# Skill: Delivery & Janitor (Recolector de Basura)

## Objetivo
Entregar el archivo de audio procesado al usuario a través de Telegram y garantizar la eliminación absoluta de los archivos temporales en el disco del servidor para evitar saturación de almacenamiento.

## Flujo de Trabajo
1. **Input:** Recibe la ruta absoluta del MP3 procesado y el `chat_id` del usuario.
2. **Subida:** Utiliza el método `send_document` o `send_audio` de la API de Telegram para transmitir el archivo. Se implementa un `timeout` alto para prevenir cortes en la subida.
3. **Limpieza (Bloque `finally`):**
   - Independientemente de si la subida fue exitosa, falló por red, o el usuario canceló la petición, se ejecuta un `os.remove()` sobre la ruta del archivo.
   - Se registra en el log del sistema si la eliminación fue exitosa o si hubo un bloqueo de archivo (File in Use).
4. **Output:** Confirmación de entrega al sistema y cierre del ciclo de la petición.
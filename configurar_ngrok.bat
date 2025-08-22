@echo off
echo ============================================
echo      CONFIGURACION DE NGROK PARA FACEBOOK
echo ============================================
echo.

echo [PASO 1] Descarga ngrok si no lo tienes:
echo https://ngrok.com/download
echo.

echo [PASO 2] Ejecuta este comando en otra terminal:
echo ngrok http 5000
echo.

echo [PASO 3] Copia la URL HTTPS que te dara ngrok
echo (Ejemplo: https://abc123.ngrok.io)
echo.

echo [PASO 4] Ve a Facebook Developers:
echo https://developers.facebook.com/apps/
echo.

echo [PASO 5] Configura el Webhook:
echo URL: https://TU_URL_NGROK.ngrok.io/webhook
echo Token: mi_token_secreto_marketplace_2024
echo.

echo [PASO 6] Suscribete a estos eventos:
echo - messages
echo - messaging_postbacks
echo.

echo ============================================
echo         TUS TOKENS CONFIGURADOS:
echo ============================================
echo ✓ PAGE_ACCESS_TOKEN: EAAJNMIKacyw... (configurado)
echo ✓ FACEBOOK_APP_SECRET: b34b6e3f... (configurado)
echo ✓ VERIFY_TOKEN: mi_token_secreto_marketplace_2024
echo ============================================
echo.

echo Presiona cualquier tecla para abrir Facebook Developers...
pause >nul
start https://developers.facebook.com/apps/

echo.
echo Presiona cualquier tecla para abrir ngrok download...
pause >nul
start https://ngrok.com/download

echo.
echo ¡Configuracion lista! Ejecuta ngrok en otra terminal.
echo.
pause
@echo off
echo ============================================
echo   INICIANDO BOT DE FACEBOOK MARKETPLACE
echo ============================================
echo.

cd /d "C:\Users\datila\Desktop\marketplace-bot-local"

echo [1/3] Verificando dependencias...
python -c "import flask; print('✓ Flask instalado')" 2>nul || (
    echo ✗ Flask no instalado. Instalando...
    pip install -r requirements.txt
)

echo.
echo [2/3] Iniciando servidor del bot...
echo Server: http://localhost:5000
echo Test: http://localhost:5000/test
echo Admin: http://localhost:5000/admin
echo.

echo [3/3] ¡Bot iniciado! Presiona Ctrl+C para parar
echo.
echo ============================================
echo   INSTRUCCIONES PARA FACEBOOK:
echo ============================================
echo 1. Instala ngrok: https://ngrok.com/download
echo 2. En otra terminal ejecuta: ngrok http 5000
echo 3. Copia la URL HTTPS de ngrok
echo 4. Ve a Facebook Developers y configura webhook
echo 5. Lee CONFIGURACION_FACEBOOK.md para más detalles
echo ============================================
echo.

python app.py
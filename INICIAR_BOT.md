# 🚀 INICIAR BOT DE FACEBOOK

## Pasos para activar el bot:

### 1. Servidor Local (Ya está corriendo ✅)
```bash
cd "C:\Users\datila\Desktop\marketplace-bot-local"
python app.py
```

### 2. Ngrok (NECESARIO - NO ESTÁ CORRIENDO ❌)
**En una nueva terminal:**
```bash
ngrok http 5000
```

**Obtendrás una URL como:**
```
https://abc123.ngrok.io
```

### 3. Configurar Webhook en Facebook
1. Ir a: https://developers.facebook.com/apps/
2. Seleccionar tu app
3. Messenger > Settings > Webhooks
4. Configurar:
   - **URL**: `https://TU_URL_NGROK.ngrok.io/webhook`
   - **Verify Token**: `mi_token_secreto_marketplace_2024`
   - **Suscribirse a**: messages, messaging_postbacks

### 4. Probar
- Enviar mensaje a tu página de Facebook
- Verificar logs en la terminal del bot

## 🔍 Verificar Estado
```bash
python verificar_facebook_simple.py
```

## 📝 Tokens Configurados ✅
- PAGE_ACCESS_TOKEN: OK (215 chars)
- FACEBOOK_APP_SECRET: OK (32 chars)  
- VERIFY_TOKEN: mi_token_secreto_marketplace_2024

## ⚠️ El problema actual:
**NGROK NO ESTÁ CORRIENDO** - Por eso no llegan mensajes de Facebook